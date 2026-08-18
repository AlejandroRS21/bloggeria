"""
Morphological style-adherence analysis.

For each generated article, compares quantitative morphological features against
the assigned author's style profile and produces a 0-100 adherence score, then
adds an LLM judge verdict. Combined score = 0.5*morph + 0.5*llm.

Features (language-aware via spaCy es/en):
  - avg sentence length (words)
  - type-token ratio (lexical richness)
  - 1st/2nd person verb ratio (voice)
  - exclamation/question density (tone)
  - vocabulary overlap with profile['vocabulary'] + expressions
  - avg paragraph length
"""
import json, re, os, statistics, urllib.request
from pathlib import Path
from html import unescape

import spacy

PROFILE_DIR = Path(__file__).parent.parent / "profiles"
_NLP = {}

# map blogger preset id -> profile filename stem
ID_TO_PROFILE = {
    "javipas": "javipas", "microsiervos": "microsiervos", "simonwillison": "simon_willison",
    "jvns": "julia_evans", "danluu": "dan_luu", "overreacted": "dan_abramov",
    "kiko-llaneras": "kiko_llaneras", "ezra-klein": "ezra_klein", "zenda-libros": "zenda_libros",
    "marginalian": "marginalian", "el-comidista": "el_comidista", "serious-eats": "serious_eats",
    "lecturas-cotilleos": "lecturas_cotilleos",
}

# map display name -> profile stem (style_source stores the display name)
NAME_TO_PROFILE = {
    "JaviPas": "javipas", "Microsiervos": "microsiervos", "Simon Willison": "simon_willison",
    "Julia Evans": "julia_evans", "Dan Luu": "dan_luu", "Dan Abramov": "dan_abramov",
    "Kiko Llaneras": "kiko_llaneras", "Ezra Klein": "ezra_klein", "Zenda": "zenda_libros",
    "The Marginalian": "marginalian", "El Comidista": "el_comidista", "Serious Eats": "serious_eats",
    "Lecturas": "lecturas_cotilleos",
}


def _nlp(lang):
    key = "es" if lang == "es" else "en"
    if key not in _NLP:
        _NLP[key] = spacy.load("es_core_news_sm" if key == "es" else "en_core_web_sm")
    return _NLP[key]


def strip_html(html):
    text = re.sub(r"<[^>]+>", " ", html or "")
    return re.sub(r"\s+", " ", unescape(text)).strip()


def morph_features(text, lang):
    nlp = _nlp(lang)
    doc = nlp(text[:100000])
    sents = [s for s in doc.sents if len(s.text.strip()) > 0]
    words = [t for t in doc if t.is_alpha]
    n_words = max(len(words), 1)
    n_sents = max(len(sents), 1)

    # sentence length
    avg_sent_len = n_words / n_sents
    # lexical richness
    ttr = len(set(t.lower_ for t in words)) / n_words
    # person: 1st/2nd person pronouns + verb morphology
    first_second = 0
    for t in words:
        morph = t.morph.to_dict()
        person = morph.get("Person")
        if person in ("1", "2"):
            first_second += 1
    person_ratio = first_second / n_words
    # tone: punctuation density
    excl = text.count("!") + text.count("¡")
    ques = text.count("?") + text.count("¿")
    punct_density = (excl + ques) / n_sents

    return {
        "avg_sentence_length": round(avg_sent_len, 2),
        "ttr": round(ttr, 3),
        "person_ratio": round(person_ratio, 4),
        "punct_density": round(punct_density, 3),
        "n_words": n_words,
        "n_sentences": n_sents,
    }


def vocab_overlap(text, profile):
    low = text.lower()
    vocab = [w.lower() for w in profile.get("vocabulary", [])]
    exprs = [e.lower() for e in profile.get("expressions", []) + profile.get("transition_phrases", [])]
    v_hits = sum(1 for w in vocab if w in low)
    e_hits = sum(1 for e in exprs if e in low)
    v_score = v_hits / max(len(vocab), 1)
    e_score = e_hits / max(len(exprs), 1)
    return {
        "vocab_hits": v_hits, "vocab_total": len(vocab), "vocab_score": round(v_score, 3),
        "expr_hits": e_hits, "expr_total": len(exprs), "expr_score": round(e_score, 3),
    }


def morph_score(feat, prof, vov):
    """Heuristic 0-100 from feature adherence to profile expectations."""
    score = 0.0
    # sentence pattern: profiles say 'frases cortas' -> reward < 20 wpm
    sp = (prof.get("sentence_pattern", "") + prof.get("paragraph_pattern", "")).lower()
    if any(k in sp for k in ["corta", "breve", "short", "punchy"]):
        score += 20 if feat["avg_sentence_length"] <= 20 else 8
    else:
        score += 20 if 15 <= feat["avg_sentence_length"] <= 32 else 10
    # voice: 1st/2nd person expected for 'tú a tú' / 'primera persona'
    voice = prof.get("voice", "").lower()
    if any(k in voice for k in ["primera persona", "tú", "first person", "you", "conversational"]):
        score += 20 if feat["person_ratio"] >= 0.02 else 8
    else:
        score += 15
    # lexical richness sanity
    score += 15 if 0.30 <= feat["ttr"] <= 0.75 else 7
    # tone punctuation for humor/irreverent
    tone = (prof.get("tone", "") + prof.get("use_of_humor", "")).lower()
    if any(k in tone for k in ["exclam", "irreverent", "cachond", "humor", "desvergon"]):
        score += 15 if feat["punct_density"] >= 0.15 else 6
    else:
        score += 12
    # vocabulary + expressions (30 pts)
    score += 20 * vov["vocab_score"] + 10 * min(vov["expr_score"] * 3, 1.0)
    return round(min(score, 100), 1)


def llm_judge(text, prof, blogger_name, lang):
    """Ask the LLM to rate style adherence 0-100 with a one-line reason."""
    or_key = os.getenv("OPENROUTER_API_KEY")
    snippet = text[:2500]
    profile_desc = (
        f"Autor: {blogger_name}\nTono: {prof.get('tone')}\nVoz: {prof.get('voice')}\n"
        f"Patrón de frase: {prof.get('sentence_pattern')}\nHumor: {prof.get('use_of_humor')}\n"
        f"Vocabulario típico: {', '.join(prof.get('vocabulary', [])[:10])}\n"
        f"Expresiones: {', '.join(prof.get('expressions', [])[:6])}"
    )
    prompt = (
        f"Eres un analista de estilo literario. Este es el perfil del autor:\n{profile_desc}\n\n"
        f"Texto generado (fragmento):\n\"\"\"{snippet}\"\"\"\n\n"
        "¿En qué grado el texto imita el estilo de ese autor? Responde SOLO con JSON: "
        '{\"score\": <0-100>, \"reason\": \"<una frase>\"}'
    )
    if not or_key:
        return None
    body = json.dumps({
        "model": "nvidia/nemotron-3-super-120b-a12b:free",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2, "max_tokens": 200,
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {or_key}", "Content-Type": "application/json",
                 "HTTP-Referer": "https://blogger-agent-tfg.vercel.app", "X-Title": "BloggerIA"})
    try:
        r = urllib.request.urlopen(req, timeout=90)
        content = json.loads(r.read().decode())["choices"][0]["message"]["content"]
        from aphra_blogger.llm.json_utils import extract_json
        return extract_json(content)
    except Exception as e:
        return {"score": None, "reason": f"judge error: {str(e)[:80]}"}


def analyze(posts):
    results = []
    for p in posts:
        prof_stem = ID_TO_PROFILE.get(p.get("blogger_id")) or NAME_TO_PROFILE.get(p.get("style_source"))
        if not prof_stem:
            print(f"SKIP (no profile): {p.get('title', '')[:40]} | style={p.get('style_source')}")
            continue
        prof_path = PROFILE_DIR / f"{prof_stem}_style_profile.json"
        if not prof_path.exists():
            continue
        prof = json.load(open(prof_path))
        lang = prof.get("language", p.get("lang", "es"))
        blogger_name = p.get("style_source") or p.get("blogger", prof.get("alias", prof_stem))
        text = strip_html(p["content"])
        feat = morph_features(text, lang)
        vov = vocab_overlap(text, prof)
        m = morph_score(feat, prof, vov)
        judge = llm_judge(text, prof, blogger_name, lang)
        j = judge.get("score") if judge else None
        combined = round((m + j) / 2, 1) if isinstance(j, (int, float)) else m
        results.append({
            "title": p["title"], "blogger": blogger_name, "niche": prof.get("niche"),
            "lang": lang, "morph_score": m, "llm_score": j,
            "combined": combined, "features": feat, "vocab": vov,
            "llm_reason": judge.get("reason") if judge else None,
        })
    return results


if __name__ == "__main__":
    import sys
    posts = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "/tmp/regen_posts.json"))
    res = analyze(posts)
    json.dump(res, open("/tmp/style_analysis.json", "w"), ensure_ascii=False, indent=2)
    print(f"{'BLOGGER':18} {'NICHE':11} {'MORPH':>6} {'LLM':>5} {'COMB':>6}  TITLE")
    print("-" * 90)
    for r in sorted(res, key=lambda x: -x["combined"]):
        llm = f"{r['llm_score']}" if r["llm_score"] is not None else "-"
        print(f"{r['blogger'][:17]:18} {str(r['niche'])[:10]:11} {r['morph_score']:6.1f} {llm:>5} {r['combined']:6.1f}  {r['title'][:38]}")
    scores = [r["combined"] for r in res]
    if scores:
        print("-" * 90)
        print(f"MEDIA combined: {statistics.mean(scores):.1f} | min {min(scores):.1f} | max {max(scores):.1f} | n={len(scores)}")

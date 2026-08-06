"""
News Research Agent.

Busca noticias actuales sobre un tema y extrae información relevante
para escribir artículos actualizados.
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NewsArticle:
    """Artículo de noticia encontrado."""

    title: str
    source: str
    url: str
    date: str
    summary: str
    relevance_score: float = 0.0
    full_text: str = ""


@dataclass
class ResearchResult:
    """Resultado de investigación de noticias."""

    topic: str
    search_date: str
    articles: List[NewsArticle]
    key_findings: List[str]
    related_topics: List[str]
    summary: str
    scrape_stats: Optional[Dict[str, int]] = None
    research_synthesis: str = ""


class NewsResearchAgent:
    """
    Agente de investigación de noticias actuales.

    Busca noticias sobre un tema y las organiza para su uso
    en la generación de contenido.
    """

    def __init__(self):
        self.search_tools_available = self._check_search_tools()

    def _check_search_tools(self) -> List[str]:
        """Check what search tools are available."""
        available = []

        # DuckDuckGo: primary search (no API key needed)
        try:
            from duckduckgo_search import DDGS
            # Verify it works with a quick test
            with DDGS() as ddgs:
                list(ddgs.text("test", max_results=1))
            available.append("duckduckgo")
            print("DuckDuckGo search available (primary)")
        except Exception as e:
            print(f"DuckDuckGo search not available: {e}")

        # Check Brave Search via direct HTTP (no package needed)
        import os
        if os.environ.get("BRAVE_API_KEY"):
            available.append("brave")
        else:
            print("Info: BRAVE_API_KEY not set, Brave Search won't be available")

        # Check Exa (code search)
        try:
            from exa_py import Exa

            available.append("exa")
        except ImportError:
            pass

        # Fallback to requests for basic web scraping
        try:
            import requests

            available.append("requests")
        except ImportError:
            pass

        return available

    def _search_brave(self, topic: str, max_articles: int, time_range: str) -> List[NewsArticle]:
        """Search using Brave Search API via direct HTTP (no brave_search package needed)."""
        import requests
        import os

        try:
            api_key = os.environ.get("BRAVE_API_KEY")

            if not api_key:
                print("Warning: BRAVE_API_KEY not set")
                return self._search_fallback(topic, max_articles)

            # Map time range to Brave's freshness format
            freshness_map = {
                "w": "pw",  # past week
                "m": "pm",  # past month
                "y": "py",  # past year
            }
            freshness = freshness_map.get(time_range, "pm")

            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {
                "X-Subscription-Token": api_key,
                "Accept": "application/json",
            }
            params = {
                "q": topic,
                "count": max_articles,
                "freshness": freshness,
                "safesearch": "moderate",
            }

            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            articles = []
            web_results = data.get("web", {}).get("results", [])

            for item in web_results:
                meta_url = item.get("meta_url", {}) or {}
                articles.append(
                    NewsArticle(
                        title=item.get("title", ""),
                        source=meta_url.get("hostname", item.get("profile", {}).get("name", "")),
                        url=item.get("url", ""),
                        date=item.get("age", "") or "",
                        summary=item.get("description", ""),
                    )
                )

            if not articles:
                print(f"Brave Search returned no results for '{topic}', falling back")
                return self._search_fallback(topic, max_articles)

            return articles

        except requests.exceptions.RequestException as e:
            print(f"Brave Search HTTP error: {e}")
            return self._search_fallback(topic, max_articles)
        except Exception as e:
            print(f"Brave Search error: {e}")
            return self._search_fallback(topic, max_articles)

    def _search_duckduckgo(self, topic: str, max_articles: int, time_range: str = "m") -> List[NewsArticle]:
        """Search using DuckDuckGo (no API key needed)."""
        from duckduckgo_search import DDGS

        try:
            # Map time range to DuckDuckGo's format
            # ddg supports: d (day), w (week), m (month), y (year)
            ddg_time = time_range  # already 'd','w','m','y'

            results = []
            with DDGS() as ddgs:
                ddg_results = ddgs.text(
                    topic,
                    max_results=max_articles,
                    region="es-es",
                    safesearch="moderate",
                    timelimit=ddg_time if ddg_time in ("d", "w", "m", "y") else None,
                )
                for item in ddg_results:
                    results.append(
                        NewsArticle(
                            title=item.get("title", ""),
                            source=item.get("source", "") or self._extract_hostname(item.get("href", "")),
                            url=item.get("href", ""),
                            date="",
                            summary=item.get("body", ""),
                        )
                    )

            if not results:
                print(f"DuckDuckGo returned no results for '{topic}', falling back")
                return self._search_fallback(topic, max_articles)

            return results

        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            return self._search_fallback(topic, max_articles)

    @staticmethod
    def _extract_hostname(url: str) -> str:
        """Extract hostname from a URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.hostname or url
        except Exception:
            return url

    def _search_exa(self, topic: str, max_articles: int) -> List[NewsArticle]:
        """Search using Exa (for news)."""
        from exa_py import Exa

        try:
            import os

            api_key = os.environ.get("EXA_API_KEY")

            if not api_key:
                return self._search_fallback(topic, max_articles)

            exa = Exa(api_key)

            results = exa.search(query=topic, num_results=max_articles, type="auto")

            articles = []
            for item in results:
                articles.append(
                    NewsArticle(
                        title=item.get("title", ""),
                        source=item.get("source", ""),
                        url=item.get("url", ""),
                        date=item.get("published", ""),
                        summary=item.get("text", "")[:200],
                    )
                )

            return articles

        except Exception as e:
            print(f"Exa Search error: {e}")
            return self._search_fallback(topic, max_articles)

    def _search_fallback(self, topic: str, max_articles: int) -> List[NewsArticle]:
        """Fallback: basic web search using requests and BeautifulSoup."""
        import requests
        from bs4 import BeautifulSoup
        import urllib.parse

        try:
            # Use DuckDuckGo news
            query = urllib.parse.quote(topic)
            url = f"https://news.google.com/search?q={query}&hl=es"

            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                # Fallback to a simple mock
                return self._mock_news(topic, max_articles)

            soup = BeautifulSoup(response.text, "html.parser")

            articles = []
            # Try to find news articles (Google News structure)
            for item in soup.select("article")[:max_articles]:
                title_elem = item.select_one("h3")
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                link = item.select_one("a")
                url = link.get("href", "") if link else ""

                if url and not url.startswith("http"):
                    url = "https://news.google.com" + url

                articles.append(
                    NewsArticle(
                        title=title,
                        source="Google News",
                        url=url,
                        date=datetime.now().strftime("%Y-%m-%d"),
                        summary=f"Noticia sobre {topic}",
                    )
                )

            if not articles:
                return self._mock_news(topic, max_articles)

            return articles

        except Exception as e:
            print(f"Search fallback error: {e}")
            return self._mock_news(topic, max_articles)

    def _mock_news(self, topic: str, max_articles: int) -> List[NewsArticle]:
        """Mock news for testing when no API available."""
        return [
            NewsArticle(
                title=f"Últimas noticias sobre {topic}",
                source="Noticias Tech",
                url="https://ejemplo.com",
                date=datetime.now().strftime("%Y-%m-%d"),
                summary=f"Desarrollos recientes en el campo de {topic} están generando gran interés.",
            ),
            NewsArticle(
                title=f"{topic}: análisis y perspectivas",
                source="Tech Review",
                url="https://ejemplo.com",
                date=datetime.now().strftime("%Y-%m-%d"),
                summary=f"Expertos analizan el impacto de {topic} en la industria tecnológica.",
            ),
        ]

    def _extract_key_findings(self, articles: List[NewsArticle]) -> List[str]:
        """Extrae los hallazgos clave de las noticias."""
        if not articles:
            return []

        findings = []

        for article in articles[:5]:
            # Take first 150 chars of summary as finding
            summary = article.summary[:150]
            if summary:
                findings.append(summary + "..." if len(article.summary) > 150 else summary)

        return findings

    def _extract_related_topics(self, articles: List[NewsArticle]) -> List[str]:
        """Extrae temas relacionados de las noticias."""
        # Simple extraction - look for capitalized words in titles
        related = set()

        for article in articles:
            words = article.title.split()
            for word in words:
                # Take longer words as potential topics
                if len(word) > 5 and word[0].isupper():
                    related.add(word.rstrip(".,:;"))

        return list(related)[:10]

    def _generate_summary(self, topic: str, articles: List[NewsArticle]) -> str:
        """Genera un resumen de la investigación."""
        if not articles:
            return f"No se encontraron noticias recientes sobre {topic}."

        sources = list(set([a.source for a in articles]))
        sources_str = ", ".join(sources[:5])

        summary = f"""
Investigación sobre '{topic}' - {len(articles)} artículos encontrados.
Fuentes: {sources_str}

Las noticias cubren los últimos desarrollos en {topic}, con enfoque en
{articles[0].summary[:100] if articles else "temas relacionados"}...
"""
        return summary.strip()

    # ------------------------------------------------------------------ #
    # Deep Research: Scraping
    # ------------------------------------------------------------------ #

    def _scrape_with_scrapling(self, url: str, max_chars: int = 5000) -> Optional[str]:
        """Scrape full article text via Scrapling Fetcher (stealth HTTP).

        Uses Scrapling's stealth Fetcher to bypass anti-bot protection and
        extract clean article text. Returns up to max_chars characters.

        Args:
            url: The article URL to scrape.
            max_chars: Maximum characters to return (default 5000).

        Returns:
            Clean article text string, or None on any failure.
        """
        try:
            from scrapling import Fetcher
        except ImportError:
            print("Warning: scrapling not available, skipping deep scrape")
            return None

        try:
            resp = Fetcher.get(url, timeout=30)

            if resp.status >= 400:
                print(f"Scrapling HTTP error {resp.status} for {url}")
                return None

            text = resp.get_all_text(ignore_tags=("script", "style"))
            text_str = str(text).strip()

            if not text_str:
                print(f"Scrapling returned empty content for {url}")
                return None

            return text_str[:max_chars]

        except Exception as e:
            print(f"Scrapling error scraping {url}: {e}")
            return None

    def _scrape_multiple_articles(
        self, articles_data: List[Dict], max_articles: int = 5
    ) -> Tuple[List[Dict], Dict[str, int]]:
        """Scrape multiple article URLs with Scrapling.

        Iterates through article metadata, scraping each URL. Returns a list
        of scraped article dicts and a stats dict with counts.

        Args:
            articles_data: List of dicts with 'title', 'source', 'url' keys.
            max_articles: Maximum number of URLs to scrape (default 5).

        Returns:
            Tuple of (scraped_articles, stats) where:
            - scraped_articles: list of dicts with title, source, url,
              full_text, word_count, scrape_success
            - stats: dict with total, succeeded, failed counts
        """
        scraped = []
        succeeded = 0
        failed = 0
        total = min(len(articles_data), max_articles)

        for article in articles_data[:max_articles]:
            url = article.get("url", "")
            title = article.get("title", "")
            source = article.get("source", "")

            if not url:
                failed += 1
                scraped.append(
                    {
                        "title": title,
                        "source": source,
                        "url": "",
                        "full_text": "",
                        "word_count": 0,
                        "scrape_success": False,
                    }
                )
                continue

            full_text = self._scrape_with_scrapling(url)

            if full_text:
                succeeded += 1
                scraped.append(
                    {
                        "title": title,
                        "source": source,
                        "url": url,
                        "full_text": full_text,
                        "word_count": len(full_text.split()),
                        "scrape_success": True,
                    }
                )
            else:
                failed += 1
                scraped.append(
                    {
                        "title": title,
                        "source": source,
                        "url": url,
                        "full_text": "",
                        "word_count": 0,
                        "scrape_success": False,
                    }
                )

        stats = {"total": total, "succeeded": succeeded, "failed": failed}
        return scraped, stats

    # ------------------------------------------------------------------ #
    # Deep Research: Synthesis
    # ------------------------------------------------------------------ #

    def _synthesize_research(self, articles: List[Dict], llm_provider) -> str:
        """LLM synthesis of scraped articles into a structured research brief.

        Takes scraped article texts and uses the provided LLM to produce a
        structured brief with: key facts, perspectives, quotes, and source list.
        Falls back to raw text concatenation on LLM failure.

        Args:
            articles: List of scraped article dicts (must have scrape_success,
                     full_text, title, source, url keys).
            llm_provider: LLM provider instance (from ContentGenerator).

        Returns:
            Structured brief string (up to 8000 chars), or empty string if
            no articles were successfully scraped.
        """
        successful = [a for a in articles if a.get("scrape_success") and a.get("full_text")]

        if not successful:
            return ""

        # Build a rich synthesis prompt from scraped texts
        prompt_parts = [
            "Synthesize the following article extracts into a structured research brief. "
            "Organize the brief into these sections:\n"
            "- Key Facts & Data: statistics, dates, figures mentioned\n"
            "- Different Perspectives: contrasting viewpoints found across sources\n"
            "- Relevant Context: background information that provides depth\n"
            "- Important Names / Dates / Figures: people, organizations, events cited\n"
            "- Source List: numbered list with titles, source names, and URLs\n\n"
            "SOURCE ARTICLES:",
        ]

        char_budget = 15000  # Total chars to feed to LLM
        used = 0

        for i, article in enumerate(successful, 1):
            text = (article.get("full_text") or "")[:5000]  # per-article cap
            entry = (
                f"\n--- Article {i}: {article.get('title', 'Unknown')} ---\n"
                f"Source: {article.get('source', 'Unknown')} | "
                f"URL: {article.get('url', '')}\n{text}\n"
            )
            if used + len(entry) > char_budget:
                break
            prompt_parts.append(entry)
            used += len(entry)

        prompt_parts.append(
            "\n\nNow produce the structured research brief covering: "
            "key facts & data, different perspectives, relevant context, "
            "important names/dates/figures, and a numbered source list with URLs."
        )

        prompt = "\n".join(prompt_parts)

        try:
            messages = llm_provider.create_messages(
                system_prompt=(
                    "You are a research synthesis assistant. Your job is to extract "
                    "key information from articles and produce a structured, factual "
                    "brief. Be concise, accurate, and cite your sources."
                ),
                user_prompt=prompt,
            )
            response = llm_provider.chat_completion(
                messages, temperature=0.3, max_tokens=2048
            )
            return (response.content or "")[:8000]

        except Exception as e:
            print(f"Synthesis LLM error: {e}, falling back to raw article text")
            fallback_parts = []
            for article in successful:
                text = (article.get("full_text") or "")[:2000]
                title = article.get("title", "Unknown")
                fallback_parts.append(f"\n--- {title} ---\n{text}\n")
            return ("\n".join(fallback_parts))[:8000]

    # ------------------------------------------------------------------ #
    # Modified: research() with deep research pipeline
    # ------------------------------------------------------------------ #

    def _extract_company_name(self, topic: str) -> Optional[str]:
        """Extract the most likely company/product name from a topic.

        Heuristic: take the text before the first comma, or the first 2-3
        capitalized words. Returns None if nothing plausible is found.

        Args:
            topic: The raw topic string.

        Returns:
            Company name string, or None.
        """
        # Before first comma
        if "," in topic:
            candidate = topic.split(",")[0].strip()
            words = candidate.split()
            if 1 <= len(words) <= 5 and any(w[0].isupper() for w in words if w):
                return candidate
        # First 2-3 capitalized words from the whole topic
        words = topic.split()
        cap_words = []
        for w in words:
            if w[0].isupper() and w.lower() not in ("la", "el", "los", "las", "un", "una", "the", "a", "an"):
                cap_words.append(w.strip(",:;.()"))
            elif cap_words:
                break  # stop at first lowercase after a run of caps
        if cap_words:
            return " ".join(cap_words[:3])
        return None

    def _generate_search_queries(self, topic: str) -> List[str]:
        """Generate multiple search query variations from a topic.

        Produces 2-3 queries to maximize coverage: original, key entities,
        and a shortened version. Also adds site-specific queries targeting
        forums and review sites where company-specific discussions live
        (Reddit, Trustpilot, Puntua).

        Args:
            topic: Original user topic.

        Returns:
            List of query strings, best-first.
        """
        queries = [topic]

        # Shorten: remove filler words, keep core subject (first 5 significant words)
        stopwords = {"la", "el", "los", "las", "un", "una", "de", "del", "en",
                     "que", "es", "por", "con", "para", "sobre", "entre",
                     "the", "a", "an", "of", "in", "to", "for", "and", "or"}
        words = topic.split()
        significant = [w for w in words if w.lower() not in stopwords]
        if len(significant) >= 3:
            short = " ".join(significant[:5])
            if short != topic:
                queries.append(short)

        # Key entities: split on commas, use first part if multi-topic
        if "," in topic:
            parts = [p.strip() for p in topic.split(",")]
            for part in parts[:2]:
                if part not in queries and len(part.split()) >= 3:
                    queries.append(part)

        # Site-specific queries for forums / review sites
        company = self._extract_company_name(topic)
        if company:
            for site in ("reddit.com", "trustpilot.com", "puntua.net"):
                queries.append(f"site:{site} {company}")

        # Remove queries that are too short (< 3 words) — they return noise
        # but ALWAYS keep the original topic even if it's short
        original = queries[0] if queries else topic
        queries = [q for q in queries if len(q.split()) >= 3]
        if not queries:
            queries = [original]

        return queries

    def _search_duckduckgo_multi(
        self, topic: str, max_articles: int, time_range: str
    ) -> List[NewsArticle]:
        """Try multiple DuckDuckGo queries and merge unique results.

        Short queries work better with DuckDuckGo, so we generate
        varied queries from the topic and deduplicate by URL.

        Args:
            topic: Original topic to research.
            max_articles: Maximum articles to return.
            time_range: Freshness filter ('w', 'm', 'y').

        Returns:
            List of unique NewsArticle objects, best results first.
        """
        queries = self._generate_search_queries(topic)
        if not queries:
            queries = [topic]

        seen_urls: set = set()
        merged: List[NewsArticle] = []

        per_query = max(3, max_articles // len(queries))
        for q in queries:
            results = self._search_duckduckgo(q, per_query, time_range)
            for article in results:
                if article.url and article.url not in seen_urls:
                    seen_urls.add(article.url)
                    merged.append(article)
                    if len(merged) >= max_articles:
                        return merged

        return merged[:max_articles]

    def _search_brave_multi(
        self, topic: str, max_articles: int, time_range: str
    ) -> List[NewsArticle]:
        """Try multiple search queries and merge unique results.

        Generates query variations from the topic, runs each through
        Brave Search, and merges deduplicated results (by URL) up to
        max_articles. Distributes the article budget across queries to
        ensure diversity — Brave returning different results per query
        is the whole point.

        Args:
            topic: Original topic to research.
            max_articles: Maximum articles to return.
            time_range: Freshness filter ('w', 'm', 'y').

        Returns:
            List of unique NewsArticle objects, best results first.
        """
        queries = self._generate_search_queries(topic)
        seen_urls: set = set()
        merged: List[NewsArticle] = []

        # Distribute budget: smaller per-query to force multi-query diversity
        per_query = max(3, max_articles // len(queries))
        for q in queries:
            results = self._search_brave(q, per_query, time_range)
            for article in results:
                if article.url and article.url not in seen_urls:
                    seen_urls.add(article.url)
                    merged.append(article)
                    if len(merged) >= max_articles:
                        return merged

        return merged[:max_articles]

    def research(
        self,
        topic: str,
        max_articles: int = 10,
        time_range: str = "m",
        llm_provider=None,
        enable_deep_research: bool = True,
    ) -> ResearchResult:
        """
        Investiga noticias actuales sobre un tema.

        Cuando enable_deep_research=True y hay artículos disponibles, también
        scrapea el contenido completo de los artículos y realiza síntesis LLM.

        Args:
            topic: Tema a investigar
            max_articles: Máximo de artículos a buscar
            time_range: 'm' (mes), 'w' (semana), 'y' (año)
            llm_provider: LLM provider para síntesis (opcional)
            enable_deep_research: Si es True, habilita scraping + síntesis

        Returns:
            ResearchResult con noticias, hallazgos clave y datos de
            investigación profunda (scrape_stats, research_synthesis)
        """
        articles = []

        # Search stage: try multiple query variations for better coverage
        if "duckduckgo" in self.search_tools_available:
            articles = self._search_duckduckgo_multi(topic, max_articles, time_range)
        elif "brave" in self.search_tools_available:
            articles = self._search_brave_multi(topic, max_articles, time_range)
        elif "exa" in self.search_tools_available:
            articles = self._search_exa(topic, max_articles)
        else:
            articles = self._search_fallback(topic, max_articles)

        scrape_stats = None
        research_synthesis = ""

        # Deep research: scrape full articles and synthesize
        if enable_deep_research and articles and llm_provider is not None:
            articles_meta = [
                {"title": a.title, "source": a.source, "url": a.url}
                for a in articles
            ]
            scraped_articles, scrape_stats = self._scrape_multiple_articles(
                articles_meta, max_articles=max_articles
            )

            # Enrich NewsArticle objects with scraped full_text
            url_to_scraped = {sa["url"]: sa for sa in scraped_articles if sa["url"]}
            for article in articles:
                if article.url in url_to_scraped:
                    article.full_text = url_to_scraped[article.url].get("full_text", "")

            # Synthesize if LLM is available
            if hasattr(llm_provider, "is_available") and llm_provider.is_available():
                research_synthesis = self._synthesize_research(scraped_articles, llm_provider)

        # Extract key findings
        key_findings = self._extract_key_findings(articles)
        related_topics = self._extract_related_topics(articles)

        # Generate summary
        summary = self._generate_summary(topic, articles)

        return ResearchResult(
            topic=topic,
            search_date=datetime.now().isoformat(),
            articles=articles,
            key_findings=key_findings,
            related_topics=related_topics,
            summary=summary,
            scrape_stats=scrape_stats,
            research_synthesis=research_synthesis,
        )

    # ------------------------------------------------------------------ #
    # Modified: research_and_format_for_generation()
    # ------------------------------------------------------------------ #

    def research_and_format_for_generation(
        self,
        topic: str,
        llm_provider=None,
        max_articles: int = 5,
    ) -> Dict[str, Any]:
        """
        Investiga y formatea los resultados para usar en ContentGenerator.

        Args:
            topic: Tema a investigar
            llm_provider: LLM provider opcional para síntesis
            max_articles: Máximo de artículos a procesar

        Returns:
            Dict con toda la información necesaria para generar contenido,
            incluyendo research_synthesis, scrape_stats y full_text
        """
        result = self.research(
            topic,
            max_articles=max_articles,
            llm_provider=llm_provider,
            enable_deep_research=True,
        )

        # Use LLM synthesis as primary context when available
        context = ""
        if result.research_synthesis:
            context = result.research_synthesis
        else:
            # Fall back to raw context formatting
            context = self._build_context_from_result(result)

        return {
            "topic": result.topic,
            "context": context,
            "articles": [
                {
                    "title": a.title,
                    "source": a.source,
                    "summary": a.summary,
                    "full_text": a.full_text,
                    "url": a.url,
                    "scrape_success": bool(a.full_text),
                }
                for a in result.articles
            ],
            "key_findings": result.key_findings,
            "related_topics": result.related_topics,
            "scrape_stats": result.scrape_stats,
            "research_synthesis": result.research_synthesis,
        }

    def _build_context_from_result(self, result: ResearchResult) -> str:
        """Build the legacy raw context string from a ResearchResult."""
        context = (
            f"\nTEMA ACTUAL: {result.topic}\n"
            f"FECHA: {result.search_date}\n\n"
            "ÚLTIMAS NOTICIAS Y DESARROLLOS:\n"
        )

        for i, article in enumerate(result.articles[:5], 1):
            context += (
                f"\n{i}. {article.title}\n"
                f"   Fuente: {article.source}\n"
                f"   Fecha: {article.date}\n"
                f"   Resumen: {article.summary}\n"
            )

        context += "\nHALLAZGOS CLAVE:\n"
        for finding in result.key_findings[:3]:
            context += f"- {finding}\n"

        context += (
            f'\nTEMAS RELACIONADOS: {", ".join(result.related_topics[:5])}\n\n'
            f"RESUMEN: {result.summary}\n"
        )
        return context


# Convenience function
def research_topic(
    topic: str, llm_provider=None, max_articles: int = 5
) -> Dict[str, Any]:
    """Investiga un tema y retorna el contexto formateado."""
    agent = NewsResearchAgent()
    return agent.research_and_format_for_generation(
        topic, llm_provider=llm_provider, max_articles=max_articles
    )


if __name__ == "__main__":
    # Test
    import sys

    topic = sys.argv[1] if len(sys.argv) > 1 else "inteligencia artificial"

    print(f"Investigando: {topic}")
    print("=" * 50)

    agent = NewsResearchAgent()
    result = agent.research_and_format_for_generation(topic)

    print(result["context"][:1500])
    print("\n...")

"""
Main Orchestrator for Blogger Agent.

Coordinates all agents through a multi-phase workflow:
1. Style Analysis
2. Keyword Extraction
3. Content Generation
4. Critique & Refinement
5. HTML Building
6. Image Selection
"""

import time
import uuid
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from .config import OrchestratorConfig
from .state import StateManager, WorkflowState, PhaseStatus
from .bloggers_registry import get_prebaked_profile
from aphra_blogger.agents.style_analyzer import StyleAnalyzer
from aphra_blogger.agents.keyword_extractor import KeywordExtractor
from aphra_blogger.agents.content_generator import ContentGenerator
from aphra_blogger.agents.critic import CriticAgent
from aphra_blogger.agents.image_selector import ImageSelectorAgent
from aphra_blogger.agents.unsplash import enrich_images
from aphra_blogger.agents.html_builder import HTMLBuilder
from aphra_blogger.agents.news_research_agent import research_topic as research_topic_online


class BloggerOrchestrator:
    """
    Main orchestrator that coordinates all agents in the blogger workflow.
    
    This class implements a robust execution pipeline with:
    - Phase-based execution
    - Error handling and retries
    - Progress tracking
    - State persistence
    """
    
    def __init__(
        self,
        config: Optional[OrchestratorConfig] = None,
        verbose: bool = True
    ):
        """
        Initialize the orchestrator.
        
        Args:
            config: Configuration object. If None, uses default config.
            verbose: Whether to print progress messages.
        """
        if config is None:
            # Try to load from default location
            config_path = Path(__file__).parent.parent.parent / "aphra_blogger" / "config" / "default.toml"
            if config_path.exists():
                config = OrchestratorConfig.from_toml(str(config_path))
            else:
                config = OrchestratorConfig.default()
        
        config.validate()
        
        self.config = config
        self.verbose = verbose or config.verbose
        self.state_manager: Optional[StateManager] = None
        
        # Initialize agents — pass None so each agent's factory resolves
        # the right API key from environment variables (GEMINI_API_KEY, etc.)
        self.style_analyzer = StyleAnalyzer(api_key=None, model=config.default_model)
        self.keyword_extractor = KeywordExtractor(api_key=None)
        self.content_generator = ContentGenerator(api_key=None, model=config.default_model)
        self.critic = CriticAgent(api_key=None, model=config.default_model)
        self.image_selector = ImageSelectorAgent(api_key=None)
        self.html_builder = HTMLBuilder()
    
    def _log(self, message: str, level: str = "INFO") -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")
    
    def _execute_with_retry(
        self,
        phase_name: str,
        agent_name: str,
        func,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a function with retry logic.
        
        Args:
            phase_name: Name of the current phase
            agent_name: Name of the agent
            func: Function to execute
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Result of the function
            
        Raises:
            Exception: If all retries fail
        """
        retry_count = 0
        delay = self.config.retry_delay
        
        while retry_count <= self.config.max_retries:
            try:
                self._log(f"{phase_name}: Executing {agent_name}...")
                result = func(*args, **kwargs)
                
                if retry_count > 0:
                    self._log(f"{phase_name}: ✓ Succeeded after {retry_count} retries", "SUCCESS")
                else:
                    self._log(f"{phase_name}: ✓ Completed", "SUCCESS")
                
                return result
                
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                
                if retry_count <= self.config.max_retries:
                    self._log(
                        f"{phase_name}: ✗ Failed (attempt {retry_count}/{self.config.max_retries + 1}): {error_msg}",
                        "WARNING"
                    )
                    self.state_manager.fail_phase(phase_name, error_msg, retry=True)
                    time.sleep(delay)
                    delay *= self.config.backoff_factor
                else:
                    self._log(f"{phase_name}: ✗ Failed after {retry_count} attempts: {error_msg}", "ERROR")
                    raise
        
        raise RuntimeError(f"Unexpected error in retry logic for {phase_name}")
    
    @staticmethod
    def _resolve_language(language: str, style_profile: Optional[Dict[str, Any]]) -> str:
        """Resolve the effective generation language (REQ-4).

        Explicit "es"/"en" wins; "auto" reads style_profile["language"];
        missing or invalid values fall back to "es".
        """
        if language in ("es", "en"):
            return language
        profile_language = (style_profile or {}).get("language")
        if profile_language in ("es", "en"):
            return profile_language
        return "es"

    def run(
        self,
        topic: str,
        blogger_urls: List[str],
        language: str = "auto",
        output_path: Optional[str] = None,
        preset_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute the complete orchestrated workflow.
        
        Args:
            topic: Topic to write about
            blogger_urls: List of URLs to analyze for style
            language: "auto" (explicit > style_profile > "es"), "es" or "en"
            output_path: Optional path to save workflow state JSON
            preset_id: Optional frontend blogger preset ID (slug)
            
        Returns:
            Dictionary with generated content and metadata
        """
        if language not in ("es", "en", "auto"):
            self._log(f"Invalid language '{language}'; defaulting to 'auto'", "WARNING")
            language = "auto"

        # Initialize state
        workflow_id = str(uuid.uuid4())[:8]
        state = WorkflowState(
            workflow_id=workflow_id,
            topic=topic,
            blogger_urls=blogger_urls,
            language=language,
        )
        self.state_manager = StateManager(state)
        
        self._log("=" * 60)
        self._log(f"Blogger Orchestrator Started [ID: {workflow_id}]")
        self._log(f"Topic: {topic}")
        self._log(f"Blogger URLs: {len(blogger_urls)} URL(s)")
        if preset_id:
            self._log(f"Preset ID: {preset_id}")
        self._log("=" * 60)
        
        try:
            # Phase 1: Style Analysis
            self._phase_style_analysis(blogger_urls, preset_id=preset_id)
            
            # Phase 2: Keyword Extraction
            self._phase_keyword_extraction(blogger_urls)
            
            # Phase 3: Research (información factual sobre el tema)
            self._phase_research(topic)
            
            # Phase 4: Content Generation (Draft)
            self._phase_content_generation_draft(topic)
            
            # Phase 5: Critique (if enabled)
            if self.config.enable_critique:
                self._phase_critique()
                
                # Phase 6: Refinement (if critique suggests changes)
                if self._needs_refinement():
                    self._phase_refinement()
                else:
                    # Critique ran but didn't request changes → draft IS final
                    state.final_content = state.draft_content
            else:
                self.state_manager.skip_phase("critique", "Critique disabled in config")
                self.state_manager.skip_phase("refinement", "Critique disabled")
                state.final_content = state.draft_content
            
            # Phase 7: Image Selection (before HTML building so images are included)
            self._phase_image_selection()
            
            # Phase 8: Image Enrichment with Unsplash (real photos from prompts)
            self._phase_image_enrichment()
            
            # Phase 9: HTML Building (with images + real URLs)
            self._phase_html_building()
            
            # Finalize
            self.state_manager.finalize()
            
            # Summary
            summary = self.state_manager.get_summary()
            self._log("=" * 60)
            self._log(f"Workflow Completed Successfully!")
            self._log(f"Duration: {summary['duration']:.2f}s")
            self._log(f"Phases: {summary['phases_completed']}/{summary['total_phases']} completed")
            if summary['warnings'] > 0:
                self._log(f"Warnings: {summary['warnings']}", "WARNING")
            self._log("=" * 60)
            
            # Save state if requested
            if output_path:
                self.state_manager.save_to_file(output_path)
                self._log(f"State saved to: {output_path}")
            
            # Return result
            return self._build_result()
            
        except Exception as e:
            self._log(f"Workflow Failed: {str(e)}", "ERROR")
            if self.state_manager:
                self.state_manager.finalize()
                if output_path:
                    self.state_manager.save_to_file(output_path)
            raise
    
    def _discover_blog_posts(self, base_url: str, limit: int = 3) -> List[str]:
        """Discover blog post URLs from a base URL."""
        try:
            self._log(f"Discovering blog posts from {base_url}...")
            response = requests.get(base_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code != 200:
                return [base_url]
                
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=True)
            
            base_domain = urlparse(base_url).netloc
            discovered = set()
            
            for link in links:
                href = link['href']
                full_url = urljoin(base_url, href)
                parsed = urlparse(full_url)
                
                # Basic filters: same domain, not the home itself, and NO fragments (like #comments)
                if parsed.netloc != base_domain or parsed.path in ["", "/"] or parsed.fragment:
                    continue
                
                # Heuristic for blog posts:
                # 1. Contains numbers (dates)
                # 2. Longer paths
                # 3. Not common category/tag/feed paths
                path = parsed.path.lower()
                if any(x in path for x in ['/category/', '/tag/', '/feed/', '/author/', '/page/']):
                    continue
                
                # Check for date patterns (e.g. /2024/05/...)
                has_date = any(char.isdigit() for char in path)
                # Check for slug-like structure
                has_slug = path.count('-') >= 2 or len(path.split('/')) >= 3
                
                if has_date or has_slug:
                    discovered.add(full_url)
                    if len(discovered) >= limit:
                        break
            
            result = list(discovered)
            self._log(f"Discovered {len(result)} potential posts: {', '.join(result)}")
            return result if result else [base_url]
            
        except Exception as e:
            self._log(f"Error discovering posts: {e}", "WARNING")
            return [base_url]

    def _phase_style_analysis(
        self,
        blogger_urls: List[str],
        preset_id: Optional[str] = None,
    ) -> None:
        """Phase 1: Analyze blogger style.

        REQ-BE-LOADER: registered presets short-circuit to pre-baked style
        profiles — no network, no StyleAnalyzer. Custom (unregistered) URLs
        keep the live-scrape fallback.
        """
        phase_name = "style_analysis"
        self.state_manager.start_phase(phase_name, "StyleAnalyzer")

        # 1. Try explicit preset_id first
        if preset_id:
            profile = get_prebaked_profile(preset_id)
            if profile is not None:
                self._log(f"Using pre-baked style profile for preset_id '{preset_id}'")
                self.state_manager.state.style_profile = profile
                self.state_manager.complete_phase(phase_name, profile)
                return

        # 2. Try pre-baked profile resolution by URL
        if blogger_urls:
            for url in blogger_urls:
                profile = get_prebaked_profile(url)
                if profile is not None:
                    self._log(f"Using pre-baked style profile matching URL '{url}'")
                    self.state_manager.state.style_profile = profile
                    self.state_manager.complete_phase(phase_name, profile)
                    return

        def analyze():
            combined_sample_text = ""
            
            if blogger_urls:
                # If only one URL provided, try to discover more
                target_urls = blogger_urls
                if len(blogger_urls) == 1:
                    discovered = self._discover_blog_posts(blogger_urls[0])
                    # Add discovered ones but keep original first
                    target_urls = list(dict.fromkeys([blogger_urls[0]] + discovered))
                
                for url in target_urls[:5]: # Cap at 5 URLs
                    try:
                        self._log(f"Fetching sample text from {url}...")
                        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            
                            # Clean up soup: remove scripts, styles
                            for script in soup(["script", "style"]):
                                script.decompose()
                                
                            # Extract text from p tags to get content
                            paragraphs = soup.find_all('p')
                            text = "\n\n".join([p.get_text() for p in paragraphs if len(p.get_text().split()) > 10])
                            
                            combined_sample_text += f"\n--- CONTENT FROM {url} ---\n{text}\n"
                            
                    except Exception as e:
                        self._log(f"Error scraping {url}: {e}", "WARNING")
                
                # Final cleanup and limit
                combined_sample_text = combined_sample_text.strip()
                combined_sample_text = combined_sample_text[:30000]  # Increase limit for multi-post context
                self._log(f"Extracted total {len(combined_sample_text)} characters from {len(target_urls)} URL(s)")
            
            # Save the extracted text to state so other phases can use it
            self.state_manager.state.metadata['sample_text'] = combined_sample_text
            
            return self.style_analyzer.analyze(blogger_urls, sample_text=combined_sample_text)
        
        result = self._execute_with_retry(phase_name, "StyleAnalyzer", analyze)
        self.state_manager.state.style_profile = result
        self.state_manager.complete_phase(phase_name, result)
    
    def _phase_keyword_extraction(self, blogger_urls: List[str]) -> None:
        """Phase 2: Extract keywords and phrases."""
        phase_name = "keyword_extraction"
        self.state_manager.start_phase(phase_name, "KeywordExtractor")
        
        def extract():
            sample_text = self.state_manager.state.metadata.get('sample_text', "")
            extraction_result = self.keyword_extractor.extract(blogger_urls, sample_text=sample_text)
            # Return just the keywords list for backward compatibility
            return extraction_result.get("keywords", [])
        
        result = self._execute_with_retry(phase_name, "KeywordExtractor", extract)
        self.state_manager.state.keywords = result
        self.state_manager.complete_phase(phase_name, result)
    
    def _phase_research(self, topic: str) -> None:
        """Phase 3: Research the topic for factual grounding."""
        phase_name = "research"
        self.state_manager.start_phase(phase_name, "ResearchAgent")
        
        def research():
            self._log(f"Researching topic: {topic}")
            
            # Pass the ContentGenerator's LLM provider for deep research synthesis
            llm = getattr(self.content_generator, 'llm', None)
            
            research_result = research_topic_online(
                topic,
                llm_provider=llm,
                max_articles=self.config.max_research_articles,
            )
            
            # Store in state for content generation
            self.state_manager.state.metadata['research_context'] = research_result.get("context", "")
            self.state_manager.state.metadata['research_articles'] = research_result.get("articles", [])
            self.state_manager.state.metadata['research_findings'] = research_result.get("key_findings", [])
            self.state_manager.state.metadata['research_synthesis'] = research_result.get("research_synthesis", "")
            self.state_manager.state.metadata['scrape_stats'] = research_result.get("scrape_stats", {})
            
            # Richer logging
            articles_count = len(research_result.get('articles', []))
            scrape_stats = research_result.get('scrape_stats', {})
            synthesis = research_result.get('research_synthesis', '')
            
            stats_log = ""
            if scrape_stats:
                stats_log = f", scraped {scrape_stats.get('succeeded', 0)}/{scrape_stats.get('total', 0)}"
            if synthesis:
                stats_log += f", synthesis: {len(synthesis)} chars"
            
            result_summary = f"{articles_count} articles found{stats_log}"
            self._log(f"Research complete: {result_summary}")
            return result_summary
        
        result = self._execute_with_retry(phase_name, "ResearchAgent", research)
        self.state_manager.complete_phase(phase_name, result)
    
    def _phase_content_generation_draft(self, topic: str) -> None:
        """Phase 4: Generate initial draft."""
        phase_name = "content_generation"
        self.state_manager.start_phase(phase_name, "ContentGenerator")
        
        def generate():
            style = self.state_manager.state.style_profile
            keywords = self.state_manager.state.keywords
            sample_text = self.state_manager.state.metadata.get('sample_text', '')
            
            # Use research_synthesis as primary context, fall back to research_context
            research_context = (
                self.state_manager.state.metadata.get('research_synthesis', '')
                or self.state_manager.state.metadata.get('research_context', '')
            )
            
            draft = self.content_generator.generate_draft(
                topic=topic,
                style_profile=style,
                keywords=keywords,
                sample_text=sample_text,
                research_context=research_context,
                min_words=self.config.min_word_count,
                max_words=self.config.max_word_count,
                blogger_urls=self.state_manager.state.blogger_urls,
                language=self._resolve_language(
                    self.state_manager.state.language, style
                ),
            )
            return draft
        
        result = self._execute_with_retry(phase_name, "ContentGenerator", generate)
        self.state_manager.state.draft_content = result
        self.state_manager.complete_phase(phase_name, output=f"{len(result)} characters")
    
    def _phase_critique(self) -> None:
        """Phase 4: Critique the draft."""
        phase_name = "critique"
        self.state_manager.start_phase(phase_name, "CriticAgent")
        
        def critique():
            draft = self.state_manager.state.draft_content
            style = self.state_manager.state.style_profile
            topic = self.state_manager.state.topic
            
            return self.critic.critique(
                content=draft,
                style_profile=style,
                topic=topic
            )
        
        result = self._execute_with_retry(phase_name, "CriticAgent", critique)
        self.state_manager.state.critique_feedback = str(result)
        self.state_manager.state.metadata['critique_result'] = result
        self.state_manager.complete_phase(phase_name, result)
    
    def _needs_refinement(self) -> bool:
        """Check if content needs refinement based on critique."""
        if not self.state_manager.state.metadata.get('critique_result'):
            return False
        
        critique_result = self.state_manager.state.metadata['critique_result']
        
        # Check if critique suggests revision
        if isinstance(critique_result, dict):
            return critique_result.get('needs_revision', False)
        
        return False
    
    def _phase_refinement(self) -> None:
        """Phase 5: Refine content based on critique."""
        phase_name = "refinement"
        self.state_manager.start_phase(phase_name, "ContentGenerator")
        
        def refine():
            draft = self.state_manager.state.draft_content
            critique = self.state_manager.state.metadata.get('critique_result', {})
            style = self.state_manager.state.style_profile

            refined = self.content_generator.refine_content(
                draft=draft,
                critique_feedback=critique,
                style_profile=style,
                language=self._resolve_language(
                    self.state_manager.state.language, style
                ),
            )
            return refined
        
        result = self._execute_with_retry(phase_name, "ContentGenerator", refine)
        self.state_manager.state.final_content = result
        self.state_manager.complete_phase(phase_name, output=f"{len(result)} characters")
    def _phase_html_building(self) -> None:
        """Phase 6: Build HTML structure."""
        phase_name = "html_building"
        self.state_manager.start_phase(phase_name, "HTMLBuilder")
        
        def build():
            # Use final content if available, otherwise use draft
            content = self.state_manager.state.final_content or self.state_manager.state.draft_content
            topic = self.state_manager.state.topic
            style_profile = self.state_manager.state.style_profile
            
            # Use selected images (now selected in previous phase)
            images = self.state_manager.state.image_prompts
            
            html_output = self.html_builder.build(
                content=content,
                topic=topic,
                images=images,
                style_profile=style_profile,
                language=self._resolve_language(
                    self.state_manager.state.language, style_profile
                ),
            )
            
            # Generate slug from topic (lowercase, replace spaces with hyphens)
            slug = topic.lower().replace(' ', '-').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
            slug = ''.join(c for c in slug if c.isalnum() or c == '-')
            
            # Convert to dictionary for state storage
            return {
                "html": html_output.html,
                "full_page": html_output.full_page,
                "metadata": {
                    "title": html_output.meta_title,
                    "description": html_output.meta_description,
                    "keywords": html_output.meta_keywords,
                    "reading_time": html_output.reading_time,
                    "word_count": html_output.word_count,
                    "slug": slug,
                },
                "headings": html_output.headings
            }
        
        result = self._execute_with_retry(phase_name, "HTMLBuilder", build)
        self.state_manager.state.html_structure = result
        self.state_manager.complete_phase(phase_name, result['metadata'])
    
    def _phase_image_selection(self) -> None:
        """Phase 7: Select and place images."""
        phase_name = "image_selection"
        self.state_manager.start_phase(phase_name, "ImageSelectorAgent")
        
        def select():
            content = self.state_manager.state.final_content or self.state_manager.state.draft_content
            topic = self.state_manager.state.topic
            
            return self.image_selector.select_images(
                content=content,
                topic=topic,
                num_images=3
            )
        
        result = self._execute_with_retry(phase_name, "ImageSelectorAgent", select)
        self.state_manager.state.image_prompts = result
        self.state_manager.complete_phase(phase_name, result)
    
    def _phase_image_enrichment(self) -> None:
        """Phase 8: Enrich image prompts with real Unsplash photo URLs."""
        phase_name = "image_enrichment"
        self.state_manager.start_phase(phase_name, "UnsplashAgent")
        
        prompts = self.state_manager.state.image_prompts
        if prompts:
            self._log(f"[Unsplash] Searching photos for {len(prompts)} images...")
            enriched = enrich_images(prompts)
            self.state_manager.state.image_prompts = enriched
            urls_found = sum(1 for p in enriched if p.get("url"))
            self._log(f"[Unsplash] Found {urls_found}/{len(enriched)} real photos")
        else:
            self._log("[Unsplash] No image prompts to enrich, skipping")
        
        self.state_manager.complete_phase(phase_name, {
            "total": len(prompts) if prompts else 0,
            "enriched": sum(1 for p in (prompts or []) if p.get("url")),
        })
    
    def _build_result(self) -> Dict[str, Any]:
        """Build final result dictionary."""
        state = self.state_manager.state
        
        return {
            "workflow_id": state.workflow_id,
            "topic": state.topic,
            "blogger_urls": state.blogger_urls,
            "style_profile": state.style_profile,
            "keywords": state.keywords,
            "content": state.final_content,
            "html_structure": state.html_structure,
            "image_prompts": state.image_prompts,
            "metadata": {
                "duration": state.total_duration,
                "phases": {
                    name: phase.to_dict()
                    for name, phase in state.phases.items()
                },
                "errors": state.errors,
                "warnings": state.warnings,
            }
        }
    
    def get_state(self) -> Optional[WorkflowState]:
        """Get current workflow state."""
        return self.state_manager.state if self.state_manager else None

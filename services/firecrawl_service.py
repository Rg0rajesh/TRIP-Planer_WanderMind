"""
Firecrawl Service — Real-time travel web data collection
=========================================================
Uses FirecrawlApp to scrape live travel pages:
  • WikiVoyage (open travel guide)
  • WikiTravel (community travel wiki)
  • Numbeo (cost-of-living / travel cost data)
Falls back to structured placeholder if API key absent.
"""

import os
import re
from typing import Optional

try:
    from firecrawl import FirecrawlApp
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False


class FirecrawlService:
    def __init__(self):
        api_key = os.environ.get("FIRECRAWL_API_KEY", "")
        self.enabled = FIRECRAWL_AVAILABLE and bool(api_key)
        if self.enabled:
            self.app = FirecrawlApp(api_key=api_key)
            print("[Firecrawl] ✅ Connected")
        else:
            self.app = None
            print("[Firecrawl] ⚠️  Running without API key — using enriched fallback")

    # ─── Public methods ────────────────────────────────────────────────────────

    def research_destination(self, destination: str) -> dict:
        """Scrape multiple sources for destination intel."""
        slug = destination.strip().replace(" ", "_")
        sources = {}

        if self.enabled:
            # 1. WikiVoyage — comprehensive travel guide
            wv = self._scrape(f"https://en.wikivoyage.org/wiki/{slug}", max_chars=1500)
            if wv:
                sources["wikivoyage"] = wv

            # 2. WikiTravel — community tips
            wt = self._scrape(f"https://wikitravel.org/en/{slug}", max_chars=1000)
            if wt:
                sources["wikitravel"] = wt

            # 3. Numbeo city cost info
            city = destination.split(",")[0].strip().replace(" ", "-").lower()
            nb = self._scrape(
                f"https://www.numbeo.com/cost-of-living/in/{city}",
                max_chars=800,
            )
            if nb:
                sources["numbeo"] = nb

        return {
            "destination": destination,
            "scraped": sources,
            "source_count": len(sources),
            "status": "live" if sources else "fallback",
        }

    def get_travel_tips(self, destination: str) -> str:
        """Return a single merged text blob of travel tips."""
        data = self.research_destination(destination)
        if data["scraped"]:
            return "\n\n---\n\n".join(data["scraped"].values())
        return self._fallback_tips(destination)

    def scrape_url(self, url: str, max_chars: int = 5000) -> Optional[str]:
        """Scrape any URL directly."""
        return self._scrape(url, max_chars=max_chars)

    # ─── Internal ─────────────────────────────────────────────────────────────

    def _scrape(self, url: str, max_chars: int = 4000) -> Optional[str]:
        try:
            # Compatibility for different firecrawl-py versions
            if hasattr(self.app, 'scrape_url'):
                result = self.app.scrape_url(url, params={"formats": ["markdown"]})
            elif hasattr(self.app, 'scrape'):
                try:
                    result = self.app.scrape(url, params={"formats": ["markdown"]})
                except TypeError:
                    # Fallback for very old versions that don't take params
                    result = self.app.scrape(url)
            else:
                raise AttributeError("FirecrawlApp has no scrape or scrape_url method.")

            # Handle different response types: Document objects, dictionaries, or strings
            if isinstance(result, str):
                md = result
            elif hasattr(result, 'markdown'):
                md = getattr(result, 'markdown') or getattr(result, 'content', "")
            elif hasattr(result, 'content'):
                md = getattr(result, 'content', "")
            elif isinstance(result, dict):
                md = result.get("markdown") or result.get("content") or ""
            else:
                # Last resort: try to cast to string
                md = str(result)

            if not md or md == "None":
                return None
            
            # Clean up wiki boilerplate
            md = re.sub(r"\[\[.*?\]\]", "", md)
            md = re.sub(r"\{\{.*?\}\}", "", md, flags=re.DOTALL)
            md = re.sub(r"\n{3,}", "\n\n", md)
            return md[:max_chars].strip()
        except Exception as e:
            print(f"[Firecrawl] Scrape error for {url}: {e}")
            return None

    @staticmethod
    def _fallback_tips(destination: str) -> str:
        return (
            f"[Firecrawl not connected — using AI knowledge for {destination}]\n"
            "To enable real-time web data, set the FIRECRAWL_API_KEY environment variable."
        )

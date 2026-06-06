from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re

from app.crawler.sources.base import BaseSource
from app.crawler.utils import parse_datetime, clean_html, generate_summary


class BaseRSSSource(BaseSource):
    rss_url: str = ""

    async def parse_list(self, html: str) -> List[Dict[str, Any]]:
        items = []
        try:
            soup = BeautifulSoup(html, "lxml-xml")
            entries = soup.find_all(["item", "entry"])

            for entry in entries:
                try:
                    item = self._parse_entry(entry)
                    if item and item.get("title") and item.get("url"):
                        items.append(item)
                except Exception:
                    continue
        except Exception as e:
            print(f"RSS parse error: {e}")

        return items

    def _parse_entry(self, entry) -> Dict[str, Any]:
        title = ""
        title_elem = entry.find(["title"])
        if title_elem:
            title = title_elem.get_text(strip=True)

        url = ""
        link_elem = entry.find(["link"])
        if link_elem:
            url = link_elem.get("href", "") or link_elem.get_text(strip=True)
            if not url.startswith("http"):
                url = f"{self.base_url}{url}"

        summary = ""
        desc_elem = entry.find(["description", "summary", "content"])
        if desc_elem:
            raw_summary = desc_elem.get_text(strip=False)
            cleaned = clean_html(raw_summary)
            summary = generate_summary(cleaned, 500)

        author = ""
        author_elem = entry.find(["author", "creator", "dc:creator"])
        if author_elem:
            author = author_elem.get_text(strip=True)

        publish_time_str = ""
        pub_date_elem = entry.find(["pubDate", "published", "updated", "dc:date"])
        if pub_date_elem:
            publish_time_str = pub_date_elem.get_text(strip=True)

        tags = []
        for cat in entry.find_all(["category", "category"]):
            tag = cat.get_text(strip=True)
            if tag and tag not in tags:
                tags.append(tag)

        return {
            "title": title,
            "url": url,
            "summary": summary,
            "author": author,
            "publish_time": publish_time_str,
            "tags": tags[:5],
            "heat": None,
        }

    @property
    def list_url(self) -> str:
        return self.rss_url

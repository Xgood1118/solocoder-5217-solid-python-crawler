from typing import List, Dict, Any
from bs4 import BeautifulSoup
import re

from app.crawler.sources.base import BaseSource


class HuXiuSource(BaseSource):
    source_id = "huxiu"
    source_name = "虎嗅"
    base_url = "https://www.huxiu.com"
    list_url = "https://www.huxiu.com"

    async def parse_list(self, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        items = []

        for article in soup.select("div.article-item, div[data-cid], article"):
            try:
                title_elem = article.select_one("h2 a, h3 a, .article-title a, a.title")
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                href = title_elem.get("href", "")
                if not href:
                    continue

                url = href if href.startswith("http") else f"{self.base_url}{href}"

                summary_elem = article.select_one(".article-summary, .summary, p.desc")
                summary = summary_elem.get_text(strip=True) if summary_elem else ""

                author_elem = article.select_one(".author-name, .user-name, .author a")
                author = author_elem.get_text(strip=True) if author_elem else ""

                time_elem = article.select_one(".time, .date, .article-time, span.time")
                publish_time = time_elem.get_text(strip=True) if time_elem else ""

                tags = []
                for tag_elem in article.select(".tag, .category, .article-tags a"):
                    tag_text = tag_elem.get_text(strip=True)
                    if tag_text:
                        tags.append(tag_text)

                heat_elem = article.select_one(".view-count, .read-count, .like-count, .heat")
                heat = None
                if heat_elem:
                    heat_text = heat_elem.get_text(strip=True)
                    heat_match = re.search(r"[\d,]+", heat_text)
                    if heat_match:
                        heat = int(heat_match.group().replace(",", ""))

                items.append({
                    "title": title,
                    "url": url,
                    "summary": summary,
                    "author": author,
                    "publish_time": publish_time,
                    "tags": tags[:5],
                    "heat": heat,
                })
            except Exception:
                continue

        return items

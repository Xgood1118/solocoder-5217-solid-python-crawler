from typing import List, Dict, Any
from bs4 import BeautifulSoup
import re

from app.crawler.sources.base import BaseSource


class JueJinSource(BaseSource):
    source_id = "juejin"
    source_name = "掘金"
    base_url = "https://juejin.cn"
    list_url = "https://juejin.cn"

    async def parse_list(self, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        items = []

        for article in soup.select("article, .item, .entry, .article-item, .entry-list .item"):
            try:
                title_elem = article.select_one("h2 a, h3 a, .title a, .article-title a, a.title")
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                href = title_elem.get("href", "")
                if not href:
                    continue

                url = href if href.startswith("http") else f"{self.base_url}{href}"

                summary_elem = article.select_one(".summary, .abstract, .article-summary, .content")
                summary = summary_elem.get_text(strip=True) if summary_elem else ""

                author_elem = article.select_one(".author-name, .username, .user-name a, .author a")
                author = author_elem.get_text(strip=True) if author_elem else ""

                time_elem = article.select_one(".time, .date, .publish-time, .ctime-text")
                publish_time = time_elem.get_text(strip=True) if time_elem else ""

                tags = []
                for tag_elem in article.select(".tag, .category, .tag-title, .article-tags a"):
                    tag_text = tag_elem.get_text(strip=True)
                    if tag_text:
                        tags.append(tag_text)

                heat_elem = article.select_one(".view-count, .read-count, .like-count, .praise .count")
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

    async def parse_detail(self, html: str, article_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            soup = BeautifulSoup(html, "lxml")

            content_elem = soup.select_one(".article-content, .markdown-body, .entry-content")
            if content_elem:
                article_data["content"] = str(content_elem)

            author_elem = soup.select_one(".author-name, .username, .user-info .name")
            if author_elem and not article_data.get("author"):
                article_data["author"] = author_elem.get_text(strip=True)

            tags = []
            for tag_elem in soup.select(".tag-list a, .category-list a, .article-tags .item"):
                tag_text = tag_elem.get_text(strip=True)
                if tag_text:
                    tags.append(tag_text)
            if tags and not article_data.get("tags"):
                article_data["tags"] = tags[:5]

        except Exception as e:
            article_data["error"] = f"Detail parse error: {str(e)}"

        return article_data

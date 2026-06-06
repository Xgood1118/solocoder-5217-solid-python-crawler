from typing import List, Dict, Any
from bs4 import BeautifulSoup
import re

from app.crawler.sources.base import BaseSource


class InfoQSource(BaseSource):
    source_id = "infoq"
    source_name = "InfoQ"
    base_url = "https://www.infoq.cn"
    list_url = "https://www.infoq.cn"

    async def parse_list(self, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        items = []

        for article in soup.select("article, .article-item, .article-list-item, .list-item"):
            try:
                title_elem = article.select_one("h2 a, h3 a, .article-title a, a.title, .list-title a")
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                href = title_elem.get("href", "")
                if not href:
                    continue

                url = href if href.startswith("http") else f"{self.base_url}{href}"

                summary_elem = article.select_one(".article-summary, .summary, .article-desc, .desc")
                summary = summary_elem.get_text(strip=True) if summary_elem else ""

                author_elem = article.select_one(".author, .author-name, .article-author")
                author = author_elem.get_text(strip=True) if author_elem else ""

                time_elem = article.select_one(".time, .date, .publish-time, .article-time")
                publish_time = time_elem.get_text(strip=True) if time_elem else ""

                tags = []
                for tag_elem in article.select(".tag, .topic, .article-tags a, .category"):
                    tag_text = tag_elem.get_text(strip=True)
                    if tag_text:
                        tags.append(tag_text)

                heat_elem = article.select_one(".view-count, .read-count, .like-count, .comment-count")
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

            content_elem = soup.select_one(".article-content, .content, .article-detail, .article-text")
            if content_elem:
                article_data["content"] = str(content_elem)

            author_elem = soup.select_one(".author-name, .article-author a")
            if author_elem and not article_data.get("author"):
                article_data["author"] = author_elem.get_text(strip=True)

            tags = []
            for tag_elem in soup.select(".article-tags a, .tag-list a"):
                tag_text = tag_elem.get_text(strip=True)
                if tag_text:
                    tags.append(tag_text)
            if tags and not article_data.get("tags"):
                article_data["tags"] = tags[:5]

        except Exception as e:
            article_data["error"] = f"Detail parse error: {str(e)}"

        return article_data

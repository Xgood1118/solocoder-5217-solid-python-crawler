from typing import List, Dict, Any
from bs4 import BeautifulSoup

from app.crawler.sources.rss_base import BaseRSSSource


class Kr36Source(BaseRSSSource):
    source_id = "36kr"
    source_name = "36氪"
    base_url = "https://36kr.com"
    rss_url = "https://36kr.com/feed"

    async def parse_detail(self, html: str, article_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            soup = BeautifulSoup(html, "lxml")

            content_elem = soup.select_one(".article-detail-content, .content, .article-content, #app article")
            if content_elem:
                for tag in content_elem.select("script, style, iframe, .ad, .advertisement, .recommend, .related"):
                    tag.decompose()
                article_data["content"] = str(content_elem)

            author_elem = soup.select_one(".author-name, .author, .author-info .name")
            if author_elem and not article_data.get("author"):
                article_data["author"] = author_elem.get_text(strip=True)

            tags = []
            for tag_elem in soup.select(".article-tags a, .tag-box a, .tags a, .label-list a"):
                tag_text = tag_elem.get_text(strip=True)
                if tag_text and tag_text not in tags:
                    tags.append(tag_text)
            if tags and not article_data.get("tags"):
                article_data["tags"] = tags[:5]

        except Exception as e:
            article_data["error"] = f"Detail parse error: {str(e)}"

        return article_data

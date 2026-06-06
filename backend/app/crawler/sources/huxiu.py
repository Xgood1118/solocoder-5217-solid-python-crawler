from typing import List, Dict, Any
from bs4 import BeautifulSoup

from app.crawler.sources.rss_base import BaseRSSSource


class HuXiuSource(BaseRSSSource):
    source_id = "huxiu"
    source_name = "虎嗅"
    base_url = "https://www.huxiu.com"
    rss_url = "https://rss.huxiu.com/"

    async def parse_detail(self, html: str, article_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            soup = BeautifulSoup(html, "lxml")

            content_elem = soup.select_one(".article-content-wrap, .article-content, #article_content, .article-detail-content")
            if content_elem:
                for tag in content_elem.select("script, style, iframe, .ad, .advertisement, .recommend, .related"):
                    tag.decompose()
                article_data["content"] = str(content_elem)

            author_elem = soup.select_one(".author-name, .user-name, .author .name")
            if author_elem and not article_data.get("author"):
                article_data["author"] = author_elem.get_text(strip=True)

            tags = []
            for tag_elem in soup.select(".article-tags a, .tag-box a, .tags a"):
                tag_text = tag_elem.get_text(strip=True)
                if tag_text and tag_text not in tags:
                    tags.append(tag_text)
            if tags and not article_data.get("tags"):
                article_data["tags"] = tags[:5]

        except Exception as e:
            article_data["error"] = f"Detail parse error: {str(e)}"

        return article_data

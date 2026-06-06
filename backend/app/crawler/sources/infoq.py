from typing import List, Dict, Any
from bs4 import BeautifulSoup

from app.crawler.sources.rss_base import BaseRSSSource


class InfoQSource(BaseRSSSource):
    source_id = "infoq"
    source_name = "InfoQ"
    base_url = "https://www.infoq.cn"
    rss_url = "https://www.infoq.cn/feed"

    async def parse_detail(self, html: str, article_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            soup = BeautifulSoup(html, "lxml")

            content_elem = soup.select_one(".article-content, .article-detail, #articleContent, .article-detail-content, .article__content")
            if content_elem:
                for tag in content_elem.select("script, style, iframe, .ad, .advertisement, .recommend, .related"):
                    tag.decompose()
                article_data["content"] = str(content_elem)

            author_elem = soup.select_one(".author-name, .author, .author-info .name, .author-name a, .article-author .name")
            if author_elem and not article_data.get("author"):
                article_data["author"] = author_elem.get_text(strip=True)

            tags = []
            for tag_elem in soup.select(".article-tags a, .tag-box a, .tags a, .topic-tags .tag, .article__tags a"):
                tag_text = tag_elem.get_text(strip=True)
                if tag_text and tag_text not in tags:
                    tags.append(tag_text)
            if tags and not article_data.get("tags"):
                article_data["tags"] = tags[:5]

        except Exception as e:
            article_data["error"] = f"Detail parse error: {str(e)}"

        return article_data

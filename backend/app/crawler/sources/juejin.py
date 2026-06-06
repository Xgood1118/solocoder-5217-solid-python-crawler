from typing import List, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup

from app.crawler.sources.base import BaseSource
from app.models import Article
from app.crawler.utils import generate_article_id, normalize_url, clean_html, generate_summary


class JueJinSource(BaseSource):
    source_id = "juejin"
    source_name = "掘金"
    base_url = "https://juejin.cn"
    list_url = "https://api.juejin.cn/recommend_api/v1/article/recommend_all_feed"

    async def parse_list(self, html: str) -> List[Dict[str, Any]]:
        return []

    def _extract_article_data(self, item: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(item, dict):
            return {}

        item_info = item.get("item_info") or item.get("article_info") or {}
        if not isinstance(item_info, dict):
            return {}

        article_info = item_info.get("article_info") or item_info
        if not isinstance(article_info, dict):
            return {}

        article_id = str(
            article_info.get("article_id")
            or article_info.get("id")
            or item_info.get("article_id")
            or item.get("article_id")
            or ""
        )
        if not article_id or not article_id.isdigit():
            return {}

        url = f"{self.base_url}/article/{article_id}"

        title = str(article_info.get("title") or article_info.get("article_title") or "").strip()
        if not title:
            return {}

        summary = str(
            article_info.get("brief_content")
            or article_info.get("summary")
            or article_info.get("desc")
            or article_info.get("description")
            or ""
        ).strip()

        author = ""
        author_info = (
            item_info.get("author_user_info")
            or item.get("author_user_info")
            or article_info.get("author_user_info")
            or article_info.get("user")
            or {}
        )
        if isinstance(author_info, dict):
            author = str(
                author_info.get("user_name")
                or author_info.get("name")
                or author_info.get("username")
                or ""
            ).strip()

        tags = []
        category = item_info.get("category") or article_info.get("category") or {}
        if isinstance(category, dict):
            cat_name = category.get("category_name") or category.get("name")
            if cat_name:
                tags.append(str(cat_name))

        tag_list = (
            item_info.get("tags")
            or item.get("tags")
            or article_info.get("tags")
            or []
        )
        if isinstance(tag_list, list):
            for tag in tag_list[:4]:
                if isinstance(tag, dict):
                    tag_name = tag.get("tag_name") or tag.get("name")
                    if tag_name and tag_name not in tags:
                        tags.append(str(tag_name))
                elif isinstance(tag, str):
                    if tag and tag not in tags:
                        tags.append(tag)

        heat = None
        for heat_field in [
            "view_count", "read_count", "digg_count", "like_count",
            "collect_count", "comment_count", "hot_index", "rank_index"
        ]:
            val = article_info.get(heat_field) or item_info.get(heat_field)
            if val is not None:
                try:
                    heat = int(val)
                    if heat > 0:
                        break
                except (ValueError, TypeError):
                    pass

        publish_time = None
        for time_field in ["ctime", "mtime", "rtime", "publish_time", "create_time"]:
            val = article_info.get(time_field) or item_info.get(time_field) or item.get(time_field)
            if val is not None:
                try:
                    ts = int(val)
                    if ts > 10000000000:
                        ts = ts // 1000
                    publish_time = datetime.fromtimestamp(ts)
                    break
                except (ValueError, TypeError):
                    pass

        return {
            "id": generate_article_id(url),
            "title": title,
            "url": url,
            "summary": summary,
            "author": author,
            "publish_time": publish_time,
            "tags": tags[:5],
            "heat": heat,
            "content": "",
        }

    async def crawl_list(self, engine) -> List[Article]:
        if not self.enabled:
            return []

        try:
            payload = {
                "id_type": 2,
                "client_type": 2608,
                "sort_type": 200,
                "cursor": "0",
                "limit": 20,
            }
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://juejin.cn",
                "Referer": "https://juejin.cn/",
            }

            data = await engine.fetch_json(
                self.list_url,
                method="POST",
                json=payload,
                headers=headers,
            )

            items = []
            data_list = data.get("data") or data.get("d") or []
            if isinstance(data_list, list):
                for item in data_list:
                    try:
                        article_data = self._extract_article_data(item)
                        if article_data and article_data.get("title") and article_data.get("url"):
                            items.append(article_data)
                    except Exception:
                        continue

            articles = []
            for item in items:
                try:
                    article = self._create_article(item)
                    articles.append(article)
                except Exception:
                    continue

            return articles
        except Exception as e:
            raise Exception(f"Crawl list failed: {str(e)}") from e

    async def parse_detail(self, html: str, article_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            soup = BeautifulSoup(html, "lxml")

            content_elem = soup.select_one(".article-content, .markdown-body, .entry-content, .article-detail-content, #article-root .markdown-body")
            if content_elem:
                for tag in content_elem.select("script, style, iframe, .ad, .advertisement, .recommend, .related, .author-info-block, .article-copyright"):
                    tag.decompose()
                article_data["content"] = str(content_elem)

            author_elem = soup.select_one(".author-name, .username, .user-info .name, .author-info .user-name, .author-user-name")
            if author_elem and not article_data.get("author"):
                article_data["author"] = author_elem.get_text(strip=True)

            tags = []
            for tag_elem in soup.select(".tag-list a, .category-list a, .article-tags .item, .meta-box .tag, .article-tag-list .tag-item"):
                tag_text = tag_elem.get_text(strip=True)
                if tag_text and tag_text not in tags:
                    tags.append(tag_text)
            if tags and not article_data.get("tags"):
                article_data["tags"] = tags[:5]

        except Exception as e:
            article_data["error"] = f"Detail parse error: {str(e)}"

        return article_data

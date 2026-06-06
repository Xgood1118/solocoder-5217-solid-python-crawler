from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from bs4 import BeautifulSoup
from datetime import datetime
import dateparser
import hashlib
import re


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    hostname = parsed.hostname.lower() if parsed.hostname else ""

    query_params = parse_qs(parsed.query, keep_blank_values=True)
    filtered_params = {}
    for key, value in query_params.items():
        if not key.startswith("utm_") and key not in ("fbclid", "gclid", "ref", "ref_src"):
            filtered_params[key] = value

    new_query = urlencode(filtered_params, doseq=True)

    normalized = urlunparse((
        parsed.scheme.lower(),
        hostname + (f":{parsed.port}" if parsed.port else ""),
        parsed.path,
        parsed.params,
        new_query,
        ""
    ))

    return normalized


def generate_article_id(url: str) -> str:
    normalized = normalize_url(url)
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup.find_all(["script", "style", "noscript", "iframe"]):
        tag.decompose()

    for ad_class in ["ad", "ads", "advertisement", "adv", "ad-banner", "ad-box", "sponsor", "sponsored", "promotion", "promo"]:
        for tag in soup.find_all(class_=re.compile(ad_class, re.I)):
            tag.decompose()

    for ad_id in ["ad", "ads", "advertisement", "adv", "sponsor", "sponsored"]:
        for tag in soup.find_all(id=re.compile(ad_id, re.I)):
            tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def generate_summary(content: str, max_length: int = 500) -> str:
    if not content:
        return ""
    text = content.strip()
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit("。", 1)[0] if "。" in text[:max_length] else text[:max_length] + "..."


def parse_datetime(date_str: str) -> datetime | None:
    if not date_str:
        return None

    date_str = date_str.strip()

    try:
        if re.match(r"^\d{10}$", date_str):
            return datetime.fromtimestamp(int(date_str))
        if re.match(r"^\d{13}$", date_str):
            return datetime.fromtimestamp(int(date_str) / 1000)
    except (ValueError, OSError):
        pass

    try:
        parsed = dateparser.parse(
            date_str,
            languages=["zh", "en"],
            settings={
                "PREFER_DATES_FROM": "past",
                "TIMEZONE": "Asia/Shanghai",
                "RETURN_AS_TIMEZONE_AWARE": False,
            }
        )
        return parsed
    except Exception:
        return None


def extract_domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.hostname.lower() if parsed.hostname else ""

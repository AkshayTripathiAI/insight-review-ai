import time
from typing import List
from typing import Optional

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def init_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def _parse_reviews_from_html(html: str, page_number: int) -> List[dict]:
    if not html or len(html.strip()) < 100:
        return []
    soup = BeautifulSoup(html, "html.parser")
    reviews_data: List[dict] = []
    review_selectors = [
        "li[data-hook='review']",
        "[data-hook='review']",
        ".review.aok-relative",
        "div[data-cel-widget*='customer_review']",
    ]
    reviews = []
    for selector in review_selectors:
        found = soup.select(selector)
        if found:
            reviews = found
            break
    if not reviews:
        potential = soup.find_all(attrs={"data-hook": lambda x: x and "review" in x})
        if potential:
            reviews = potential
    for review in reviews:
        reviewer_name: Optional[str] = None
        for selector in [
            "span.a-profile-name",
            ".a-profile-name",
            "[data-hook='review-author']",
            ".a-profile .a-profile-name",
        ]:
            element = review.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text:
                    reviewer_name = text
                    break
        review_title: Optional[str] = None
        for selector in [
            "a[data-hook='review-title'] span",
            "a[data-hook='review-title']",
            "[data-hook='review-title']",
            ".review-title",
            "h4 a span",
            "h4 span",
        ]:
            element = review.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text:
                    review_title = text
                    break
        rating_text: Optional[str] = None
        for selector in [
            "i[data-hook*='star-rating'] span",
            "i[data-hook*='star-rating']",
            ".a-icon-star span",
            "[class*='star'] span",
            "i.a-icon-star span.a-icon-alt",
        ]:
            element = review.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and ("star" in text.lower() or "out of" in text.lower()):
                    rating_text = text
                    break
        body_text: Optional[str] = None
        for selector in [
            "span[data-hook='review-body'] span",
            "span[data-hook='review-body']",
            "[data-hook='review-body']",
            ".review-text",
            ".review-body",
        ]:
            element = review.select_one(selector)
            if element:
                spans = element.select("span")
                if spans:
                    for span in reversed(spans):
                        span_text = span.get_text(strip=True)
                        if span_text and len(span_text) > 20:
                            body_text = span_text
                            break
                if not body_text:
                    body_text = element.get_text(strip=True)
                if body_text and len(body_text) > 10:
                    break
        date_text: Optional[str] = None
        for selector in [
            "span[data-hook='review-date']",
            "[data-hook='review-date']",
            ".review-date",
            ".a-color-secondary.review-date",
        ]:
            element = review.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text:
                    date_text = text
                    break
        if review_title:
            value = review_title.replace("\n", " ").replace("\r", " ").strip()
            prefixes = [
                "5.0 out of 5 stars",
                "4.0 out of 5 stars",
                "3.0 out of 5 stars",
                "2.0 out of 5 stars",
                "1.0 out of 5 stars",
            ]
            for prefix in prefixes:
                if value.startswith(prefix):
                    value = value.replace(prefix, "").strip()
            review_title = value
        if body_text:
            body_text = body_text.replace("\n", " ").replace("\r", " ").strip()
        if date_text:
            date_text = date_text.replace("\n", " ").replace("\r", " ").strip()
        if rating_text:
            rating_text = rating_text.replace("\n", " ").replace("\r", " ").strip()
        if reviewer_name:
            reviewer_name = reviewer_name.replace("\n", " ").replace("\r", " ").strip()
        if (review_title and len(review_title) > 3) or (body_text and len(body_text) > 10):
            reviews_data.append(
                {
                    "reviewerName": reviewer_name or "",
                    "rating": rating_text or "",
                    "reviewTitle": review_title or "",
                    "reviewDate": date_text or "",
                    "reviewText": body_text or "",
                    "source_page": page_number,
                }
            )
    return reviews_data


def fetch_reviews_for_asin(asin: str, max_pages: int = 1) -> List[dict]:
    driver = init_driver()
    all_reviews: List[dict] = []
    try:
        for page in range(1, max_pages + 1):
            url = f"https://www.amazon.com/product-reviews/{asin}/?pageNumber={page}"
            driver.get(url)
            time.sleep(3)
            html = driver.page_source
            page_reviews = _parse_reviews_from_html(html, page)
            if not page_reviews:
                break
            all_reviews.extend(page_reviews)
    finally:
        driver.quit()
    return all_reviews


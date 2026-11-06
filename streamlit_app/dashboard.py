import os

import pandas as pd
import requests
import streamlit as st


def _api_base_url() -> str:
    url = os.getenv("API_BASE_URL")
    if not url:
        try:
            url = st.secrets["API_BASE_URL"]
        except Exception:
            url = "http://api:8000/api/v1"
    return url.rstrip("/")


API_BASE_URL = _api_base_url()
TIMEOUT = 90  # the free-tier API can take up to a minute to wake up


def _get(path: str):
    try:
        response = requests.get(f"{API_BASE_URL}{path}", timeout=TIMEOUT)
    except requests.RequestException:
        return None
    return response.json() if response.ok else None


def _post(path: str, payload: dict):
    try:
        response = requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=TIMEOUT)
    except requests.RequestException as e:
        return {"error": str(e)}
    if response.ok:
        return response.json()
    try:
        return {"error": response.json().get("detail", response.text)}
    except ValueError:
        return {"error": response.text}


@st.cache_data(ttl=60, show_spinner=False)
def get_products() -> list[dict]:
    return _get("/products/") or []


@st.cache_data(ttl=60, show_spinner=False)
def get_product_summary(product_id: int) -> dict | None:
    return _get(f"/analytics/products/{product_id}/summary")


@st.cache_data(ttl=60, show_spinner=False)
def get_aspects(product_id: int) -> list[dict]:
    return _get(f"/analytics/products/{product_id}/aspects") or []


@st.cache_data(ttl=60, show_spinner=False)
def get_reviews(product_id: int) -> list[dict]:
    return _get(f"/reviews/product/{product_id}?limit=100") or []


def main() -> None:
    st.set_page_config(page_title="InsightReview AI", page_icon="🔎", layout="wide")
    st.title("🔎 InsightReview AI")
    st.caption(
        "LLM aspect-based sentiment, semantic search and RAG Q&A over product reviews. "
        "The demo uses hand-written sample reviews for fictional products."
    )

    with st.spinner("Connecting to the API (the free tier may take up to a minute to wake up)..."):
        products = get_products()

    if not products:
        st.warning("No products yet. The API may still be starting up; refresh in a minute.")
        if st.button("Retry"):
            st.cache_data.clear()
            st.rerun()
        return

    product_options = {p["name"]: p for p in products}
    selected_name = st.selectbox("Product", list(product_options.keys()))
    product_id = product_options[selected_name]["id"]
    reviews = get_reviews(product_id)

    ratings = [r["rating"] for r in reviews if r.get("rating")]
    m1, m2 = st.columns(2)
    m1.metric("Reviews", len(reviews))
    m2.metric("Average rating", f"{sum(ratings) / len(ratings):.1f} / 5" if ratings else "n/a")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("AI summary")
        summary = get_product_summary(product_id)
        if summary:
            st.markdown(f"**Overall sentiment:** {summary['overall_sentiment']}")
            st.markdown(summary["summary_markdown"])
            pros_col, cons_col = st.columns(2)
            with pros_col:
                st.markdown("**👍 Pros**")
                st.markdown(summary.get("pros_markdown") or "_none_")
            with cons_col:
                st.markdown("**👎 Cons**")
                st.markdown(summary.get("cons_markdown") or "_none_")
        else:
            st.write("No summary available yet.")

    with col2:
        st.subheader("Aspect sentiment")
        aspects = get_aspects(product_id)
        if aspects:
            df = pd.DataFrame(aspects).set_index("aspect")
            df = df.rename(
                columns={"positive_count": "positive", "negative_count": "negative", "neutral_count": "neutral"}
            )
            st.bar_chart(df[["positive", "neutral", "negative"]], color=["#2e9e5b", "#9aa0a6", "#d9534f"], horizontal=True)
        else:
            st.write("No aspect data available.")

    st.divider()
    st.subheader("💬 Ask about this product")
    st.caption("Answers come only from the reviews and cite them, e.g. *How is the battery life?* or *Any durability problems?*")
    question = st.text_input("Question", placeholder="Is it comfortable for long use?")
    if question:
        with st.spinner("Retrieving reviews and generating an answer..."):
            result = _post(f"/rag/products/{product_id}/qa", {"question": question, "top_k": 5})
        if "error" in result:
            st.error(result["error"])
        else:
            st.markdown(result.get("answer", ""))
            with st.expander("Sources"):
                for source in result.get("sources", []):
                    st.markdown(f"**Review {source['review_id']}** · similarity {source['score']:.2f}")
                    st.write(source["snippet"])

    st.subheader("🔍 Semantic search")
    query = st.text_input("Search reviews by meaning", placeholder="connection problems")
    if query:
        result = _post(f"/rag/products/{product_id}/semantic-search", {"query": query, "top_k": 5})
        if "error" in result:
            st.error(result["error"])
        for hit in result.get("hits", []):
            st.markdown(f"**{hit.get('rating') or '?'}★** · similarity {hit['score']:.2f}")
            st.write(hit["snippet"])

    with st.expander(f"All reviews ({len(reviews)})"):
        for r in reviews:
            st.markdown(f"**{r.get('rating') or '?'}★ {r.get('title') or ''}**")
            st.write(r["body"])


if __name__ == "__main__":
    main()

import os

import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000/api/v1")


def get_products() -> list[dict]:
    response = requests.get(f"{API_BASE_URL}/products")
    if response.ok:
        return response.json()
    return []


def get_product_summary(product_id: int) -> dict | None:
    response = requests.get(f"{API_BASE_URL}/analytics/products/{product_id}/summary")
    if response.ok:
        return response.json()
    return None


def get_aspects(product_id: int) -> list[dict]:
    response = requests.get(f"{API_BASE_URL}/analytics/products/{product_id}/aspects")
    if response.ok:
        return response.json()
    return []


def semantic_search(product_id: int, query: str) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/rag/products/{product_id}/semantic-search",
        json={"query": query, "top_k": 5},
    )
    if response.ok:
        return response.json()
    return {"hits": []}


def ask_question(product_id: int, question: str) -> dict:
    response = requests.post(
        f"{API_BASE_URL}/rag/products/{product_id}/qa",
        json={"question": question, "top_k": 5},
    )
    if response.ok:
        return response.json()
    return {"answer": "", "sources": []}


def main() -> None:
    st.set_page_config(page_title="InsightReview Dashboard", layout="wide")
    st.title("InsightReview AI Dashboard")

    products = get_products()
    product_options = {p["name"]: p for p in products}
    if not product_options:
        st.info("No products found. Create a product and ingest reviews via the API.")
        if st.button("Create demo product with mock reviews"):
            create_response = requests.post(
                f"{API_BASE_URL}/products",
                json={"name": "Demo Product", "source": "mock", "url": None, "external_id": None},
            )
            if create_response.ok:
                product = create_response.json()
                product_id = product["id"]
                requests.post(f"{API_BASE_URL}/products/{product_id}/ingest")
                requests.post(f"{API_BASE_URL}/products/{product_id}/process")
                st.experimental_rerun()
        return

    selected_name = st.selectbox("Select product", list(product_options.keys()))
    product = product_options[selected_name]
    product_id = product["id"]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Product summary")
        summary = get_product_summary(product_id)
        if summary:
            st.markdown(summary["summary_markdown"])
        else:
            st.write("No summary available yet.")

    with col2:
        st.subheader("Aspect sentiment")
        aspects = get_aspects(product_id)
        if aspects:
            st.dataframe(aspects, use_container_width=True)
        else:
            st.write("No aspect data available.")

    st.subheader("Semantic search")
    query = st.text_input("Search reviews semantically")
    if query:
        results = semantic_search(product_id, query)
        for hit in results.get("hits", []):
            st.markdown(f"Score: {hit['score']:.3f} Rating: {hit.get('rating')}")
            st.write(hit["snippet"])
            st.markdown("---")

    st.subheader("Q&A over reviews")
    question = st.text_input("Ask a question about this product")
    if question:
        answer_response = ask_question(product_id, question)
        st.markdown("**Answer**")
        st.write(answer_response.get("answer", ""))
        st.markdown("**Sources**")
        for source in answer_response.get("sources", []):
            st.markdown(f"Review {source['review_id']} (score {source['score']:.3f})")
            st.write(source["snippet"])
            st.markdown("---")


if __name__ == "__main__":
    main()

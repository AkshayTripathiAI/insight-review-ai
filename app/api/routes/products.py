from typing import List

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.guards import require_writable
from app.db import get_db
from app.db.models import Product
from app.pipelines.review_enrichment import enrich_reviews_for_product
from app.pipelines.review_ingestion import ingest_product_reviews
from app.schemas.product import ProductCreate
from app.schemas.product import ProductRead
from app.services.review_service import create_product
from app.services.review_service import get_product
from app.services.review_service import list_products


router = APIRouter()


@router.post("/", response_model=ProductRead, dependencies=[Depends(require_writable)])
def create_product_endpoint(payload: ProductCreate, db: Session = Depends(get_db)) -> Product:
    product = create_product(
        db=db,
        name=payload.name,
        source=payload.source,
        url=payload.url,
        external_id=payload.external_id,
    )
    return product


@router.get("/", response_model=List[ProductRead])
def list_products_endpoint(db: Session = Depends(get_db)) -> List[Product]:
    products = list_products(db)
    return products


@router.post("/{product_id}/ingest", dependencies=[Depends(require_writable)])
def ingest_product_reviews_endpoint(product_id: int, db: Session = Depends(get_db)) -> dict:
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    try:
        count = ingest_product_reviews(db, product)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok", "ingested_reviews": count}


@router.post("/{product_id}/process", dependencies=[Depends(require_writable)])
def process_product_reviews(product_id: int, db: Session = Depends(get_db)) -> dict:
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    count = enrich_reviews_for_product(db, product)
    return {"status": "ok", "processed_reviews": count}


@router.get("/{product_id}", response_model=ProductRead)
def get_product_endpoint(product_id: int, db: Session = Depends(get_db)) -> Product:
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

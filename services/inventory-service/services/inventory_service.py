from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from shared.models.inventory import Batch, Inventory, Product
from shared.models.store import Store

from schemas.inventory import BatchCreate, DeductStockRequest, ProductCreate, StockCreate


class InventoryService:
    def __init__(self, db: Session):
        self.db = db

    def create_product(self, payload: ProductCreate) -> Product:
        existing = self.db.scalar(select(Product).where(Product.sku == payload.sku))
        if existing:
            raise HTTPException(status_code=409, detail="Product with this SKU already exists")

        product = Product(
            sku=payload.sku,
            name=payload.name,
            category=payload.category,
            price=payload.price,
            unit=payload.unit,
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def get_product(self, product_id: int) -> Product:
        product = self.db.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product

    def add_stock(self, payload: StockCreate) -> Inventory:
        self._ensure_store_exists(payload.store_id)
        self._ensure_product_exists(payload.product_id)

        inventory = self.db.scalar(
            select(Inventory).where(
                Inventory.product_id == payload.product_id,
                Inventory.store_id == payload.store_id,
            )
        )

        if inventory:
            inventory.quantity_on_hand += payload.quantity
            inventory.reorder_level = payload.reorder_level
            inventory.last_updated = datetime.utcnow()
        else:
            inventory = Inventory(
                product_id=payload.product_id,
                store_id=payload.store_id,
                quantity_on_hand=payload.quantity,
                reorder_level=payload.reorder_level,
                last_updated=datetime.utcnow(),
            )
            self.db.add(inventory)

        self.db.commit()
        self.db.refresh(inventory)
        return inventory

    def get_stock_by_store(self, store_id: int) -> list[Inventory]:
        self._ensure_store_exists(store_id)
        stock = self.db.scalars(select(Inventory).where(Inventory.store_id == store_id)).all()
        return list(stock)

    def create_batch(self, payload: BatchCreate) -> Batch:
        self._ensure_store_exists(payload.store_id)
        self._ensure_product_exists(payload.product_id)

        batch = Batch(
            product_id=payload.product_id,
            store_id=payload.store_id,
            batch_number=payload.batch_number,
            expiry_date=payload.expiry_date,
            quantity=payload.quantity,
        )
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def deduct_stock(self, payload: DeductStockRequest) -> tuple[bool, str, int | None]:
        inventory = self.db.scalar(
            select(Inventory).where(
                Inventory.product_id == payload.product_id,
                Inventory.store_id == payload.store_id,
            )
        )
        if not inventory:
            return False, "Inventory record not found", None

        if inventory.quantity_on_hand < payload.quantity:
            return False, "Insufficient stock", inventory.quantity_on_hand

        inventory.quantity_on_hand -= payload.quantity
        inventory.last_updated = datetime.utcnow()
        self.db.commit()
        self.db.refresh(inventory)
        return True, "Stock deducted successfully", inventory.quantity_on_hand

    def _ensure_store_exists(self, store_id: int) -> None:
        store = self.db.get(Store, store_id)
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")

    def _ensure_product_exists(self, product_id: int) -> None:
        product = self.db.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

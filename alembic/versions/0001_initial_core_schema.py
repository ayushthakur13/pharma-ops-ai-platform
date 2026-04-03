"""initial core schema

Revision ID: 0001_initial_core_schema
Revises: 
Create Date: 2026-04-04

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_core_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roles")),
    )
    op.create_index(op.f("ix_roles_id"), "roles", ["id"], unique=False)
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], name=op.f("fk_users_role_id_roles"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_role_id"), "users", ["role_id"], unique=False)

    op.create_table(
        "stores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("region", sa.String(length=100), nullable=False),
        sa.Column("is_online", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_stores")),
    )
    op.create_index(op.f("ix_stores_id"), "stores", ["id"], unique=False)
    op.create_index(op.f("ix_stores_is_online"), "stores", ["is_online"], unique=False)
    op.create_index(op.f("ix_stores_region"), "stores", ["region"], unique=False)

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sku", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_products")),
    )
    op.create_index(op.f("ix_products_category"), "products", ["category"], unique=False)
    op.create_index(op.f("ix_products_id"), "products", ["id"], unique=False)
    op.create_index(op.f("ix_products_name"), "products", ["name"], unique=False)
    op.create_index(op.f("ix_products_sku"), "products", ["sku"], unique=True)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("old_value", sa.JSON(), nullable=True),
        sa.Column("new_value", sa.JSON(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_audit_logs_user_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"], unique=False)
    op.create_index(op.f("ix_audit_logs_id"), "audit_logs", ["id"], unique=False)
    op.create_index(op.f("ix_audit_logs_timestamp"), "audit_logs", ["timestamp"], unique=False)
    op.create_index(op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False)

    op.create_table(
        "inventory",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("quantity_on_hand", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reorder_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name=op.f("fk_inventory_product_id_products"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], name=op.f("fk_inventory_store_id_stores"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_inventory")),
        sa.UniqueConstraint("store_id", "product_id", name="uq_inventory_store_id_product_id"),
    )
    op.create_index(op.f("ix_inventory_id"), "inventory", ["id"], unique=False)
    op.create_index(op.f("ix_inventory_product_id"), "inventory", ["product_id"], unique=False)
    op.create_index(op.f("ix_inventory_store_id"), "inventory", ["store_id"], unique=False)

    op.create_table(
        "batches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("batch_number", sa.String(length=100), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name=op.f("fk_batches_product_id_products"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], name=op.f("fk_batches_store_id_stores"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_batches")),
    )
    op.create_index(op.f("ix_batches_batch_number"), "batches", ["batch_number"], unique=False)
    op.create_index(op.f("ix_batches_expiry_date"), "batches", ["expiry_date"], unique=False)
    op.create_index(op.f("ix_batches_id"), "batches", ["id"], unique=False)
    op.create_index(op.f("ix_batches_product_id"), "batches", ["product_id"], unique=False)
    op.create_index(op.f("ix_batches_store_id"), "batches", ["store_id"], unique=False)

    op.create_table(
        "prescriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.String(length=100), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="created"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name=op.f("fk_prescriptions_created_by_user_id_users"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], name=op.f("fk_prescriptions_store_id_stores"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_prescriptions")),
    )
    op.create_index(op.f("ix_prescriptions_created_by_user_id"), "prescriptions", ["created_by_user_id"], unique=False)
    op.create_index(op.f("ix_prescriptions_id"), "prescriptions", ["id"], unique=False)
    op.create_index(op.f("ix_prescriptions_patient_id"), "prescriptions", ["patient_id"], unique=False)
    op.create_index(op.f("ix_prescriptions_status"), "prescriptions", ["status"], unique=False)
    op.create_index(op.f("ix_prescriptions_store_id"), "prescriptions", ["store_id"], unique=False)

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("prescription_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("payment_method", sa.String(length=50), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name=op.f("fk_transactions_created_by_user_id_users"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["prescription_id"], ["prescriptions.id"], name=op.f("fk_transactions_prescription_id_prescriptions"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], name=op.f("fk_transactions_store_id_stores"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transactions")),
    )
    op.create_index(op.f("ix_transactions_created_by_user_id"), "transactions", ["created_by_user_id"], unique=False)
    op.create_index(op.f("ix_transactions_id"), "transactions", ["id"], unique=False)
    op.create_index(op.f("ix_transactions_prescription_id"), "transactions", ["prescription_id"], unique=False)
    op.create_index(op.f("ix_transactions_store_id"), "transactions", ["store_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_transactions_store_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_prescription_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_created_by_user_id"), table_name="transactions")
    op.drop_table("transactions")

    op.drop_index(op.f("ix_prescriptions_store_id"), table_name="prescriptions")
    op.drop_index(op.f("ix_prescriptions_status"), table_name="prescriptions")
    op.drop_index(op.f("ix_prescriptions_patient_id"), table_name="prescriptions")
    op.drop_index(op.f("ix_prescriptions_id"), table_name="prescriptions")
    op.drop_index(op.f("ix_prescriptions_created_by_user_id"), table_name="prescriptions")
    op.drop_table("prescriptions")

    op.drop_index(op.f("ix_batches_store_id"), table_name="batches")
    op.drop_index(op.f("ix_batches_product_id"), table_name="batches")
    op.drop_index(op.f("ix_batches_id"), table_name="batches")
    op.drop_index(op.f("ix_batches_expiry_date"), table_name="batches")
    op.drop_index(op.f("ix_batches_batch_number"), table_name="batches")
    op.drop_table("batches")

    op.drop_index(op.f("ix_inventory_store_id"), table_name="inventory")
    op.drop_index(op.f("ix_inventory_product_id"), table_name="inventory")
    op.drop_index(op.f("ix_inventory_id"), table_name="inventory")
    op.drop_table("inventory")

    op.drop_index(op.f("ix_audit_logs_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_timestamp"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_entity_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_entity_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index(op.f("ix_products_sku"), table_name="products")
    op.drop_index(op.f("ix_products_name"), table_name="products")
    op.drop_index(op.f("ix_products_id"), table_name="products")
    op.drop_index(op.f("ix_products_category"), table_name="products")
    op.drop_table("products")

    op.drop_index(op.f("ix_stores_region"), table_name="stores")
    op.drop_index(op.f("ix_stores_is_online"), table_name="stores")
    op.drop_index(op.f("ix_stores_id"), table_name="stores")
    op.drop_table("stores")

    op.drop_index(op.f("ix_users_role_id"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    op.drop_index(op.f("ix_roles_name"), table_name="roles")
    op.drop_index(op.f("ix_roles_id"), table_name="roles")
    op.drop_table("roles")

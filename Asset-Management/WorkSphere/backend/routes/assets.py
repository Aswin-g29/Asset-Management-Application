from pathlib import Path
from uuid import uuid4

import qrcode
from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import CurrentUser, require_roles
from database import fetch_all, fetch_one, get_db
from schemas import ApiMessage, AssetCreate, AssetUpdate, Pager


router = APIRouter(prefix="/assets", tags=["Assets"])
EDITOR = Depends(require_roles("Admin", "IT Manager"))
ADMIN = Depends(require_roles("Admin"))


def _asset_or_404(asset_id: int) -> dict:
    asset = fetch_one(
        """
        SELECT *
        FROM asset_master
        WHERE asset_id = %s
        LIMIT 1
        """,
        (asset_id,),
    )
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.get("", response_model=Pager)
def list_assets(
    _: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    search: str | None = None,
    status_filter: str | None = None,
    type_filter: str | None = None,
    department: str | None = None,
):
    filters = ["is_retired = FALSE"]
    params: list = []
    if search:
        filters.append("(asset_name LIKE %s OR serial_number LIKE %s OR brand LIKE %s)")
        search_value = f"%{search}%"
        params.extend([search_value, search_value, search_value])
    if status_filter:
        filters.append("asset_status = %s")
        params.append(status_filter)
    if type_filter:
        filters.append("asset_type = %s")
        params.append(type_filter)
    if department:
        filters.append("department = %s")
        params.append(department)

    where_clause = " AND ".join(filters)
    total_row = fetch_one(f"SELECT COUNT(*) AS total FROM asset_master WHERE {where_clause}", tuple(params))
    offset = (page - 1) * page_size
    items = fetch_all(
        f"""
        SELECT *
        FROM asset_master
        WHERE {where_clause}
        ORDER BY modified_on DESC, created_on DESC
        LIMIT %s OFFSET %s
        """,
        tuple([*params, page_size, offset]),
    )
    return {"page": page, "page_size": page_size, "total": total_row["total"], "items": items}


@router.get("/{asset_id}")
def get_asset(asset_id: int, _: CurrentUser):
    asset = _asset_or_404(asset_id)
    transactions = fetch_all(
        """
        SELECT at.*, u1.user_name AS from_employee_name, u2.user_name AS to_assignee_name, up.user_name AS performed_by_name
        FROM asset_transaction at
        LEFT JOIN users u1 ON at.from_employee = u1.user_id
        LEFT JOIN users u2 ON at.to_assignee = u2.user_id
        LEFT JOIN users up ON at.performed_by = up.user_id
        WHERE at.asset_id = %s
        ORDER BY at.action_date DESC
        """,
        (asset_id,),
    )
    maintenance = fetch_all(
        """
        SELECT *
        FROM maintenance
        WHERE asset_id = %s
        ORDER BY created_on DESC
        """,
        (asset_id,),
    )
    return {"asset": asset, "transactions": transactions, "maintenance": maintenance}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_asset(payload: AssetCreate, current_user: dict = EDITOR):
    qr_value = f"WS-{payload.asset_type[:3].upper()}-{uuid4().hex[:12]}"
    query = """
        INSERT INTO asset_master (
            asset_name, asset_type, category, serial_number, qr_code_value, model, brand, specifications,
            purchase_date, purchase_cost, vendor_name, invoice_number, warranty_start_date, warranty_expiry,
            asset_status, condition_status, location, department, is_retired, created_by, modified_by
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE, %s, %s
        )
    """
    with get_db() as (_, cursor):
        cursor.execute(
            query,
            (
                payload.asset_name,
                payload.asset_type,
                payload.category,
                payload.serial_number,
                qr_value,
                payload.model,
                payload.brand,
                payload.specifications,
                payload.purchase_date,
                payload.purchase_cost,
                payload.vendor_name,
                payload.invoice_number,
                payload.warranty_start_date,
                payload.warranty_expiry,
                payload.asset_status,
                payload.condition_status,
                payload.location,
                payload.department,
                current_user["user_id"],
                current_user["user_id"],
            ),
        )
        asset_id = cursor.lastrowid
    return {"message": "Asset created successfully", "asset_id": asset_id, "qr_code_value": qr_value}


@router.put("/{asset_id}")
def update_asset(asset_id: int, payload: AssetUpdate, current_user: dict = EDITOR):
    asset = _asset_or_404(asset_id)
    data = payload.model_dump(exclude_unset=True)
    if not data:
        return {"message": "No changes supplied", "asset_id": asset_id}

    assignments = ", ".join(f"{field} = %s" for field in data.keys())
    values = list(data.values()) + [current_user["user_id"], asset_id]
    with get_db() as (_, cursor):
        cursor.execute(
            f"UPDATE asset_master SET {assignments}, modified_by = %s, modified_on = CURRENT_TIMESTAMP WHERE asset_id = %s",
            tuple(values),
        )
    return {"message": "Asset updated successfully", "asset_before": asset}


@router.patch("/{asset_id}/retire", response_model=ApiMessage)
def retire_asset(asset_id: int, current_user: dict = ADMIN):
    _asset_or_404(asset_id)
    with get_db() as (_, cursor):
        cursor.execute(
            """
            UPDATE asset_master
            SET is_retired = TRUE, asset_status = 'Retired', modified_by = %s, modified_on = CURRENT_TIMESTAMP
            WHERE asset_id = %s
            """,
            (current_user["user_id"], asset_id),
        )
    return {"message": "Asset retired successfully"}


@router.post("/{asset_id}/qr")
def generate_qr(asset_id: int, _: dict = EDITOR):
    asset = _asset_or_404(asset_id)
    qr_value = asset["qr_code_value"] or f"WS-ASSET-{asset_id}"
    qr_dir = Path(__file__).resolve().parent.parent / "static" / "qrcodes"
    qr_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"asset_{asset_id}.png"
    file_path = qr_dir / file_name

    image = qrcode.make(qr_value)
    image.save(file_path)

    image_url = f"/static/qrcodes/{file_name}"
    with get_db() as (_, cursor):
        cursor.execute(
            "UPDATE asset_master SET qr_code_value = %s, qr_code_image_url = %s, modified_on = CURRENT_TIMESTAMP WHERE asset_id = %s",
            (qr_value, image_url, asset_id),
        )
    return {"message": "QR code generated successfully", "qr_code_value": qr_value, "qr_code_image_url": image_url}

from fastapi import APIRouter, Depends, HTTPException

from auth import CurrentUser, require_roles
from database import fetch_all, fetch_one, get_db
from schemas import MaintenanceCreate, MaintenanceUpdate


router = APIRouter(prefix="/maintenance", tags=["Maintenance"])
EDITOR = Depends(require_roles("Admin", "IT Manager"))


def _maintenance_or_404(maintenance_id: int) -> dict:
    row = fetch_one("SELECT * FROM maintenance WHERE maintenance_id = %s LIMIT 1", (maintenance_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    return row


@router.get("")
def list_maintenance(_: CurrentUser):
    rows = fetch_all(
        """
        SELECT m.*, am.asset_name, am.serial_number, am.asset_status
        FROM maintenance m
        INNER JOIN asset_master am ON m.asset_id = am.asset_id
        ORDER BY m.created_on DESC
        """
    )
    return rows


@router.post("")
def create_maintenance(payload: MaintenanceCreate, current_user: dict = EDITOR):
    asset = fetch_one("SELECT asset_id FROM asset_master WHERE asset_id = %s LIMIT 1", (payload.asset_id,))
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    with get_db() as (_, cursor):
        cursor.execute(
            """
            INSERT INTO maintenance (
                asset_id, issue_description, issue_type, warranty_applicable,
                maintenance_status, vendor, resolution_notes, created_on, modified_on
            ) VALUES (%s, %s, %s, %s, 'Open', %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (
                payload.asset_id,
                payload.issue_description,
                payload.issue_type,
                payload.warranty_applicable,
                payload.vendor,
                payload.resolution_notes,
            ),
        )
        cursor.execute(
            """
            UPDATE asset_master
            SET asset_status = 'In Repair', modified_by = %s, modified_on = CURRENT_TIMESTAMP
            WHERE asset_id = %s
            """,
            (current_user["user_id"], payload.asset_id),
        )
    return {"message": "Maintenance issue logged successfully"}


@router.put("/{maintenance_id}")
def update_maintenance(maintenance_id: int, payload: MaintenanceUpdate, _: dict = EDITOR):
    _maintenance_or_404(maintenance_id)
    data = payload.model_dump(exclude_unset=True)
    if not data:
        return {"message": "No changes supplied"}
    assignments = ", ".join(f"{key} = %s" for key in data.keys())
    values = list(data.values()) + [maintenance_id]
    with get_db() as (_, cursor):
        cursor.execute(
            f"UPDATE maintenance SET {assignments}, modified_on = CURRENT_TIMESTAMP WHERE maintenance_id = %s",
            tuple(values),
        )
    return {"message": "Maintenance record updated successfully"}


@router.patch("/{maintenance_id}/close")
def close_maintenance(maintenance_id: int, current_user: dict = EDITOR):
    record = _maintenance_or_404(maintenance_id)
    with get_db() as (_, cursor):
        cursor.execute(
            """
            UPDATE maintenance
            SET maintenance_status = 'Closed', modified_on = CURRENT_TIMESTAMP
            WHERE maintenance_id = %s
            """,
            (maintenance_id,),
        )
        cursor.execute(
            """
            UPDATE asset_master
            SET asset_status = 'Available', modified_by = %s, modified_on = CURRENT_TIMESTAMP
            WHERE asset_id = %s
            """,
            (current_user["user_id"], record["asset_id"]),
        )
    return {"message": "Maintenance closed and asset marked available"}

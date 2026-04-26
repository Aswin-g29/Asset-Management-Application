from fastapi import APIRouter, Depends, HTTPException, status

from auth import CurrentUser, require_roles
from database import fetch_all, fetch_one, get_db
from schemas import AssignmentRequest, TransferRequest


router = APIRouter(prefix="/transactions", tags=["Transactions"])
EDITOR = Depends(require_roles("Admin", "IT Manager"))


def _find_asset(asset_id: int) -> dict:
    asset = fetch_one("SELECT * FROM asset_master WHERE asset_id = %s LIMIT 1", (asset_id,))
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


def _find_user(user_id: int) -> dict:
    user = fetch_one("SELECT user_id, user_name, is_active FROM users WHERE user_id = %s LIMIT 1", (user_id,))
    if not user or not user["is_active"]:
        raise HTTPException(status_code=404, detail="Assignee not found or inactive")
    return user


@router.get("")
def list_transactions(_: CurrentUser):
    rows = fetch_all(
        """
        SELECT at.*, am.asset_name, am.serial_number,
               u1.user_name AS from_employee_name,
               u2.user_name AS to_assignee_name,
               up.user_name AS performed_by_name
        FROM asset_transaction at
        INNER JOIN asset_master am ON at.asset_id = am.asset_id
        LEFT JOIN users u1 ON at.from_employee = u1.user_id
        LEFT JOIN users u2 ON at.to_assignee = u2.user_id
        LEFT JOIN users up ON at.performed_by = up.user_id
        ORDER BY at.action_date DESC
        """
    )
    return rows


@router.post("/assign", status_code=status.HTTP_201_CREATED)
def assign_asset(payload: AssignmentRequest, current_user: dict = EDITOR):
    asset = _find_asset(payload.asset_id)
    _find_user(payload.to_assignee)
    if asset["asset_status"] != "Available":
        raise HTTPException(status_code=400, detail="Only available assets can be assigned")

    with get_db() as (_, cursor):
        cursor.execute(
            """
            INSERT INTO asset_transaction (
                asset_id, asset_type, from_employee, to_assignee, action_date,
                transaction_type, remarks, performed_by, created_by, created_on
            ) VALUES (%s, %s, NULL, %s, NOW(), 'New Asset', %s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (payload.asset_id, asset["asset_type"], payload.to_assignee, payload.remarks, current_user["user_id"], current_user["user_id"]),
        )
        cursor.execute(
            """
            UPDATE asset_master
            SET asset_status = 'Assigned', modified_by = %s, modified_on = CURRENT_TIMESTAMP
            WHERE asset_id = %s
            """,
            (current_user["user_id"], payload.asset_id),
        )
    return {"message": "Asset assigned successfully"}


@router.post("/transfer", status_code=status.HTTP_201_CREATED)
def transfer_asset(payload: TransferRequest, current_user: dict = EDITOR):
    asset = _find_asset(payload.asset_id)
    _find_user(payload.to_assignee)
    if asset["asset_status"] != "Assigned":
        raise HTTPException(status_code=400, detail="Only assigned assets can be transferred")

    previous = fetch_one(
        """
        SELECT to_assignee
        FROM asset_transaction
        WHERE asset_id = %s
        ORDER BY action_date DESC, transaction_id DESC
        LIMIT 1
        """,
        (payload.asset_id,),
    )
    if not previous or not previous["to_assignee"]:
        raise HTTPException(status_code=400, detail="Transfer requires an existing assignee")

    with get_db() as (_, cursor):
        cursor.execute(
            """
            INSERT INTO asset_transaction (
                asset_id, asset_type, from_employee, to_assignee, action_date,
                transaction_type, remarks, performed_by, created_by, created_on
            ) VALUES (%s, %s, %s, %s, NOW(), 'Asset Transfer', %s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (
                payload.asset_id,
                asset["asset_type"],
                previous["to_assignee"],
                payload.to_assignee,
                payload.remarks,
                current_user["user_id"],
                current_user["user_id"],
            ),
        )
    return {"message": "Asset transferred successfully", "from_employee": previous["to_assignee"]}

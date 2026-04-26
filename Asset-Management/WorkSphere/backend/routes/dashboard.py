from fastapi import APIRouter

from auth import CurrentUser
from database import fetch_all


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("")
def get_dashboard(_: CurrentUser):
    counts = fetch_all(
        """
        SELECT asset_status, COUNT(*) AS count
        FROM asset_master
        GROUP BY asset_status
        """
    )
    summary = {
        "total_assets": 0,
        "available": 0,
        "assigned": 0,
        "in_repair": 0,
        "retired": 0,
    }
    for row in counts:
        summary["total_assets"] += row["count"]
        status = row["asset_status"]
        if status == "Available":
            summary["available"] = row["count"]
        elif status == "Assigned":
            summary["assigned"] = row["count"]
        elif status == "In Repair":
            summary["in_repair"] = row["count"]
        elif status == "Retired":
            summary["retired"] = row["count"]

    warranty_alerts = fetch_all(
        """
        SELECT asset_id, asset_name, serial_number, warranty_start_date, warranty_expiry,
               DATE_ADD(warranty_start_date, INTERVAL warranty_expiry YEAR) AS warranty_end_date
        FROM asset_master
        WHERE is_retired = FALSE
          AND warranty_start_date IS NOT NULL
          AND warranty_expiry IS NOT NULL
          AND DATEDIFF(DATE_ADD(warranty_start_date, INTERVAL warranty_expiry YEAR), CURDATE()) BETWEEN 0 AND 30
        ORDER BY warranty_end_date ASC
        """
    )

    recent_transactions = fetch_all(
        """
        SELECT at.transaction_id, at.transaction_type, at.action_date, am.asset_name,
               u1.user_name AS from_employee_name, u2.user_name AS to_assignee_name
        FROM asset_transaction at
        INNER JOIN asset_master am ON at.asset_id = am.asset_id
        LEFT JOIN users u1 ON at.from_employee = u1.user_id
        LEFT JOIN users u2 ON at.to_assignee = u2.user_id
        ORDER BY at.action_date DESC
        LIMIT 5
        """
    )

    recent_maintenance = fetch_all(
        """
        SELECT m.maintenance_id, m.issue_type, m.maintenance_status, m.created_on, am.asset_name
        FROM maintenance m
        INNER JOIN asset_master am ON m.asset_id = am.asset_id
        ORDER BY m.created_on DESC
        LIMIT 5
        """
    )

    return {
        "counts": summary,
        "warranty_alerts": warranty_alerts,
        "recent_transactions": recent_transactions,
        "recent_maintenance": recent_maintenance,
    }

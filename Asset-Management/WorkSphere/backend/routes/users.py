from fastapi import APIRouter, Depends, HTTPException, status

from auth import CurrentUser, hash_password, require_roles
from database import fetch_all, fetch_one, get_db
from schemas import ApiMessage, UserCreate, UserUpdate


router = APIRouter(prefix="/users", tags=["Users"])
ADMIN = Depends(require_roles("Admin"))
MANAGER_OR_ADMIN = Depends(require_roles("Admin", "IT Manager"))


@router.get("/assignable")
def list_assignable_users(_: dict = MANAGER_OR_ADMIN):
    return fetch_all(
        """
        SELECT user_id, user_name, username, role, is_active
        FROM users
        WHERE is_active = TRUE
        ORDER BY user_name ASC
        """
    )


@router.get("")
def list_users(_: dict = ADMIN):
    return fetch_all(
        """
        SELECT user_id, user_name, username, email, role, is_active, created_on, modified_on
        FROM users
        ORDER BY user_name ASC
        """
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, _: dict = ADMIN):
    existing = fetch_one(
        "SELECT user_id FROM users WHERE username = %s OR email = %s LIMIT 1",
        (payload.username, payload.email),
    )
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    with get_db() as (_, cursor):
        cursor.execute(
            """
            INSERT INTO users (user_name, username, email, password_hash, role, is_active, created_on, modified_on)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (
                payload.user_name,
                payload.username,
                payload.email,
                hash_password(payload.password),
                payload.role,
                payload.is_active,
            ),
        )
        user_id = cursor.lastrowid
    return {"message": "User created successfully", "user_id": user_id}


@router.put("/{user_id}")
def update_user(user_id: int, payload: UserUpdate, _: dict = ADMIN):
    user = fetch_one("SELECT user_id FROM users WHERE user_id = %s LIMIT 1", (user_id,))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    data = payload.model_dump(exclude_unset=True)
    if not data:
        return {"message": "No changes supplied"}
    if "password" in data:
        data["password_hash"] = hash_password(data.pop("password"))
    assignments = ", ".join(f"{key} = %s" for key in data.keys())
    values = list(data.values()) + [user_id]
    with get_db() as (_, cursor):
        cursor.execute(
            f"UPDATE users SET {assignments}, modified_on = CURRENT_TIMESTAMP WHERE user_id = %s",
            tuple(values),
        )
    return {"message": "User updated successfully"}


@router.patch("/{user_id}/deactivate", response_model=ApiMessage)
def deactivate_user(user_id: int, _: dict = ADMIN):
    user = fetch_one("SELECT user_id FROM users WHERE user_id = %s LIMIT 1", (user_id,))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    with get_db() as (_, cursor):
        cursor.execute(
            "UPDATE users SET is_active = FALSE, modified_on = CURRENT_TIMESTAMP WHERE user_id = %s",
            (user_id,),
        )
    return {"message": "User deactivated successfully"}

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


RoleType = Literal["Admin", "IT Manager", "Viewer"]
AssetType = Literal["Laptop", "Desktop", "Server", "Furniture", "Printer", "Phone", "Monitor", "UPS", "Other"]
CategoryType = Literal["IT", "Non-IT"]
AssetStatus = Literal["Available", "Assigned", "In Repair", "Retired", "Lost"]
ConditionStatus = Literal["New", "Good", "Damaged"]
TransactionType = Literal["New Asset", "Asset Transfer"]
IssueType = Literal["Repair", "Physical Damage", "Theft", "Software Issue"]
MaintenanceStatus = Literal["Open", "In Progress", "Closed"]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class LoginRequest(BaseModel):
    username: str
    password: str


class UserBase(BaseModel):
    user_name: str = Field(..., max_length=100)
    username: str = Field(..., max_length=50)
    email: EmailStr
    role: RoleType
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=4, max_length=100)


class UserUpdate(BaseModel):
    user_name: str | None = None
    username: str | None = None
    email: EmailStr | None = None
    role: RoleType | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=4, max_length=100)


class AssetBase(BaseModel):
    asset_name: str
    asset_type: AssetType
    category: CategoryType
    serial_number: str
    model: str | None = None
    brand: str | None = None
    specifications: str | None = None
    purchase_date: date | None = None
    purchase_cost: Decimal | None = None
    vendor_name: str | None = None
    invoice_number: str | None = None
    warranty_start_date: date | None = None
    warranty_expiry: int | None = None
    asset_status: AssetStatus = "Available"
    condition_status: ConditionStatus = "New"
    location: str | None = None
    department: str | None = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    asset_name: str | None = None
    asset_type: AssetType | None = None
    category: CategoryType | None = None
    serial_number: str | None = None
    model: str | None = None
    brand: str | None = None
    specifications: str | None = None
    purchase_date: date | None = None
    purchase_cost: Decimal | None = None
    vendor_name: str | None = None
    invoice_number: str | None = None
    warranty_start_date: date | None = None
    warranty_expiry: int | None = None
    asset_status: AssetStatus | None = None
    condition_status: ConditionStatus | None = None
    location: str | None = None
    department: str | None = None


class AssignmentRequest(BaseModel):
    asset_id: int
    to_assignee: int
    remarks: str | None = None


class TransferRequest(BaseModel):
    asset_id: int
    to_assignee: int
    remarks: str | None = None


class MaintenanceCreate(BaseModel):
    asset_id: int
    issue_description: str
    issue_type: IssueType
    warranty_applicable: bool = False
    vendor: str | None = None
    resolution_notes: str | None = None


class MaintenanceUpdate(BaseModel):
    issue_description: str | None = None
    issue_type: IssueType | None = None
    warranty_applicable: bool | None = None
    maintenance_status: MaintenanceStatus | None = None
    vendor: str | None = None
    resolution_notes: str | None = None


class ApiMessage(BaseModel):
    message: str


class Pager(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page: int
    page_size: int
    total: int
    items: list[dict]


class DashboardResponse(BaseModel):
    counts: dict
    warranty_alerts: list[dict]
    recent_transactions: list[dict]
    recent_maintenance: list[dict]

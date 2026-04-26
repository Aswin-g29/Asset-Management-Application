from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from auth import authenticate_user, create_access_token
from routes import assets, dashboard, maintenance, transactions, users
from schemas import LoginRequest, TokenResponse


app = FastAPI(title="WorkSphere Asset Management System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def root():
    return {"message": "WorkSphere API is running"}


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    access_token = create_access_token({"sub": str(user["user_id"]), "role": user["role"], "username": user["username"]})
    user.pop("password_hash", None)
    return {"access_token": access_token, "token_type": "bearer", "user": user}


app.include_router(dashboard.router)
app.include_router(assets.router)
app.include_router(transactions.router)
app.include_router(maintenance.router)
app.include_router(users.router)

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from .schemas import UserCreate
from .service import (
    existing_user,
    create_user,
    authenticate,
    create_access_token,
    get_current_user,
)

router = APIRouter()


@router.post("/signup", tags=["auth"], status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate):
    user_exists = await existing_user(user.username, user.email)
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already in use",
        )

    create_result = await create_user(user)

    # Use user info from the request (or existing_user function) since create_user returns no user details
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": create_result["user_id"],
            "role": "user",  # default role or from UserCreate if available
        }
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "role": "user",
    }


@router.post("/token", tags=["auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(
    data={
        "sub": user["username"],
        "user_id": user["id"],        # <-- fix here
        "role": user["role"],
        }
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/profile")
async def profile(current_user: dict = Depends(get_current_user)):
    # Return current user info (excluding sensitive info)
    user_data = current_user.copy()
    user_data.pop("hashed_password", None)
    return user_data

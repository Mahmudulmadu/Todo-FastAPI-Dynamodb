from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: str
    role: Optional[str] = "user"  # Default to user role

class UserCreate(UserBase):
    password: str 

class User(UserBase):
    created_dt: datetime

class UserSchema(BaseModel):

    username: str
    email: str
    role: str
    created_dt: datetime

    class Config:
        from_attributes = True  # or orm_mode = True if Pydantic v1

import os
import aioboto3
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends, Security
from fastapi.security import OAuth2PasswordBearer
from contextlib import asynccontextmanager
import uuid
from boto3.dynamodb.conditions import Key, Attr
from .schemas import UserCreate

SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")
ALGORITHM = "HS256"
EXPIRE_MINUTES = 60 * 24  # 1 day
DYNAMO_REGION = "us-east-1"
USERS_TABLE = "users"

bcrypt_context = CryptContext(schemes=["bcrypt"])
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")

session = aioboto3.Session()


@asynccontextmanager
async def get_dynamodb_client():
    async with session.client("dynamodb", region_name=DYNAMO_REGION) as client:
        yield client

def generate_user_id():
    return str(uuid.uuid4())

async def create_user(user: UserCreate):
    if await existing_user(user.username, user.email):
        raise HTTPException(status_code=400, detail="User already exists.")

    hashed_password = bcrypt_context.hash(user.password)
    user_id = generate_user_id()

    user_item = {
        "id": {"S": user_id},
        "username": {"S": user.username},
        "email": {"S": user.email},
        "hashed_password": {"S": hashed_password},
        "role": {"S": user.role if user.role else "user"}  # <-- allow admin/user
    }

    async with get_dynamodb_client() as client:
        await client.put_item(TableName=USERS_TABLE, Item=user_item)

    return {"message": "User created successfully", "user_id": user_id}


async def existing_user(username: str, email: str):
    async with get_dynamodb_client() as client:
        # Query username-index
        response_username = await client.query(
            TableName=USERS_TABLE,
            IndexName="username-index",
            KeyConditionExpression="username = :username",
            ExpressionAttributeValues={":username": {"S": username}}
        )
        if response_username.get("Items"):
            return response_username["Items"][0]

        # Query email-index
        response_email = await client.query(
            TableName=USERS_TABLE,
            IndexName="email-index",
            KeyConditionExpression="email = :email",
            ExpressionAttributeValues={":email": {"S": email}}
        )
        if response_email.get("Items"):
            return response_email["Items"][0]

        return None

async def authenticate(username: str, password: str):
    async with get_dynamodb_client() as client:
        response = await client.query(
            TableName=USERS_TABLE,
            IndexName="username-index",
            KeyConditionExpression="username = :username",
            ExpressionAttributeValues={":username": {"S": username}}
        )
        items = response.get("Items", [])
        if not items:
            return None
        # convert DynamoDB item from AttributeValue format to dict
        user = {k: list(v.values())[0] for k, v in items[0].items()}
        if not bcrypt_context.verify(password, user["hashed_password"]):
            return None
        return user

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=EXPIRE_MINUTES)
    to_encode.update({
        "exp": int(expire.timestamp()),
        "role": data.get("role")  # include role in token
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def deserialize_dynamodb_item(item):
    # simple helper to convert DynamoDB attribute values to plain dict
    return {k: list(v.values())[0] for k, v in item.items()}

async def get_current_user(token: str = Depends(oauth2_bearer)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        username: str = payload.get("sub")
        exp = payload.get("exp")

        if datetime.utcnow().timestamp() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        if user_id is None or username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        async with get_dynamodb_client() as table:
            response = await table.get_item(
                TableName=USERS_TABLE,
                Key={"id": {"S": user_id}}
            )

            item = response.get("Item")
            if not item:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )

            user = deserialize_dynamodb_item(item)
            return user  # keep role from DynamoDB, not JWT

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        username: str = payload.get("sub")
        role: str = payload.get("role")
        exp = payload.get("exp")

        if datetime.utcnow().timestamp() > exp:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
        if user_id is None or username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        async with get_dynamodb_client() as table:
            response = await table.get_item(
                TableName=USERS_TABLE,
                Key={"id": {"S": user_id}}
            )

            item = response.get("Item")
            if not item:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

            user = deserialize_dynamodb_item(item)
            user["role"] = role  # you can override from token or keep from DynamoDB if stored there
            return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def RoleChecker(allowed_roles: list[str]):
    async def checker(current_user=Security(get_current_user)):
        print("User role:", current_user.get('role'))
        if current_user.get('role') not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have enough permissions"
            )
        return current_user
    return checker



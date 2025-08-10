import aioboto3
from datetime import datetime
import uuid
from contextlib import asynccontextmanager

DYNAMO_REGION = "us-east-1"
TODOS_TABLE = "todos"

session = aioboto3.Session()

@asynccontextmanager
async def get_dynamodb_table():
    async with session.resource("dynamodb", region_name=DYNAMO_REGION) as dynamodb:
        table = await dynamodb.Table(TODOS_TABLE)
        yield table


async def create_todo(todo_data: dict):
    todo_data["todo_id"] = str(uuid.uuid4())
    todo_data["created_dt"] = datetime.utcnow().isoformat()

    async with get_dynamodb_table() as table:
        await table.put_item(Item=todo_data)

    return todo_data


async def get_todo(todo_id: str):
    async with get_dynamodb_table() as table:
        response = await table.get_item(Key={"todo_id": todo_id})
        return response.get("Item")


async def get_todos(limit: int = None):
    async with get_dynamodb_table() as table:
        response = await table.scan()
        items = response.get("Items", [])
        return items[:limit] if limit else items


async def update_todo(todo_id: str, updated_fields: dict):
    existing = await get_todo(todo_id)
    if not existing:
        return None

    # Merge updated fields (skip None)
    for k, v in updated_fields.items():
        if v is not None:
            existing[k] = v

    async with get_dynamodb_table() as table:
        await table.put_item(Item=existing)

    return existing


async def delete_todo(todo_id: str):
    existing = await get_todo(todo_id)
    if not existing:
        return None

    async with get_dynamodb_table() as table:
        await table.delete_item(Key={"todo_id": todo_id})

    return existing

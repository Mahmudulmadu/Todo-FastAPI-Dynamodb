from fastapi import FastAPI, Depends, HTTPException, status
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import IntEnum
from UserManagement.service import get_current_user, RoleChecker
from UserManagement import todo_service  # import your new todo_service async Dynamo calls
from UserManagement.routes import router as auth_router
app = FastAPI()
app.include_router(auth_router, prefix="/auth")
class Priority(IntEnum):
    LOW = 3
    MEDIUM = 2
    HIGH = 1

class TodoBase(BaseModel):
    todo_name: str = Field(..., min_length=3, max_length=512)
    todo_description: str = Field(..., min_length=1)
    priority: Priority = Priority.LOW

class TodoCreate(TodoBase):
    pass

class TodoUpdate(BaseModel):
    todo_name: Optional[str] = Field(None, min_length=3, max_length=512)
    todo_description: Optional[str] = None
    priority: Optional[Priority] = None

class TodoResponse(TodoBase):
    todo_id: str

@app.post("/todos", response_model=TodoResponse)
async def create_todo(todo: TodoCreate):
    new_todo = await todo_service.create_todo(todo.dict())
    return TodoResponse(**new_todo)

@app.get("/todos/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: str):
    todo = await todo_service.get_todo(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return TodoResponse(**todo)

@app.get("/todos", response_model=List[TodoResponse])
async def get_todos(first_n: Optional[int] = None):
    todos = await todo_service.get_todos(limit=first_n)
    return [TodoResponse(**t) for t in todos]

@app.put("/todos/{todo_id}", response_model=TodoResponse)
async def update_todo(todo_id: str, todo_update: TodoUpdate):
    updated_todo = await todo_service.update_todo(todo_id, todo_update.dict(exclude_unset=True))
    if not updated_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return TodoResponse(**updated_todo)

@app.delete("/todos/{todo_id}", response_model=TodoResponse)
async def delete_todo(
    todo_id: str,
    current_user=Depends(RoleChecker(["admin"]))  # Only admin can delete
):
    deleted = await todo_service.delete_todo(todo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Todo not found")
    return TodoResponse(**deleted)

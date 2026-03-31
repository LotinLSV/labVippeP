from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    is_admin: bool = False

class User(UserBase):
    id: int
    n8n_link: Optional[str] = None
    is_admin: bool = False
    
    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    name: str
    scope: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    value: Optional[float] = None

class ProjectCreate(ProjectBase):
    pass

class TaskBase(BaseModel):
    name: str
    start_date: datetime
    end_date: datetime
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    status: Optional[str] = "A Fazer"
    percentage: Optional[float] = 0.0

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: int
    project_id: int
    class Config:
        from_attributes = True

class Project(ProjectBase):
    id: int
    tap_generated: bool
    created_at: datetime
    owner_id: int
    scheduled_start_date: Optional[datetime] = None
    scheduled_end_date: Optional[datetime] = None
    percentage: Optional[float] = 0.0
    tasks: List[Task] = []

    class Config:
        from_attributes = True

class ChatMessage(BaseModel):
    role: str
    content: str

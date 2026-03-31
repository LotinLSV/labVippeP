from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    n8n_link = Column(String, nullable=True)
    typebot_link = Column(String, nullable=True)
    minion_link = Column(String, nullable=True)
    lovable_link = Column(String, nullable=True)
    open_claw_link = Column(String, nullable=True)
    quickcharts_link = Column(String, nullable=True)
    dify_link = Column(String, nullable=True)
    chatwoot_link = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    show_projects = Column(Boolean, default=False)
    
    projects = relationship("Project", back_populates="owner")
    files = relationship("UploadedFile", back_populates="owner")
    chats = relationship("ChatMessage", back_populates="owner")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    scope = Column(Text)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    value = Column(Float, nullable=True)
    tap_generated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    scheduled_start_date = Column(DateTime, nullable=True)
    scheduled_end_date = Column(DateTime, nullable=True)
    percentage = Column(Float, default=0.0)
    
    out_of_scope = Column(Text, nullable=True)
    justification = Column(Text, nullable=True)
    objectives = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    assumptions = Column(Text, nullable=True)
    restrictions = Column(Text, nullable=True)
    risks = Column(Text, nullable=True)
    
    baseline_start_date = Column(DateTime, nullable=True)
    baseline_end_date = Column(DateTime, nullable=True)
    
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    actual_start_date = Column(DateTime, nullable=True)
    actual_end_date = Column(DateTime, nullable=True)
    status = Column(String, default="A Fazer")
    percentage = Column(Float, default=0.0)
    
    project_id = Column(Integer, ForeignKey("projects.id"))
    project = relationship("Project", back_populates="tasks")

class UploadedFile(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    filepath = Column(String)
    content_type = Column(String)
    vector_ids = Column(String, nullable=True)
    
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="files")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String) # 'user' or 'ai'
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="chats")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    project = relationship("Project")

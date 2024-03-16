"""app.py"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
# from celery import Celery
# from celery import shared_task
from celery.app import Celery
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

"""Create SQLite database engine"""
SQLALCHEMY_DATABASE_URL = "sqlite:///./db.sqlite3"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

"""Create a Session class for interacting with the database"""
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

"""Define the base class for ORM models"""
Base = declarative_base()

"""Define ORM model for User"""
class User(Base):
    __tablename__ = "user_user"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String, unique=False, index=False)
    is_active = Column(Boolean, default=False)
    is_staff = Column(Boolean, default=False)

"""Define ORM model for Task"""
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    due_date = Column(DateTime)
    priority = Column(String)
    assigned_to = Column(String, ForeignKey('user_user.email'))

"""Initialize FastAPI app"""
app = FastAPI()

"""Celery instance"""
CELERY_IMPORTS=(__name__)

celery = Celery(
    __name__,
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

"""Celery task to send email notification"""
@celery.task(name='send_email_notification')
def send_email_notification(email: str, subject: str, body: str):
    """Email configuration (replace with your SMTP settings)"""
    smtp_host = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'your email address'
    smtp_password = 'your password'

    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, email, msg.as_string())

"""Pydantic model for Task"""
class TaskCreate(BaseModel):
    title: str
    description: str
    due_date: datetime
    priority: str
    assigned_to: str

"""Create tables in the database"""
Base.metadata.create_all(bind=engine)

"""Endpoint to create a task"""
@app.post("/tasks/")
async def create_task(task: TaskCreate, background_tasks: BackgroundTasks):
    db = SessionLocal()
    db_task = Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    db.close()
    send_email_notification.delay(task.assigned_to)

    # celery.send_task(
    #     "send_email_notification",
    #     (
    #         task.assigned_to,
    #         "Task Created",
    #         f"New Task: {task.title} assigned to you."
    #     ),
    # )

    return {"message": "Task created successfully"}

"""Endpoint to retrieve all tasks"""
@app.get("/tasks/")
async def get_tasks():
    db = SessionLocal()
    tasks = db.query(Task).all()
    db.close()
    return tasks

"""Endpoint to retrieve a single task by id"""
@app.get("/tasks/{task_id}")
async def get_task(task_id: int):
    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id).first()
    db.close()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

"""Endpoint to update a task"""
@app.put("/tasks/{task_id}")
async def update_task(task_id: int, task: TaskCreate):
    db = SessionLocal()
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        db.close()
        raise HTTPException(status_code=404, detail="Task not found")
    
    old_assigned_to = db_task.assigned_to

    for key, value in task.dict().items():
        setattr(db_task, key, value)
    db.commit()
    db.refresh(db_task)
    db.close()

    if task.assigned_to != old_assigned_to:
        celery.send_task(
            "send_email_notification",
            (
                task.assigned_to,
                "Task Updated",
                f"Task: {task.title} has been reassigned to you."
            )
        )

    return {"message": "Task updated successfully"}

"""Endpoint to delete a task"""
@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    db = SessionLocal()
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        db.close()
        raise HTTPException(status_code=404, detail="Task not found")
    
    assigned_to = db_task.assigned_to
    task_title = db_task.title

    db.delete(db_task)
    db.commit()
    db.close()

    celery.send_task(
        "send_email_notification",
        (
            assigned_to,
            "Task Deleted",
            f"Task: {task_title} assigned to you has been deleted."
        ),
    )

    return {"message": "Task deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

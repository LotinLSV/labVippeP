from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from dotenv import load_dotenv

load_dotenv()

from . import models, database
from .routes import auth, chat, projects, admin

os.makedirs("app/static/css", exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("data/uploads", exist_ok=True)

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="@lab niscios")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(projects.router)
app.include_router(admin.router)

@app.get("/", response_class=HTMLResponse)
async def dashboard_view(request: Request):
    db_gen = database.get_db()
    db = next(db_gen)
    user = auth.get_current_user_from_cookie(request, db)
    try:
        next(db_gen)
    except StopIteration:
        pass
        
    if not user:
        return templates.TemplateResponse("login.html", {"request": request})
        
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@app.get("/login", response_class=HTMLResponse)
async def login_view(request: Request):
    error = request.query_params.get("error")
    return templates.TemplateResponse("login.html", {"request": request, "error": error})

@app.get("/register", response_class=HTMLResponse)
async def register_view(request: Request):
    error = request.query_params.get("error")
    return templates.TemplateResponse("register.html", {"request": request, "error": error})

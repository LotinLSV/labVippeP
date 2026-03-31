from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from .. import models, database
from .auth import get_current_admin_user, get_password_hash

router = APIRouter(prefix="/admin", tags=["admin"])

SERVICE_FIELDS = [
    "n8n_link", "typebot_link", "minion_link", "lovable_link",
    "open_claw_link", "quickcharts_link", "dify_link", "chatwoot_link"
]

# ─── List Users ───────────────────────────────────────────────────────────────
@router.get("/users", response_class=HTMLResponse)
async def admin_users_list(
    request: Request,
    db: Session = Depends(database.get_db),
    admin_user: models.User = Depends(get_current_admin_user)
):
    users = db.query(models.User).all()
    from ..main import templates
    return templates.TemplateResponse("admin_users.html", {
        "request": request, "user": admin_user, "users_list": users
    })

# ─── New User ─────────────────────────────────────────────────────────────────
@router.get("/users/new", response_class=HTMLResponse)
async def admin_user_new(
    request: Request,
    db: Session = Depends(database.get_db),
    admin_user: models.User = Depends(get_current_admin_user)
):
    from ..main import templates
    return templates.TemplateResponse("admin_user_new.html", {
        "request": request, "user": admin_user
    })

@router.post("/users/new")
async def create_user_admin(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    is_admin: Optional[str] = Form(None),
    show_projects: Optional[str] = Form(None),
    n8n_link: str = Form(""),
    typebot_link: str = Form(""),
    minion_link: str = Form(""),
    lovable_link: str = Form(""),
    open_claw_link: str = Form(""),
    quickcharts_link: str = Form(""),
    dify_link: str = Form(""),
    chatwoot_link: str = Form(""),
    db: Session = Depends(database.get_db),
    admin_user: models.User = Depends(get_current_admin_user)
):
    db_user = db.query(models.User).filter(models.User.username == username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Usuário já registrado no sistema.")

    hashed_password = get_password_hash(password)
    new_user = models.User(
        username=username,
        hashed_password=hashed_password,
        is_admin=(is_admin == "true"),
        show_projects=(show_projects == "true"),
        n8n_link=n8n_link or None,
        typebot_link=typebot_link or None,
        minion_link=minion_link or None,
        lovable_link=lovable_link or None,
        open_claw_link=open_claw_link or None,
        quickcharts_link=quickcharts_link or None,
        dify_link=dify_link or None,
        chatwoot_link=chatwoot_link or None,
    )
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=302)

# ─── Edit User ────────────────────────────────────────────────────────────────
@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
async def admin_user_edit_form(
    user_id: int,
    request: Request,
    db: Session = Depends(database.get_db),
    admin_user: models.User = Depends(get_current_admin_user)
):
    target_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    from ..main import templates
    return templates.TemplateResponse("admin_user_edit.html", {
        "request": request, "user": admin_user, "target_user": target_user
    })

@router.post("/users/{user_id}/edit")
async def admin_user_edit_submit(
    user_id: int,
    request: Request,
    username: str = Form(...),
    new_password: str = Form(""),
    is_admin: Optional[str] = Form(None),
    show_projects: Optional[str] = Form(None),
    n8n_link: str = Form(""),
    typebot_link: str = Form(""),
    minion_link: str = Form(""),
    lovable_link: str = Form(""),
    open_claw_link: str = Form(""),
    quickcharts_link: str = Form(""),
    dify_link: str = Form(""),
    chatwoot_link: str = Form(""),
    db: Session = Depends(database.get_db),
    admin_user: models.User = Depends(get_current_admin_user)
):
    target_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    # Check username conflict (ignore self)
    conflict = db.query(models.User).filter(
        models.User.username == username,
        models.User.id != user_id
    ).first()
    if conflict:
        raise HTTPException(status_code=400, detail="Nome de usuário já em uso por outro usuário.")

    target_user.username = username
    target_user.is_admin = (is_admin == "true")
    target_user.show_projects = (show_projects == "true")
    target_user.n8n_link = n8n_link or None
    target_user.typebot_link = typebot_link or None
    target_user.minion_link = minion_link or None
    target_user.lovable_link = lovable_link or None
    target_user.open_claw_link = open_claw_link or None
    target_user.quickcharts_link = quickcharts_link or None
    target_user.dify_link = dify_link or None
    target_user.chatwoot_link = chatwoot_link or None

    if new_password.strip():
        target_user.hashed_password = get_password_hash(new_password.strip())

    db.commit()
    return RedirectResponse(url="/admin/users", status_code=302)

# ─── Delete User ──────────────────────────────────────────────────────────────
@router.post("/users/{user_id}/delete")
async def admin_user_delete(
    user_id: int,
    request: Request,
    db: Session = Depends(database.get_db),
    admin_user: models.User = Depends(get_current_admin_user)
):
    if user_id == admin_user.id:
        raise HTTPException(status_code=400, detail="Você não pode deletar sua própria conta.")
    target_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    db.delete(target_user)
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=302)

from fastapi import APIRouter, Depends, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from .. import models, database
from .auth import get_current_user_required
from ..services import document_processor, llm_agent

router = APIRouter(prefix="/chat", tags=["chat"])

@router.get("/", response_class=HTMLResponse)
async def chat_view(request: Request, db: Session = Depends(database.get_db)):
    user = get_current_user_required(request, db)
    files = db.query(models.UploadedFile).filter(models.UploadedFile.owner_id == user.id).all()
    messages = db.query(models.ChatMessage).filter(models.ChatMessage.owner_id == user.id).order_by(models.ChatMessage.created_at.asc()).all()
    
    from ..main import templates
    return templates.TemplateResponse("chat.html", {"request": request, "user": user, "files": files, "messages": messages})

@router.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    user = get_current_user_required(request, db)
    
    await document_processor.process_and_store(file, user.id, db)
    return RedirectResponse(url="/chat", status_code=302)

@router.post("/message")
async def send_message(request: Request, message: str = Form(...), db: Session = Depends(database.get_db)):
    user = get_current_user_required(request, db)
    
    user_msg = models.ChatMessage(role="user", content=message, owner_id=user.id)
    db.add(user_msg)
    db.commit()
    
    ai_response = await llm_agent.get_response(message, user.id, db)
    
    ai_msg = models.ChatMessage(role="ai", content=ai_response, owner_id=user.id)
    db.add(ai_msg)
    db.commit()
    
    return RedirectResponse(url="/chat", status_code=302)

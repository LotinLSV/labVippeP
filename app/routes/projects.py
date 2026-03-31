from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models, database
from .auth import get_current_user_required
from datetime import datetime
from ..services import project_agent

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("/", response_class=HTMLResponse)
async def projects_view(request: Request, db: Session = Depends(database.get_db)):
    user = get_current_user_required(request, db)
    projects = db.query(models.Project).filter(models.Project.owner_id == user.id).order_by(models.Project.created_at.desc()).all()
    
    from ..main import templates
    return templates.TemplateResponse("projects.html", {"request": request, "user": user, "projects": projects})

@router.get("/reports", response_class=HTMLResponse)
async def reports_view(request: Request, db: Session = Depends(database.get_db)):
    user = get_current_user_required(request, db)
    
    projects = db.query(models.Project).filter(models.Project.owner_id == user.id).all()
    
    total_projects = len(projects)
    total_value = sum([(p.value or 0.0) for p in projects])
    avg_completion = sum([(p.percentage or 0.0) for p in projects]) / total_projects if total_projects > 0 else 0
    
    # Task distribution across all projects
    all_tasks = db.query(models.Task).join(models.Project).filter(models.Project.owner_id == user.id).all()
    status_dist = {"A Fazer": 0, "Em Andamento": 0, "Concluído": 0}
    for task in all_tasks:
        if task.status in status_dist:
            status_dist[task.status] += 1
            
    # Delay analysis
    delayed_count = 0
    on_track_count = 0
    for p in projects:
        if p.baseline_end_date and p.scheduled_end_date:
            if p.scheduled_end_date > p.baseline_end_date:
                delayed_count += 1
            else:
                on_track_count += 1
        else:
            on_track_count += 1 # Or just count those with baseline separately
            
    # Project data for table/charts
    project_metrics = []
    project_names = []
    project_percentages = []
    for p in projects:
        project_metrics.append({
            "id": p.id,
            "name": p.name,
            "percentage": p.percentage or 0,
            "value": p.value or 0,
            "delayed": (p.baseline_end_date and p.scheduled_end_date and p.scheduled_end_date > p.baseline_end_date),
            "baseline_end": p.baseline_end_date.strftime("%d/%m/%Y") if p.baseline_end_date else "N/A",
            "scheduled_end": p.scheduled_end_date.strftime("%d/%m/%Y") if p.scheduled_end_date else "N/A"
        })
        project_names.append(p.name)
        project_percentages.append(p.percentage or 0)

    from ..main import templates
    return templates.TemplateResponse("reports.html", {
        "request": request, 
        "user": user,
        "total_projects": total_projects,
        "total_value": total_value,
        "avg_completion": avg_completion,
        "status_dist": status_dist,
        "delayed_count": delayed_count,
        "on_track_count": on_track_count,
        "project_metrics": project_metrics,
        "project_names": project_names,
        "project_percentages": project_percentages
    })

@router.get("/new", response_class=HTMLResponse)
async def new_project_view(request: Request, db: Session = Depends(database.get_db)):
    user = get_current_user_required(request, db)
    from ..main import templates
    return templates.TemplateResponse("project_new.html", {"request": request, "user": user})

@router.post("/new")
async def create_project(
    request: Request, 
    name: str = Form(...), 
    scope: str = Form(...),
    out_of_scope: str = Form(""),
    justification: str = Form(""),
    objectives: str = Form(""),
    requirements: str = Form(""),
    assumptions: str = Form(""),
    restrictions: str = Form(""),
    risks: str = Form(""),
    start_date: str = Form(""),
    end_date: str = Form(""),
    value: float = Form(0.0),
    db: Session = Depends(database.get_db)
):
    user = get_current_user_required(request, db)
    sd = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    ed = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
    
    project = models.Project(
        name=name, scope=scope, 
        out_of_scope=out_of_scope, justification=justification, objectives=objectives,
        requirements=requirements, assumptions=assumptions, restrictions=restrictions, risks=risks,
        start_date=sd, end_date=ed, value=value,
        tap_generated=False, owner_id=user.id
    )
    db.add(project)
    db.commit()
    
    return RedirectResponse(url="/projects", status_code=302)

@router.get("/{project_id}", response_class=HTMLResponse)
async def project_detail(request: Request, project_id: int, db: Session = Depends(database.get_db)):
    user = get_current_user_required(request, db)
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
        
    tasks = db.query(models.Task).filter(models.Task.project_id == project_id).order_by(models.Task.start_date.asc()).all()
    
    from ..main import templates
    return templates.TemplateResponse("project_detail.html", {"request": request, "user": user, "project": project, "tasks": tasks})

@router.get("/{project_id}/tap", response_class=HTMLResponse)
async def project_tap_view(request: Request, project_id: int, db: Session = Depends(database.get_db)):
    user = get_current_user_required(request, db)
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
        
    from ..main import templates
    return templates.TemplateResponse("project_tap.html", {"request": request, "user": user, "project": project})

def update_project_metrics(project_id: int, db: Session):
    min_date = db.query(func.min(models.Task.start_date)).filter(models.Task.project_id == project_id).scalar()
    max_date = db.query(func.max(models.Task.end_date)).filter(models.Task.project_id == project_id).scalar()
    avg_pct = db.query(func.avg(models.Task.percentage)).filter(models.Task.project_id == project_id).scalar()
    
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if project:
        project.scheduled_start_date = min_date
        project.scheduled_end_date = max_date
        project.percentage = avg_pct if avg_pct else 0.0
        db.commit()

@router.post("/{project_id}/tasks")
async def add_task(
    request: Request,
    project_id: int,
    name: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    db: Session = Depends(database.get_db)
):
    user = get_current_user_required(request, db)
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404)
        
    sd = datetime.strptime(start_date, "%Y-%m-%d")
    ed = datetime.strptime(end_date, "%Y-%m-%d")
    
    task = models.Task(name=name, start_date=sd, end_date=ed, project_id=project_id)
    db.add(task)
    db.commit()
    
    update_project_metrics(project_id, db)
    return RedirectResponse(url=f"/projects/{project_id}", status_code=302)

@router.post("/{project_id}/tasks/{task_id}/delete")
async def delete_task(request: Request, project_id: int, task_id: int, db: Session = Depends(database.get_db)):
    user = get_current_user_required(request, db)
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404)
        
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.project_id == project_id).first()
    if task:
        db.delete(task)
        db.commit()
        update_project_metrics(project_id, db)
        
    return RedirectResponse(url=f"/projects/{project_id}", status_code=302)

@router.get("/{project_id}/tasks/{task_id}/edit", response_class=HTMLResponse)
async def edit_task_view(request: Request, project_id: int, task_id: int, db: Session = Depends(database.get_db)):
    user = get_current_user_required(request, db)
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404)
        
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404)
        
    from ..main import templates
    return templates.TemplateResponse("task_edit.html", {"request": request, "user": user, "project": project, "task": task})

@router.post("/{project_id}/tasks/{task_id}/edit")
async def edit_task(
    request: Request, project_id: int, task_id: int,
    name: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    actual_start_date: str = Form(""),
    actual_end_date: str = Form(""),
    status: str = Form("A Fazer"),
    percentage: float = Form(0.0),
    db: Session = Depends(database.get_db)
):
    user = get_current_user_required(request, db)
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404)
        
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.project_id == project_id).first()
    if task:
        task.name = name
        task.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        task.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        task.actual_start_date = datetime.strptime(actual_start_date, "%Y-%m-%d") if actual_start_date else None
        task.actual_end_date = datetime.strptime(actual_end_date, "%Y-%m-%d") if actual_end_date else None
        task.status = status
        task.percentage = percentage
        db.commit()
        update_project_metrics(project_id, db)
        
    return RedirectResponse(url=f"/projects/{project_id}", status_code=302)

@router.post("/{project_id}/baseline/save")
async def save_baseline(request: Request, project_id: int, db: Session = Depends(database.get_db)):
    user = get_current_user_required(request, db)
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404)
        
    project.baseline_start_date = project.scheduled_start_date
    project.baseline_end_date = project.scheduled_end_date
    db.commit()
    
    return RedirectResponse(url=f"/projects/{project_id}", status_code=302)

@router.post("/{project_id}/baseline/delete")
async def delete_baseline(request: Request, project_id: int, db: Session = Depends(database.get_db)):
    user = get_current_user_required(request, db)
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404)
        
    project.baseline_start_date = None
    project.baseline_end_date = None
    db.commit()
    
    return RedirectResponse(url=f"/projects/{project_id}", status_code=302)

@router.get("/{project_id}/agent", response_class=HTMLResponse)
async def project_agent_view(request: Request, project_id: int, db: Session = Depends(database.get_db)):
    user = get_current_user_required(request, db)
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404)
        
    messages = db.query(models.ChatMessage).filter(models.ChatMessage.project_id == project_id).order_by(models.ChatMessage.created_at.asc()).all()
    
    from ..main import templates
    return templates.TemplateResponse("project_agent.html", {"request": request, "user": user, "project": project, "messages": messages})

@router.post("/{project_id}/agent/message")
async def project_agent_message(
    request: Request, project_id: int, 
    message: str = Form(...), 
    db: Session = Depends(database.get_db)
):
    user = get_current_user_required(request, db)
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404)
        
    # Save user message
    user_msg = models.ChatMessage(role="user", content=message, owner_id=user.id, project_id=project_id)
    db.add(user_msg)
    db.commit()
    
    # Get AI Analysis
    tasks = db.query(models.Task).filter(models.Task.project_id == project_id).all()
    ai_response = await project_agent.analyze_project(project, tasks, message)
    
    # Save AI message
    ai_msg = models.ChatMessage(role="ai", content=ai_response, owner_id=user.id, project_id=project_id)
    db.add(ai_msg)
    db.commit()
    
    return RedirectResponse(url=f"/projects/{project_id}/agent", status_code=302)



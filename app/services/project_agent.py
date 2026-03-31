from sqlalchemy.orm import Session
from .. import models
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime, date
import os


def _format_tasks(tasks: list) -> str:
    """Convert task objects to a readable markdown table for the LLM."""
    if not tasks:
        return "Nenhuma tarefa cadastrada no projeto."

    today = datetime.utcnow().date()
    lines = []
    for t in tasks:
        sch_start = t.start_date.strftime("%d/%m/%Y") if t.start_date else "—"
        sch_end = t.end_date.strftime("%d/%m/%Y") if t.end_date else "—"
        act_start = t.actual_start_date.strftime("%d/%m/%Y") if t.actual_start_date else "—"
        act_end = t.actual_end_date.strftime("%d/%m/%Y") if t.actual_end_date else "—"

        # Calculate delay flag
        delay = ""
        if t.status != "Concluído":
            if t.end_date and t.end_date.date() < today:
                delay = " ⚠️ ATRASADA"

        lines.append(
            f"- **{t.name}** | Status: {t.status}{delay} | Avanço: {t.percentage:.0f}% "
            f"| Previsto: {sch_start}→{sch_end} | Real: {act_start}→{act_end}"
        )

    return "\n".join(lines)


def _format_project(project: models.Project, tasks: list) -> str:
    """Build a full structured context string about the project."""
    today = datetime.utcnow().date()

    sch_start = project.scheduled_start_date.strftime("%d/%m/%Y") if project.scheduled_start_date else "N/A"
    sch_end = project.scheduled_end_date.strftime("%d/%m/%Y") if project.scheduled_end_date else "N/A"
    bs_start = project.baseline_start_date.strftime("%d/%m/%Y") if project.baseline_start_date else "Sem baseline"
    bs_end = project.baseline_end_date.strftime("%d/%m/%Y") if project.baseline_end_date else "Sem baseline"

    total = len(tasks)
    done = sum(1 for t in tasks if t.status == "Concluído")
    in_progress = sum(1 for t in tasks if t.status == "Em Andamento")
    overdue = sum(1 for t in tasks if t.status != "Concluído" and t.end_date and t.end_date.date() < today)

    return f"""
PROJETO: {project.name}
Escopo: {project.scope or 'Não informado'}
Progresso geral: {project.percentage:.1f}%
Datas previstas: {sch_start} → {sch_end}
Baseline: {bs_start} → {bs_end}
Data de referência: {today.strftime("%d/%m/%Y")}

RESUMO DAS TAREFAS:
- Total: {total} | Concluídas: {done} | Em andamento: {in_progress} | Atrasadas: {overdue}

DETALHAMENTO DAS TAREFAS:
{_format_tasks(tasks)}
""".strip()


async def analyze_project(project: models.Project, tasks: list, user_question: str) -> str:
    """
    Main entry point: given a project + tasks + user question,
    return an AI analysis in Portuguese.
    """
    project_context = _format_project(project, tasks)

    system_prompt = """Você é um Agente de Análise de Projetos experiente.
Você recebe dados estruturados sobre um projeto e suas tarefas e responde perguntas do gestor.

Suas responsabilidades:
- Identificar tarefas atrasadas, em risco ou concluídas
- Calcular desvios entre datas previstas e reais
- Identificar gargalos e pontos críticos
- Sugerir ações corretivas quando pertinente
- Apresentar um status executivo claro e objetivo

Regras de formatação:
- Use **negrito** para destacar itens críticos
- Use emojis com moderação para facilitar leitura (✅ concluído, ⚠️ atenção, 🔴 crítico, 📈 progresso)
- Formate em Markdown limpo
- Seja direto e objetivo — o gestor precisa de informação rápida e confiável"""

    user_prompt = f"""Dados do projeto:
---
{project_context}
---

Pergunta do gestor: {user_question}"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    llm = ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "phi3:mini"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.2
    )

    try:
        chain = prompt | llm
        result = await chain.ainvoke({"input": user_prompt})
        return result.content
    except Exception as e:
        return f"⚠️ Erro ao contatar o agente de IA local (Ollama): {str(e)}"

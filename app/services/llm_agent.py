from sqlalchemy.orm import Session
from .. import models
from .document_processor import get_vector_store
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from datetime import datetime
import os
from dotenv import load_dotenv
import shutil

load_dotenv()

class CreateProjectSchema(BaseModel):
    name: str = Field(description="Project name to be created.")
    scope: str = Field(description="Detailed scope/TAP of the project.")
    start_date: str = Field(description="Start date format YYYY-MM-DD")
    end_date: str = Field(description="End date format YYYY-MM-DD")
    value: float = Field(description="Estimated value in float format (e.g. 5000.0)")

def generate_db_tool(db: Session, user_id: int):
    def create_project(name: str, scope: str, start_date: str, end_date: str, value: float) -> str:
        """Create a new Project/TAP in the system based on user instructions and documents."""
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d")
            ed = datetime.strptime(end_date, "%Y-%m-%d")
            
            p = models.Project(
                name=name,
                scope=scope,
                start_date=sd,
                end_date=ed,
                value=value,
                tap_generated=True,
                owner_id=user_id
            )
            db.add(p)
            db.commit()
            return f"Successfully created project '{name}' in the database."
        except Exception as e:
            return f"Failed to create project due to formatting error: {str(e)}"
            
    return StructuredTool.from_function(
        func=create_project,
        name="create_project",
        description="Creates a new project in the system given the necessary parameters.",
        args_schema=CreateProjectSchema
    )

async def get_response(message: str, user_id: int, db: Session) -> str:
    try:
        # Retrieve RAG context if applicable
        vectorstore = get_vector_store()
        retriever = vectorstore.as_retriever(
            search_kwargs={'filter': {'user_id': str(user_id)}, 'k': 4}
        )
        
        # Get relevant docs
        docs = retriever.invoke(message)
        context_str = "\n\n".join([d.page_content for d in docs])
    except Exception as e:
        context_str = "No documents found or Vector Store not initialized."
    
    system_prompt = f"""Você é um assistente de GP (Gerente de Projetos).
Sua missão é ajudar o usuário respondendo dúvidas e criando o TAP (Termo de Abertura de Projeto).
Contexto relevante extraído dos documentos enviados pelo usuário:
---
{context_str}
---
Se o usuário pedir para gerar um TAP, use seu conhecimento para estruturar o escopo. 
Se ele pedir para CRIAR e SALVAR o projeto, use a ferramenta 'create_project' para realizar a persistência no banco de dados. Informe o usuário quando realizar a operação. Formate suas respostas em Markdown limpo para a web (use ** para negrito, não use HTML bruto)."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    llm = ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "phi3:mini"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0
    )
    tools = [generate_db_tool(db, user_id)]
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    try:
        result = await agent_executor.ainvoke({"input": message})
        return result["output"]
    except Exception as e:
        return f"Erro ao contatar IA local (Ollama): {str(e)}"

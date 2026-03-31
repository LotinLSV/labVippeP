# VIPPE - Portal de Gestão de Projetos com IA

VIPPE é uma plataforma web robusta desenvolvida em Python para gestão de projetos, integrando inteligência artificial para análise de documentos e automação de processos. O sistema permite o acompanhamento detalhado de cronogramas, métricas de progresso e gestão de instâncias multi-tenant do n8n.

## ✨ Funcionalidades Principais

### 🚀 Gestão de Projetos e TAP
- **Criação de Projetos**: Suporte para criação manual ou gerada por IA.
- **Termo de Abertura de Projeto (TAP) Expandido**: Documentação completa incluindo Escopo, Fora do Escopo, Justificativa, Objetivos, Requisitos, Premissas, Restrições e Riscos.
- **Visualização Otimizada**: Página dedicada para detalhes do TAP, garantindo legibilidade de documentos extensos.
- **Linha de Base (Baseline)**: Capacidade de congelar cronogramas agendados para comparação futura e controle de desvios.

### 📅 Cronograma e Tarefas
- **Sistema CRUD de Tarefas**: Gestão completa de atividades com datas previstas e realizadas.
- **Métricas Automatizadas**: Cálculo em tempo real do progresso do projeto e datas agendadas com base nas tarefas.
- **Status Tracking**: Acompanhamento visual de tarefas (A Fazer, Em Andamento, Concluído).

### 🤖 Inteligência Artificial e Chat
- **RAG (Retrieval-Augmented Generation)**: Chatbot habilitado para responder perguntas baseadas em documentos enviados (PDF/Texto).
- **Agente de Análise de Processos**: Novo agente vinculado a projetos que lê cronogramas, identifica atrasos/gargalos e fornece insights operacionais via chat interativo.
- **Renderização de Markdown**: Interface de IA aprimorada com suporte a listas, negritos e tabelas formatadas.
- **Processamento de Documentos**: Extração e processamento de conhecimento para análise contextual.

### 🔐 Administração e Segurança
- **Gestão de Serviços (Laboratório)**: Controle administrativo de 8 instâncias por usuário (n8n, Typebot, Minion, Lovable, Open Claw, Quickcharts, DiFy, Chatwoot).
- **Dashboard Dinâmico**: Ocultação automática de ferramentas não configuradas, mantendo o portal limpo e personalizado.
- **Controle de Visibilidade**: Opção administrativa para habilitar ou ocultar a seção de Projetos de forma granular por usuário.
- **Autenticação Segura**: Sistema de login e registro com senhas criptografadas (BCrypt).

## 🛠️ Tecnologias Utilizadas

- **Core**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **Banco de Dados**: SQLAlchemy com suporte a SQLite e PostgreSQL.
- **Frontend**: Jinja2 Templates & Tailwind CSS.
- **IA/LLM**: LangChain, OpenAI API, ChromaDB (Vector Store).
- **Processamento**: PyPDF, python-multipart.
- **Servidor**: Uvicorn.

## 📂 Estrutura do Projeto

```text
VIPPE/
├── app/
│   ├── routes/          # Rotas da API (Auth, Chat, Projetos, Admin)
│   ├── services/        # Lógica de IA e Processamento de Documentos
│   ├── templates/       # Interface (HTML/Jinja2)
│   ├── models.py        # Definições de Tabelas (SQLAlchemy)
│   ├── database.py      # Configuração de Conexão com Banco
│   └── main.py          # Ponto de entrada da aplicação
├── data/                # Banco de dados local (SQLite)
├── .env                 # Variáveis de ambiente
├── requirements.txt     # Dependências do projeto
└── migrate.py           # Script de migração de banco de dados
```

## 🚀 Como Executar

1. **Configurar Ambiente**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .\.venv\Scripts\activate   # Windows
   ```

2. **Instalar Dependências**:
   ```bash
   pip install -r requirements.txt
   ```

### Opção 2: Produção com Docker (Recomendado para VPS)

1. **Configurar Ambiente**:
   Crie um arquivo `.env` com `DATABASE_PASSWORD` e `OPENAI_API_KEY`.

2. **Subir com Docker Compose**:
   ```bash
   docker compose up -d --build
   ```
   *Isso iniciará automaticamente a aplicação, o banco de dados PostgreSQL e o servidor Nginx.*

3. **Configurar SSL**:
   Siga as instruções no arquivo `nginx.conf` para configurar o Certbot/Let's Encrypt.

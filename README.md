# ArchAnalyzer

Sistema de análise automática de diagramas de arquitetura de software utilizando Inteligência Artificial com agentes especializados, RAG e observabilidade completa.

---

## 📋 Descrição do Problema

Empresas que operam sistemas distribuídos possuem dezenas de diagramas de arquitetura analisados manualmente, o que demanda tempo, depende de especialistas e não escala. O ArchAnalyzer automatiza esse processo, permitindo o envio de um diagrama e recebendo em troca um relatório técnico estruturado com componentes identificados, riscos arquiteturais e recomendações.

---

## 🏗️ Arquitetura Proposta

O sistema é baseado em **microsserviços**, onde cada serviço possui responsabilidade única e comunicação via REST e mensageria assíncrona (RabbitMQ).

### Serviços

| Serviço | Porta | Responsabilidade |
|---|---|---|
| api-gateway | 8000 | Porta de entrada, roteia requisições |
| upload-service | 8001 | Recebe arquivos, cria jobs, publica na fila |
| processing-service | — | Consome a fila, orquestra agentes de IA, persiste resultado |
| report-service | 8003 | Serve o relatório final |
| frontend | 3000 | Interface web de demonstração |
| grafana | 3001 | Dashboards de observabilidade |
| prometheus | 9090 | Coleta de métricas |
| loki | 3100 | Agregação de logs estruturados |
| rabbitmq | 5672 | Mensageria assíncrona |
| postgres | 5432 | Banco de dados relacional |

### Tecnologias

- **Python + FastAPI** — APIs REST
- **RabbitMQ** — Mensageria assíncrona
- **PostgreSQL** — Banco de dados
- **OpenAI GPT-4o** — Análise do diagrama via visão computacional
- **LangChain** — Orquestração de agentes de IA
- **ChromaDB** — Banco vetorial para RAG
- **Prometheus + Grafana + Loki** — Observabilidade
- **Docker + Docker Compose** — Containerização
- **GitHub Actions** — CI/CD

---

## 🔄 Fluxo da Solução

```
Cliente
  │
  ▼
API Gateway (POST /api/v1/upload)
  │
  ▼
Upload Service → Salva arquivo → Cria Job (status: received) → Publica na fila
  │
  ▼
RabbitMQ (analysis_queue)
  │
  ▼
Processing Service → Orquestrador de Agentes
  ├── Agente Extrator        → Identifica componentes
  ├── Agente de Riscos       → Analisa riscos (RAG + GPT-4o)
  ├── Agente de Recomendações → Gera recomendações (RAG + GPT-4o)
  └── Agente Validador       → Revisa e consolida relatório
  │
  ▼
Report Service (GET /api/v1/report/{job_id})
  │
  ▼
Cliente recebe relatório estruturado + opção de download PDF/JSON
```

---

## 🤖 Pipeline de IA

A IA é acionada pelo **processing-service** ao consumir uma mensagem da fila. O sistema utiliza uma arquitetura de **agentes especializados com orquestrador** e **RAG** para enriquecer as análises com boas práticas arquiteturais.

### Agentes

| Agente | Responsabilidade |
|---|---|
| Orquestrador | Coordena o pipeline e repassa tarefas aos agentes |
| Agente Extrator | Identifica componentes arquiteturais no diagrama |
| Agente de Riscos | Analisa riscos usando RAG com documentos de boas práticas |
| Agente de Recomendações | Gera recomendações baseadas nos componentes e riscos |
| Agente Validador | Revisa, remove duplicatas e consolida o relatório final |

### RAG — Base de Conhecimento

O sistema utiliza documentos de boas práticas arquiteturais (AWS Well-Architected Framework, Twelve-Factor App) indexados no ChromaDB. O vectorstore é construído **uma única vez na inicialização** do serviço e reutilizado em todas as análises.

### Guardrails

- Validação estrutural do JSON retornado pela IA
- Verificação dos campos obrigatórios: `components`, `risks`, `recommendations`
- Resposta de fallback em caso de falha
- Temperature baixa (0.2) para respostas mais determinísticas

### Justificativa da Abordagem

Foi escolhido o uso de **LLM com visão computacional (GPT-4o)** combinado com **agentes especializados e RAG** por ser a abordagem mais eficaz para análise de diagramas. Cada agente tem um papel claro e isolado, o que facilita manutenção, avaliação e evolução individual de cada etapa da análise.

### Limitações do Modelo

- Diagramas muito complexos ou de baixa resolução podem reduzir a precisão
- O modelo pode não identificar tecnologias pouco conhecidas
- Alucinações são mitigadas pelos guardrails, mas não eliminadas completamente
- Custo por requisição à API da OpenAI
- O banco de dados é compartilhado entre upload-service e processing-service — decisão de simplicidade do MVP

---

## 🔒 Segurança

### Requisitos de Segurança Adotados

- **Validação de entrada:** Apenas arquivos PNG, JPG e PDF são aceitos com tamanho máximo de 10MB
- **Variáveis de ambiente:** A chave da OpenAI é armazenada em `.env` e nunca commitada no repositório (protegido pelo `.gitignore`)
- **Comunicação interna:** Os serviços se comunicam dentro da rede interna do Docker, sem exposição desnecessária de portas
- **Guardrails de IA:** A resposta da IA é validada estruturalmente antes de ser persistida, evitando dados corrompidos
- **Logs estruturados:** Todos os serviços emitem logs em JSON com nível, serviço e timestamp, sem expor dados sensíveis
- **Tratamento de falhas:** Qualquer erro atualiza o job para status `error` com registro em log, sem expor detalhes internos ao cliente
- **Sem autenticação de usuário:** Por ser um MVP, não há autenticação implementada. Em produção, recomenda-se adicionar JWT ou OAuth2 no API Gateway

### Principais Riscos e Limitações

| Risco | Mitigação |
|---|---|
| Vazamento da chave OpenAI | Uso de `.env` + `.gitignore` |
| Upload de arquivos maliciosos | Validação de tipo e tamanho |
| Alucinações da IA | Guardrails de formato e fallback |
| Banco compartilhado entre serviços | Documentado como limitação do MVP |
| Ausência de autenticação | Documentado como limitação do MVP |
| SPOF no RabbitMQ | Fora do escopo do MVP |

---

## 🚀 Instruções de Execução

### Pré-requisitos

- Docker instalado ([download](https://www.docker.com/products/docker-desktop))
- Chave de API da OpenAI ([obter aqui](https://platform.openai.com/api-keys))
- Git instalado

### Passos

1. Clone o repositório:
```bash
git clone https://github.com/diegosdomingos/archanalyzer.git
cd archanalyzer
```

2. Crie o arquivo `.env` na raiz com sua chave da OpenAI:
```env
OPENAI_API_KEY=sua_chave_aqui
```

3. Suba todos os serviços com um único comando:
```bash
docker compose up --build
```

> ⚠️ Na primeira execução o build pode demorar 5-10 minutos. Aguarde todos os serviços subirem.

4. Acesse os serviços:

| Serviço | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Grafana | http://localhost:3001 |
| RabbitMQ | http://localhost:15672 |
| Prometheus | http://localhost:9090 |

> Credenciais Grafana: `admin` / `admin`
> Credenciais RabbitMQ: `guest` / `guest`

---

## 🖥️ Como Usar

### Via Frontend (recomendado)

1. Acesse **http://localhost:3000**
2. Arraste ou selecione um diagrama (PNG, JPG ou PDF)
3. Acompanhe o progresso dos agentes em tempo real no log
4. Visualize e baixe o relatório em PDF ou JSON

### Via API

**1. Enviar um diagrama:**
```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@seu_diagrama.png"
```

Resposta:
```json
{
  "job_id": "uuid-do-job",
  "status": "queued",
  "filename": "seu_diagrama.png"
}
```

**2. Consultar o status:**
```bash
curl http://localhost:8000/api/v1/status/{job_id}
```

Resposta:
```json
{
  "job_id": "uuid-do-job",
  "status": "analyzed",
  "agent_status": "Pipeline concluído com sucesso."
}
```

**3. Obter o relatório:**
```bash
curl http://localhost:8000/api/v1/report/{job_id}
```

Resposta:
```json
{
  "job_id": "uuid-do-job",
  "report": {
    "components": ["API Gateway", "PostgreSQL", "RabbitMQ"],
    "risks": ["Ponto único de falha no gateway", "Ausência de cache"],
    "recommendations": ["Adicionar load balancer", "Implementar circuit breaker"]
  }
}
```

---

## 📊 Observabilidade

O sistema conta com stack completa de observabilidade:

- **Grafana** (http://localhost:3001) — Dashboards pré-configurados com:
  - Logs em tempo real de todos os serviços
  - Requisições por segundo por serviço
  - Latência média por endpoint
  - Volume de logs por serviço
  - Total de erros na última hora
- **Prometheus** (http://localhost:9090) — Métricas de todos os serviços FastAPI
- **Loki** — Agregação de logs estruturados em JSON enviados por cada serviço

---

## ✅ Testes

Para rodar os testes de cada serviço individualmente:

```bash
cd api-gateway && pytest tests/ -v
cd upload-service && pytest tests/ -v
cd processing-service && pytest tests/ -v
cd report-service && pytest tests/ -v
```

O CI/CD via GitHub Actions roda os testes automaticamente a cada push na branch `main`.

---

## 📁 Estrutura do Projeto

```
archanalyzer/
├── api-gateway/          # Porta de entrada REST
├── upload-service/       # Upload e orquestração de jobs
├── processing-service/   # Agentes de IA + RAG
│   └── app/
│       ├── core/
│       │   ├── agents.py        # Agentes especializados
│       │   ├── orchestrator.py  # Orquestrador do pipeline
│       │   └── rag.py           # Base de conhecimento RAG
│       └── knowledge/           # PDFs de boas práticas
├── report-service/       # Serviço de relatórios
├── frontend/             # Interface web
├── observability/        # Prometheus, Loki, Grafana
│   └── grafana/
│       └── provisioning/
│           └── dashboards/
│               └── archanalyzer.json  # Dashboard pré-configurado
├── .github/workflows/    # CI/CD GitHub Actions
├── docker-compose.yml
└── .env                  # Não commitado — criar manualmente
```
# ArchAnalyzer

Sistema de análise automática de diagramas de arquitetura de software utilizando Inteligência Artificial.

---

## 📋 Descrição do Problema

Empresas que operam sistemas distribuídos possuem dezenas de diagramas de arquitetura analisados manualmente, o que demanda tempo, depende de especialistas e não escala. O ArchAnalyzer automatiza esse processo, permitindo o envio de um diagrama e recebendo em troca um relatório técnico estruturado com componentes identificados, riscos arquiteturais e recomendações.

---

## 🏗️ Arquitetura Proposta

O sistema é baseado em **microsserviços**, onde cada serviço possui responsabilidade única, banco de dados próprio e comunicação via REST e mensageria assíncrona (RabbitMQ).

### Serviços

| Serviço | Porta | Responsabilidade |
|---|---|---|
| api-gateway | 8000 | Porta de entrada, roteia requisições |
| upload-service | 8001 | Recebe arquivos, cria jobs, publica na fila |
| processing-service | - | Consome a fila, aciona a IA, persiste resultado |
| report-service | 8003 | Serve o relatório final |

### Tecnologias

- **Python + FastAPI** — APIs REST
- **RabbitMQ** — Mensageria assíncrona
- **PostgreSQL** — Banco de dados
- **OpenAI GPT-4o** — Análise do diagrama via visão computacional
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
Upload Service → Salva arquivo → Cria Job (status: received)
  │
  ▼
RabbitMQ (analysis_queue)
  │
  ▼
Processing Service → Analisa com GPT-4o → Persiste relatório → Atualiza Job (status: analyzed)
  │
  ▼
Report Service (GET /api/v1/report/{job_id})
  │
  ▼
Cliente recebe relatório estruturado
```

---

## 🤖 Pipeline de IA

A IA é acionada pelo **processing-service** ao consumir uma mensagem da fila. O fluxo é:

1. O arquivo é lido e convertido para base64
2. A imagem é enviada ao GPT-4o com um prompt estruturado
3. A resposta é validada (guardrails):
   - Verifica se é JSON válido
   - Verifica se contém os campos obrigatórios: `components`, `risks`, `recommendations`
4. Em caso de falha, uma resposta padrão (fallback) é persistida
5. O relatório é salvo no banco e o status do job é atualizado

### Justificativa da Abordagem

Foi escolhido o uso de **LLM com visão computacional (GPT-4o)** por ser a abordagem mais eficaz para análise de diagramas, que são imagens com elementos visuais e textuais combinados. O prompt engineering garante respostas estruturadas e previsíveis.

### Limitações do Modelo

- Diagramas muito complexos ou de baixa resolução podem reduzir a precisão
- O modelo pode não identificar tecnologias pouco conhecidas
- Alucinações são mitigadas pelos guardrails, mas não eliminadas completamente
- Custo por requisição à API da OpenAI

---

## 🔒 Segurança

### Requisitos de Segurança Adotados

- **Validação de entrada:** Apenas arquivos PNG, JPG e PDF são aceitos. O tamanho máximo é de 10MB.
- **Variáveis de ambiente:** A chave da OpenAI é armazenada em `.env` e nunca commitada no repositório.
- **Comunicação interna:** Os serviços se comunicam dentro da rede interna do Docker, sem exposição desnecessária de portas.
- **Guardrails de IA:** A resposta da IA é validada estruturalmente antes de ser persistida, evitando dados corrompidos.
- **Tratamento de falhas:** Qualquer erro no processamento atualiza o job para status `error` e registra logs estruturados, sem expor detalhes internos ao cliente.
- **Sem autenticação de usuário:** Por ser um MVP, não há autenticação implementada. Em produção, recomenda-se adicionar JWT ou OAuth2 no API Gateway.

### Principais Riscos e Limitações

| Risco | Mitigação |
|---|---|
| Vazamento da chave OpenAI | Uso de `.env` + `.gitignore` |
| Upload de arquivos maliciosos | Validação de tipo e tamanho |
| Alucinações da IA | Guardrails de formato e fallback |
| Ausência de autenticação | Documentado como limitação do MVP |
| SPOF no RabbitMQ | Fora do escopo do MVP |

---

## 🚀 Instruções de Execução

### Pré-requisitos

- Docker instalado
- Chave de API da OpenAI

### Passos

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/archanalyzer.git
cd archanalyzer
```

2. Crie o arquivo `.env` na raiz:
```env
OPENAI_API_KEY=sua_chave_aqui
```

3. Suba todos os serviços:
```bash
docker compose up --build
```

4. Acesse a documentação da API:
- API Gateway: http://localhost:8000/docs

---

## 📡 Como Usar

### 1. Enviar um diagrama

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

### 2. Consultar o status

```bash
curl http://localhost:8000/api/v1/status/{job_id}
```

Resposta:
```json
{
  "job_id": "uuid-do-job",
  "status": "analyzed"
}
```

### 3. Obter o relatório

```bash
curl http://localhost:8000/api/v1/report/{job_id}
```

Resposta:
```json
{
  "job_id": "uuid-do-job",
  "report": {
    "components": ["API Gateway", "Serviço de Autenticação", "Banco PostgreSQL"],
    "risks": ["Ponto único de falha no gateway", "Ausência de cache"],
    "recommendations": ["Adicionar load balancer", "Implementar circuit breaker"]
  }
}
```

---

## ✅ Testes

Para rodar os testes de cada serviço individualmente:

```bash
cd api-gateway && pytest tests/ -v
cd upload-service && pytest tests/ -v
cd processing-service && pytest tests/ -v
cd report-service && pytest tests/ -v
```
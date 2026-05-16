import base64
import json
import logging
from openai import OpenAI
from app.core.config import OPENAI_API_KEY
from app.core.rag import query_knowledge

logger = logging.getLogger(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)


def _call_gpt(system: str, user: str, image_b64: str = None, media_type: str = None) -> str:
    content = []
    if image_b64 and media_type:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{media_type};base64,{image_b64}",
                "detail": "high"
            }
        })
    content.append({"type": "text", "text": user})

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": content}
        ],
        max_tokens=1000,
        temperature=0.2
    )
    return response.choices[0].message.content.strip()


def agent_extractor(image_b64: str, media_type: str) -> list:
    logger.info("Agente Extrator: identificando componentes...")
    system = """Você é um especialista em leitura de diagramas de arquitetura de software.
Retorne APENAS um JSON com a chave 'components' contendo uma lista de strings.
Exemplo: {"components": ["API Gateway", "PostgreSQL", "Redis"]}
Não inclua texto fora do JSON."""

    user = """Identifique todos os componentes arquiteturais visíveis neste diagrama.
Retorne SOMENTE o JSON, sem markdown."""

    raw = _call_gpt(system, user, image_b64, media_type)
    clean = raw.replace("```json", "").replace("```", "").strip()
    data = json.loads(clean)
    components = data.get("components", [])
    logger.info(f"Agente Extrator: {len(components)} componentes identificados.")
    return components


def agent_risks(components: list, vectorstore) -> list:
    logger.info("Agente de Riscos: analisando riscos arquiteturais...")
    context = query_knowledge(
        vectorstore,
        f"riscos arquiteturais para: {', '.join(components)}"
    )

    system = """Você é um especialista em segurança e riscos de arquitetura de software.
Retorne APENAS um JSON com a chave 'risks' contendo uma lista de strings descrevendo riscos.
Exemplo: {"risks": ["Ponto único de falha no API Gateway"]}
Não inclua texto fora do JSON."""

    user = f"""Componentes identificados no diagrama:
{json.dumps(components, ensure_ascii=False)}

Contexto de boas práticas (base de conhecimento):
{context}

Com base nos componentes e nas boas práticas acima, liste os principais riscos arquiteturais.
Retorne SOMENTE o JSON, sem markdown."""

    raw = _call_gpt(system, user)
    clean = raw.replace("```json", "").replace("```", "").strip()
    data = json.loads(clean)
    risks = data.get("risks", [])
    logger.info(f"Agente de Riscos: {len(risks)} riscos identificados.")
    return risks


def agent_recommendations(components: list, risks: list, vectorstore) -> list:
    logger.info("Agente de Recomendações: gerando recomendações...")
    context = query_knowledge(
        vectorstore,
        f"recomendações arquiteturais para: {', '.join(components)}"
    )

    system = """Você é um arquiteto de software sênior especializado em boas práticas.
Retorne APENAS um JSON com a chave 'recommendations' contendo uma lista de strings.
Exemplo: {"recommendations": ["Adicionar circuit breaker entre serviços"]}
Não inclua texto fora do JSON."""

    user = f"""Componentes identificados:
{json.dumps(components, ensure_ascii=False)}

Riscos identificados:
{json.dumps(risks, ensure_ascii=False)}

Contexto de boas práticas (base de conhecimento):
{context}

Com base nos componentes, riscos e boas práticas, liste recomendações técnicas concretas.
Retorne SOMENTE o JSON, sem markdown."""

    raw = _call_gpt(system, user)
    clean = raw.replace("```json", "").replace("```", "").strip()
    data = json.loads(clean)
    recommendations = data.get("recommendations", [])
    logger.info(f"Agente de Recomendações: {len(recommendations)} recomendações geradas.")
    return recommendations


def agent_validator(components: list, risks: list, recommendations: list) -> dict:
    logger.info("Agente Validador: validando relatório final...")

    system = """Você é um revisor técnico de relatórios de arquitetura de software.
Retorne APENAS um JSON com as chaves 'components', 'risks' e 'recommendations', cada uma contendo uma lista de strings revisada e melhorada.
Não inclua texto fora do JSON."""

    user = f"""Revise e melhore o relatório abaixo, removendo duplicatas, corrigindo inconsistências e garantindo clareza técnica:

Componentes: {json.dumps(components, ensure_ascii=False)}
Riscos: {json.dumps(risks, ensure_ascii=False)}
Recomendações: {json.dumps(recommendations, ensure_ascii=False)}

Retorne SOMENTE o JSON revisado, sem markdown."""

    raw = _call_gpt(system, user)
    clean = raw.replace("```json", "").replace("```", "").strip()
    data = json.loads(clean)
    logger.info("Agente Validador: relatório validado com sucesso.")
    return data
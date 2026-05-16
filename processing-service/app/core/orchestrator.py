import base64
import json
import logging
from app.core.agents import agent_extractor, agent_risks, agent_recommendations, agent_validator

logger = logging.getLogger(__name__)


def encode_image(file_path: str) -> tuple:
    with open(file_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    if file_path.lower().endswith(".png"):
        media_type = "image/png"
    elif file_path.lower().endswith(".pdf"):
        media_type = "application/pdf"
    else:
        media_type = "image/jpeg"
    return data, media_type


def _fallback_response(reason: str) -> dict:
    return {
        "components": ["Não foi possível identificar os componentes."],
        "risks": ["Análise não concluída devido a erro no processamento."],
        "recommendations": ["Verifique o diagrama enviado e tente novamente."],
        "raw": f"ERRO: {reason}"
    }


def run_pipeline(file_path: str, vectorstore=None, update_status=None) -> dict:
    logger.info("Orquestrador: iniciando pipeline de agentes...")

    def update(msg):
        if update_status:
            update_status(msg)
        logger.info(f"Orquestrador: {msg}")

    try:
        image_b64, media_type = encode_image(file_path)

        update("Agente Extrator: identificando componentes...")
        components = agent_extractor(image_b64, media_type)

        update("Agente de Riscos: analisando riscos arquiteturais...")
        risks = agent_risks(components, vectorstore)

        update("Agente de Recomendações: gerando recomendações...")
        recommendations = agent_recommendations(components, risks, vectorstore)

        update("Agente Validador: revisando relatório final...")
        final = agent_validator(components, risks, recommendations)

        update("Pipeline concluído com sucesso.")
        return {
            "components": final.get("components", components),
            "risks": final.get("risks", risks),
            "recommendations": final.get("recommendations", recommendations),
            "raw": json.dumps(final, ensure_ascii=False)
        }

    except Exception as e:
        logger.error(f"Orquestrador: erro no pipeline — {e}")
        return _fallback_response(str(e))
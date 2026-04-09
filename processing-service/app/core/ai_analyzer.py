import base64
import logging
import json
from openai import OpenAI
from app.core.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """Você é um arquiteto de software sênior especializado em análise de diagramas de arquitetura.
Sua tarefa é analisar diagramas de arquitetura de software e retornar APENAS um JSON válido, sem texto adicional.
Seja objetivo, técnico e preciso. Nunca invente componentes que não estejam visíveis no diagrama."""

USER_PROMPT = """Analise este diagrama de arquitetura de software e retorne APENAS o seguinte JSON, sem markdown, sem explicações:

{
  "components": ["lista dos componentes identificados no diagrama"],
  "risks": ["lista de possíveis riscos arquiteturais identificados"],
  "recommendations": ["lista de recomendações técnicas baseadas no diagrama"]
}

Regras:
- Retorne SOMENTE o JSON, nada mais.
- Cada lista deve ter entre 3 e 8 itens.
- Baseie-se APENAS no que está visível no diagrama.
- Se não conseguir identificar o diagrama, retorne listas com o item "Não foi possível identificar o componente".
"""


def encode_image(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def analyze_diagram(file_path: str) -> dict:
    logger.info(f"Iniciando análise do arquivo: {file_path}")

    try:
        is_pdf = file_path.lower().endswith(".pdf")

        if is_pdf:
            # Para PDF, converte primeira página em imagem
            from PIL import Image
            import io
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(file_path)
                page = doc[0]
                pix = page.get_pixmap()
                img_bytes = pix.tobytes("png")
                base64_image = base64.b64encode(img_bytes).decode("utf-8")
                media_type = "image/png"
            except ImportError:
                logger.warning("PyMuPDF não disponível, tentando enviar PDF direto.")
                base64_image = encode_image(file_path)
                media_type = "application/pdf"
        else:
            base64_image = encode_image(file_path)
            media_type = "image/png" if file_path.lower().endswith(".png") else "image/jpeg"

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{base64_image}",
                                "detail": "high"
                            }
                        },
                        {"type": "text", "text": USER_PROMPT}
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0.2
        )

        raw = response.choices[0].message.content.strip()
        logger.info(f"Resposta bruta da IA: {raw[:200]}")

        # Guardrail: garante que a resposta é um JSON válido
        clean = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean)

        # Guardrail: valida estrutura esperada
        for key in ["components", "risks", "recommendations"]:
            if key not in result or not isinstance(result[key], list):
                raise ValueError(f"Campo '{key}' ausente ou inválido na resposta da IA.")

        logger.info("Análise concluída com sucesso.")
        return {"components": result["components"], "risks": result["risks"], "recommendations": result["recommendations"], "raw": raw}

    except json.JSONDecodeError as e:
        logger.error(f"Resposta da IA não é JSON válido: {e}")
        return _fallback_response("Resposta da IA em formato inválido.")
    except ValueError as e:
        logger.error(f"Estrutura inválida na resposta da IA: {e}")
        return _fallback_response(str(e))
    except Exception as e:
        logger.error(f"Erro inesperado na análise: {e}")
        return _fallback_response(str(e))


def _fallback_response(reason: str) -> dict:
    return {
        "components": ["Não foi possível identificar os componentes."],
        "risks": ["Análise não concluída devido a erro no processamento."],
        "recommendations": ["Verifique o diagrama enviado e tente novamente."],
        "raw": f"ERRO: {reason}"
    }
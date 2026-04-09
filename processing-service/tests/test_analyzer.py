from unittest.mock import patch, MagicMock
from app.core.ai_analyzer import analyze_diagram, _fallback_response


def test_fallback_response():
    result = _fallback_response("Erro de teste")
    assert "components" in result
    assert "risks" in result
    assert "recommendations" in result


@patch("app.core.ai_analyzer.client")
@patch("builtins.open", create=True)
def test_analyze_diagram_success(mock_open, mock_openai):
    mock_open.return_value.__enter__.return_value.read.return_value = b"fake image"

    mock_choice = MagicMock()
    mock_choice.message.content = '{"components": ["API Gateway"], "risks": ["SPOF"], "recommendations": ["Adicionar cache"]}'
    mock_openai.chat.completions.create.return_value.choices = [mock_choice]

    result = analyze_diagram("fake_path.png")
    assert "components" in result
    assert "risks" in result
    assert "recommendations" in result
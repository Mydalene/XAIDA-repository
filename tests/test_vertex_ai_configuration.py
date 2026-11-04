from types import SimpleNamespace

import pytest
from google.genai import types

from core import vertex_ai_client


def test_missing_vertex_ai_settings_have_actionable_error(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_LOCATION", raising=False)

    with pytest.raises(RuntimeError) as error:
        vertex_ai_client.create_client()

    assert "GOOGLE_CLOUD_PROJECT" in str(error.value)
    assert "GOOGLE_CLOUD_LOCATION" in str(error.value)


def test_invalid_google_cloud_project_id_is_rejected(monkeypatch):
    monkeypatch.setenv(
        "GOOGLE_CLOUD_PROJECT",
        "project-82d4ae4c-6f99-47cd-bb3x",
    )
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-central1")

    with pytest.raises(RuntimeError, match="actual Google Cloud project ID"):
        vertex_ai_client.create_client()


def test_current_gcp_project_id_meets_google_length_and_format_rules():
    vertex_ai_client.validate_project_id(
        "project-82d4ae4c-6f99-47cd-bb3"
    )


def test_vertex_ai_requires_explicit_data_transfer_approval(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    monkeypatch.delenv("XAIDA_VERTEX_AI_APPROVED", raising=False)

    with pytest.raises(RuntimeError, match="data transfer is disabled"):
        vertex_ai_client.create_client()


def test_missing_vertex_ai_sdk_has_environment_install_instructions(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    monkeypatch.setenv("XAIDA_VERTEX_AI_APPROVED", "true")

    def missing_sdk(_):
        raise ImportError("SDK missing")

    monkeypatch.setattr(
        vertex_ai_client,
        "import_module",
        missing_sdk,
    )

    with pytest.raises(RuntimeError, match="pip install -r requirements.txt"):
        vertex_ai_client.create_client()


def test_vertex_ai_client_uses_project_location_and_model(monkeypatch):
    settings = {}
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    monkeypatch.setenv("XAIDA_VERTEX_AI_APPROVED", "true")
    monkeypatch.setenv("XAIDA_VERTEX_AI_MODEL", "gemini-test-model")
    monkeypatch.setattr(
        vertex_ai_client,
        "_load_genai_sdk",
        lambda: (
            SimpleNamespace(
                Client=lambda **kwargs: settings.update(kwargs) or object()
            ),
            types,
        ),
    )

    client = vertex_ai_client.create_client()

    assert settings == {
        "vertexai": True,
        "project": "test-project",
        "location": "us-central1",
    }
    assert client.model == "gemini-test-model"


def test_vertex_ai_uses_flash_lite_by_default(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    monkeypatch.setenv("XAIDA_VERTEX_AI_APPROVED", "true")
    monkeypatch.delenv("XAIDA_VERTEX_AI_MODEL", raising=False)
    monkeypatch.setattr(
        vertex_ai_client,
        "_load_genai_sdk",
        lambda: (SimpleNamespace(Client=lambda **kwargs: object()), types),
    )

    assert (
        vertex_ai_client.create_client().model
        == "gemini-3.5-flash-lite"
    )


def test_vertex_ai_adapter_maps_system_and_chat_messages(monkeypatch):
    request = {}
    sdk_client = SimpleNamespace(
        models=SimpleNamespace(
            generate_content=lambda **kwargs: (
                request.update(kwargs)
                or SimpleNamespace(text="Grounded response")
            )
        )
    )
    client = vertex_ai_client.VertexAIClient(
        sdk_client,
        "gemini-test-model",
    )
    monkeypatch.setattr(
        vertex_ai_client,
        "_load_genai_sdk",
        lambda: (None, types),
    )

    result = client.generate_content(
        [
            {"role": "system", "content": "System policy"},
            {"role": "user", "content": "Question"},
            {"role": "assistant", "content": "Earlier answer"},
        ]
    )

    assert result == "Grounded response"
    assert request["model"] == "gemini-test-model"
    assert request["config"].system_instruction == "System policy"
    assert [
        (content.role, content.parts[0].text)
        for content in request["contents"]
    ] == [
        ("user", "Question"),
        ("model", "Earlier answer"),
    ]


def test_vertex_ai_adapter_rejects_unsupported_roles(monkeypatch):
    client = vertex_ai_client.VertexAIClient(object(), "gemini-test-model")
    monkeypatch.setattr(
        vertex_ai_client,
        "_load_genai_sdk",
        lambda: (None, types),
    )

    with pytest.raises(ValueError, match="Unsupported AI message role"):
        client.generate_content([{"role": "tool", "content": "output"}])


def test_vertex_ai_adapter_merges_consecutive_same_role_messages(monkeypatch):
    request = {}
    sdk_client = SimpleNamespace(
        models=SimpleNamespace(
            generate_content=lambda **kwargs: (
                request.update(kwargs)
                or SimpleNamespace(text="Grounded response")
            )
        )
    )
    client = vertex_ai_client.VertexAIClient(sdk_client, "gemini-test-model")
    monkeypatch.setattr(
        vertex_ai_client,
        "_load_genai_sdk",
        lambda: (None, types),
    )

    client.generate_content(
        [
            {"role": "user", "content": "Evidence context"},
            {"role": "user", "content": "Question"},
        ]
    )

    assert len(request["contents"]) == 1
    assert request["contents"][0].parts[0].text == (
        "Evidence context\n\nQuestion"
    )

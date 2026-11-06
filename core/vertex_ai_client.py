import os
import re
from importlib import import_module

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "gemini-3.1-flash-lite"
UNAVAILABLE_MODELS = {"gemini-1.5-flash"}
PROJECT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$")


def validate_project_id(project_id):
    if not PROJECT_ID_PATTERN.fullmatch(project_id):
        raise RuntimeError(
            "GOOGLE_CLOUD_PROJECT must be the actual Google Cloud project ID "
            "(6-30 lowercase letters, digits, or hyphens; start with a "
            "letter and end with a letter or digit). Check the Project ID in "
            "Google Cloud Console."
        )


def _load_genai_sdk():
    try:
        genai = import_module("google.genai")
        types = import_module("google.genai.types")
    except ImportError as error:
        raise RuntimeError(
            "The Vertex AI assistant dependency is unavailable. Activate the "
            "Python environment used to run XAIDA and install the project "
            "dependencies with `python -m pip install -r requirements.txt`."
        ) from error
    return genai, types


class VertexAIClient:
    def __init__(self, client, model):
        self.client = client
        self.model = model

    def generate_content(self, messages):
        _, types = _load_genai_sdk()
        system_instructions = []
        conversation = []
        role_mapping = {
            "user": "user",
            "assistant": "model",
        }

        for message in messages:
            role = message.get("role")
            content = message.get("content")
            if not isinstance(content, str):
                raise TypeError("AI message content must be a string.")

            if role == "system":
                system_instructions.append(content)
                continue

            if role not in role_mapping:
                raise ValueError(f"Unsupported AI message role: {role!r}.")

            mapped_role = role_mapping[role]
            if conversation and conversation[-1]["role"] == mapped_role:
                conversation[-1]["content"] += "\n\n" + content
            else:
                conversation.append(
                    {
                        "role": mapped_role,
                        "content": content,
                    }
                )

        if not conversation:
            raise ValueError("At least one user or assistant message is required.")

        contents = [
            types.Content(
                role=message["role"],
                parts=[types.Part.from_text(text=message["content"])],
            )
            for message in conversation
        ]

        config = types.GenerateContentConfig(
            system_instruction="\n\n".join(system_instructions) or None,
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )
        return response.text or ""


def create_client():
    required_settings = (
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_CLOUD_LOCATION",
    )
    missing_settings = [
        setting
        for setting in required_settings
        if not os.getenv(setting, "").strip()
    ]
    if missing_settings:
        missing = ", ".join(missing_settings)
        raise RuntimeError(
            "XAIDA Vertex AI is not configured. Set the required environment "
            f"variables: {missing}."
        )

    project = os.environ["GOOGLE_CLOUD_PROJECT"].strip()
    validate_project_id(project)

    if os.getenv(
        "XAIDA_VERTEX_AI_APPROVED",
        "false",
    ).strip().casefold() != "true":
        raise RuntimeError(
            "XAIDA Vertex AI Assistant data transfer is disabled. Set "
            "XAIDA_VERTEX_AI_APPROVED=true only after the organization "
            "approves the configured Vertex AI project, region, and data "
            "handling controls."
        )

    model = os.getenv("XAIDA_VERTEX_AI_MODEL", DEFAULT_MODEL).strip()
    if not model:
        raise RuntimeError("XAIDA_VERTEX_AI_MODEL must not be empty.")
    if model in UNAVAILABLE_MODELS:
        raise RuntimeError(
            f"XAIDA_VERTEX_AI_MODEL is set to unavailable model {model!r}. "
            f"Update the deployment setting to {DEFAULT_MODEL!r} and deploy "
            "a new revision."
        )

    genai, _ = _load_genai_sdk()
    client = genai.Client(
        vertexai=True,
        project=project,
        location=os.environ["GOOGLE_CLOUD_LOCATION"].strip(),
    )
    return VertexAIClient(client, model)

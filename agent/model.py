"""Choose which AI model the agent uses.

Change MODEL_PROVIDER and MODEL_ID in the .env file. No code changes needed.
"""
import os

from dotenv import load_dotenv

load_dotenv()


def get_model():
    provider = os.getenv("MODEL_PROVIDER", "anthropic")

    if provider == "anthropic":
        from strands.models.anthropic import AnthropicModel

        return AnthropicModel(
            model_id=os.getenv("MODEL_ID", "claude-haiku-5-5"),
            max_tokens=2000,  # cap on output length per call, keeps cost low
        )

    if provider == "openai":
        from strands.models.openai import OpenAIModel

        return OpenAIModel(model_id=os.environ["MODEL_ID"])

    raise ValueError(f"Unknown MODEL_PROVIDER: {provider}")
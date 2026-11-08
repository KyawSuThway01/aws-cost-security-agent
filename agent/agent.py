from strands import Agent

from agent.aws_tools import ALL_TOOLS
from agent.model import get_model
from agent.prompts import SYSTEM_PROMPT


def build_agent(quiet=False):
    """quiet=True hides the live printing so only the final JSON is shown."""
    extra = {"callback_handler": None} if quiet else {}
    return Agent(
        model=get_model(),
        system_prompt=SYSTEM_PROMPT,
        tools=ALL_TOOLS,
        **extra,
    )


if __name__ == "__main__":
    agent = build_agent()
    agent("Scan my AWS account and give me a short summary of any problems.")
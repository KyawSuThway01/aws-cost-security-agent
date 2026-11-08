"""Run the agent and return a validated, structured report."""
from strands.types.exceptions import StructuredOutputException

from agent.agent import build_agent
from agent.schemas import Report

RISK_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

PROMPT = (
    "Scan my AWS account using your tools. Then return the report: "
    "every problem you found, with risk level and a suggested fix."
)


def run_report():
    agent = build_agent(quiet=True)
    try:
        result = agent(PROMPT, structured_output_model=Report)
    except StructuredOutputException as e:
        raise RuntimeError(f"Agent did not return a valid report: {e}") from e

    report = result.structured_output
    # Sort in code, not by trusting the model: highest risk first.
    report.findings.sort(key=lambda f: RISK_ORDER[f.risk_level])
    return report


if __name__ == "__main__":
    print(run_report().model_dump_json(indent=2))
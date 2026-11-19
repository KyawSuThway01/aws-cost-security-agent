import json

from agent.agent import build_agent

PROMPT = "Scan my AWS account and give me a short summary of any problems."


def lambda_handler(event, context):
    agent = build_agent(quiet=True)
    result = agent(PROMPT)
    text = str(result)
    print(text)  # goes to CloudWatch Logs
    return {"statusCode": 200, "body": json.dumps({"report": text})}
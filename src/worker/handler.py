import json
import os
import boto3

# REGION = os.getenv("AWS_REGION", "us-east-2")
REGION = boto3.session.Session().region_name

RESPONSE_Q_URL = os.getenv("RESPONSE_Q_URL", "")

sqs = boto3.client("sqs", region_name=REGION)

def process_request(body: dict) -> dict:
    return {
        "request_id": body.get("request_id"),
        "status": "processed",
        "response": {"original": body, "note": "Processed by worker lambda"}
    }

def lambda_handler(event, context):
    if "Records" not in event:
        return {"status": "no_records"}

    for record in event["Records"]:
        body = json.loads(record["body"])
        result = process_request(body)
        sqs.send_message(QueueUrl=RESPONSE_Q_URL, MessageBody=json.dumps(result))
        print("Processed:", result)
    return {"status": "ok", "processed": len(event["Records"])}

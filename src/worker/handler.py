import json
import os
import boto3

REGION = boto3.session.Session().region_name

REQUEST_Q_URL = os.getenv("REQUEST_Q_URL", "")
RESPONSE_Q_URL = os.getenv("RESPONSE_Q_URL", "")

sqs = boto3.client("sqs", region_name=REGION)

def process_request(body: dict) -> dict:
    """
    Example processing function.
    Customize this logic as per your actual use case.
    """
    return {
        "request_id": body.get("request_id"),
        "status": "processed",
        "response": {"original": body, "note": "Processed by worker lambda"}
    }

def lambda_handler(event, context):
    """
    Lambda triggered by RequestQueue SQS messages.
    Processes each message and sends result to ResponseQueue.
    """
    if "Records" not in event:
        return {"status": "no_records"}

    processed_count = 0
    for record in event["Records"]:
        try:
            body = json.loads(record["body"])
            result = process_request(body)
            sqs.send_message(
                QueueUrl=RESPONSE_Q_URL,
                MessageBody=json.dumps(result)
            )
            processed_count += 1
            print("Processed:", result)
        except Exception as e:
            print("Error processing record:", e)
            # Let SQS retry or send to DLQ automatically

    return {"status": "ok", "processed": processed_count}

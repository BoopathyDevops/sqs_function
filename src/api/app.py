import json
import uuid
import os
import boto3
from fastapi import FastAPI, HTTPException
from mangum import Mangum
from pydantic import BaseModel

REGION = os.getenv("AWS_REGION", "us-east-2")
REQUEST_Q_URL = os.getenv("REQUEST_Q_URL", "")
RESPONSE_Q_URL = os.getenv("RESPONSE_Q_URL", "")

sqs = boto3.client("sqs", region_name=REGION)

app = FastAPI(
    title="Houdini API with SQS (Lambda)",
    description="API Lambda for sending requests to request-queue and checking responses.",
    version="1.0.0"
)

class SendPayload(BaseModel):
    message: str

@app.post("/send")
def send_request(payload: SendPayload):
    request_id = str(uuid.uuid4())
    body = {"message": payload.message, "request_id": request_id}
    try:
        sqs.send_message(QueueUrl=REQUEST_Q_URL, MessageBody=json.dumps(body))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {e}")
    return {"message": "Request sent", "request_id": request_id}

@app.get("/response/{request_id}")
def get_response(request_id: str):
    try:
        messages = sqs.receive_message(
            QueueUrl=RESPONSE_Q_URL,
            MaxNumberOfMessages=5,
            WaitTimeSeconds=2
        )
        if "Messages" not in messages:
            raise HTTPException(status_code=404, detail="Response not ready")

        for msg in messages["Messages"]:
            body = json.loads(msg["Body"])
            if body.get("request_id") == request_id:
                sqs.delete_message(
                    QueueUrl=RESPONSE_Q_URL,
                    ReceiptHandle=msg["ReceiptHandle"]
                )
                return {"response": body}
        raise HTTPException(status_code=404, detail="Response not found yet")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def health_check():
    return {"status": "houdini process"}

handler = Mangum(app)

import json
import hmac
import hashlib
import urllib.request
import urllib.error
import os
import logging
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)


def build_body():
    timestamp = os.environ.get("SUBMISSION_TIMESTAMP", "").strip()
    if not timestamp:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    payload = {
        "timestamp": timestamp,
        "name": os.environ["SUBMISSION_NAME"],
        "email": os.environ["SUBMISSION_EMAIL"],
        "resume_link": os.environ["SUBMISSION_RESUME_LINK"],
        "repository_link": os.environ["SUBMISSION_REPOSITORY_LINK"],
        "action_run_link": os.environ["SUBMISSION_ACTION_RUN_LINK"]
    }
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True
    ).encode("utf-8")


def create_signature(secret, body):
    digest = hmac.new(
        secret.encode("utf-8"),
        body,
        hashlib.sha256
    ).hexdigest()
    return f"sha256={digest}"


def execute_request(url, secret, body):
    signature = create_signature(secret, body)
    logging.info("Generated signature: %s", signature)

    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Signature-256": signature
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))

            logging.info("HTTP Status: %s", response.status)

            if response.status == 200 and result.get("success"):
                logging.info("SUCCESS!")
                logging.info("Receipt: %s", result["receipt"])
            else:
                logging.error("Submission failed: %s", result)

    except urllib.error.HTTPError as e:
        logging.error("HTTP Error: %s", e.code)
        logging.error("%s", e.read().decode("utf-8"))
        raise


url = os.environ["SUBMISSION_URL"]
secret = os.environ["SECRET"]

body = build_body()
logging.info("Payload: %s", body.decode("utf-8"))

execute_request(url, secret, body)
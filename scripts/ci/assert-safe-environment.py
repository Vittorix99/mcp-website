"""Fail-closed, value-redacted check for pull-request test jobs."""
import os
import sys


def validate_ci_environment(environ):
    def reject(key):
        raise ValueError(f"Unsafe CI configuration: {key}")
    if environ.get("MCP_ENV") != "test":
        reject("MCP_ENV")
    if environ.get("GCLOUD_PROJECT") != "demo-mcp-test":
        reject("GCLOUD_PROJECT")
    if environ.get("GOOGLE_CLOUD_PROJECT","demo-mcp-test") != "demo-mcp-test":
        reject("GOOGLE_CLOUD_PROJECT")
    if environ.get("STORAGE_BUCKET","demo-mcp-test.appspot.com") != "demo-mcp-test.appspot.com":
        reject("STORAGE_BUCKET")
    for key in (
        "GOOGLE_APPLICATION_CREDENTIALS","GOOGLE_CREDENTIALS","FIREBASE_SERVICE_ACCOUNT_JSON",
        "FIREBASE_SERVICE_ACCOUNT","FIREBASE_TOKEN","PAYPAL_CLIENT_ID","PAYPAL_CLIENT_SECRET",
        "PAYPAL_LIVE_CLIENT_ID","PAYPAL_LIVE_CLIENT_SECRET","MAILERSEND_API_KEY","MAILERSEND_TOKEN",
        "SENDER_API_KEY","SENDER_WEBHOOK_SECRET","PASS2U_API_KEY","GENDER_API_KEY",
        "SOUNDCLOUD_CLIENT_ID","SOUNDCLOUD_CLIENT_SECRET",
    ):
        if environ.get(key):
            reject(key)
    for key, value in environ.items():
        if any(project in value for project in ("mcp-website-2a1ad","mcp-website-dev-39539")):
            reject(key)
        if key in {f"{provider}_MODE" for provider in ("PAYPAL","MAIL","SENDER","PASS2U","GENDER","SOUNDCLOUD")} and value not in {"fake","disabled"}:
            reject(key)


if __name__ == "__main__":
    try:
        validate_ci_environment(os.environ)
        print("CI environment: demo-only, no cloud/provider credentials")
    except ValueError as error:
        print(str(error),file=sys.stderr)
        sys.exit(1)

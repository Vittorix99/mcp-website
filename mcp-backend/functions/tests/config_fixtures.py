"""Synthetic complete cloud profiles; never used for real provider calls."""


def cloud_environment(environment):
    return {
        "MCP_ENV": environment,
        "PAYPAL_CLIENT_ID": "fake-public-client",
        "PAYPAL_CLIENT_SECRET": "fake-private-secret",
        "MAILERSEND_API_KEY": "fake-mail-key",
        "MAILERSEND_FROM_EMAIL": "sender@example.test",
        "PASS2U_API_KEY": "fake-wallet-key",
        "SOUNDCLOUD_CLIENT_ID": "fake-radio-client",
        "SOUNDCLOUD_CLIENT_SECRET": "fake-radio-secret",
    }

"""Per-function provider capabilities and Secret Manager bindings; no secret reads."""
import os
import re
from functools import lru_cache

from firebase_functions.params import SecretParam

from config.runtime_settings import (
    ProviderMode, RuntimeConfigurationError, get_provider_settings,
    get_runtime_policy, get_runtime_settings,
)

# Public identifiers (PayPal/SoundCloud client IDs) remain runtime configuration.
_SECRET_NAMES = {
    'paypal': ('PAYPAL_CLIENT_SECRET',),
    'mail': ('MAILERSEND_API_KEY',),
    'pass2u': ('PASS2U_API_KEY',),
    'soundcloud': ('SOUNDCLOUD_CLIENT_SECRET',),
    'gender': ('GENDER_API_KEY',),
}

FUNCTION_PROVIDERS = {
    'create_order_event': ('paypal',),
    'capture_order_event': ('paypal', 'pass2u', 'mail'),
    'recover_order_event': ('paypal', 'pass2u'),
    'create_membership': ('pass2u', 'mail'),
    'update_membership': ('pass2u', 'mail'),
    'renew_membership': ('pass2u', 'mail'),
    'delete_membership': ('pass2u',),
    'merge_memberships': ('pass2u',),
    'send_membership_card': ('pass2u', 'mail'),
    'create_wallet_pass': ('pass2u',),
    'invalidate_wallet_pass': ('pass2u',),
    'create_participant': ('pass2u', 'gender'),
    'update_participant': ('pass2u', 'gender'),
    'send_ticket': ('mail',),
    'send_location': ('mail',),
    'send_omaggio_emails': ('mail',),
    'contact_us': ('mail',),
    'reply_to_message': ('mail',),
    'newsletter_signup': ('mail',),
    'admin_create_radio_episode': ('soundcloud',),
    'admin_update_radio_episode': ('soundcloud',),
    'on_participant_created': ('gender', 'mail'),
    'on_membership_created': ('gender', 'pass2u', 'mail'),
    'process_send_location_job': ('mail',),
}


@lru_cache(maxsize=None)
def _secret(name: str) -> SecretParam:
    return SecretParam(name)


def secrets_for_function(name: str) -> list[SecretParam]:
    providers = get_runtime_policy().providers
    return [_secret(secret)
            for provider in FUNCTION_PROVIDERS.get(name, ())
            if getattr(providers, provider) in {ProviderMode.SANDBOX, ProviderMode.STAGING, ProviderMode.LIVE}
            for secret in _SECRET_NAMES.get(provider, ())]


def validate_function_providers(name: str) -> None:
    for provider in FUNCTION_PROVIDERS.get(name, ()):
        get_provider_settings(provider)


def startup_settings():
    target = os.environ.get('FUNCTION_TARGET')
    if target:
        settings = get_runtime_policy()
        validate_function_providers(target)
        return settings
    if os.environ.get('ADMIN_PORT') and not os.environ.get('K_SERVICE'):
        port = os.environ['ADMIN_PORT']
        if not port.isdecimal() or not 0 < int(port) < 65536:
            raise RuntimeConfigurationError('Unsafe or invalid runtime setting: ADMIN_PORT')
        return get_runtime_policy()
    # Ordinary startup retains the original fail-closed credential contract.
    return get_runtime_settings()


def configure_runtime_identity(settings):
    """Set the managed runtime identity before any function decorator is evaluated."""
    account = os.environ.get('MCP_RUNTIME_SERVICE_ACCOUNT', '')
    if not account and not os.environ.get('MCP_RELEASE_SHA'):
        return
    if settings.environment.value not in {'staging', 'production'} or not re.fullmatch(
        r'[a-z][a-z0-9-]{4,28}[a-z0-9]@' + re.escape(settings.firebase.project_id) +
        r'\.iam\.gserviceaccount\.com', account
    ):
        raise RuntimeConfigurationError('Unsafe or invalid runtime setting: MCP_RUNTIME_SERVICE_ACCOUNT')
    from firebase_functions import options
    options.set_global_options(service_account=account)

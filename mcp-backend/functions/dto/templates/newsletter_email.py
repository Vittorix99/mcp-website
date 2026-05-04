from .common import EmailTemplateBasePayload


class NewsletterSignupEmailPayload(EmailTemplateBasePayload):
    email: str

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Type

from pydantic import BaseModel


REPO_ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS_DIR = REPO_ROOT / "mcp-backend" / "functions"
if str(FUNCTIONS_DIR) not in sys.path:
    sys.path.insert(0, str(FUNCTIONS_DIR))

from dto.templates import (  # noqa: E402
    CommunityEmailPayload,
    LocationEmailPayload,
    MembershipCardPdfPayload,
    MembershipEmailPayload,
    NewsletterSignupEmailPayload,
    OmaggioEmailPayload,
    TicketEmailPayload,
    TicketPdfPayload,
)
from services.templates.template_preview_service import TemplatePreviewService  # noqa: E402


@dataclass(frozen=True)
class PreviewDefinition:
    template_name: str
    fixture_path: Path
    payload_model: Type[BaseModel]
    output_name: str


FIXTURES_DIR = FUNCTIONS_DIR / "templates" / "fixtures"
PREVIEWS: dict[str, PreviewDefinition] = {
    "membership_email": PreviewDefinition(
        "emails/membership.html",
        FIXTURES_DIR / "emails" / "membership.json",
        MembershipEmailPayload,
        "membership_email.html",
    ),
    "ticket_email": PreviewDefinition(
        "emails/ticket.html",
        FIXTURES_DIR / "emails" / "ticket.json",
        TicketEmailPayload,
        "ticket_email.html",
    ),
    "location_email": PreviewDefinition(
        "emails/location.html",
        FIXTURES_DIR / "emails" / "location.json",
        LocationEmailPayload,
        "location_email.html",
    ),
    "newsletter_signup": PreviewDefinition(
        "emails/newsletter_signup.html",
        FIXTURES_DIR / "emails" / "newsletter_signup.json",
        NewsletterSignupEmailPayload,
        "newsletter_signup.html",
    ),
    "community_signup": PreviewDefinition(
        "emails/community.html",
        FIXTURES_DIR / "emails" / "community_signup.json",
        CommunityEmailPayload,
        "community_signup.html",
    ),
    "community_welcome": PreviewDefinition(
        "emails/community.html",
        FIXTURES_DIR / "emails" / "community_welcome.json",
        CommunityEmailPayload,
        "community_welcome.html",
    ),
    "omaggio_email": PreviewDefinition(
        "emails/omaggio.html",
        FIXTURES_DIR / "emails" / "omaggio.json",
        OmaggioEmailPayload,
        "omaggio_email.html",
    ),
    "member_ticket_pdf": PreviewDefinition(
        "pdf/member_ticket.html",
        FIXTURES_DIR / "pdf" / "member_ticket.json",
        TicketPdfPayload,
        "member_ticket_pdf.html",
    ),
    "membership_card_pdf": PreviewDefinition(
        "pdf/membership_card.html",
        FIXTURES_DIR / "pdf" / "membership_card.json",
        MembershipCardPdfPayload,
        "membership_card_pdf.html",
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Renderizza preview HTML dei template MCP.")
    parser.add_argument(
        "--template",
        default="all",
        choices=["all", *sorted(PREVIEWS.keys())],
        help="Template da renderizzare. Default: all.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "runtime-data" / "template-previews"),
        help="Directory di output per gli HTML renderizzati.",
    )
    parser.add_argument("--list", action="store_true", help="Mostra i template disponibili.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.list:
        for name in sorted(PREVIEWS):
            print(name)
        return 0

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    service = TemplatePreviewService()

    selected = PREVIEWS if args.template == "all" else {args.template: PREVIEWS[args.template]}
    for name, definition in selected.items():
        html = service.render_fixture(
            template_name=definition.template_name,
            fixture_path=definition.fixture_path,
            payload_model=definition.payload_model,
        )
        output_path = output_dir / definition.output_name
        output_path.write_text(html, encoding="utf-8")
        print(f"rendered {name}: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

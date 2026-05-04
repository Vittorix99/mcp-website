from __future__ import annotations

import json
from pathlib import Path
from typing import Type

from pydantic import BaseModel

from .template_renderer import TemplateRenderer


class TemplatePreviewService:
    """Genera preview statiche usando lo stesso renderer del runtime."""

    def __init__(self, renderer: TemplateRenderer | None = None) -> None:
        self.renderer = renderer or TemplateRenderer()

    def render_fixture(
        self,
        *,
        template_name: str,
        fixture_path: Path,
        payload_model: Type[BaseModel],
    ) -> str:
        payload = payload_model.model_validate(json.loads(fixture_path.read_text(encoding="utf-8")))
        return self.renderer.render(template_name, payload)

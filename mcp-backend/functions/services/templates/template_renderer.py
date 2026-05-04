from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from pydantic import BaseModel


class TemplateRenderer:
    """Renderer unico per email, PDF e preview.

    La business logic prepara solo payload tipizzati. Il renderer conosce Jinja2
    e i path dei template, evitando HTML embedded nei service.
    """

    def __init__(self, templates_dir: Path | None = None) -> None:
        self.templates_dir = templates_dir or Path(__file__).resolve().parents[2] / "templates"
        self.environment = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(("html", "xml")),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_name: str, context: BaseModel | Mapping[str, Any]) -> str:
        payload = context.model_dump() if isinstance(context, BaseModel) else dict(context)
        return self.environment.get_template(template_name).render(**payload).strip()


@lru_cache(maxsize=1)
def _default_renderer() -> TemplateRenderer:
    return TemplateRenderer()


def render_template(template_name: str, context: BaseModel | Mapping[str, Any]) -> str:
    return _default_renderer().render(template_name, context)

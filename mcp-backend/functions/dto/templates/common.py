from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EmailTemplateBasePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    logo_url: str = "#"
    footer_logo: str = "https://musiconnectingpeople.com/secondaryLogoWhite.png"
    prod_url: str = "https://musiconnectingpeople.com"
    instagram_url: Optional[str] = None
    year: int = datetime.now().year

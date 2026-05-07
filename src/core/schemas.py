from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class WindowInfo(BaseModel):
    """Informace zachycené z operačního systému."""
    title: str
    executable: str
    is_whitelisted: bool = Field(default=False)
    # default_factory=datetime.now zajistí, že se čas vygeneruje znovu pro každé okno.
    timestamp: datetime = Field(default_factory=datetime.now)

class ContextMatch(BaseModel):
    """Výsledek analýzy - ke komu aktivita patří."""
    client_name: str
    project_name: str

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class WindowInfo(BaseModel):
    """Informace zachycené z operačního systému."""
    title: str
    executable: str
    timestamp: datetime = datetime.now()

class ContextMatch(BaseModel):
    """Výsledek analýzy - ke komu aktivita patří."""
    client_name: str
    project_name: str
    confidence: float = 1.0  # Jak moc si je systém jistý (0.0 až 1.0)
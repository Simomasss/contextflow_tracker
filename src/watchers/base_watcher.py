from abc import ABC, abstractmethod
from typing import Any, Optional

class BaseWatcher(ABC):
    """
    Abstraktní základ pro všechny 'senzory' v aplikaci.
    Definuje společné rozhraní, které musí každý watcher splnit.
    """
    
    @abstractmethod
    def watch(self) -> Optional[Any]:
        """
        Metoda pro sběr dat. 
        Vrací buď zachycená data, nebo None, pokud není co reportovat.
        Každý watcher musí implementovat tuto metodu.
        """
        pass
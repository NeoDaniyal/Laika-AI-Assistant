from abc import ABC, abstractmethod
from typing import Any, Dict

class Tool(ABC):
    """
    Abstract base class for all Laika agent tools.

    Any tool integrated into Laika must inherit from this class
    and implement its properties and execution logic.
    """

    @property
    @abstractmethod
    def name(self)-> str:
        """Unique string identifier for the tool used by the LLM."""
        pass
    
    @property
    @abstractmethod
    def description(self)-> str:
        """Explanation of when and why the LLM should invoke this tool."""
        pass

    
    @property
    @abstractmethod
    def parameters(self)-> Dict[str, Any]:
        """JSON Schema defination expected arguments for the tool."""
        pass

    @abstractmethod
    def execute(self, arguments: Dict[str, Any])-> Any:
        """Execute the Python logic given arguements provided by the LLM."""
        pass

    def to_schema(self) -> Dict[str, Any]:
        """Exports the tool metadata schema for context injection into the LLM prompt."""
        return{
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
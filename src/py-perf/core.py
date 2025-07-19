from typing import Any, Optional


class YourMainClass:
    """Main class for your library functionality."""
    
    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        """Initialize the class.
        
        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {}
    
    def main_method(self, data: str) -> str:
        """Main method that does something useful.
        
        Args:
            data: Input data to process.
            
        Returns:
            Processed data.
            
        Raises:
            ValueError: If data is empty.
        """
        if not data:
            raise ValueError("Data cannot be empty")
        
        return f"Processed: {data}"
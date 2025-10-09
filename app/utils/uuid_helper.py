import uuid
from typing import Any, Dict, List, Union

def convert_uuid_to_str(obj: Any) -> Any:
    """
    Recursively convert UUID objects to strings in a nested structure.
    
    Args:
        obj: The object to convert, can be a dict, list, UUID, or other type
        
    Returns:
        The object with all UUIDs converted to strings
    """
    if isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: convert_uuid_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_uuid_to_str(item) for item in obj]
    elif hasattr(obj, "__dict__"):
        # For SQLAlchemy models and other objects with __dict__
        return {k: convert_uuid_to_str(v) for k, v in obj.__dict__.items() 
                if not k.startswith("_")}
    else:
        return obj

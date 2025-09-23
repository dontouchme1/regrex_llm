from pydantic import BaseModel, Field
from typing import List, Optional

class TransformRequest(BaseModel):
    instruction: str = Field(..., description="Natural language, e.g., 'find email addresses'")
    columns: Optional[List[str]] = None

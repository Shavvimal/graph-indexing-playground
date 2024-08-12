from pydantic import BaseModel
from typing import List, Optional

class Transcript(BaseModel):
    """
    Represents an AI news update newsletter.
    """
    video_id: str
    content: str
    date: str
    title: str
    description: Optional[str]
    tags: Optional[List[str]]
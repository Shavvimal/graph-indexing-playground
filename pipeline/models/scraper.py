from pydantic import BaseModel
from typing import List, Optional

class Article(BaseModel):
    """
    Represents an Antler Article
    """
    id: str
    title: str
    author: str
    date: str
    description: Optional[str]
    content: str
    url: str
    tags: List[str]


class Book(BaseModel):
    title: Optional[str] = None  # Title of the book
    author: Optional[str] = None  # Author of the book
    language: Optional[str] = None  # Language code (e.g., 'en', 'en-US')
    identifier: Optional[str] = None  # Unique identifier (e.g., ISBN)
    publisher: Optional[str] = None  # Publisher of the book
    date: Optional[str] = None  # Publication date
    description: Optional[str] = None  # Description or summary of the book
    content: str
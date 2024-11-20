from pydantic import BaseModel
from typing import List, Dict, Optional

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    context: Dict[str, list]
    
class DocumentSummary(BaseModel):
    text_summaries: List[str]
    table_summaries: List[str]
    image_summaries: List[str]
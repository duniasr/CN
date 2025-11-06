from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from datetime import datetime
import uuid

class Note(BaseModel):
    note_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    author: str = Field(..., min_length=1, max_length=255)
    # Campo 'message' del formulario
    message: str = Field(..., min_length=1)
    # Campo 'color' del formulario
    color: str = Field(default_factory="#FFFACD") # Color amarillo por defecto
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    class Config:
        # Esto permite que la API devuelva 'note_id'
        json_schema_extra = {
            "example": {
                "note_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "author": "Ana",
                "message": "Recordar comprar leche",
                "color": "#FFFACD",
                "created_at": "2025-11-03T14:00:00Z"
            }
        }
    
    def update_timestamp(self):
        self.updated_at = datetime.utcnow().isoformat()
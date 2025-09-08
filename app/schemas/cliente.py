from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import uuid

class ClienteBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100)
    documento: Optional[str] = Field(None, max_length=20)
    telefone: Optional[str] = Field(None, max_length=20)
    endereco: Optional[str] = None

class ClienteCreate(ClienteBase):
    uuid: Optional[str] = None

class ClienteUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    documento: Optional[str] = Field(None, max_length=20)
    telefone: Optional[str] = Field(None, max_length=20)
    endereco: Optional[str] = None

class ClienteResponse(ClienteBase):
    id: str
    ativo: bool
    created_at: datetime
    updated_at: datetime

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v)
        }

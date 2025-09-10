from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import uuid

class ItemVendaBase(BaseModel):
    produto_id: str
    quantidade: int = Field(..., ge=0)
    peso_kg: Optional[float] = Field(0.0, ge=0)
    preco_unitario: float = Field(..., gt=0)
    subtotal: float = Field(..., gt=0)

class ItemVendaCreate(ItemVendaBase):
    pass

class ItemVendaResponse(ItemVendaBase):
    id: str
    venda_id: str
    created_at: datetime
    updated_at: datetime

    @field_validator('id', 'venda_id', 'produto_id', mode='before')
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

class VendaBase(BaseModel):
    cliente_id: Optional[str] = None
    total: float = Field(..., gt=0)
    desconto: Optional[float] = Field(0.0, ge=0)
    forma_pagamento: str = Field(..., min_length=1, max_length=50)
    observacoes: Optional[str] = None

class VendaCreate(VendaBase):
    uuid: Optional[str] = None
    itens: Optional[List[ItemVendaCreate]] = []

class VendaUpdate(BaseModel):
    cliente_id: Optional[str] = None
    total: Optional[float] = Field(None, gt=0)
    desconto: Optional[float] = Field(None, ge=0)
    forma_pagamento: Optional[str] = Field(None, min_length=1, max_length=50)
    observacoes: Optional[str] = None
    cancelada: Optional[bool] = None

class VendaResponse(VendaBase):
    id: str
    cancelada: bool
    created_at: datetime
    updated_at: datetime
    itens: List[ItemVendaResponse] = []

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

from sqlalchemy import Column, String, Boolean, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import DeclarativeBase
from datetime import datetime
from typing import Optional
import uuid


class User(DeclarativeBase):
    __tablename__ = "usuarios"

    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    usuario: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class Produto(DeclarativeBase):
    __tablename__ = "produtos"

    codigo: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    preco_custo: Mapped[float] = mapped_column(Float, default=0.0)
    preco_venda: Mapped[float] = mapped_column(Float, nullable=False)
    estoque: Mapped[int] = mapped_column(Integer, default=0)
    estoque_minimo: Mapped[int] = mapped_column(Integer, default=0)
    categoria_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    venda_por_peso: Mapped[bool] = mapped_column(Boolean, default=False)
    unidade_medida: Mapped[str] = mapped_column(String(10), default='un')
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class Cliente(DeclarativeBase):
    __tablename__ = "clientes"

    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    documento: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    telefone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    endereco: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class Venda(DeclarativeBase):
    __tablename__ = "vendas"

    cliente_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=True)
    total: Mapped[float] = mapped_column(Float, nullable=False)
    desconto: Mapped[float] = mapped_column(Float, default=0.0)
    forma_pagamento: Mapped[str] = mapped_column(String(50), nullable=False)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cancelada: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relacionamentos
    cliente: Mapped[Optional["Cliente"]] = relationship("Cliente", back_populates="vendas")
    itens: Mapped[list["ItemVenda"]] = relationship("ItemVenda", back_populates="venda")


class ItemVenda(DeclarativeBase):
    __tablename__ = "itens_venda"

    venda_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("vendas.id"), nullable=False)
    produto_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("produtos.id"), nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    peso_kg: Mapped[float] = mapped_column(Float, default=0.0)
    preco_unitario: Mapped[float] = mapped_column(Float, nullable=False)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Relacionamentos
    venda: Mapped["Venda"] = relationship("Venda", back_populates="itens")
    produto: Mapped["Produto"] = relationship("Produto")


# Adicionar relacionamentos reversos
Cliente.vendas = relationship("Venda", back_populates="cliente")

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from typing import List
import uuid
from datetime import datetime

from ..db.database import get_db_session
from ..db.models import Venda, ItemVenda
from ..schemas.venda import VendaCreate, VendaUpdate, VendaResponse

router = APIRouter(prefix="/api/vendas", tags=["vendas"])

@router.get("/", response_model=List[VendaResponse])
async def listar_vendas(db: AsyncSession = Depends(get_db_session)):
    """Lista todas as vendas."""
    try:
        result = await db.execute(
            select(Venda)
            .options(selectinload(Venda.itens), selectinload(Venda.cliente))
            .where(Venda.cancelada == False)
        )
        vendas = result.scalars().all()
        return vendas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar vendas: {str(e)}")

@router.get("/{venda_id}", response_model=VendaResponse)
async def obter_venda(venda_id: str, db: AsyncSession = Depends(get_db_session)):
    """Obtém uma venda específica por UUID."""
    try:
        result = await db.execute(
            select(Venda)
            .options(selectinload(Venda.itens), selectinload(Venda.cliente))
            .where(Venda.id == venda_id)
        )
        venda = result.scalar_one_or_none()
        
        if not venda:
            raise HTTPException(status_code=404, detail="Venda não encontrada")
        
        return venda
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de venda inválido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter venda: {str(e)}")

@router.post("/", response_model=VendaResponse)
async def criar_venda(venda: VendaCreate, db: AsyncSession = Depends(get_db_session)):
    """Cria uma nova venda."""
    try:
        # Criar nova venda
        venda_uuid = uuid.uuid4()
        if hasattr(venda, 'uuid') and venda.uuid:
            try:
                venda_uuid = uuid.UUID(venda.uuid)
            except ValueError:
                venda_uuid = uuid.uuid4()
        
        # Converter cliente_id se fornecido
        cliente_uuid = None
        if venda.cliente_id:
            try:
                cliente_uuid = uuid.UUID(venda.cliente_id)
            except ValueError:
                cliente_uuid = None
        
        nova_venda = Venda(
            id=venda_uuid,
            cliente_id=cliente_uuid,
            total=venda.total,
            desconto=venda.desconto or 0.0,
            forma_pagamento=venda.forma_pagamento,
            observacoes=venda.observacoes,
            cancelada=False
        )
        
        db.add(nova_venda)
        await db.flush()  # Para obter o ID da venda
        
        # Criar itens da venda se fornecidos
        if hasattr(venda, 'itens') and venda.itens:
            for item_data in venda.itens:
                item = ItemVenda(
                    venda_id=nova_venda.id,
                    produto_id=uuid.UUID(item_data.produto_id),
                    quantidade=item_data.quantidade,
                    preco_unitario=item_data.preco_unitario,
                    subtotal=item_data.subtotal
                )
                db.add(item)
        
        await db.commit()
        await db.refresh(nova_venda)
        
        return nova_venda
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar venda: {str(e)}")

@router.put("/{venda_id}", response_model=VendaResponse)
async def atualizar_venda(venda_id: str, venda: VendaUpdate, db: AsyncSession = Depends(get_db_session)):
    """Atualiza uma venda existente."""
    try:
        # Buscar venda existente
        result = await db.execute(select(Venda).where(Venda.id == venda_id))
        venda_existente = result.scalar_one_or_none()
        
        if not venda_existente:
            raise HTTPException(status_code=404, detail="Venda não encontrada")
        
        # Atualizar campos
        update_data = {}
        if venda.cliente_id is not None:
            try:
                update_data[Venda.cliente_id] = uuid.UUID(venda.cliente_id) if venda.cliente_id else None
            except ValueError:
                update_data[Venda.cliente_id] = None
        if venda.total is not None:
            update_data[Venda.total] = venda.total
        if venda.desconto is not None:
            update_data[Venda.desconto] = venda.desconto
        if venda.forma_pagamento is not None:
            update_data[Venda.forma_pagamento] = venda.forma_pagamento
        if venda.observacoes is not None:
            update_data[Venda.observacoes] = venda.observacoes
        if venda.cancelada is not None:
            update_data[Venda.cancelada] = venda.cancelada
        
        update_data[Venda.updated_at] = datetime.utcnow()
        
        await db.execute(
            update(Venda).where(Venda.id == venda_id).values(**update_data)
        )
        await db.commit()
        
        # Retornar venda atualizada
        result = await db.execute(
            select(Venda)
            .options(selectinload(Venda.itens), selectinload(Venda.cliente))
            .where(Venda.id == venda_id)
        )
        return result.scalar_one()
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar venda: {str(e)}")

@router.delete("/{venda_id}")
async def cancelar_venda(venda_id: str, db: AsyncSession = Depends(get_db_session)):
    """Cancela uma venda (soft delete)."""
    try:
        # Buscar venda existente
        result = await db.execute(select(Venda).where(Venda.id == venda_id))
        venda_existente = result.scalar_one_or_none()
        
        if not venda_existente:
            raise HTTPException(status_code=404, detail="Venda não encontrada")
        
        # Cancelar venda
        await db.execute(
            update(Venda)
            .where(Venda.id == venda_id)
            .values(cancelada=True, updated_at=datetime.utcnow())
        )
        await db.commit()
        
        return {"message": "Venda cancelada com sucesso"}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao cancelar venda: {str(e)}")

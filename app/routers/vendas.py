from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from typing import List
import uuid
from datetime import datetime

from ..db.database import get_db_session
from sqlalchemy.exc import IntegrityError
from ..db.models import Venda, ItemVenda, Produto, Usuario
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
        
        # Converter usuario_id se fornecido
        usuario_uuid = None
        if hasattr(venda, 'usuario_id') and venda.usuario_id:
            try:
                usuario_uuid = uuid.UUID(venda.usuario_id)
            except ValueError:
                usuario_uuid = None

        nova_venda = Venda(
            id=venda_uuid,
            usuario_id=usuario_uuid,
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
                # Validar UUID de produto individualmente para evitar 500 genérico
                try:
                    produto_uuid = uuid.UUID(item_data.produto_id)
                except (ValueError, TypeError):
                    raise HTTPException(status_code=400, detail=f"produto_id inválido: {item_data.produto_id}")

                # Verificar existência do produto para evitar erro de FK
                result_prod = await db.execute(select(Produto).where(Produto.id == produto_uuid))
                produto_db = result_prod.scalar_one_or_none()
                if not produto_db:
                    raise HTTPException(status_code=400, detail=f"Produto inexistente no servidor: {item_data.produto_id}")

                item = ItemVenda(
                    venda_id=nova_venda.id,
                    produto_id=produto_uuid,
                    quantidade=max(1, int(item_data.quantidade or 0)),
                    peso_kg=getattr(item_data, 'peso_kg', 0.0),
                    preco_unitario=item_data.preco_unitario,
                    subtotal=item_data.subtotal
                )
                db.add(item)
        
        await db.commit()
        await db.refresh(nova_venda)
        
        return nova_venda
    except IntegrityError as ie:
        # Possíveis causas: UUID duplicado, FK de produto inexistente, etc.
        await db.rollback()
        msg = str(ie.orig) if getattr(ie, 'orig', None) else str(ie)
        # Quando for chave duplicada, retornar 409 para o cliente tratar como 'já existe'
        if "duplicate key" in msg.lower() or "unique" in msg.lower():
            raise HTTPException(status_code=409, detail=f"Venda já existe (conflito de chave): {msg}")
        raise HTTPException(status_code=400, detail=f"Violação de integridade ao criar venda: {msg}")
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
async def deletar_venda(venda_id: str, db: AsyncSession = Depends(get_db_session)):
    """Deletar uma venda específica."""
    try:
        # Buscar a venda
        stmt = select(Venda).where(Venda.id == venda_id)
        result = await db.execute(stmt)
        venda = result.scalar_one_or_none()
        
        if not venda:
            raise HTTPException(status_code=404, detail="Venda não encontrada")
        
        # Deletar itens da venda primeiro (devido à foreign key)
        stmt_itens = delete(ItemVenda).where(ItemVenda.venda_id == venda_id)
        await db.execute(stmt_itens)
        
        # Deletar a venda
        await db.delete(venda)
        await db.commit()
        
        return {"message": "Venda deletada com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao deletar venda: {str(e)}")

@router.get("/usuario/{usuario_id}")
async def listar_vendas_usuario(
    usuario_id: int,
    data_inicio: str = None,
    data_fim: str = None,
    status_filter: str = None,
    db: AsyncSession = Depends(get_db_session)
):
    """Listar vendas de um usuário específico com filtros opcionais."""
    try:
        # Query base
        stmt = select(Venda).options(selectinload(Venda.itens))
        
        # Filtrar por usuário
        stmt = stmt.where(Venda.usuario_id == usuario_id)
        
        # Aplicar filtros de data se fornecidos
        if data_inicio:
            stmt = stmt.where(func.date(Venda.created_at) >= data_inicio)
        if data_fim:
            stmt = stmt.where(func.date(Venda.created_at) <= data_fim)
            
        # Aplicar filtro de status se fornecido
        if status_filter:
            if status_filter == "Não Fechadas":
                stmt = stmt.where(Venda.cancelada == False)
            elif status_filter == "Fechadas":
                stmt = stmt.where(Venda.cancelada == True)
        
        # Ordenar por data mais recente
        stmt = stmt.order_by(Venda.created_at.desc())
        
        result = await db.execute(stmt)
        vendas = result.scalars().all()
        
        return [VendaResponse.model_validate(venda) for venda in vendas]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar vendas do usuário: {str(e)}")

@router.get("/periodo")
async def listar_vendas_periodo(
    data_inicio: str,
    data_fim: str,
    usuario_id: int = None,
    limit: int = None,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session)
):
    """Listar vendas em um período específico com paginação."""
    try:
        # Query base com JOIN para buscar nome do usuário
        stmt = (
            select(Venda)
            .options(selectinload(Venda.itens), selectinload(Venda.cliente), selectinload(Venda.usuario))
            .join(Usuario, Venda.usuario_id == Usuario.id, isouter=True)
        )
        
        # Filtrar por período
        stmt = stmt.where(
            Venda.data_venda >= data_inicio,
            Venda.data_venda <= data_fim
        )
        
        # Filtrar por usuário se especificado
        if usuario_id is not None:
            stmt = stmt.where(Venda.usuario_id == usuario_id)
        
        # Ordenar por data mais recente
        stmt = stmt.order_by(Venda.data_venda.desc())
        
        # Aplicar paginação se especificada
        if limit:
            stmt = stmt.limit(limit).offset(offset)
        
        result = await db.execute(stmt)
        vendas = result.scalars().all()
        
        return [VendaResponse.model_validate(venda) for venda in vendas]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar vendas do período: {str(e)}")

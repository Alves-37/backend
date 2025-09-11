from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List
import uuid
from datetime import datetime

from ..db.database import get_db_session
from ..db.models import Cliente
from ..schemas.cliente import ClienteCreate, ClienteUpdate, ClienteResponse

router = APIRouter(prefix="/api/clientes", tags=["clientes"])

@router.get("/", response_model=List[ClienteResponse])
async def listar_clientes(db: AsyncSession = Depends(get_db_session)):
    """Lista todos os clientes."""
    try:
        result = await db.execute(select(Cliente).where(Cliente.ativo == True))
        clientes = result.scalars().all()
        return clientes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar clientes: {str(e)}")

@router.get("/{cliente_id}", response_model=ClienteResponse)
async def obter_cliente(cliente_id: str, db: AsyncSession = Depends(get_db_session)):
    """Obtém um cliente específico por UUID."""
    try:
        result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
        cliente = result.scalar_one_or_none()
        
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        return cliente
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de cliente inválido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter cliente: {str(e)}")

@router.post("/", response_model=ClienteResponse)
async def criar_cliente(cliente: ClienteCreate, db: AsyncSession = Depends(get_db_session)):
    """Cria um novo cliente."""
    try:
        # Criar novo cliente
        cliente_uuid = uuid.uuid4()
        if hasattr(cliente, 'uuid') and cliente.uuid:
            try:
                cliente_uuid = uuid.UUID(cliente.uuid)
            except ValueError:
                cliente_uuid = uuid.uuid4()
        
        novo_cliente = Cliente(
            id=cliente_uuid,
            nome=cliente.nome,
            documento=cliente.documento,
            telefone=cliente.telefone,
            endereco=cliente.endereco,
            ativo=True
        )
        
        db.add(novo_cliente)
        await db.commit()
        await db.refresh(novo_cliente)
        
        return novo_cliente
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar cliente: {str(e)}")

@router.put("/{cliente_id}", response_model=ClienteResponse)
async def atualizar_cliente(cliente_id: str, cliente: ClienteUpdate, db: AsyncSession = Depends(get_db_session)):
    """Atualiza um cliente existente."""
    try:
        # Buscar cliente existente
        result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
        cliente_existente = result.scalar_one_or_none()
        
        if not cliente_existente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        # Atualizar campos
        update_data = {}
        if cliente.nome is not None:
            update_data[Cliente.nome] = cliente.nome
        if cliente.documento is not None:
            update_data[Cliente.documento] = cliente.documento
        if cliente.telefone is not None:
            update_data[Cliente.telefone] = cliente.telefone
        if cliente.endereco is not None:
            update_data[Cliente.endereco] = cliente.endereco
        
        update_data[Cliente.updated_at] = datetime.utcnow()
        
        await db.execute(
            update(Cliente).where(Cliente.id == cliente_id).values(**update_data)
        )
        await db.commit()
        
        # Retornar cliente atualizado
        result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
        return result.scalar_one()
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar cliente: {str(e)}")

@router.delete("/{cliente_id}")
async def deletar_cliente(cliente_id: str, db: AsyncSession = Depends(get_db_session)):
    """Deleta um cliente (hard delete)."""
    try:
        # Buscar cliente existente (independente de ativo)
        result = await db.execute(select(Cliente).where(Cliente.id == cliente_id))
        cliente_existente = result.scalar_one_or_none()
        
        if not cliente_existente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        # Hard delete (remoção física)
        await db.execute(
            delete(Cliente).where(Cliente.id == cliente_id)
        )
        await db.commit()
        
        return {"message": "Cliente removido definitivamente"}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao deletar cliente: {str(e)}")

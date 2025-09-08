"""
Endpoints para gerenciamento de produtos com sincronização.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List, Optional
import uuid
from datetime import datetime

from app.db.database import get_db_session
from app.db.models import Produto
from pydantic import BaseModel

router = APIRouter(prefix="/api/produtos", tags=["Produtos"])

# Schemas Pydantic
class ProdutoCreate(BaseModel):
    codigo: str
    nome: str
    descricao: str = ""
    preco_custo: float = 0.0
    preco_venda: float
    estoque: int = 0
    estoque_minimo: int = 0
    categoria_id: Optional[int] = None
    venda_por_peso: bool = False
    unidade_medida: str = "un"
    uuid: Optional[str] = None

class ProdutoUpdate(BaseModel):
    codigo: Optional[str] = None
    nome: Optional[str] = None
    descricao: Optional[str] = None
    preco_custo: Optional[float] = None
    preco_venda: Optional[float] = None
    estoque: Optional[int] = None
    estoque_minimo: Optional[int] = None
    categoria_id: Optional[int] = None
    venda_por_peso: Optional[bool] = None
    unidade_medida: Optional[str] = None

class ProdutoResponse(BaseModel):
    id: str
    codigo: str
    nome: str
    descricao: str = None
    preco_custo: float
    preco_venda: float
    estoque: int
    estoque_minimo: int
    categoria_id: int = None
    venda_por_peso: bool
    unidade_medida: str
    ativo: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=str(obj.id),
            codigo=obj.codigo,
            nome=obj.nome,
            descricao=obj.descricao,
            preco_custo=obj.preco_custo,
            preco_venda=obj.preco_venda,
            estoque=obj.estoque,
            estoque_minimo=obj.estoque_minimo,
            categoria_id=obj.categoria_id,
            venda_por_peso=obj.venda_por_peso,
            unidade_medida=obj.unidade_medida,
            ativo=obj.ativo,
            created_at=obj.created_at,
            updated_at=obj.updated_at
        )

@router.get("/", response_model=List[ProdutoResponse])
async def get_produtos(db: AsyncSession = Depends(get_db_session)):
    """Lista todos os produtos ativos."""
    try:
        result = await db.execute(
            select(Produto).where(Produto.ativo == True).order_by(Produto.nome)
        )
        produtos = result.scalars().all()
        return [ProdutoResponse.from_orm(p) for p in produtos]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar produtos: {str(e)}"
        )

@router.get("/{produto_uuid}", response_model=ProdutoResponse)
async def get_produto(produto_uuid: str, db: AsyncSession = Depends(get_db_session)):
    """Busca produto por UUID."""
    try:
        # Tentar converter para UUID
        produto_id = uuid.UUID(produto_uuid)
        
        result = await db.execute(
            select(Produto).where(
                Produto.id == produto_id,
                Produto.ativo == True
            )
        )
        produto = result.scalar_one_or_none()
        
        if not produto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto não encontrado"
            )
        
        return ProdutoResponse.from_orm(produto)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="UUID inválido"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar produto: {str(e)}"
        )

@router.post("/", response_model=ProdutoResponse, status_code=status.HTTP_201_CREATED)
async def create_produto(produto_data: ProdutoCreate, db: AsyncSession = Depends(get_db_session)):
    """Cria novo produto."""
    try:
        # Gerar UUID se não fornecido
        produto_uuid = uuid.UUID(produto_data.uuid) if produto_data.uuid else uuid.uuid4()
        
        # Verificar se UUID já existe
        existing = await db.execute(
            select(Produto).where(Produto.id == produto_uuid)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Produto com este UUID já existe"
            )
        
        # Criar produto
        produto = Produto(
            id=produto_uuid,
            codigo=produto_data.codigo,
            nome=produto_data.nome,
            descricao=produto_data.descricao,
            preco_custo=produto_data.preco_custo,
            preco_venda=produto_data.preco_venda,
            estoque=produto_data.estoque,
            estoque_minimo=produto_data.estoque_minimo,
            categoria_id=produto_data.categoria_id,
            venda_por_peso=produto_data.venda_por_peso,
            unidade_medida=produto_data.unidade_medida,
            ativo=True
        )
        
        db.add(produto)
        await db.commit()
        await db.refresh(produto)
        
        return ProdutoResponse.from_orm(produto)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar produto: {str(e)}"
        )

@router.put("/{produto_uuid}", response_model=ProdutoResponse)
async def update_produto(
    produto_uuid: str, 
    produto_data: ProdutoUpdate, 
    db: AsyncSession = Depends(get_db_session)
):
    """Atualiza produto existente."""
    try:
        # Converter UUID
        produto_id = uuid.UUID(produto_uuid)
        
        # Buscar produto
        result = await db.execute(
            select(Produto).where(
                Produto.id == produto_id,
                Produto.ativo == True
            )
        )
        produto = result.scalar_one_or_none()
        
        if not produto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto não encontrado"
            )
        
        # Atualizar campos fornecidos
        update_data = produto_data.dict(exclude_unset=True)
        if update_data:
            update_data['updated_at'] = datetime.utcnow()
            
            await db.execute(
                update(Produto)
                .where(Produto.id == produto_id)
                .values(**update_data)
            )
            await db.commit()
            await db.refresh(produto)
        
        return ProdutoResponse.from_orm(produto)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="UUID inválido"
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar produto: {str(e)}"
        )

@router.delete("/{produto_uuid}")
async def delete_produto(produto_uuid: str, db: AsyncSession = Depends(get_db_session)):
    """Deleta produto (soft delete)."""
    try:
        # Converter UUID
        produto_id = uuid.UUID(produto_uuid)
        
        # Verificar se produto existe
        result = await db.execute(
            select(Produto).where(
                Produto.id == produto_id,
                Produto.ativo == True
            )
        )
        produto = result.scalar_one_or_none()
        
        if not produto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto não encontrado"
            )
        
        # Soft delete
        await db.execute(
            update(Produto)
            .where(Produto.id == produto_id)
            .values(ativo=False, updated_at=datetime.utcnow())
        )
        await db.commit()
        
        return {"message": "Produto deletado com sucesso"}
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="UUID inválido"
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao deletar produto: {str(e)}"
        )

# Endpoints de sincronização
@router.post("/sync/push")
async def sync_push_produtos(
    produtos: List[dict], 
    db: AsyncSession = Depends(get_db_session)
):
    """Recebe produtos do cliente para sincronização."""
    try:
        synced_count = 0
        errors = []
        
        for produto_data in produtos:
            try:
                produto_uuid = uuid.UUID(produto_data['uuid'])
                
                # Verificar se produto já existe
                result = await db.execute(
                    select(Produto).where(Produto.id == produto_uuid)
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    # Atualizar produto existente
                    update_data = {
                        'codigo': produto_data.get('codigo', ''),
                        'nome': produto_data['nome'],
                        'descricao': produto_data.get('descricao', ''),
                        'preco_custo': produto_data.get('preco_custo', 0),
                        'preco_venda': produto_data.get('preco_venda', 0),
                        'estoque': produto_data.get('estoque', 0),
                        'estoque_minimo': produto_data.get('estoque_minimo', 0),
                        'categoria_id': produto_data.get('categoria_id'),
                        'venda_por_peso': produto_data.get('venda_por_peso', False),
                        'unidade_medida': produto_data.get('unidade_medida', 'un'),
                        'updated_at': datetime.utcnow()
                    }
                    
                    await db.execute(
                        update(Produto)
                        .where(Produto.id == produto_uuid)
                        .values(**update_data)
                    )
                else:
                    # Criar novo produto
                    produto = Produto(
                        id=produto_uuid,
                        codigo=produto_data.get('codigo', ''),
                        nome=produto_data['nome'],
                        descricao=produto_data.get('descricao', ''),
                        preco_custo=produto_data.get('preco_custo', 0),
                        preco_venda=produto_data.get('preco_venda', 0),
                        estoque=produto_data.get('estoque', 0),
                        estoque_minimo=produto_data.get('estoque_minimo', 0),
                        categoria_id=produto_data.get('categoria_id'),
                        venda_por_peso=produto_data.get('venda_por_peso', False),
                        unidade_medida=produto_data.get('unidade_medida', 'un'),
                        ativo=True
                    )
                    db.add(produto)
                
                synced_count += 1
                
            except Exception as e:
                errors.append({
                    'uuid': produto_data.get('uuid', 'unknown'),
                    'error': str(e)
                })
        
        await db.commit()
        
        return {
            'synced_count': synced_count,
            'errors': errors,
            'message': f'{synced_count} produtos sincronizados com sucesso'
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na sincronização: {str(e)}"
        )

@router.get("/sync/pull")
async def sync_pull_produtos(
    last_sync: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """Envia produtos atualizados para o cliente."""
    try:
        query = select(Produto).where(Produto.ativo == True)
        
        # Filtrar por data de última sincronização se fornecida
        if last_sync:
            try:
                last_sync_date = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                query = query.where(Produto.updated_at > last_sync_date)
            except ValueError:
                pass  # Ignorar data inválida
        
        result = await db.execute(query.order_by(Produto.updated_at))
        produtos = result.scalars().all()
        
        return {
            'produtos': [
                {
                    'uuid': str(produto.id),
                    'codigo': produto.codigo,
                    'nome': produto.nome,
                    'descricao': produto.descricao,
                    'preco_custo': produto.preco_custo,
                    'preco_venda': produto.preco_venda,
                    'estoque': produto.estoque,
                    'estoque_minimo': produto.estoque_minimo,
                    'categoria_id': produto.categoria_id,
                    'venda_por_peso': produto.venda_por_peso,
                    'unidade_medida': produto.unidade_medida,
                    'ativo': produto.ativo,
                    'created_at': produto.created_at.isoformat(),
                    'updated_at': produto.updated_at.isoformat()
                }
                for produto in produtos
            ],
            'count': len(produtos),
            'sync_timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar produtos para sincronização: {str(e)}"
        )

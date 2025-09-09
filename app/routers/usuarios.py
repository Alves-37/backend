from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List
import uuid
from datetime import datetime

from ..db.database import get_db_session
from ..db.models import User
from ..schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse

router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])

@router.get("/", response_model=List[dict])
async def listar_usuarios(db: AsyncSession = Depends(get_db_session)):
    """Lista todos os usuários."""
    try:
        result = await db.execute(select(User).where(User.ativo == True))
        usuarios = result.scalars().all()
        
        # Converter para dict com uuid
        usuarios_dict = []
        for usuario in usuarios:
            usuario_dict = {
                'uuid': str(usuario.id),
                'id': str(usuario.id),
                'nome': usuario.nome,
                'usuario': usuario.usuario,
                'is_admin': usuario.is_admin,
                'ativo': usuario.ativo,
                'created_at': usuario.created_at.isoformat(),
                'updated_at': usuario.updated_at.isoformat()
            }
            usuarios_dict.append(usuario_dict)
        
        return usuarios_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar usuários: {str(e)}")

@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def obter_usuario(usuario_id: str, db: AsyncSession = Depends(get_db_session)):
    """Obtém um usuário específico por UUID."""
    try:
        # Tentar buscar por UUID primeiro
        result = await db.execute(select(User).where(User.id == usuario_id))
        usuario = result.scalar_one_or_none()
        
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        return usuario
    except ValueError:
        # Se não for UUID válido, retornar erro
        raise HTTPException(status_code=400, detail="ID de usuário inválido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter usuário: {str(e)}")

@router.post("/", response_model=UsuarioResponse)
async def criar_usuario(usuario: UsuarioCreate, db: AsyncSession = Depends(get_db_session)):
    """Cria um novo usuário."""
    try:
        # Verificar se já existe usuário com mesmo nome de usuário
        result = await db.execute(select(User).where(User.usuario == usuario.usuario))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Nome de usuário já existe")
        
        # Criar novo usuário
        usuario_uuid = uuid.uuid4()
        if hasattr(usuario, 'uuid') and usuario.uuid:
            try:
                usuario_uuid = uuid.UUID(usuario.uuid)
            except ValueError:
                usuario_uuid = uuid.uuid4()

        # Verificar duplicidade de UUID (id) antes de inserir
        existing_by_id = await db.execute(select(User).where(User.id == str(usuario_uuid)))
        if existing_by_id.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Usuário já existe (mesmo id)")
        
        novo_usuario = User(
            id=usuario_uuid,
            nome=usuario.nome,
            usuario=usuario.usuario,
            senha_hash=usuario.senha,  # Assumindo que já vem hasheada
            is_admin=usuario.is_admin,
            ativo=True
        )
        
        db.add(novo_usuario)
        await db.commit()
        await db.refresh(novo_usuario)
        
        return novo_usuario
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar usuário: {str(e)}")

@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def atualizar_usuario(usuario_id: str, usuario: UsuarioUpdate, db: AsyncSession = Depends(get_db_session)):
    """Atualiza um usuário existente."""
    try:
        # Buscar usuário existente
        result = await db.execute(select(User).where(User.id == usuario_id))
        usuario_existente = result.scalar_one_or_none()
        
        if not usuario_existente:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        # Atualizar campos
        update_data = {}
        if usuario.nome is not None:
            update_data['nome'] = usuario.nome
        if usuario.usuario is not None:
            update_data['usuario'] = usuario.usuario
        if usuario.senha is not None:
            update_data['senha_hash'] = usuario.senha
        if usuario.is_admin is not None:
            update_data['is_admin'] = usuario.is_admin
        if hasattr(usuario, 'ativo') and usuario.ativo is not None:
            update_data['ativo'] = usuario.ativo
        
        update_data['updated_at'] = datetime.utcnow()
        
        if update_data:
            await db.execute(
                update(User).where(User.id == usuario_id).values(**update_data)
            )
        await db.commit()
        
        # Retornar usuário atualizado
        result = await db.execute(select(User).where(User.id == usuario_id))
        return result.scalar_one()
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar usuário: {str(e)}")

@router.delete("/{usuario_id}")
async def deletar_usuario(usuario_id: str, db: AsyncSession = Depends(get_db_session)):
    """Deleta um usuário (soft delete)."""
    try:
        # Buscar usuário existente
        result = await db.execute(select(User).where(User.id == usuario_id))
        usuario_existente = result.scalar_one_or_none()
        
        if not usuario_existente:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        # Soft delete
        await db.execute(
            update(User)
            .where(User.id == usuario_id)
            .values(ativo=False, updated_at=datetime.utcnow())
        )
        await db.commit()
        
        return {"message": "Usuário deletado com sucesso"}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao deletar usuário: {str(e)}")

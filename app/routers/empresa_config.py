from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db_session
from app.db.models import EmpresaConfig
from app.core.deps import get_current_admin_user, get_tenant_id
import uuid

router = APIRouter(prefix="/api/config", tags=["configuracao"])


async def _get_singleton_config(db: AsyncSession, tenant_id: uuid.UUID) -> EmpresaConfig:
  """Retorna o registro único de configuração de empresa por tenant, criando se não existir."""
  result = await db.execute(
    select(EmpresaConfig).where(EmpresaConfig.tenant_id == tenant_id)
  )
  cfg = result.scalar_one_or_none()
  if cfg is None:
    cfg = EmpresaConfig(tenant_id=tenant_id)
    db.add(cfg)
    await db.commit()
    await db.refresh(cfg)
  return cfg


@router.get("/empresa")
async def get_empresa_config(
  db: AsyncSession = Depends(get_db_session),
  tenant_id: uuid.UUID = Depends(get_tenant_id),
):
  cfg = await _get_singleton_config(db, tenant_id)
  return {
    "id": str(cfg.id),
    "nome": cfg.nome,
    "nuit": cfg.nuit,
    "telefone": cfg.telefone,
    "email": cfg.email,
    "endereco": cfg.endereco,
    "logo_path": cfg.logo_path,
  }


@router.put("/empresa")
async def update_empresa_config(
  payload: dict,
  db: AsyncSession = Depends(get_db_session),
  tenant_id: uuid.UUID = Depends(get_tenant_id),
  user=Depends(get_current_admin_user),
):
  cfg = await _get_singleton_config(db, tenant_id)

  cfg.nome = payload.get("nome", cfg.nome)
  cfg.nuit = payload.get("nuit", cfg.nuit)
  cfg.telefone = payload.get("telefone", cfg.telefone)
  cfg.email = payload.get("email", cfg.email)
  cfg.endereco = payload.get("endereco", cfg.endereco)

  db.add(cfg)
  await db.commit()
  await db.refresh(cfg)

  return {
    "id": str(cfg.id),
    "nome": cfg.nome,
    "nuit": cfg.nuit,
    "telefone": cfg.telefone,
    "email": cfg.email,
    "endereco": cfg.endereco,
    "logo_path": cfg.logo_path,
  }


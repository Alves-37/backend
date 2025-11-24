from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from app.db.database import get_db_session
from app.db.models import Venda, ItemVenda
from app.core.deps import get_current_admin_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/reset-dados")
async def reset_dados_online(
  db: AsyncSession = Depends(get_db_session),
  user=Depends(get_current_admin_user),
):
  """Reseta dados operacionais online (apenas vendas), preservando produtos, clientes e usuários.

  Somente administradores podem executar esta operação.
  """
  # Apagar itens de venda primeiro devido a foreign key
  await db.execute(delete(ItemVenda))
  await db.execute(delete(Venda))
  await db.commit()
  return {"status": "ok", "message": "Dados de vendas online foram resetados."}

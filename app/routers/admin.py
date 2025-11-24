from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.database import get_db_session
from app.core.deps import get_current_admin_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/reset-dados")
async def reset_dados_online(
    db: AsyncSession = Depends(get_db_session),
    user=Depends(get_current_admin_user),
):
    """Reseta TODO o banco de dados online, apagando todos os registros.

    Somente administradores podem executar esta operação.
    """
    tables_to_truncate = [
        "itens_venda",
        "vendas",
        "produtos",
        "clientes",
        "users",
        "empresa_config",
    ]

    try:
        # Desabilita verificação de FKs para permitir TRUNCATE em cascata
        await db.execute(text("SET session_replication_role = 'replica';"))

        for table in tables_to_truncate:
            await db.execute(
                text(f'TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;')
            )

        await db.execute(text("SET session_replication_role = 'origin';"))
        await db.commit()

        return {
            "status": "ok",
            "message": "Banco de dados online foi totalmente resetado (tabelas principais esvaziadas).",
        }
    except Exception as e:
        await db.execute(text("SET session_replication_role = 'origin';"))
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao resetar banco de dados: {str(e)}",
        )

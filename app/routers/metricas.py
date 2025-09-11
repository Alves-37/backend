from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, date

from ..db.database import get_db_session
from ..db.models import Venda, ItemVenda

router = APIRouter(prefix="/api/metricas", tags=["metricas"]) 

@router.get("/vendas-dia")
async def vendas_dia(db: AsyncSession = Depends(get_db_session)):
    """Retorna o total de vendas (não canceladas) do dia atual."""
    hoje = date.today()
    stmt = select(func.coalesce(func.sum(Venda.total), 0.0)).where(
        Venda.cancelada == False,
        func.date(Venda.created_at) == hoje
    )
    # Tentativa principal + 1 retry leve
    for attempt in range(2):
        try:
            result = await db.execute(stmt)
            total = float(result.scalar() or 0.0)
            return {"data": str(hoje), "total": total}
        except Exception as e:
            if attempt == 0:
                continue
            # Fallback gracioso: retornar 0 com status 200
            return {"data": str(hoje), "total": 0.0, "warning": "fallback"}

@router.get("/vendas-mes")
async def vendas_mes(db: AsyncSession = Depends(get_db_session)):
    """Retorna o total de vendas (não canceladas) do mês atual."""
    try:
        agora = datetime.utcnow()
        primeiro_dia = date(agora.year, agora.month, 1)
        # próximo mês
        proximo_mes = date(agora.year + (1 if agora.month == 12 else 0), 1 if agora.month == 12 else agora.month + 1, 1)
        # Intervalo [primeiro_dia, proximo_mes)
        stmt = select(func.coalesce(func.sum(Venda.total), 0.0)).where(
            Venda.cancelada == False,
            Venda.created_at >= primeiro_dia,
            Venda.created_at < proximo_mes
        )
        for attempt in range(2):
            try:
                result = await db.execute(stmt)
                total = float(result.scalar() or 0.0)
                return {"ano_mes": primeiro_dia.strftime("%Y-%m"), "total": total}
            except Exception:
                if attempt == 0:
                    continue
                return {"ano_mes": primeiro_dia.strftime("%Y-%m"), "total": 0.0, "warning": "fallback"}
    except Exception:
        return {"ano_mes": datetime.utcnow().strftime("%Y-%m"), "total": 0.0, "warning": "fallback"}

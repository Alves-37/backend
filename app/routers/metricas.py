from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, date
import asyncio

from ..db.database import get_db_session
from ..db.models import Venda, ItemVenda

router = APIRouter(prefix="/api/metricas", tags=["metricas"]) 

# Cache em memória simples para suavizar cold start (TTL curto)
_metrics_cache = {
    "vendas_dia": {"value": None, "ts": 0.0},
    "vendas_mes": {"value": None, "ts": 0.0},
}
_cache_ttl_seconds = 15
_cache_lock = asyncio.Lock()

def _now_ts() -> float:
    return datetime.utcnow().timestamp()

@router.get("/vendas-dia")
async def vendas_dia(db: AsyncSession = Depends(get_db_session)):
    """Retorna o total de vendas (não canceladas) do dia atual."""
    hoje = date.today()
    # Servir cache se fresco
    async with _cache_lock:
        if _metrics_cache["vendas_dia"]["value"] is not None and (_now_ts() - _metrics_cache["vendas_dia"]["ts"]) < _cache_ttl_seconds:
            return {"data": str(hoje), "total": float(_metrics_cache["vendas_dia"]["value"]) }

    stmt = select(func.coalesce(func.sum(Venda.total), 0.0)).where(
        Venda.cancelada == False,
        func.date(Venda.created_at) == hoje
    )
    # Tentativa principal + 1 retry leve
    for attempt in range(2):
        try:
            result = await db.execute(stmt)
            total = float(result.scalar() or 0.0)
            async with _cache_lock:
                _metrics_cache["vendas_dia"] = {"value": total, "ts": _now_ts()}
            return {"data": str(hoje), "total": total}
        except Exception:
            if attempt == 0:
                await asyncio.sleep(0.2)
                continue
            # Fallback: servir cache antigo se existir, senão 0
            async with _cache_lock:
                cached = _metrics_cache["vendas_dia"]["value"]
            return {"data": str(hoje), "total": float(cached or 0.0), "warning": "cached"}

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
        # Servir cache se fresco
        async with _cache_lock:
            if _metrics_cache["vendas_mes"]["value"] is not None and (_now_ts() - _metrics_cache["vendas_mes"]["ts"]) < _cache_ttl_seconds:
                return {"ano_mes": primeiro_dia.strftime("%Y-%m"), "total": float(_metrics_cache["vendas_mes"]["value"]) }

        for attempt in range(2):
            try:
                result = await db.execute(stmt)
                total = float(result.scalar() or 0.0)
                async with _cache_lock:
                    _metrics_cache["vendas_mes"] = {"value": total, "ts": _now_ts()}
                return {"ano_mes": primeiro_dia.strftime("%Y-%m"), "total": total}
            except Exception:
                if attempt == 0:
                    await asyncio.sleep(0.2)
                    continue
                async with _cache_lock:
                    cached = _metrics_cache["vendas_mes"]["value"]
                return {"ano_mes": primeiro_dia.strftime("%Y-%m"), "total": float(cached or 0.0), "warning": "cached"}
    except Exception:
        # Falha inesperada: retornar cache ou zero
        async with _cache_lock:
            cached = _metrics_cache["vendas_mes"]["value"]
        return {"ano_mes": datetime.utcnow().strftime("%Y-%m"), "total": float(cached or 0.0), "warning": "cached"}

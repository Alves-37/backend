from fastapi import APIRouter, HTTPException, Depends
from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, date
import asyncio

from ..db.database import get_db_session
from ..db.models import Venda, ItemVenda, Produto

router = APIRouter(prefix="/api/metricas", tags=["metricas"]) 

# Cache em memória simples para suavizar cold start (TTL curto)
_metrics_cache = {
    "vendas_dia": {"value": None, "ts": 0.0},
    "vendas_mes": {"value": None, "ts": 0.0},
    "estoque_valores": {"value": None, "ts": 0.0},
}
_cache_ttl_seconds = 15
_cache_lock = asyncio.Lock()

def _now_ts() -> float:
    return datetime.utcnow().timestamp()

@router.get("/vendas-dia")
async def vendas_dia(
    data: str | None = Query(default=None, description="Data no formato YYYY-MM-DD (timezone do cliente)"),
    db: AsyncSession = Depends(get_db_session)
):
    """Retorna o total de vendas (não canceladas) do dia informado (ou dia atual)."""
    # Data alvo: usar a recebida do cliente ou o dia do servidor
    try:
        alvo = date.fromisoformat(data) if data else date.today()
    except Exception:
        alvo = date.today()
    # Servir cache se fresco
    async with _cache_lock:
        if _metrics_cache["vendas_dia"]["value"] is not None and (_now_ts() - _metrics_cache["vendas_dia"]["ts"]) < _cache_ttl_seconds:
            return {"data": str(alvo), "total": float(_metrics_cache["vendas_dia"]["value"]) }

    stmt = select(func.coalesce(func.sum(Venda.total), 0.0)).where(
        Venda.cancelada == False,
        func.date(Venda.created_at) == alvo
    )
    # Tentativa principal + 1 retry leve
    for attempt in range(2):
        try:
            result = await db.execute(stmt)
            total = float(result.scalar() or 0.0)
            async with _cache_lock:
                _metrics_cache["vendas_dia"] = {"value": total, "ts": _now_ts()}
            return {"data": str(alvo), "total": total}
        except Exception:
            if attempt == 0:
                await asyncio.sleep(0.2)
                continue
            # Fallback: servir cache antigo se existir, senão 0
            async with _cache_lock:
                cached = _metrics_cache["vendas_dia"]["value"]
            return {"data": str(alvo), "total": float(cached or 0.0), "warning": "cached"}

@router.get("/vendas-mes")
async def vendas_mes(
    ano_mes: str | None = Query(default=None, description="Ano-mês no formato YYYY-MM (timezone do cliente)"),
    db: AsyncSession = Depends(get_db_session)
):
    """Retorna o total de vendas (não canceladas) do mês informado (ou mês atual)."""
    try:
        if ano_mes:
            try:
                ano, mes = map(int, ano_mes.split("-"))
                primeiro_dia = date(ano, mes, 1)
            except Exception:
                dnow = datetime.utcnow()
                primeiro_dia = date(dnow.year, dnow.month, 1)
        else:
            dnow = datetime.utcnow()
            primeiro_dia = date(dnow.year, dnow.month, 1)
        # próximo mês
        proximo_mes = date(
            primeiro_dia.year + (1 if primeiro_dia.month == 12 else 0),
            1 if primeiro_dia.month == 12 else primeiro_dia.month + 1,
            1
        )
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

@router.get("/estoque-valores")
async def estoque_valores(db: AsyncSession = Depends(get_db_session)):
    """Retorna o valor total do estoque (custo) e o valor potencial (preço de venda).
    - valor_estoque: soma de preco_custo * estoque
    - valor_potencial: soma de preco_venda * estoque
    Considera apenas produtos ativos.
    """
    # Servir cache se fresco
    async with _cache_lock:
        if _metrics_cache["estoque_valores"]["value"] is not None and (_now_ts() - _metrics_cache["estoque_valores"]["ts"]) < _cache_ttl_seconds:
            cached = _metrics_cache["estoque_valores"]["value"]
            return {
                "valor_estoque": float(cached["valor_estoque"]),
                "valor_potencial": float(cached["valor_potencial"])
            }

    stmt = select(
        func.coalesce(func.sum(Produto.preco_custo * Produto.estoque), 0.0),
        func.coalesce(func.sum(Produto.preco_venda * Produto.estoque), 0.0)
    ).where(Produto.ativo == True)

    try:
        result = await db.execute(stmt)
        valor_custo, valor_venda = result.one()
        payload = {
            "valor_estoque": float(valor_custo or 0.0),
            "valor_potencial": float(valor_venda or 0.0)
        }
        async with _cache_lock:
            _metrics_cache["estoque_valores"] = {"value": payload, "ts": _now_ts()}
        return payload
    except Exception as e:
        # Fallback: servir cache antigo se existir, senão zeros
        async with _cache_lock:
            cached = _metrics_cache["estoque_valores"]["value"]
        if cached is not None:
            return {"valor_estoque": float(cached.get("valor_estoque", 0.0)), "valor_potencial": float(cached.get("valor_potencial", 0.0)), "warning": "cached"}
        raise HTTPException(status_code=500, detail=f"Erro ao calcular valores de estoque: {str(e)}")

from fastapi import APIRouter, HTTPException, Depends
from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from datetime import datetime, date
import asyncio

from ..db.database import get_db_session
from ..db.models import Venda, ItemVenda, Produto

router = APIRouter(prefix="/api/metricas", tags=["metricas"]) 

# Cache em memória simples para suavizar cold start (TTL curto)
_metrics_cache = {
    "vendas_dia": {"value": None, "ts": 0.0},
    "vendas_mes": {"value": None, "ts": 0.0},
    "estoque": {"value": None, "ts": 0.0},
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


@router.get("/estoque")
async def estoque_metricas(db: AsyncSession = Depends(get_db_session)):
    """
    Retorna métricas de estoque calculadas no servidor para garantir paridade entre clientes:
    - valor_estoque: SUM(estoque * preco_custo) de produtos ativos com estoque > 0
    - valor_potencial: SUM(estoque * preco_venda) idem
    - lucro_potencial: valor_potencial - valor_estoque
    - baixo_estoque: contagem de produtos ativos considerados baixo estoque
        Regra: se estoque_minimo > 0, usa estoque <= estoque_minimo; senão, usa estoque <= 5
    """
    # Servir cache se estiver fresco
    async with _cache_lock:
        if _metrics_cache["estoque"]["value"] is not None and (_now_ts() - _metrics_cache["estoque"]["ts"]) < _cache_ttl_seconds:
            return _metrics_cache["estoque"]["value"]

    # Expressões
    valor_custo_expr = func.coalesce(func.sum(Produto.estoque * Produto.preco_custo), 0.0)
    valor_venda_expr = func.coalesce(func.sum(Produto.estoque * Produto.preco_venda), 0.0)

    cond_min_def = (
        (Produto.estoque_minimo != None)
        & (Produto.estoque_minimo > 0)
        & (Produto.estoque <= Produto.estoque_minimo)
    )
    cond_sem_min = (
        ((Produto.estoque_minimo == None) | (Produto.estoque_minimo == 0))
        & (Produto.estoque <= 5)
    )
    cond_baixo = cond_min_def | cond_sem_min
    baixo_estoque_expr = func.coalesce(
        func.sum(
            case(
                (cond_baixo, 1),
                else_=0,
            )
        ),
        0,
    )

    stmt = (
        select(valor_custo_expr.label("valor_custo"), valor_venda_expr.label("valor_venda"), baixo_estoque_expr.label("baixo_estoque"))
        .where(Produto.ativo == True, Produto.estoque > 0)
    )

    try:
        result = await db.execute(stmt)
        row = result.first()
        valor_estoque = float(row.valor_custo if row and row.valor_custo is not None else 0.0)
        valor_potencial = float(row.valor_venda if row and row.valor_venda is not None else 0.0)
        baixo_estoque = int(row.baixo_estoque if row and row.baixo_estoque is not None else 0)

        payload = {
            "valor_estoque": valor_estoque,
            "valor_potencial": valor_potencial,
            "lucro_potencial": float(valor_potencial - valor_estoque),
            "baixo_estoque": baixo_estoque,
        }
        async with _cache_lock:
            _metrics_cache["estoque"] = {"value": payload, "ts": _now_ts()}
        return payload
    except Exception as e:
        # Fallback para cache/zeros
        async with _cache_lock:
            cached = _metrics_cache["estoque"]["value"]
        return cached or {"valor_estoque": 0.0, "valor_potencial": 0.0, "lucro_potencial": 0.0, "baixo_estoque": 0}

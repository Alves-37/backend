from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_tenant_id
from app.db.database import get_db_session
from app.db.models import Tenant

router = APIRouter(prefix="/api/categorias", tags=["categorias"])


class CategoriaOut(BaseModel):
    id: int
    nome: str
    descricao: str | None = None


# Lista padrão alinhada com o cliente PDV3 (database.py),
# mantendo os mesmos IDs, nomes e descrições.
CATEGORIAS_PADRAO: List[CategoriaOut] = [
    CategoriaOut(id=1, nome="Alimentos", descricao="Produtos alimentícios em geral"),
    CategoriaOut(id=2, nome="Bebidas", descricao="Bebidas em geral"),
    CategoriaOut(id=3, nome="Limpeza", descricao="Produtos de limpeza"),
    CategoriaOut(id=4, nome="Higiene", descricao="Produtos de higiene pessoal"),
    CategoriaOut(id=5, nome="Congelados", descricao="Produtos congelados"),
    CategoriaOut(id=6, nome="Mercearia", descricao="Produtos de mercearia em geral"),
    CategoriaOut(id=7, nome="Padaria", descricao="Produtos de padaria"),
    CategoriaOut(id=8, nome="Hortifruti", descricao="Frutas, legumes e verduras"),
    CategoriaOut(id=9, nome="Açougue", descricao="Carnes em geral"),
    CategoriaOut(id=10, nome="Laticínios", descricao="Leite e derivados"),
    CategoriaOut(id=11, nome="Outros", descricao="Outros tipos de produtos"),

    # Serviços gerais (sem controle de estoque)
]


CATEGORIAS_RESTAURANTE: List[CategoriaOut] = [
    CategoriaOut(id=1, nome="Pratos", descricao="Pratos principais"),
    CategoriaOut(id=2, nome="Bebidas", descricao="Bebidas"),
    CategoriaOut(id=3, nome="Entradas", descricao="Entradas"),
    CategoriaOut(id=4, nome="Sobremesas", descricao="Sobremesas"),
    CategoriaOut(id=5, nome="Acompanhamentos", descricao="Acompanhamentos"),
    CategoriaOut(id=6, nome="Lanches", descricao="Lanches"),
    CategoriaOut(id=7, nome="Pizzas", descricao="Pizzas"),
    CategoriaOut(id=8, nome="Saladas", descricao="Saladas"),
    CategoriaOut(id=9, nome="Grelhados", descricao="Grelhados"),
    CategoriaOut(id=10, nome="Massas", descricao="Massas"),
    CategoriaOut(id=11, nome="Outros", descricao="Outros"),
]


@router.get("/", response_model=List[CategoriaOut])
async def listar_categorias(
    db: AsyncSession = Depends(get_db_session),
    tenant_id=Depends(get_tenant_id),
) -> List[CategoriaOut]:
    """
    Lista as categorias de produtos.

    Observação: Implementação sem dependência de banco para manter compatibilidade
    imediata com o cliente. Futuramente, pode ser migrado para uma tabela real
    quando o modelo `Categoria` existir no PostgreSQL.
    """
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    tipo = (getattr(tenant, "tipo_negocio", None) if tenant else None) or "mercearia"
    if str(tipo).lower() == "restaurante":
        return CATEGORIAS_RESTAURANTE
    return CATEGORIAS_PADRAO

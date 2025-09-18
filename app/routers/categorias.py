from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/categorias", tags=["categorias"])


class CategoriaOut(BaseModel):
    id: int
    nome: str
    descricao: str | None = None


# Lista padrão alinhada ao cliente PDV3 (SQLite)
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
]


@router.get("/", response_model=List[CategoriaOut])
async def listar_categorias() -> List[CategoriaOut]:
    """
    Lista as categorias de produtos.

    Observação: Implementação sem dependência de banco para manter compatibilidade
    imediata com o cliente. Futuramente, pode ser migrado para uma tabela real
    quando o modelo `Categoria` existir no PostgreSQL.
    """
    return CATEGORIAS_PADRAO

#!/usr/bin/env python3
"""
Script de teste para POST /api/vendas/ no backend.

- Cria/garante um produto de teste e obtém seu UUID
- Envia duas vendas:
  1) Venda normal por unidade
  2) Venda por peso (peso_kg)
- Valida respostas (200/201) e imprime resultados

Uso:
  python backend/scripts/test_post_venda.py

Pré-requisitos:
  - BACKEND_URL no .env ou variável de ambiente (ex.: http://localhost:8000)
    ou editável no bloco de configuração abaixo.
"""
import os
import json
import httpx
from uuid import UUID
from pathlib import Path

def resolve_api_base() -> str:
    # 1) Env var
    url = os.getenv("BACKEND_URL")
    # 2) Fallback to pdv3/config.json server_url
    if not url:
        try:
            cfg_path = Path(__file__).resolve().parents[2] / 'pdv3' / 'config.json'
            if cfg_path.exists():
                conf = json.loads(cfg_path.read_text(encoding='utf-8'))
                url = conf.get('server_url')
        except Exception:
            url = None
    # 3) Default local
    if not url:
        url = "http://localhost:8000"
    base = url.rstrip('/')
    # If already endswith /api, remove it to avoid double /api
    if base.endswith('/api'):
        base = base[:-4]
    return base + '/api'

API_BASE = resolve_api_base()

PROD_TESTE = {
    "codigo": "TEST-POST-001",
    "nome": "Produto Teste Script",
    "preco_custo": 50.0,
    "preco_venda": 70.0,
    "estoque": 5.0,
    "ativo": True,
    "venda_por_peso": False,
}

PROD_PESO = {
    "codigo": "TEST-PESO-001",
    "nome": "Produto Peso Script",
    "preco_custo": 100.0,
    "preco_venda": 150.0,
    "estoque": 10.0,
    "ativo": True,
    "venda_por_peso": True,
}


def ensure_product(client: httpx.Client, prod: dict) -> str:
    # Tenta localizar por código
    r = client.get(f"{API_BASE}/produtos/")
    r.raise_for_status()
    for p in r.json() or []:
        if p.get('codigo') == prod['codigo']:
            return p['id']
    # Não achou, garantir categoria e criar
    cat_id = ensure_category(client)
    prod_payload = dict(prod)
    prod_payload.setdefault('categoria_id', cat_id)
    r = client.post(f"{API_BASE}/produtos/", json=prod_payload)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Falha ao criar produto {prod['codigo']}: {r.status_code} {r.text}")
    return r.json()['id']


def ensure_category(client: httpx.Client) -> int:
    """Garante a existência de uma categoria e retorna seu id (int)."""
    # Tentar listar categorias
    try:
        r = client.get(f"{API_BASE}/categorias/")
        if r.status_code == 200:
            cats = r.json() or []
            if isinstance(cats, list) and len(cats) > 0:
                cid = cats[0].get('id')
                if isinstance(cid, int):
                    return cid
    except Exception:
        pass
    # Criar uma categoria padrão
    payload = {"nome": "Script Teste", "descricao": "Criada pelo test_post_venda"}
    r = client.post(f"{API_BASE}/categorias/", json=payload)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Falha ao criar categoria: {r.status_code} {r.text}")
    data = r.json() or {}
    cid = data.get('id')
    if not isinstance(cid, int):
        raise RuntimeError("Resposta de categoria inválida (sem id inteiro)")
    return cid


def post_venda_unidade(client: httpx.Client, produto_id: str):
    payload = {
        "total": 70.0,
        "desconto": 0.0,
        "forma_pagamento": "Dinheiro",
        "itens": [
            {
                "produto_id": produto_id,
                "quantidade": 1,
                "preco_unitario": 70.0,
                "subtotal": 70.0
            }
        ]
    }
    print("\n[TESTE] Enviando venda por unidade...")
    r = client.post(f"{API_BASE}/vendas/", json=payload)
    print(f"HTTP {r.status_code}: {r.text}")
    r.raise_for_status()
    return r.json()


def post_venda_peso(client: httpx.Client, produto_id: str):
    # vende 0.667 kg a 150, subtotal 100.05 (arredonda no subtotal se necessário)
    peso_kg = 0.667
    preco = 150.0
    subtotal = round(peso_kg * preco, 2)
    payload = {
        "total": subtotal,
        "desconto": 0.0,
        "forma_pagamento": "Dinheiro",
        "itens": [
            {
                "produto_id": produto_id,
                "quantidade": 1,
                "peso_kg": peso_kg,
                "preco_unitario": preco,
                "subtotal": subtotal
            }
        ]
    }
    print("\n[TESTE] Enviando venda por peso...")
    r = client.post(f"{API_BASE}/vendas/", json=payload)
    print(f"HTTP {r.status_code}: {r.text}")
    r.raise_for_status()
    return r.json()


def main():
    print(f"API: {API_BASE}")
    with httpx.Client(timeout=15.0) as client:
        # Garantir produtos
        pid_un = ensure_product(client, PROD_TESTE)
        pid_peso = ensure_product(client, PROD_PESO)
        # Validar UUIDs
        _ = UUID(pid_un)
        _ = UUID(pid_peso)
        print(f"Produto unidade id={pid_un}")
        print(f"Produto peso id={pid_peso}")

        # Vendas
        v1 = post_venda_unidade(client, pid_un)
        v2 = post_venda_peso(client, pid_peso)

        print("\n[OK] Teste concluído.")
        print(f"Venda unidade ID: {v1.get('id')}")
        print(f"Venda por peso ID: {v2.get('id')}")


if __name__ == "__main__":
    main()

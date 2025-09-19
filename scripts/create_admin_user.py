import asyncio
import argparse
import os
import sys
from sqlalchemy.future import select

# Ensure project root is on sys.path so 'app' can be imported when running this script directly
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.db.session import AsyncSessionLocal, engine
from app.db.base import DeclarativeBase
from app.db.models import User
from app.core.security import get_password_hash


async def ensure_tables():
    async with engine.begin() as conn:
        await conn.run_sync(DeclarativeBase.metadata.create_all)


async def create_or_update_admin(nome: str, usuario: str, senha: str, is_admin: bool = True, ativo: bool = True):
    await ensure_tables()
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.usuario == usuario))
        user = result.scalar_one_or_none()
        if user:
            # Update password and flags if necessary
            user.nome = nome
            user.senha_hash = get_password_hash(senha)
            user.is_admin = is_admin
            user.ativo = ativo
            action = "updated"
        else:
            user = User(
                nome=nome,
                usuario=usuario,
                senha_hash=get_password_hash(senha),
                is_admin=is_admin,
                ativo=ativo,
            )
            session.add(user)
            action = "created"
        await session.commit()
        # Refresh to get IDs
        await session.refresh(user)
        print(f"User {action}: id={user.id}, usuario={user.usuario}, is_admin={user.is_admin}, ativo={user.ativo}")


def parse_args():
    parser = argparse.ArgumentParser(description="Create or update an admin user")
    parser.add_argument("--nome", required=True, help="Nome do usuário")
    parser.add_argument("--usuario", required=True, help="Login do usuário")
    parser.add_argument("--senha", required=True, help="Senha em texto plano (será hasheada)")
    parser.add_argument("--inativo", action="store_true", help="Marcar usuário como inativo")
    parser.add_argument("--no-admin", action="store_true", help="Não marcar como admin")
    return parser.parse_args()


async def amain():
    args = parse_args()
    await create_or_update_admin(
        nome=args.nome,
        usuario=args.usuario,
        senha=args.senha,
        is_admin=not args.no_admin,
        ativo=not args.inativo,
    )


if __name__ == "__main__":
    asyncio.run(amain())

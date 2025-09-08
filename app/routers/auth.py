from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import AsyncSessionLocal
from app.db.models import User
from app.schemas.auth import Token
from app.core.security import create_access_token, verify_password

router = APIRouter()

async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session

@router.post("/auth/login", response_model=Token, tags=["Auth"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db_session)):
    """Authenticate user and return a JWT access token."""
    result = await db.execute(select(User).where(User.usuario == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.usuario, "user_id": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

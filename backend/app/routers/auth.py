from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Usuario
from app.schemas.schemas import (
    LoginRequest, Token, UsuarioCreate, UsuarioResponse, PasswordChangeRequest,
)
from app.services.auth_service import (
    verificar_senha, gerar_hash_senha, criar_token_acesso,
    get_current_user, require_admin,
)

router = APIRouter(prefix="/auth", tags=["Autenticacao"])


@router.post("/login", response_model=Token)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.username == data.username).first()
    if not user or not verificar_senha(data.password, user.senha_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario ou senha invalidos")
    if not user.ativo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Conta desativada")
    token = criar_token_acesso({"sub": user.username, "admin": user.is_admin})
    return {"access_token": token}


@router.post("/alterar-senha")
def alterar_senha(data: PasswordChangeRequest, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verificar_senha(data.old_password, user.senha_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Senha atual incorreta")
    user.senha_hash = gerar_hash_senha(data.new_password)
    db.commit()
    return {"mensagem": "Senha alterada com sucesso"}


@router.post("/usuarios", response_model=UsuarioResponse, dependencies=[Depends(require_admin)])
def criar_usuario(data: UsuarioCreate, db: Session = Depends(get_db)):
    existing = db.query(Usuario).filter(
        (Usuario.username == data.username) | (Usuario.email == data.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Usuario ou email ja existe")
    user = Usuario(
        username=data.username,
        email=data.email,
        nome_completo=data.nome_completo,
        senha_hash=gerar_hash_senha(data.password),
        is_externo=data.is_externo,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=UsuarioResponse)
def me(user: Usuario = Depends(get_current_user)):
    return user


@router.get("/usuarios", response_model=list[UsuarioResponse], dependencies=[Depends(require_admin)])
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(Usuario).all()

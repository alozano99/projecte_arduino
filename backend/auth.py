from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

# Config
SECRET_KEY = "clauultrasecreta123"  # ⚠️ En producció guarda això com variable d'entorn
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Hash de contrasenyes
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verificar_contrasenya(plain, hashed):
    return pwd_context.verify(plain, hashed)

def hash_contrasenya(password):
    return pwd_context.hash(password)

def crear_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def llegir_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

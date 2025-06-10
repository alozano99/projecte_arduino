from database import SessionLocal, User, RolEnum
from passlib.context import CryptContext

# Contexto de hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Crear sesión de base de datos
db = SessionLocal()

# Lista de usuarios a insertar
usuarios = [
    User(
        nom="Alex",
        uid="7318FE12",
        password_hash=pwd_context.hash("alex123"),
        rol=RolEnum.alumne
    ),
    User(
        nom="Profesor",
        uid="63F29ED",
        password_hash=pwd_context.hash("profesor123"),
        rol=RolEnum.professor
    ),
    User(
        nom="Admin",
        uid="",
        password_hash=pwd_context.hash("admin123"),
        rol=RolEnum.admin
    )
]

# Añadir todos y guardar
db.add_all(usuarios)
db.commit()
db.close()

print("✅ Usuarios creados correctamente.")

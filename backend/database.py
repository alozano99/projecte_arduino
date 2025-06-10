from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Time, Boolean
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import enum

Base = declarative_base()

# Enum para roles
class RolEnum(str, enum.Enum):
    alumne = "alumne"
    professor = "professor"
    admin = "admin"

# Tabla de usuarios
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    uid = Column(String, nullable=True)  # RFID opcional
    password_hash = Column(String, nullable=False)
    rol = Column(SqlEnum(RolEnum, name="rolenum"), nullable=False)
    horaris = relationship("Horari", back_populates="usuari", cascade="all, delete-orphan")

# Tabla de aules
class Aula(Base):
    __tablename__ = "aules"
    id = Column(Integer, primary_key=True)
    nom = Column(String, nullable=False, unique=True)
    pis = Column(String, nullable=True)
    edifici = Column(String, nullable=True)
    horaris = relationship("Horari", back_populates="aula_ref")

# Tabla de horaris
class Horari(Base):
    __tablename__ = "horaris"
    id = Column(Integer, primary_key=True)
    dia_setmana = Column(String, nullable=False)
    hora_inici = Column(Time, nullable=False)
    hora_fi = Column(Time, nullable=False)

    aula_id = Column(Integer, ForeignKey("aules.id"))
    aula_ref = relationship("Aula", back_populates="horaris")

    usuari_id = Column(Integer, ForeignKey("users.id"))
    usuari = relationship("User", back_populates="horaris")

# Tabla de fichajes
class Fichaje(Base):
    __tablename__ = "fichajes"
    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")
    retard = Column(Boolean, nullable=True)

# Configuración de base de datos
engine = create_engine("sqlite:///fichajes.db")
SessionLocal = sessionmaker(bind=engine)

# Crear tablas
Base.metadata.create_all(bind=engine)

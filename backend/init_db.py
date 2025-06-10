from database import Base, engine

# Crear todas las tablas
Base.metadata.create_all(bind=engine)

print("✅ Base de datos inicializada.")
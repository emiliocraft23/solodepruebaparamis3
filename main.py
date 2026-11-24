from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import List
from fastapi.middleware.cors import CORSMiddleware
# 1. CONFIGURACIÓN DE LA BASE DE DATOS (SQL Server Local)
# Usamos el driver ODBC 17 por defecto en Windows.
DATABASE_URL = "mssql+pyodbc://@localhost/EcoRAEE_Fase2?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session

# 2. MODELO DE DATOS (Mapeo a tu tabla SQL)
# SQLModel soporta claves primarias compuestas (id_lote, secuencia_dispositivo)
class Dispositivo(SQLModel, table=True):
    __tablename__ = "Dispositivo"
    
    id_lote: int = Field(primary_key=True)
    secuencia_dispositivo: int = Field(primary_key=True)
    num_serie: str
    peso_kg: float
    condicion_actual: str = Field(default="Registrado")
    id_categoria: int
    id_marca: int

# 3. INICIALIZACIÓN DE FASTAPI
app = FastAPI(
    title="EcoRAEE Cloud API", 
    description="MVP Backend para la gestión de residuos electrónicos",
    version="1.0.0"
)
# AÑADIR ESTO PARA PERMITIR LA CONEXIÓN DESDE REACT
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción se pone la URL exacta de React, pero para local usamos "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 4. ENDPOINTS CRUD PARA DISPOSITIVOS

@app.get("/dispositivos/", response_model=List[Dispositivo])
def obtener_dispositivos(session: Session = Depends(get_session)):
    """Obtiene la lista de todos los dispositivos registrados."""
    dispositivos = session.exec(select(Dispositivo)).all()
    return dispositivos

@app.get("/dispositivos/{id_lote}/{secuencia_dispositivo}", response_model=Dispositivo)
def obtener_un_dispositivo(id_lote: int, secuencia_dispositivo: int, session: Session = Depends(get_session)):
    """Busca un dispositivo específico por su PK compuesta."""
    dispositivo = session.get(Dispositivo, (id_lote, secuencia_dispositivo))
    if not dispositivo:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    return dispositivo

@app.post("/dispositivos/", response_model=Dispositivo)
def crear_dispositivo(dispositivo: Dispositivo, session: Session = Depends(get_session)):
    """Registra un nuevo dispositivo en el lote."""
    # Validación básica (El CHECK de SQL Server también te protegerá)
    if dispositivo.peso_kg <= 0:
        raise HTTPException(status_code=400, detail="El peso debe ser mayor a 0")
        
    session.add(dispositivo)
    session.commit()
    session.refresh(dispositivo)
    return dispositivo

# Creacion de CRUD de borrado de alguna objeto
@app.delete("/dispositivos/{id_lote}/{secuencia_dispositivo}")
def eliminar_dispositivo(id_lote: int, secuencia_dispositivo: int, session: Session = Depends(get_session)):
    """Elimina un dispositivo de la base de datos."""
    dispositivo = session.get(Dispositivo, (id_lote, secuencia_dispositivo))
    if not dispositivo:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    
    session.delete(dispositivo)
    session.commit()
    return {"mensaje": "Dispositivo eliminado correctamente"}
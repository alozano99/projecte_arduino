from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.sessions import SessionMiddleware

from database import Fichaje, SessionLocal, User, Horari
from datetime import datetime, timezone, timedelta
from auth import verificar_contrasenya, crear_token, llegir_token
from auth_web import router as auth_web_router
from views_web import router as views_router
from sqlalchemy.orm import joinedload, Session
from pydantic import BaseModel
from auth_utils import verificar_rol_permis


# Inicialización FastAPI
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="super-clau-secreta")

# Templates
templates = Jinja2Templates(directory="templates")

# Routers externos
app.include_router(auth_web_router)
app.include_router(views_router)

# ---------------------- API: Fichaje RFID ----------------------
@app.post("/api/fichaje")
async def recibir_fichaje(request: Request):
    try:
        data = await request.json()
        uid = data.get("uid")

        if not uid:
            return JSONResponse(status_code=400, content={"error": "UID no proporcionado"})

        db = SessionLocal()
        user = db.query(User).filter(User.uid == uid).first()

        # Tiempo actual
        ara = datetime.now(timezone.utc) + timedelta(hours=2)

        # Traducir día al formato que usas en Horari
        dies_traduits = {
            "Monday": "Dilluns",
            "Tuesday": "Dimarts",
            "Wednesday": "Dimecres",
            "Thursday": "Dijous",
            "Friday": "Divendres",
            "Saturday": "Dissabte",
            "Sunday": "Diumenge",
        }
        dia_actual = dies_traduits[ara.strftime("%A")]

        retard = False
        if user:
            horari = db.query(Horari).filter(
                Horari.usuari_id == user.id,
                Horari.dia_setmana == dia_actual,
                Horari.hora_inici <= ara.time(),
                Horari.hora_fi >= ara.time()
            ).first()

            if horari and ara.time() > horari.hora_inici:
                retard = True

        nuevo = Fichaje(
            uid=uid,
            timestamp=ara,
            user_id=user.id if user else None,
            retard=retard
        )

        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        db.close()

        if user and horari:
            existeix = db.query(Fichaje).filter(
                Fichaje.user_id == user.id,
                Fichaje.timestamp >= datetime.combine(ara.date(), horari.hora_inici),
                Fichaje.timestamp <= datetime.combine(ara.date(), horari.hora_fi)
            ).first()

            if existeix:
                db.close()
                return JSONResponse(status_code=200, content={
                    "status": "skip",
                    "message": "Ja ha fichat en aquesta franja"
                })


        return {
            "status": "ok",
            "uid": uid,
            "user_found": bool(user),
            "timestamp": str(nuevo.timestamp),
            "retard": retard
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Error intern: {str(e)}"})



# ---------------------- API: Visualizar fichajes ----------------------
@app.get("/fichajes", response_class=HTMLResponse)
def mostrar_fichajes(request: Request):
    db = SessionLocal()
    registros = db.query(Fichaje).order_by(Fichaje.timestamp.desc()).all()
    db.close()
    return templates.TemplateResponse("fichajes.html", {"request": request, "fichajes": registros})


# ---------------------- Swagger + Token Auth ----------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    user = db.query(User).filter(User.nom == username).first()
    db.close()

    if not user or not verificar_contrasenya(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credencials incorrectes")

    token = crear_token({"sub": user.nom, "rol": user.rol})
    return {"access_token": token, "token_type": "bearer"}

def get_current_user(token: str = Depends(oauth2_scheme)):
    data = llegir_token(token)
    if not data:
        raise HTTPException(status_code=401, detail="Token invàlid")
    return data

@app.get("/usuari/protegida")
def zona_segura(user = Depends(get_current_user)):
    return {"missatge": f"Hola {user['sub']}! Ets {user['rol']}."}


# ---------------------- Web protegida per sessió ----------------------
@app.get("/web/fichajes", response_class=HTMLResponse)
def web_fichajes(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/web/login")

    db = SessionLocal()
    fichajes = db.query(Fichaje).options(joinedload(Fichaje.user)).order_by(Fichaje.timestamp.desc()).all()
    db.close()

    return templates.TemplateResponse("fichajes.html", {
        "request": request,
        "fichajes": fichajes,
        "user": user
    })


# ---------------------- API Login desde App ----------------------
class LoginRequest(BaseModel):
    uid: str
    password: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.uid == data.uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuari no trobat")
    
    if user.password_hash != data.password:
        raise HTTPException(status_code=401, detail="Contrasenya incorrecta")

    return {
        "id": user.id,
        "nom": user.nom,
        "rol": user.rol,
    }

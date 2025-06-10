from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from database import SessionLocal, User
from passlib.context import CryptContext

templates = Jinja2Templates(directory="templates")
router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.get("/web/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/web/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    db = SessionLocal()
    user = db.query(User).filter(User.nom == username).first()
    db.close()

    if not user or not pwd_context.verify(password, user.password_hash):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Usuari o contrasenya incorrectes"
        })

    # Guardar información de sesión
    request.session["user"] = {
        "id": user.id,
        "nom_usuari": user.nom,
        "rol": user.rol
    }

    # Redireccionar según rol
    if user.rol == "admin":
        return RedirectResponse(url="/web/admin", status_code=302)
    elif user.rol == "professor":
        return RedirectResponse(url="/web/professor", status_code=302)
    elif user.rol == "alumne":
        return RedirectResponse(url="/web/alumne", status_code=302)
    else:
        # Por si acaso, redirige a fichajes si no hay rol definido
        return RedirectResponse(url="/web/fichajes", status_code=302)
    
@router.get("/web/logout")
def logout(request: Request):
    request.session.clear()  # Eliminar la sesión del usuario
    return RedirectResponse(url="/web/login", status_code=302)


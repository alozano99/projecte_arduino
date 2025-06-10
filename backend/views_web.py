from fastapi import Request, APIRouter, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, time
from passlib.context import CryptContext
from typing import List

from auth_utils import verificar_rol_permis
from database import SessionLocal, Fichaje, User, RolEnum, Horari

router = APIRouter()
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/web/admin", response_class=HTMLResponse)
def admin_view(request: Request, user=Depends(verificar_rol_permis(["admin"]))):
    return templates.TemplateResponse("admin.html", {"request": request})

@router.get("/web/professor", response_class=HTMLResponse)
def professor_view(
    request: Request,
    user=Depends(verificar_rol_permis(["professor"])),
    db: Session = Depends(get_db)
):
    fichajes = (
        db.query(Fichaje)
        .options(joinedload(Fichaje.user))
        .join(User)
        .filter(User.rol == "alumne")
        .order_by(Fichaje.timestamp.desc())
        .all()
    )

    # Separar fichatges segons el tipus
    fichatges_rfid = [f for f in fichajes if f.uid is not None]
    fichatges_manual = [f for f in fichajes if f.uid is None]

    missatge = None
    if request.query_params.get("success") == "1":
        missatge = "Assistència desada correctament."

    return templates.TemplateResponse("professor.html", {
        "request": request,
        "fichatges_rfid": fichatges_rfid,
        "fichatges_manual": fichatges_manual,
        "user": user,
        "missatge": missatge
    })


@router.get("/web/alumne", response_class=HTMLResponse)
def alumne_view(
    request: Request,
    user=Depends(verificar_rol_permis(["alumne"])),
    db: Session = Depends(get_db)
):
    fichajes = (
        db.query(Fichaje)
        .filter(Fichaje.user_id == user["id"])
        .order_by(Fichaje.timestamp.desc())
        .all()
    )
    return templates.TemplateResponse("alumne.html", {
        "request": request,
        "fichajes": fichajes,
        "user": user
    })

@router.get("/web/admin/usuaris", response_class=HTMLResponse)
def veure_usuaris(
    request: Request,
    user=Depends(verificar_rol_permis(["admin"])),
    db: Session = Depends(get_db)
):
    usuaris = db.query(User).order_by(User.id).all()
    return templates.TemplateResponse("usuaris.html", {
        "request": request,
        "usuaris": usuaris,
        "user": user
    })

@router.post("/web/admin/usuaris/afegir")
def afegir_usuari(
    nom: str = Form(...),
    uid: str = Form(""),
    password: str = Form(...),
    rol: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(verificar_rol_permis(["admin"]))
):
    existent = db.query(User).filter(User.nom == nom).first()
    if existent:
        return templates.TemplateResponse("usuaris.html", {
            "request": Request,
            "error": f"L'usuari '{nom}' ja existeix",
            "user": user,
            "usuaris": db.query(User).all()
        })

    nou = User(
        nom=nom,
        uid=uid if uid else None,
        password_hash=pwd_context.hash(password),
        rol=RolEnum(rol)
    )
    db.add(nou)
    db.commit()
    return RedirectResponse(url="/web/admin/usuaris", status_code=302)

@router.get("/web/admin/usuaris/editar/{usuari_id}", response_class=HTMLResponse)
def editar_usuari_form(
    request: Request,
    usuari_id: int,
    db: Session = Depends(get_db),
    user=Depends(verificar_rol_permis(["admin"]))
):
    usuari = db.query(User).filter(User.id == usuari_id).first()
    if not usuari:
        raise HTTPException(status_code=404, detail="Usuari no trobat")
    return templates.TemplateResponse("editar_usuari.html", {"request": request, "usuari": usuari})

@router.post("/web/admin/usuaris/editar/{usuari_id}")
def editar_usuari(
    usuari_id: int,
    nom: str = Form(...),
    uid: str = Form(...),
    rol: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(verificar_rol_permis(["admin"]))
):
    usuari = db.query(User).filter(User.id == usuari_id).first()
    if not usuari:
        raise HTTPException(status_code=404, detail="Usuari no trobat")

    usuari.nom = nom
    usuari.uid = uid
    usuari.rol = RolEnum(rol)
    db.commit()

    return RedirectResponse(url="/web/admin/usuaris", status_code=302)

@router.post("/web/admin/usuaris/eliminar/{usuari_id}")
def eliminar_usuari(
    usuari_id: int,
    db: Session = Depends(get_db),
    user=Depends(verificar_rol_permis(["admin"]))
):
    usuari = db.query(User).filter(User.id == usuari_id).first()
    if usuari:
        db.delete(usuari)
        db.commit()
    return RedirectResponse(url="/web/admin/usuaris", status_code=302)

@router.get("/web/admin/editar/{usuari_id}", response_class=HTMLResponse)
def formulari_edicio(
    usuari_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(verificar_rol_permis(["admin"]))
):
    usuari = db.query(User).filter(User.id == usuari_id).first()
    if not usuari:
        raise HTTPException(status_code=404, detail="Usuari no trobat")
    
    return templates.TemplateResponse("editar_usuari.html", {
        "request": request,
        "usuari": usuari,
        "user": user
    })

@router.post("/web/admin/usuaris/editar/{usuari_id}")
def guardar_edicio(
    usuari_id: int,
    nom: str = Form(...),
    uid: str = Form(""),
    rol: str = Form(...),
    password: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(verificar_rol_permis(["admin"]))
):
    usuari = db.query(User).filter(User.id == usuari_id).first()
    if not usuari:
        raise HTTPException(status_code=404, detail="Usuari no trobat")

    usuari.nom = nom
    usuari.uid = uid if uid else None
    usuari.rol = RolEnum(rol)
    if password:
        usuari.password_hash = pwd_context.hash(password)

    db.commit()
    return RedirectResponse(url="/web/admin/usuaris", status_code=302)

@router.get("/web/professor/horaris", response_class=HTMLResponse)
def veure_horaris(
    request: Request,
    user=Depends(verificar_rol_permis(["professor"])),
    db: Session = Depends(get_db)
):
    horaris = db.query(Horari).filter(Horari.usuari_id == user["id"]).all()
    return templates.TemplateResponse("horaris.html", {
        "request": request,
        "user": user,
        "horaris": horaris
    })

@router.post("/web/professor/horaris/afegir")
def afegir_horari(
    request: Request,
    dia_setmana: str = Form(...),
    hora_inici: str = Form(...),
    hora_fi: str = Form(...),
    aula: str = Form(""),
    user=Depends(verificar_rol_permis(["professor"])),
    db: Session = Depends(get_db)
):
    try:
        hora_inici_obj = datetime.strptime(hora_inici, "%H:%M").time()
        hora_fi_obj = datetime.strptime(hora_fi, "%H:%M").time()

        nou = Horari(
            dia_setmana=dia_setmana,
            hora_inici=hora_inici_obj,
            hora_fi=hora_fi_obj,
            aula=aula if aula else None,
            usuari_id=user["id"]
        )
        db.add(nou)
        db.commit()
        return RedirectResponse(url="/web/professor/horaris", status_code=302)

    except Exception as e:
        horaris = db.query(Horari).filter(Horari.usuari_id == user["id"]).all()
        return templates.TemplateResponse("horaris.html", {
            "request": request,
            "user": user,
            "horaris": horaris,
            "error": f"Error al afegir l'horari: {str(e)}"
        })

@router.post("/web/professor/horaris/eliminar/{horari_id}")
def eliminar_horari(
    horari_id: int,
    user=Depends(verificar_rol_permis(["professor"])),
    db: Session = Depends(get_db)
):
    horari = db.query(Horari).filter(Horari.id == horari_id, Horari.usuari_id == user["id"]).first()
    if horari:
        db.delete(horari)
        db.commit()
    return RedirectResponse(url="/web/professor/horaris", status_code=302)

@router.get("/web/professor/horaris/editar/{horari_id}", response_class=HTMLResponse)
def formulari_edicio_horari(
    horari_id: int,
    request: Request,
    user=Depends(verificar_rol_permis(["professor"])),
    db: Session = Depends(get_db)
):
    horari = db.query(Horari).filter(Horari.id == horari_id, Horari.usuari_id == user["id"]).first()
    if not horari:
        raise HTTPException(status_code=404, detail="Horari no trobat")
    
    return templates.TemplateResponse("editar_horari.html", {
        "request": request,
        "horari": horari,
        "user": user
    })


@router.post("/web/professor/horaris/editar/{horari_id}")
def guardar_edicio_horari(
    horari_id: int,
    dia_setmana: str = Form(...),
    hora_inici: str = Form(...),
    hora_fi: str = Form(...),
    aula: str = Form(""),
    user=Depends(verificar_rol_permis(["professor"])),
    db: Session = Depends(get_db)
):
    horari = db.query(Horari).filter(Horari.id == horari_id, Horari.usuari_id == user["id"]).first()
    if not horari:
        raise HTTPException(status_code=404, detail="Horari no trobat")

    horari.dia_setmana = dia_setmana
    horari.hora_inici = datetime.strptime(hora_inici, "%H:%M").time()
    horari.hora_fi = datetime.strptime(hora_fi, "%H:%M").time()
    horari.aula = aula if aula else None

    db.commit()
    return RedirectResponse(url="/web/professor/horaris", status_code=302)

@router.get("/web/professor/passar_llista", response_class=HTMLResponse)
def passar_llista_form(
    request: Request,
    user=Depends(verificar_rol_permis(["professor"])),
    db: Session = Depends(get_db)
):
    ara = datetime.now().time()

    # Buscar horari actiu
    horari = db.query(Horari).filter(
        Horari.usuari_id == user["id"],
        Horari.hora_inici <= ara,
        Horari.hora_fi >= ara
    ).first()

    if not horari:
        return templates.TemplateResponse("passar_llista.html", {
            "request": request,
            "user": user,
            "missatge": "No tens cap classe activa ara mateix.",
            "alumnes": []
        })

    # Llista d'alumnes
    alumnes = db.query(User).filter(User.rol == "alumne").all()

    return templates.TemplateResponse("passar_llista.html", {
        "request": request,
        "user": user,
        "alumnes": alumnes,
        "horari": horari
    })

@router.post("/web/professor/passar_llista")
def passar_llista_guardar(
    presents: List[int] = Form([]),
    user=Depends(verificar_rol_permis(["professor"])),
    db: Session = Depends(get_db)
):
    ara = datetime.now()

    # Traducció de dies en anglès a català
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

    for alumne_id in presents:
        # Buscar si hi ha una classe activa per al professor en aquest moment
        horari = db.query(Horari).filter(
            Horari.usuari_id == user["id"],
            Horari.dia_setmana == dia_actual,
            Horari.hora_inici <= ara.time(),
            Horari.hora_fi >= ara.time()
        ).first()

        # Determinar si arriba tard
        retard = False
        if horari and ara.time() > horari.hora_inici:
            retard = True

        # Crear el fichaje
        db.add(Fichaje(
            uid=None,
            user_id=alumne_id,
            timestamp=ara,
            retard=retard
        ))
        if horari:
            existeix = db.query(Fichaje).filter(
                Fichaje.user_id == alumne_id,
                Fichaje.timestamp >= datetime.combine(ara.date(), horari.hora_inici),
                Fichaje.timestamp <= datetime.combine(ara.date(), horari.hora_fi)
            ).first()

            if existeix:
                continue  # Ja ha fitxat, no duplicar

            if ara.time() > horari.hora_inici:
                retard = True


    db.commit()
    return RedirectResponse(url="/web/professor?success=1", status_code=302)
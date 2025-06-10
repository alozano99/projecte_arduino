from fastapi import Request, HTTPException, Depends

def verificar_rol_permis(rols_permesos: list[str]):
    def inner(request: Request):
        user = request.session.get("user")
        if not user or user["rol"].lower() not in [r.lower() for r in rols_permesos]:
            raise HTTPException(status_code=403, detail="Accés denegat")
        return user
    return inner

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from enum import Enum
import json
import os

DB_FILE = "datos.json"

# 1. ENUMS
class AreaMunicipal(Enum):
    LICENCIAS = 1
    RENTAS = 2

# 2. DTOs
class TurnoCreateRequest(BaseModel):
    nombre: str
    apellido: str
    dni: str
    email: str
    telefono: str
    fecha_hora: str
    area_id: int

class TurnoReasignarRequest(BaseModel):
    nueva_fecha: str

# 3. REPOSITORIOS
class TurnoRepository:
    def __init__(self, db_file: str = DB_FILE):
        self.db_file = db_file
        self._init_db()

    def _init_db(self):
        if not os.path.exists(self.db_file):
            with open(self.db_file, "w") as f:
                json.dump({"ciudadanos": [], "turnos": []}, f)

    def leer_datos(self):
        with open(self.db_file, "r") as f:
            return json.load(f)

    def guardar_datos(self, data):
        with open(self.db_file, "w") as f:
            json.dump(data, f, indent=4)

# 4. SERVICIOS
class NotificacionService:
    @staticmethod
    def enviar(email: str, mensaje: str):
        # Abstracción del envío, preparado para extenderse a OCP más tarde
        print(f"ENVIANDO NOTIFICACIÓN a {email}: {mensaje}")


class TurnoService:
    def __init__(self, repo: TurnoRepository):
        self.repo = repo

    # Se elimina todo el código duplicado de validación de horarios y se centraliza en un método privado
    def _verificar_horario_disponible(self, area_id: int, fecha_hora: str, turnos: list):
        for turno in turnos:
            if turno["area_id"] == area_id and turno["fecha_hora"] == fecha_hora and turno["estado"] != "cancelado":
                raise HTTPException(status_code=400, detail="El horario ya está ocupado.")

    def solicitar_turno(self, request: TurnoCreateRequest):
        db = self.repo.leer_datos()
        
        self._verificar_horario_disponible(request.area_id, request.fecha_hora, db["turnos"])

        # Uso del Enum en lugar de Magic Numbers
        duracion = 15
        if request.area_id == AreaMunicipal.LICENCIAS.value:
            duracion = 30
        elif request.area_id == AreaMunicipal.RENTAS.value:
            duracion = 20

        ciudadano_existe = any(c["dni"] == request.dni for c in db["ciudadanos"])
        if not ciudadano_existe:
            db["ciudadanos"].append({
                "dni": request.dni, "nombre": request.nombre, "apellido": request.apellido, 
                "email": request.email, "telefono": request.telefono
            })

        nuevo_turno = {
            "id": len(db["turnos"]) + 1,
            "ciudadano_id": request.dni,
            "area_id": request.area_id,
            "fecha_hora": request.fecha_hora,
            "duracion": duracion,
            "estado": "pendiente"
        }
        db["turnos"].append(nuevo_turno)
        self.repo.guardar_datos(db)

        # El servicio tiene que asumir la responsabilidad y usar el NotificacionService para enviar la notificación
        mensaje = f"Hola {request.nombre}, tu turno fue confirmado para el {request.fecha_hora}."
        NotificacionService.enviar(request.email, mensaje)

        return {"mensaje": "Turno creado con éxito", "turno": nuevo_turno}

    def reasignar_turno(self, turno_id: int, request: TurnoReasignarRequest):
        db = self.repo.leer_datos()
        
        turno_actual = next((t for t in db["turnos"] if t["id"] == turno_id), None)
        if not turno_actual:
            raise HTTPException(status_code=404, detail="Turno no encontrado")

        self._verificar_horario_disponible(turno_actual["area_id"], request.nueva_fecha, db["turnos"])

        turno_actual["fecha_hora"] = request.nueva_fecha
        self.repo.guardar_datos(db)

        ciudadano = next(c for c in db["ciudadanos"] if c["dni"] == turno_actual["ciudadano_id"])
        mensaje = f"Hola {ciudadano['nombre']}, tu turno fue reprogramado al {request.nueva_fecha}."
        NotificacionService.enviar(ciudadano["email"], mensaje)

        return {"mensaje": "Turno reasignado", "turno": turno_actual}

    def cancelar_turno(self, turno_id: int):
        db = self.repo.leer_datos()
        turno = next((t for t in db["turnos"] if t["id"] == turno_id), None)
        if not turno:
            raise HTTPException(status_code=404, detail="Turno no encontrado")

        turno["estado"] = "cancelado"
        self.repo.guardar_datos(db)
        return {"mensaje": "Turno cancelado exitosamente"}

    def listar_por_area(self, area_id: int):
        db = self.repo.leer_datos()
        return [t for t in db["turnos"] if t["area_id"] == area_id and t["estado"] == "pendiente"]

# 5. CONTROLADORES
app = FastAPI(title="Gestión de Turnos Municipales - Refactorizado")
repo = TurnoRepository()
turno_service = TurnoService(repo)

@app.post("/turnos/solicitar")
def api_solicitar_turno(turno_in: TurnoCreateRequest):
    return turno_service.solicitar_turno(turno_in)

@app.put("/turnos/reasignar/{turno_id}")
def api_reasignar_turno(turno_id: int, turno_in: TurnoReasignarRequest):
    return turno_service.reasignar_turno(turno_id, turno_in)

@app.put("/turnos/cancelar/{turno_id}")
def api_cancelar_turno(turno_id: int):
    return turno_service.cancelar_turno(turno_id)

@app.get("/turnos/area/{area_id}")
def api_listar_turnos(area_id: int):
    return {"turnos": turno_service.listar_por_area(area_id)}
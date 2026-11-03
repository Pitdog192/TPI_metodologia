from fastapi import FastAPI, HTTPException
import json
import os

# 1. God Class / Violación de SRP: 
# Este archivo único (main.py) se encarga del enrutamiento, la conexión a la "base de datos", 
# la lógica de negocio, las validaciones y el envío de notificaciones.
app = FastAPI(title="Gestión de Turnos Municipales")
DB_FILE = "datos.json"

def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump({"ciudadanos": [], "turnos": []}, f)

init_db()

# 4. Long Parameter List:
# En lugar de encapsular los datos en un modelo de dominio o DTO (ej. Pydantic BaseModel), 
# la función recibe una lista interminable de tipos primitivos.
@app.post("/turnos/solicitar")
def solicitar_turno(nombre: str, apellido: str, dni: str, email: str, telefono: str, fecha_hora: str, area_id: int):
    
    # 3. Long Method:
    # Esta función es extremadamente larga y hace demasiadas cosas: lee el archivo, valida,
    # calcula reglas de negocio, escribe en el archivo y notifica.
    with open(DB_FILE, "r") as f:
        db = json.load(f)

    # 5. Duplicated Code:
    # Esta estructura de bucle para verificar la disponibilidad exacta del horario
    # se encuentra copiada y pegada tal cual en el método de reasignar_turno.
    turno_ocupado = False
    for turno in db["turnos"]:
        if turno["area_id"] == area_id and turno["fecha_hora"] == fecha_hora and turno["estado"] != "cancelado":
            turno_ocupado = True
            break
    
    if turno_ocupado:
        raise HTTPException(status_code=400, detail="El horario ya está ocupado.")

    # 2. Magic Numbers:
    # Se utilizan números literales (1, 2, 30, 20) sin asignarlos a constantes descriptivas.
    # Si el ID del área en la base de datos cambia, la lógica fallará silenciosamente.
    duracion = 15
    if area_id == 1: 
        duracion = 30
    elif area_id == 2: 
        duracion = 20

    ciudadano_existe = any(c["dni"] == dni for c in db["ciudadanos"])
    if not ciudadano_existe:
        db["ciudadanos"].append({
            "dni": dni, "nombre": nombre, "apellido": apellido, "email": email, "telefono": telefono
        })

    # 7. Inappropriate Intimacy:
    # Se manipulan directamente las claves de los diccionarios y la persistencia interna
    # exponiendo la estructura de datos cruda en lugar de usar repositorios o clases abstractas.
    nuevo_turno = {
        "id": len(db["turnos"]) + 1,
        "ciudadano_id": dni,
        "area_id": area_id,
        "fecha_hora": fecha_hora,
        "duracion": duracion,
        "estado": "pendiente"
    }
    db["turnos"].append(nuevo_turno)

    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

    # 6. Feature Envy:
    # El enrutador accede a múltiples propiedades sueltas del ciudadano para construir el nombre
    # completo, una responsabilidad que le envidia y debería pertenecer a la entidad Ciudadano.
    nombre_completo = nombre + " " + apellido + " (DNI: " + dni + ")"
    
    enviar_notificacion(nombre, apellido, dni, email, telefono, fecha_hora, area_id, "confirmacion")

    return {"mensaje": "Turno creado con éxito", "turno": nuevo_turno}


@app.put("/turnos/reasignar/{turno_id}")
def reasignar_turno(turno_id: int, nueva_fecha: str):
    with open(DB_FILE, "r") as f:
        db = json.load(f)

    turno_actual = next((t for t in db["turnos"] if t["id"] == turno_id), None)
    if not turno_actual:
        raise HTTPException(status_code=404, detail="Turno no encontrado")

    # 5. Duplicated Code (clon de la validación en solicitar_turno)
    turno_ocupado = False
    for turno in db["turnos"]:
        if turno["area_id"] == turno_actual["area_id"] and turno["fecha_hora"] == nueva_fecha and turno["estado"] != "cancelado":
            turno_ocupado = True
            break
    
    if turno_ocupado:
        raise HTTPException(status_code=400, detail="El horario ya está ocupado.")

    turno_actual["fecha_hora"] = nueva_fecha

    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

    ciudadano = next(c for c in db["ciudadanos"] if c["dni"] == turno_actual["ciudadano_id"])
    
    enviar_notificacion(ciudadano["nombre"], ciudadano["apellido"], ciudadano["dni"], ciudadano["email"], ciudadano["telefono"], nueva_fecha, turno_actual["area_id"], "reasignacion")

    return {"mensaje": "Turno reasignado", "turno": turno_actual}


@app.put("/turnos/cancelar/{turno_id}")
def cancelar_turno(turno_id: int):
    with open(DB_FILE, "r") as f:
        db = json.load(f)

    turno = next((t for t in db["turnos"] if t["id"] == turno_id), None)
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")

    turno["estado"] = "cancelado"

    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

    return {"mensaje": "Turno cancelado exitosamente"}


@app.get("/turnos/area/{area_id}")
def listar_turnos_por_area(area_id: int):
    with open(DB_FILE, "r") as f:
        db = json.load(f)
    
    turnos_area = [t for t in db["turnos"] if t["area_id"] == area_id and t["estado"] == "pendiente"]
    return {"turnos": turnos_area}


# 8. Shotgun Surgery:
# Esta función está acoplada al envío de todos los tipos de mensajes. Si se decide cambiar 
# el canal (ej. agregar SMS) o agregar un nuevo dato al mensaje, habrá que modificar la firma 
# de esta función y cazar todos los lugares en el código donde fue invocada para actualizar los argumentos.
def enviar_notificacion(nombre, apellido, dni, email, telefono, fecha, area, tipo_mensaje):
    if tipo_mensaje == "confirmacion":
        print(f"ENVIANDO EMAIL a {email}: Turno confirmado para el {fecha}.")
    elif tipo_mensaje == "reasignacion":
        print(f"ENVIANDO EMAIL a {email}: Turno reprogramado al {fecha}.")
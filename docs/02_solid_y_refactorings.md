# 2. SOLID, Clean Code y refactorings aplicados

Corresponde al tag `etapa-refactoring` (commit `f537673`). Para ver todos los cambios juntos:

```bash
git diff estado-inicial etapa-refactoring -- main.py
```

## 2.1 Estructura antes y después

| Antes (`estado-inicial`) | Después (`etapa-refactoring`) |
|---|---|
| Un único bloque de funciones-endpoint que hace todo. | Cinco capas dentro de `main.py`: enums, DTOs, repositorio, servicios y controladores. |
| Cada endpoint abre y escribe `datos.json`. | `TurnoRepository` es el único que conoce el archivo. |
| Las reglas de negocio están mezcladas con HTTP. | `TurnoService` concentra las reglas de negocio; los endpoints solo delegan (1 línea cada uno). |
| `enviar_notificacion` recibe 8 parámetros. | `NotificacionService.enviar(email, mensaje)`. |

## 2.2 Refactorings aplicados

### R1. Extract Method: verificar si el horario está libre

Elimina el smell #2 (Duplicated Code). El bucle copiado en dos endpoints pasa a ser un único método privado:

```python
# Antes: este bloque aparecía igual en solicitar_turno (l. 33-40) y reasignar_turno (l. 93-100)
turno_ocupado = False
for turno in db["turnos"]:
    if turno["area_id"] == area_id and turno["fecha_hora"] == fecha_hora and turno["estado"] != "cancelado":
        turno_ocupado = True
        break
if turno_ocupado:
    raise HTTPException(status_code=400, detail="El horario ya está ocupado.")
```

```python
# Después (main.py, l. 59-62): una sola regla, usada por solicitar y reasignar
def _verificar_horario_disponible(self, area_id: int, fecha_hora: str, turnos: list):
    for turno in turnos:
        if turno["area_id"] == area_id and turno["fecha_hora"] == fecha_hora and turno["estado"] != "cancelado":
            raise HTTPException(status_code=400, detail="El horario ya está ocupado.")
```

Además se eliminó la bandera `turno_ocupado`, porque el método lanza la excepción en cuanto encuentra el conflicto. Si mañana cambia la regla (por ejemplo, para considerar la duración del turno), se modifica en un solo lugar.

### R2. Move Method: reubicar responsabilidades en clases

Ataca los smells #1 (God Class), #3 (Long Method) y #7 (Inappropriate Intimacy):

- La lectura y escritura del JSON se movió a `TurnoRepository` (`leer_datos`, `guardar_datos`, `_init_db`; l. 28–44).
- Las reglas de negocio se movieron a `TurnoService` (l. 54–130).
- El armado y envío de mensajes se movió a `NotificacionService` (l. 47–51).
- Los endpoints quedaron como controladores delgados (l. 137–151):

```python
@app.post("/turnos/solicitar")
def api_solicitar_turno(turno_in: TurnoCreateRequest):
    return turno_service.solicitar_turno(turno_in)
```

`TurnoService` recibe el repositorio por constructor (`TurnoService(repo)`), así que se puede probar con otro repositorio sin tocar el servicio.

### R3. Introduce Parameter Object: DTOs con Pydantic

Ataca el smell #4 (Long Parameter List):

```python
# Antes (l. 22)
def solicitar_turno(nombre: str, apellido: str, dni: str, email: str, telefono: str, fecha_hora: str, area_id: int):
```

```python
# Después (l. 15-25 y l. 138)
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

def api_solicitar_turno(turno_in: TurnoCreateRequest):
```

Los datos viajan juntos, FastAPI los valida (un campo faltante devuelve 422) y ya no aparecen en la URL. Es el único cambio visible para quien consume la API: ahora se envían como JSON en el body. Lo documentamos con pruebas en `tests/test_contrato_api.py` y como observación CR-01 del code review.

### R4. Replace Magic Number with Symbolic Constant

Ataca el smell #6:

```python
# Antes (l. 45-49)
if area_id == 1:
    duracion = 30
elif area_id == 2:
    duracion = 20
```

```python
# Después (l. 10-12 y l. 70-74)
class AreaMunicipal(Enum):
    LICENCIAS = 1
    RENTAS = 2

if request.area_id == AreaMunicipal.LICENCIAS.value:
    duracion = 30
elif request.area_id == AreaMunicipal.RENTAS.value:
    duracion = 20
```

### R5. Simplificar la notificación (Remove Parameter)

Ataca el smell #5 (Shotgun Surgery). `enviar_notificacion` recibía 8 parámetros y solo usaba 2. Ahora el servicio arma el mensaje y `NotificacionService.enviar(email, mensaje)` solo lo envía. Agregar un canal nuevo implica cambiar esa clase, no cada llamada.

### R6. Remove Dead Code

Ataca el smell #8. Se eliminó la variable `nombre_completo` (l. 76), que se calculaba y nunca se usaba.

## 2.3 Principios aplicados

| Principio | Cómo se aplicó | Estado |
|---|---|---|
| **SRP** | Repositorio, servicio de turnos, servicio de notificación y controladores tienen una sola razón de cambio cada uno. | Aplicado |
| **DIP** (parcial) | `TurnoService` recibe el repositorio por constructor en vez de abrir el archivo. | Parcial: depende de la clase concreta y llama a `NotificacionService` de forma estática (ver CR-03). |
| **OCP** (parcial) | La notificación quedó aislada y se puede extender sin tocar el servicio. | Parcial: agregar un área nueva todavía obliga a editar el `if/elif` de la duración (ver CR-04). |
| **ISP** | Los DTOs piden solo lo que cada operación necesita: reasignar recibe únicamente `nueva_fecha`. | Aplicado |
| **LSP** | No hay jerarquías de herencia en este módulo, así que no aplica todavía. Aplicaría si se crean distintos repositorios o canales de notificación. | No aplica |

## 2.4 Clean Code

- **Nombres:** los endpoints se llaman `api_*` y los métodos del servicio describen la acción (`solicitar_turno`, `listar_por_area`). Los parámetros dicen qué contienen (`turno_in`, `request`).
- **Funciones:** cada endpoint tiene una línea. El método más largo del servicio (`solicitar_turno`) bajó de casi 60 a 35 líneas y no repite validaciones.
- **Manejo de errores:** los mismos códigos HTTP y mensajes que antes (400 y 404), y ahora un 422 automático cuando faltan datos.
- **Cohesión y acoplamiento:** solo el repositorio conoce el formato del archivo; el servicio todavía usa las claves del diccionario (ver CR-05).

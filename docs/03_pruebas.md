# 3. Pruebas y verificación del comportamiento

## 3.1 Estrategia

Usamos **pruebas de caracterización**: describen lo que el sistema hacía en `estado-inicial` y verifican que la versión refactorizada siga haciendo exactamente lo mismo.

- Cada prueba se ejecuta **dos veces**, una por versión. El código de `estado-inicial` se obtiene con `git show estado-inicial:main.py` y el refactorizado es el `main.py` actual (ver `tests/conftest.py`).
- Las pruebas usan la API real a través del `TestClient` de FastAPI, igual que un cliente HTTP.
- Cada prueba trabaja en una carpeta temporal, así que el `datos.json` del repositorio nunca se modifica.
- Todos los datos son sintéticos (ciudadana ficticia "Ana Pérez", DNI y emails inventados).

Las pruebas se escribieron después del refactoring. Para que sigan sirviendo como evidencia de antes y después, se ejecutan contra el código del tag `estado-inicial`: si una regla hubiera cambiado, la misma prueba daría resultados distintos en cada versión.

## 3.2 Cómo ejecutarlas

```bash
pip install -r requirements.txt
python -m pytest -v
```

El repositorio tiene que estar clonado con sus tags. `git clone` los trae por defecto; si faltan, se bajan con `git fetch --tags`.

## 3.3 Casos de prueba

| ID | Caso | Resultado esperado | Archivo |
|---|---|---|---|
| P01 | Solicitar un turno válido | 200, turno con id 1, estado `pendiente` y duración según el área | `test_comportamiento.py` |
| P02 | Duración por área (1, 2, 3 y 99) | 30, 20, 15 y 15 minutos | `test_comportamiento.py` |
| P03 | Dos turnos seguidos | Ids correlativos 1 y 2 | `test_comportamiento.py` |
| P04 | Mismo horario y misma área | 400 "El horario ya está ocupado." | `test_comportamiento.py` |
| P05 | Mismo horario en otra área | 200 | `test_comportamiento.py` |
| P06 | Horario de un turno cancelado | Se puede volver a reservar | `test_comportamiento.py` |
| P07 | Mismo DNI en dos turnos | El ciudadano se guarda una sola vez | `test_comportamiento.py` |
| P08 | Persistencia | El turno queda escrito en `datos.json` | `test_comportamiento.py` |
| P09 | Notificación al solicitar | Se envía al email del ciudadano con la fecha del turno | `test_comportamiento.py` |
| P10 | Reasignar un turno | 200 y la nueva fecha queda guardada | `test_comportamiento.py` |
| P11 | Reasignar un turno inexistente | 404 "Turno no encontrado" | `test_comportamiento.py` |
| P12 | Reasignar a un horario ocupado | 400 | `test_comportamiento.py` |
| P13 | Notificación al reasignar | Se envía con la nueva fecha | `test_comportamiento.py` |
| P14 | Cancelar un turno | 200 y `estado = "cancelado"` | `test_comportamiento.py` |
| P15 | Cancelar un turno inexistente | 404 | `test_comportamiento.py` |
| P16 | Listar por área | Solo los turnos pendientes de esa área | `test_comportamiento.py` |
| P17 | Listar un área sin turnos | Lista vacía | `test_comportamiento.py` |
| P18 | Contrato antes: query params | `estado-inicial` acepta los datos en la URL | `test_contrato_api.py` |
| P19 | Contrato después: JSON | La versión refactorizada rechaza los query params (422) y acepta JSON (200) | `test_contrato_api.py` |
| P20 | Validación de campos | Si falta un campo obligatorio, devuelve 422 | `test_contrato_api.py` |

## 3.4 Resultados

Se ejecutaron **43 pruebas**: P01–P17 corren una vez por versión, algunas con varios valores, y P18–P20 una vez cada una. **Todas pasaron.** La salida completa está en [`evidencias/pytest_antes_despues.txt`](evidencias/pytest_antes_despues.txt).

Conclusión: las reglas de negocio, las respuestas, los códigos de error, la persistencia y las notificaciones son iguales en las dos versiones. El único cambio externo es el formato de entrada (query params → JSON), que es intencional y está documentado en P18–P20 y en CR-01.

## 3.5 ¿Las pruebas detectan regresiones?

Para comprobarlo, cambiamos a propósito la duración de Rentas de 20 a 25 minutos en `main.py` y volvimos a correrlas:

```
FAILED tests/test_comportamiento.py::test_duracion_del_turno_depende_del_area[refactorizado-2-20]
1 failed, 42 passed
```

La prueba falló solo en la versión modificada, y después revertimos el cambio. Las pruebas sirven como red de seguridad para futuros refactorings.

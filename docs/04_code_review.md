# 4. Code review

Revisión de la versión refactorizada (`etapa-refactoring`) contra el `estado-inicial`.

## 4.1 Checklist técnico

| # | Criterio | Resultado | Observación |
|---|---|---|---|
| 1 | El proyecto se instala y ejecuta siguiendo el README | ❌ → ✅ | `requirements.txt` estaba vacío. Corregido (CR-06). |
| 2 | Cada clase o función tiene una única responsabilidad (SRP) | ✅ | Repositorio, servicios y controladores separados. |
| 3 | No hay lógica duplicada | ✅ | La validación de horario está en `_verificar_horario_disponible`. |
| 4 | Los nombres expresan la intención | ✅ | `api_*`, `solicitar_turno`, `listar_por_area`. |
| 5 | No hay números ni strings mágicos | ⚠️ | Áreas resueltas con `AreaMunicipal`; los estados `"pendiente"`/`"cancelado"` siguen como texto (CR-04). |
| 6 | Las funciones son cortas y de un solo nivel de abstracción | ✅ | Controladores de 1 línea; el servicio no mezcla lectura de archivos. |
| 7 | Las dependencias se inyectan y no se instancian adentro | ⚠️ | El repositorio sí; la notificación se llama de forma estática (CR-03). |
| 8 | El servicio no depende de detalles de HTTP | ❌ | `TurnoService` lanza `HTTPException` (CR-02). |
| 9 | Los errores se manejan con códigos y mensajes claros | ✅ | 400, 404 y 422 con mensajes en español. |
| 10 | Los datos de entrada se validan | ✅ | DTOs de Pydantic. |
| 11 | No hay código muerto | ✅ | Se eliminó `nombre_completo`. |
| 12 | Hay pruebas que respaldan el cambio | ❌ → ✅ | Se agregaron 43 pruebas antes/después (CR-07). |
| 13 | Los cambios visibles para el cliente están documentados | ❌ → ✅ | Cambio de query params a JSON (CR-01). |
| 14 | No hay datos personales reales | ✅ | `datos.json` vacío; las pruebas usan datos sintéticos. |
| 15 | Los commits son claros y siguen una convención | ✅ | Convención `tipo: descripción` (`chore`, `docs`, `refactor`, `test`). |

## 4.2 Observaciones y feedback

| ID | Severidad | Observación | Feedback / acción | Estado |
|---|---|---|---|---|
| CR-01 | Alta | Con los DTOs, `solicitar` y `reasignar` esperan JSON en el body en lugar de query params. Cualquier cliente que usara la URL anterior recibe un 422. | El cambio mejora la seguridad (datos personales fuera de la URL) y agrega validación, así que lo aceptamos. Hay que documentarlo y cubrirlo con pruebas. | Resuelto: P18–P20 y README actualizado |
| CR-02 | Media | `TurnoService` lanza `HTTPException`, así que la lógica de negocio depende del framework web. | Definir excepciones de dominio (`HorarioOcupadoError`, `TurnoNoEncontradoError`) y traducirlas a HTTP en el controlador. | Pendiente (mejora futura) |
| CR-03 | Media | `NotificacionService.enviar` se invoca de forma estática dentro del servicio, lo que impide reemplazarlo en pruebas o por otro canal (DIP). | Inyectar el notificador por constructor, igual que el repositorio. | Pendiente (mejora futura) |
| CR-04 | Baja | La duración se decide con `if/elif` por área y los estados son strings sueltos. Agregar un área obliga a modificar el servicio (OCP). | Usar un diccionario `{AreaMunicipal: duración}` y un `Enum` de estados. | Pendiente (mejora futura) |
| CR-05 | Baja | El servicio sigue trabajando con diccionarios (`turno["area_id"]`) en lugar de entidades `Turno` y `Ciudadano`. | Introducir modelos de dominio y que el repositorio los convierta desde y hacia JSON. | Pendiente (mejora futura) |
| CR-06 | Alta | `requirements.txt` vacío: el proyecto no se puede instalar con el README. | Declarar `fastapi`, `uvicorn`, `pytest` y `httpx`. | Corregido |
| CR-07 | Alta | No había pruebas automáticas que demostraran que el refactoring no cambió el comportamiento. | Agregar pruebas de caracterización que corran contra las dos versiones. | Corregido |
| CR-08 | Baja | `datos.json` está versionado, y al usar la app localmente se modifica y aparece como cambio en git. | Generarlo al iniciar (ya lo hace el repositorio) y agregarlo a `.gitignore`. | Pendiente (decisión del equipo) |

## 4.3 Criterios de aceptación técnica

El refactoring se acepta si:

1. ✅ Las 43 pruebas pasan en las dos versiones (`python -m pytest`).
2. ✅ Ningún endpoint cambió de ruta, de método HTTP ni de formato de respuesta.
3. ✅ Los cambios en el formato de entrada están documentados y probados (CR-01).
4. ✅ Los 8 code smells del diagnóstico están resueltos o tienen una acción registrada.
5. ✅ El proyecto se instala y ejecuta siguiendo el README.
6. ⚠️ Las observaciones de severidad media o baja (CR-02 a CR-05 y CR-08) quedan registradas como deuda técnica conocida para una próxima iteración.

**Resultado:** aprobado con observaciones. El refactoring cumple su objetivo sin regresiones, y la deuda pendiente quedó identificada y priorizada.

# Sistema de Gestión de Turnos Municipales - TPI Metodología de Sistemas II

Repositorio correspondiente al Trabajo Práctico Integrador de la asignatura Metodología de Sistemas II. Este proyecto demuestra la evolución profesional de un sistema de software mediante el diagnóstico de deuda técnica y la aplicación de refactorizaciones seguras.

**Objetivo:**
El código simula el módulo central de atención presencial de una municipalidad. Partiendo de un `estado-inicial` (monolítico y con alta deuda técnica), el proyecto evoluciona hacia una arquitectura limpia y testeable aplicando principios SOLID y Clean Code.

**Tecnologías:**
- Backend: Python 3.10+
- Framework: FastAPI
- Servidor ASGI: Uvicorn
- Persistencia: Archivo local (`datos.json`)

**Instalación y Uso:**
1. Clonar el repositorio: `git clone https://github.com/Pitdog192/TPI_metodologia.git`
2. Crear entorno virtual: `python -m venv venv`
3. Activar entorno virtual y ejecutar: `pip install -r requirements.txt`
4. Iniciar el servidor local: `uvicorn main:app --reload`
5. Acceder a la documentación interactiva (Swagger UI) en: `http://localhost:8000/docs`
6. Ejecutar las pruebas: `python -m pytest -v`

**Funcionalidades:**
- `POST /turnos/solicitar`: registra un turno (y al ciudadano, si es nuevo). Valida que el horario esté libre en el área.
- `PUT /turnos/reasignar/{turno_id}`: cambia la fecha de un turno existente.
- `PUT /turnos/cancelar/{turno_id}`: cancela un turno y libera el horario.
- `GET /turnos/area/{area_id}`: lista los turnos pendientes de un área.

Desde la versión refactorizada, `solicitar` y `reasignar` reciben los datos como JSON en el body (antes eran query params). Ver `docs/04_code_review.md`, observación CR-01.

**Documentación técnica (`/docs`):**
- [01 - Sistema base y diagnóstico](docs/01_diagnostico.md): calidad externa vs. interna, code smells y deuda técnica.
- [02 - SOLID y refactorings](docs/02_solid_y_refactorings.md): refactorings aplicados con el antes/después.
- [03 - Pruebas](docs/03_pruebas.md): casos de prueba y verificación del comportamiento.
- [04 - Code review](docs/04_code_review.md): checklist, observaciones y criterios de aceptación.

**Etapas del Proyecto (Tags):**
- `estado-inicial`: Código base con 8 code smells inyectados.
- `etapa-refactoring`: Aplicación de SOLID y patrones de diseño.
- `estado-refactorizado`: Versión final testeada y aprobada mediante Code Review.
- `etapa-diagnostico`: Diagnóstico de calidad, code smells y deuda técnica.
- `etapa-pruebas`: Pruebas de caracterización antes/después del refactoring.
- `etapa-docs`: Documentación de refactorings, code review y README.

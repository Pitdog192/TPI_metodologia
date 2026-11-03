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
1. Clonar el repositorio: `git clone [URL_DEL_REPO]`
2. Crear entorno virtual: `python -m venv venv`
3. Activar entorno virtual y ejecutar: `pip install -r requirements.txt`
4. Iniciar el servidor local: `uvicorn main:app --reload`
5. Acceder a la documentación interactiva (Swagger UI) en: `http://localhost:8000/docs`

**Etapas del Proyecto (Tags):**
- `estado-inicial`: Código base con 8 code smells inyectados.
- `etapa-refactoring`: Aplicación de SOLID y patrones de diseño.
- `estado-refactorizado`: Versión final testeada y aprobada mediante Code Review.
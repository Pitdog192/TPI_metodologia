"""
Fixtures compartidas por las pruebas de caracterización.

Cada prueba se ejecuta dos veces: una contra el código del tag `estado-inicial`
(obtenido con `git show`) y otra contra el `main.py` actual (versión refactorizada).
Si ambas pasan, el comportamiento externo se mantuvo después del refactoring.
"""
import json
import subprocess
import sys
import types
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

RAIZ_REPO = Path(__file__).resolve().parent.parent
TAG_INICIAL = "estado-inicial"


def _codigo_estado_inicial():
    try:
        resultado = subprocess.run(
            ["git", "show", f"{TAG_INICIAL}:main.py"],
            cwd=RAIZ_REPO, capture_output=True, check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        pytest.skip(f"No se pudo leer el tag '{TAG_INICIAL}' (¿se clonó el repo con sus tags?)")
    return resultado.stdout.decode("utf-8")


def _codigo_refactorizado():
    return (RAIZ_REPO / "main.py").read_text(encoding="utf-8")


# Cada versión expone los mismos endpoints, pero el refactoring (Introduce Parameter Object)
# cambió cómo viajan los datos: antes como query params, ahora como JSON en el body.
VERSIONES = {
    "estado-inicial": (_codigo_estado_inicial, "query"),
    "refactorizado": (_codigo_refactorizado, "json"),
}


def cargar_modulo(nombre, codigo):
    """Ejecuta el código fuente como un módulo nuevo (el import crea datos.json en el cwd)."""
    modulo = types.ModuleType(f"main_{nombre.replace('-', '_')}")
    sys.modules[modulo.__name__] = modulo
    exec(compile(codigo, f"<{nombre}>/main.py", "exec"), modulo.__dict__)
    return modulo


class ClienteTurnos:
    """Envía las mismas operaciones a cualquiera de las dos versiones de la API."""

    def __init__(self, http, formato, carpeta):
        self.http = http
        self.formato = formato
        self.archivo_datos = carpeta / "datos.json"

    def _enviar(self, metodo, url, datos):
        if self.formato == "query":
            return self.http.request(metodo, url, params=datos)
        return self.http.request(metodo, url, json=datos)

    def solicitar(self, **datos):
        return self._enviar("POST", "/turnos/solicitar", datos)

    def reasignar(self, turno_id, nueva_fecha):
        return self._enviar("PUT", f"/turnos/reasignar/{turno_id}", {"nueva_fecha": nueva_fecha})

    def cancelar(self, turno_id):
        return self.http.put(f"/turnos/cancelar/{turno_id}")

    def listar(self, area_id):
        return self.http.get(f"/turnos/area/{area_id}")

    def datos_guardados(self):
        return json.loads(self.archivo_datos.read_text(encoding="utf-8"))


@pytest.fixture(params=list(VERSIONES), ids=list(VERSIONES))
def api(request, tmp_path, monkeypatch):
    # Cada prueba trabaja en una carpeta temporal, así nunca se toca el datos.json del repo.
    monkeypatch.chdir(tmp_path)
    obtener_codigo, formato = VERSIONES[request.param]
    modulo = cargar_modulo(request.param, obtener_codigo())
    with TestClient(modulo.app) as http:
        yield ClienteTurnos(http, formato, tmp_path)


def datos_ciudadano(**cambios):
    datos = {
        "nombre": "Ana",
        "apellido": "Pérez",
        "dni": "30111222",
        "email": "ana.perez@example.com",
        "telefono": "3624000000",
        "fecha_hora": "2026-11-20 09:00",
        "area_id": 1,
    }
    datos.update(cambios)
    return datos

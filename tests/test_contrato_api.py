"""
Documenta el único cambio visible para quien consume la API: con Introduce Parameter Object
los datos de solicitar y reasignar pasaron de query params a un JSON en el body.
Las reglas de negocio no cambiaron (ver test_comportamiento.py).
"""
from fastapi.testclient import TestClient

from conftest import VERSIONES, cargar_modulo, datos_ciudadano


def _cliente(version, carpeta, monkeypatch):
    monkeypatch.chdir(carpeta)
    obtener_codigo, _ = VERSIONES[version]
    return TestClient(cargar_modulo(version, obtener_codigo()).app)


def test_estado_inicial_recibia_los_datos_como_query_params(tmp_path, monkeypatch):
    cliente = _cliente("estado-inicial", tmp_path, monkeypatch)

    respuesta = cliente.post("/turnos/solicitar", params=datos_ciudadano())

    assert respuesta.status_code == 200


def test_version_refactorizada_recibe_los_datos_como_json(tmp_path, monkeypatch):
    cliente = _cliente("refactorizado", tmp_path, monkeypatch)

    con_query = cliente.post("/turnos/solicitar", params=datos_ciudadano())
    con_json = cliente.post("/turnos/solicitar", json=datos_ciudadano())

    assert con_query.status_code == 422
    assert con_json.status_code == 200


def test_version_refactorizada_valida_los_campos_obligatorios(tmp_path, monkeypatch):
    cliente = _cliente("refactorizado", tmp_path, monkeypatch)
    incompleto = datos_ciudadano()
    del incompleto["email"]

    respuesta = cliente.post("/turnos/solicitar", json=incompleto)

    assert respuesta.status_code == 422

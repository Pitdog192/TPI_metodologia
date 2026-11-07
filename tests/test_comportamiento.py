"""
Pruebas de caracterización: describen lo que el sistema hacía en `estado-inicial`
y verifican que la versión refactorizada siga haciendo lo mismo.
Los datos usados son sintéticos (no corresponden a personas reales).
"""
import pytest

from conftest import datos_ciudadano


# --- Solicitar turno ---

def test_solicitar_turno_crea_turno_pendiente(api):
    respuesta = api.solicitar(**datos_ciudadano())

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["mensaje"] == "Turno creado con éxito"
    assert cuerpo["turno"] == {
        "id": 1,
        "ciudadano_id": "30111222",
        "area_id": 1,
        "fecha_hora": "2026-11-20 09:00",
        "duracion": 30,
        "estado": "pendiente",
    }


@pytest.mark.parametrize("area_id, duracion_esperada", [(1, 30), (2, 20), (3, 15), (99, 15)])
def test_duracion_del_turno_depende_del_area(api, area_id, duracion_esperada):
    respuesta = api.solicitar(**datos_ciudadano(area_id=area_id))

    assert respuesta.json()["turno"]["duracion"] == duracion_esperada


def test_los_ids_de_turno_son_correlativos(api):
    primero = api.solicitar(**datos_ciudadano(fecha_hora="2026-11-20 09:00"))
    segundo = api.solicitar(**datos_ciudadano(fecha_hora="2026-11-20 10:00"))

    assert primero.json()["turno"]["id"] == 1
    assert segundo.json()["turno"]["id"] == 2


def test_no_permite_dos_turnos_en_el_mismo_horario_y_area(api):
    api.solicitar(**datos_ciudadano())

    respuesta = api.solicitar(**datos_ciudadano(dni="40555666", email="otro@example.com"))

    assert respuesta.status_code == 400
    assert respuesta.json() == {"detail": "El horario ya está ocupado."}


def test_permite_el_mismo_horario_en_otra_area(api):
    api.solicitar(**datos_ciudadano(area_id=1))

    respuesta = api.solicitar(**datos_ciudadano(area_id=2))

    assert respuesta.status_code == 200


def test_un_horario_cancelado_vuelve_a_estar_disponible(api):
    api.solicitar(**datos_ciudadano())
    api.cancelar(1)

    respuesta = api.solicitar(**datos_ciudadano(dni="40555666"))

    assert respuesta.status_code == 200
    assert respuesta.json()["turno"]["id"] == 2


def test_el_ciudadano_se_registra_una_sola_vez(api):
    api.solicitar(**datos_ciudadano(fecha_hora="2026-11-20 09:00"))
    api.solicitar(**datos_ciudadano(fecha_hora="2026-11-21 09:00"))

    ciudadanos = api.datos_guardados()["ciudadanos"]
    assert ciudadanos == [{
        "dni": "30111222",
        "nombre": "Ana",
        "apellido": "Pérez",
        "email": "ana.perez@example.com",
        "telefono": "3624000000",
    }]


def test_el_turno_queda_persistido_en_el_archivo(api):
    respuesta = api.solicitar(**datos_ciudadano())

    assert api.datos_guardados()["turnos"] == [respuesta.json()["turno"]]


def test_solicitar_envia_notificacion_al_email_del_ciudadano(api, capsys):
    api.solicitar(**datos_ciudadano())

    salida = capsys.readouterr().out
    assert "ENVIANDO" in salida
    assert "ana.perez@example.com" in salida
    assert "2026-11-20 09:00" in salida


# --- Reasignar turno ---

def test_reasignar_cambia_la_fecha_del_turno(api):
    api.solicitar(**datos_ciudadano())

    respuesta = api.reasignar(1, "2026-11-25 11:00")

    assert respuesta.status_code == 200
    assert respuesta.json()["mensaje"] == "Turno reasignado"
    assert respuesta.json()["turno"]["fecha_hora"] == "2026-11-25 11:00"
    assert api.datos_guardados()["turnos"][0]["fecha_hora"] == "2026-11-25 11:00"


def test_reasignar_turno_inexistente_devuelve_404(api):
    respuesta = api.reasignar(42, "2026-11-25 11:00")

    assert respuesta.status_code == 404
    assert respuesta.json() == {"detail": "Turno no encontrado"}


def test_reasignar_a_un_horario_ocupado_devuelve_400(api):
    api.solicitar(**datos_ciudadano(fecha_hora="2026-11-20 09:00"))
    api.solicitar(**datos_ciudadano(dni="40555666", fecha_hora="2026-11-20 10:00"))

    respuesta = api.reasignar(2, "2026-11-20 09:00")

    assert respuesta.status_code == 400
    assert respuesta.json() == {"detail": "El horario ya está ocupado."}


def test_reasignar_envia_notificacion_con_la_nueva_fecha(api, capsys):
    api.solicitar(**datos_ciudadano())
    capsys.readouterr()

    api.reasignar(1, "2026-11-25 11:00")

    salida = capsys.readouterr().out
    assert "ana.perez@example.com" in salida
    assert "2026-11-25 11:00" in salida


# --- Cancelar turno ---

def test_cancelar_marca_el_turno_como_cancelado(api):
    api.solicitar(**datos_ciudadano())

    respuesta = api.cancelar(1)

    assert respuesta.status_code == 200
    assert respuesta.json() == {"mensaje": "Turno cancelado exitosamente"}
    assert api.datos_guardados()["turnos"][0]["estado"] == "cancelado"


def test_cancelar_turno_inexistente_devuelve_404(api):
    respuesta = api.cancelar(42)

    assert respuesta.status_code == 404
    assert respuesta.json() == {"detail": "Turno no encontrado"}


# --- Listar turnos por área ---

def test_listar_devuelve_solo_turnos_pendientes_del_area(api):
    api.solicitar(**datos_ciudadano(area_id=1, fecha_hora="2026-11-20 09:00"))
    api.solicitar(**datos_ciudadano(area_id=1, fecha_hora="2026-11-20 10:00"))
    api.solicitar(**datos_ciudadano(area_id=2, fecha_hora="2026-11-20 09:00"))
    api.cancelar(2)

    respuesta = api.listar(1)

    assert respuesta.status_code == 200
    turnos = respuesta.json()["turnos"]
    assert [t["id"] for t in turnos] == [1]


def test_listar_area_sin_turnos_devuelve_lista_vacia(api):
    respuesta = api.listar(1)

    assert respuesta.json() == {"turnos": []}

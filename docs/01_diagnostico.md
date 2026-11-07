# 1. Sistema base y diagnóstico de calidad

Corresponde al tag `estado-inicial` (commit `1325533`). Las líneas citadas son las del `main.py` de ese tag:

```bash
git show estado-inicial:main.py
```

## 1.1 Sistema base

| Aspecto | Descripción |
|---|---|
| Dominio | Gestión de turnos de atención presencial de una municipalidad. |
| Actores | Ciudadano (pide, reprograma o cancela su turno) y empleado del área (consulta los turnos pendientes). |
| Entidades | Ciudadano, Turno y Área municipal (Licencias = 1, Rentas = 2, resto = área genérica). |
| Operaciones | `POST /turnos/solicitar`, `PUT /turnos/reasignar/{id}`, `PUT /turnos/cancelar/{id}`, `GET /turnos/area/{area_id}`. |
| Persistencia | Archivo local `datos.json` con dos listas: `ciudadanos` y `turnos`. |
| Tecnología | Python 3.10+, FastAPI y Uvicorn. |

Reglas de negocio:

- No puede haber dos turnos no cancelados en la misma área y el mismo horario.
- La duración depende del área: Licencias 30 min, Rentas 20 min y el resto 15 min.
- Un ciudadano se registra la primera vez que pide turno; luego se lo identifica por DNI.
- Cancelar un turno es una baja lógica (`estado = "cancelado"`), y el horario vuelve a quedar libre.
- Al confirmar o reprogramar un turno se notifica al ciudadano por email (simulado con `print`).

## 1.2 Calidad externa vs. calidad interna

**Calidad externa (lo que ve el usuario).** Las cuatro operaciones funcionan y responden con códigos HTTP coherentes: 200 si sale bien, 400 si el horario está ocupado y 404 si el turno no existe. FastAPI genera la documentación interactiva en `/docs`. Para el ciudadano el sistema "anda".

Dos problemas se ven desde afuera aunque la lógica funcione:

- `requirements.txt` está vacío. Si se siguen los pasos del README, `pip install -r requirements.txt` no instala nada y `uvicorn main:app` falla porque falta FastAPI.
- Los datos personales viajan como *query params* (`/turnos/solicitar?nombre=...&dni=...&email=...`). Quedan en la URL, en el historial y en los logs del servidor, y nada valida que estén completos ni bien formados.

**Calidad interna (lo que sufre el equipo).** Todo vive en un único archivo de 148 líneas. Ahí se mezclan las rutas HTTP, la lectura y escritura del JSON, las reglas de negocio y las notificaciones. Cada cambio pequeño, como agregar un área, cambiar el canal de notificación o pasar a una base de datos real, obliga a tocar varias funciones a la vez. Tampoco hay ninguna prueba automática que avise si algo se rompe.

La interfaz no muestra ninguno de estos problemas, pero todos encarecen el próximo cambio. Esa es la diferencia entre las dos miradas: hoy el sistema funciona, pero evolucionarlo es caro y riesgoso.

## 1.3 Deuda técnica y code smells

Escala usada: **impacto** sobre la mantenibilidad (Alto/Medio/Bajo), **riesgo** de que un cambio futuro introduzca un error, y **prioridad** de corrección (1 = primero).

| # | Smell | Ubicación (`estado-inicial`) | Evidencia | Impacto | Riesgo | Prioridad |
|---|---|---|---|---|---|---|
| 1 | God Class / violación de SRP | Todo `main.py` (l. 1–148) | Un solo módulo maneja rutas, persistencia, reglas, validaciones y notificaciones. | Alto | Alto | 1 |
| 2 | Duplicated Code | l. 33–40 y l. 93–100; lectura del JSON en l. 27, 85, 116 y 133; escritura en l. 70, 104 y 125 | El bucle que verifica si el horario está libre está copiado en solicitar y reasignar. El `open` + `json.load/dump` se repite en cada endpoint. | Alto | Alto (si cambia la regla, hay que corregirla en dos lugares) | 1 |
| 3 | Long Method | `solicitar_turno`, l. 22–80 | Casi 60 líneas que leen el archivo, validan, calculan la duración, registran al ciudadano, guardan y notifican. | Alto | Medio | 2 |
| 4 | Long Parameter List | `solicitar_turno`, l. 22 (7 parámetros); `enviar_notificacion`, l. 144 (8 parámetros) | Datos primitivos sueltos en lugar de un objeto. No hay validación de formato. | Medio | Medio (es fácil invertir dos `str` sin que nada lo detecte) | 2 |
| 5 | Shotgun Surgery | `enviar_notificacion`, l. 144–148, y sus llamadas en l. 78 y l. 109 | Agregar un dato o un canal (SMS) obliga a cambiar la firma y todas sus llamadas. Recibe 6 parámetros que no usa. | Medio | Medio | 3 |
| 6 | Magic Numbers | l. 45–49 | `area_id == 1`, `== 2`, `30`, `20`, `15` sin nombre. No se sabe que 1 es Licencias sin leer un comentario. | Medio | Medio (si cambian los ids, falla en silencio) | 3 |
| 7 | Inappropriate Intimacy | l. 60–67 y en todo el archivo (`db["turnos"]`, `t["estado"]`) | Los endpoints conocen y manipulan la estructura cruda del JSON. Cambiar el almacenamiento obliga a reescribirlos. | Medio | Alto | 2 |
| 8 | Feature Envy / código muerto | l. 76 | `nombre_completo` arma un dato que corresponde al ciudadano y que después nunca se usa. | Bajo | Bajo | 4 |

### Deuda técnica adicional detectada

Estos problemas no estaban marcados en los comentarios del código; los encontramos durante el diagnóstico y el code review:

| # | Problema | Ubicación | Impacto | Prioridad |
|---|---|---|---|---|
| 9 | Dependencias no declaradas | `requirements.txt` vacío | El proyecto no se puede instalar con el README. Afecta la calidad externa. | 1 |
| 10 | Strings mágicos para estados | `"pendiente"` y `"cancelado"` en l. 35, 66, 95, 123 y 136 | Un error de tipeo crea un estado nuevo sin que nadie lo note. | 3 |
| 11 | Efectos al importar | `init_db()` en l. 16 | Importar el módulo crea `datos.json` en la carpeta actual. Complica las pruebas. | 3 |
| 12 | Sin pruebas automáticas | Repositorio | No hay forma de verificar que un cambio no rompe el comportamiento. | 1 |

### Orden de corrección recomendado

1. Tener pruebas de caracterización que fijen el comportamiento actual (#12) y declarar las dependencias (#9).
2. Separar responsabilidades: persistencia, servicio y notificación (#1, #7).
3. Eliminar la duplicación con Extract Method (#2) y partir el método largo (#3).
4. Introducir objetos de parámetros (#4) y simplificar la notificación (#5).
5. Reemplazar los números mágicos (#6), borrar el código muerto (#8) y, como deuda pendiente, los strings mágicos (#10).

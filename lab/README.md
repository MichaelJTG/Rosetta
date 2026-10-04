# Laboratorio del Modo Auditoría (RF-06)

Objetivo **propio y local** para demostrar el Modo Auditoría (Nuclei + Nmap)
sin escanear sistemas de terceros. Es un nginx en la red interna de Docker
Compose: **no publica ningún puerto** en el equipo anfitrión y solo es accesible
desde el contenedor de ROSETTA.

Tiene errores de configuración **intencionados** y contenido **ficticio**:

| Fallo intencionado | Fichero | Qué debería detectar |
|---|---|---|
| Versión del servidor visible (`server_tokens on`) | `nginx.conf` | Nmap / Nuclei (divulgación de tecnología) |
| Listado de directorio en `/backups/` | `nginx.conf` | Nuclei (directory listing) |
| Fichero `.env` publicado con valores falsos | `www/.env` | Nuclei (exposición de configuración) |
| Sin cabeceras de seguridad HTTP | `nginx.conf` | Nuclei (cabeceras ausentes) |

## Uso

1. Autoriza el laboratorio **en el servidor**, en `.env`:
   `ROSETTA_AUDIT_ALLOWLIST=lab-objetivo`.
   Sin esa línea, ROSETTA lo rechaza porque resuelve a una IP privada (B-8).
2. Arranca el laboratorio junto a ROSETTA:
   `docker compose --profile lab up -d`.
3. En el dashboard, pestaña **Modo Auditoría**:
   - objetivo `http://lab-objetivo`;
   - adaptadores Nuclei y Nmap;
   - declaración de alcance, por ejemplo: «Laboratorio propio local, contenedor
     lab-objetivo, autorizado por el autor para la demo de la P3».
4. Para pararlo: `docker compose --profile lab down`.

Uso ético: este laboratorio es el único objetivo de las demostraciones. Nunca se
escanean sistemas de terceros, ni siquiera "para comprobar que funciona".

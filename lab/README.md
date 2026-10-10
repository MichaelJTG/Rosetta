# Laboratorio del Modo Auditoría (RF-06)

Objetivo **propio y local** para demostrar el Modo Auditoría (Nuclei + Nmap)
sin escanear sistemas de terceros. Es un nginx en la red interna de Docker
Compose: **no publica ningún puerto** en el equipo anfitrión y solo es accesible
desde el contenedor de ROSETTA.

Tiene errores de configuración **intencionados** y contenido **ficticio**:

| Fallo intencionado | Fichero | Qué detecta (auditoría real del 2026-10-10) |
|---|---|---|
| Versión del servidor visible (`server_tokens on`) | `nginx.conf` | Nuclei `nginx-version`, `nginx-eol`, `tech-detect` (info) y Nmap (puerto 80/tcp abierto, servicio identificado con `-sV`) |
| Fichero `.env` publicado con valores falsos | `www/.env` | Nuclei `generic-env`, `laravel-env`, `codeigniter-env` (high) |
| Sin cabeceras de seguridad HTTP | `nginx.conf` | Nuclei `http-missing-security-headers` (info) |
| Listado de directorio en `/backups/` | `nginx.conf` | **No lo detecta**: ninguna plantilla pública de Nuclei prueba la ruta `/backups/`, y Nuclei no rastrea enlaces |

Resultado con la configuración por defecto (`ROSETTA_NUCLEI_TAGS=exposure,misconfig,tech`,
todas las severidades): 18 hallazgos, 17 de Nuclei y 1 de Nmap, en unos 40 s.

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

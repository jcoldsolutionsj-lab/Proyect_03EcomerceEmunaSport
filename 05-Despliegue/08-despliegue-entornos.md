# 08 – Despliegue y entornos

## Entornos
| Entorno | Base de datos | Dónde | Para qué |
|---|---|---|---|
| `local` | SQLite | Computadora de Jonathan | Desarrollo y pruebas |
| `demo` | PostgreSQL de prueba o SQLite con datos de ejemplo | Render (web service) | Que Richard vea y pruebe el piloto |
| `production` | PostgreSQL persistente | Render con plan de pago + Cloudflare | Operación real |

## Limitaciones del plan gratuito de Render (verificar antes de depender de ellas)
- Un **Static Site** no ejecuta Django. Se necesita un **Web Service**.
- Un web service gratuito se apaga tras unos 15 minutos sin tráfico y tarda alrededor de un minuto en volver a arrancar.
- El disco es efímero: SQLite local y los archivos subidos se pierden al reiniciar o redesplegar.
- La base PostgreSQL gratuita expira a los 30 días.

Consecuencia: en `demo` la base se **recrea con datos de ejemplo** en cada despliegue (`python manage.py seed_demo`). Es normal que los datos de la demo se reinicien. Para producción se usa PostgreSQL persistente.

## Fotos
Las fotos van a un bucket compatible con S3 (Cloudflare R2) desde el principio, para que sobrevivan los reinicios. En `local` pueden usar el disco.

## Cloudflare y dominio
- La cuenta de Cloudflare se crea **a nombre de Richard**, con su correo; Jonathan entra como miembro con acceso y 2FA.
- El dominio oficial se registra y se paga bajo esa cuenta; DNS apuntando al servicio en Render.
- Acordar por escrito qué pertenece a Richard (dominio, cuentas, datos, fotos) y qué a Jonathan (código y licencia de uso).

## Variables de entorno (ejemplo en `.env.example`, sin valores reales)
`DJANGO_SETTINGS_MODULE`, `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL`, `CSRF_TRUSTED_ORIGINS`, `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_PUBLIC`, `R2_BUCKET_PRIVATE`, `R2_PUBLIC_URL`, `SITE_URL`, `TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY`, `GA4_MEASUREMENT_ID`.

## Despliegue en Render (resumen)
- Build: instalar dependencias, `collectstatic`, `migrate`.
- Start: `gunicorn config.wsgi`.
- Archivo `render.yaml` versionado, sin secretos.
- Verificar tras cada despliegue: página de inicio, un pedido de prueba, el PDF y el admin.

## Antes de salir a producción (Checklist completo en doc 15)
Dominio y HTTPS activos; PostgreSQL persistente con respaldo; bucket R2 configurado; QR y titular de Yape cargados por el admin y confirmados con Richard; usuarios y grupos creados; pruebas unitarias, E2E (Playwright), carga (Grafana k6 en `03-Diseno-Tecnico/pruebas-carga-k6/`) y los **20 puntos de `05-Despliegue/15-checklist-antes-de-lanzar-web.md`** verificados al 100%; `DEBUG=False`.

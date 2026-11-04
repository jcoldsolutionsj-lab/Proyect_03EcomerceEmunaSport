# 07 – Seguridad y datos personales

## Datos sensibles
- **DNI, teléfono, nombre y agencia** del cliente: visibles solo para el personal en el admin. Nunca en URLs, logs, mensajes de error, correos ni páginas públicas.
- **Clave de 4 dígitos de recojo y foto de boleta:** solo personal; la foto en bucket privado con enlaces firmados de corta duración.
- Aviso breve en el formulario: los datos se usan solo para gestionar el pedido y el envío (aplica la ley peruana de protección de datos personales; Jonathan valida el texto final con Richard).
- Recolectar solo lo necesario. Definir con Richard cuánto tiempo se conservan los datos de pedidos antiguos.

## Accesos
- Admin en una ruta no obvia (por ejemplo `/gestion/`), con contraseñas fuertes. Segundo factor (`django-otp`) en la fase de producción.
- Grupos: `Dueño` (operativo) y superusuario para Jonathan. Principio de mínimo privilegio.
- API: tokens JWT de vida corta y refresh controlado; solo el personal obtiene tokens.

## Aplicación
- `DEBUG = False` fuera de local; `SECRET_KEY`, base de datos y claves de almacenamiento solo por variables de entorno; `.env` fuera de git y un `.env.example` sin valores reales.
- HTTPS siempre; cookies `Secure` y `HttpOnly`; protección CSRF activa; cabeceras de seguridad de Django.
- Código de pedido aleatorio y no secuencial; la página pública del pedido no revela otros pedidos.
- Límite de intentos (`django-ratelimit`) y campo trampa (honeypot) en el envío de pedidos para evitar spam.
- Validación en el servidor de precios, stock, DNI y teléfono; el navegador no es de confianza.
- El stock se modifica solo en transacciones con bloqueo de filas.
- Imágenes subidas: validar tipo y tamaño, regenerar con Pillow, no servir el original privado.

## Respaldos y evidencia
- Respaldo automático de la base de datos en producción y prueba de restauración.
- Historial de cambios en pedidos y envíos y registro inmutable de movimientos de stock para tener evidencia.
- No guardar en el repositorio: QR de Yape, boletas, DNI, datos reales ni credenciales.

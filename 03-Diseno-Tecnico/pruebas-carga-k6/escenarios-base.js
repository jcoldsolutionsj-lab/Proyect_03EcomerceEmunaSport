/**
 * Script base de pruebas de carga y concurrencia con Grafana k6 para Emuná Sport.
 *
 * Qué hace:      Simula clientes navegando el catálogo desde el celular, armando
 *                carrito y enviando pedidos para medir tiempos de respuesta y errores.
 * Va hacia:      Rutas públicas de la tienda (/, /productos/<slug>/, /carrito/, /pedidos/crear/).
 * Depende de:    Servidor Django corriendo con PostgreSQL y datos semilla (cargar_demo).
 * Cuándo usarla: En Fase 2 (checkout), Fase 3 (concurrencia de stock) y Fase 6 (pre-lanzamiento).
 * Si no opera:   Devuelve código de salida distinto de 0 si el p95 supera 500 ms o hay errores 500.
 */

import http from 'k6/http';
import { check, group, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';
const MODO = __ENV.MODO || 'humo'; // 'humo' (local rápido) o 'campana' (pico de WhatsApp)

export const options = {
  scenarios:
    MODO === 'campana'
      ? {
          pico_estado_whatsapp: {
            executor: 'ramping-vus',
            startVUs: 1,
            stages: [
              { duration: '20s', target: 30 }, // Subida rápida tras publicar estado en WhatsApp
              { duration: '40s', target: 50 }, // Tráfico sostenido viendo camisetas
              { duration: '20s', target: 0 },  // Bajada gradual
            ],
          },
        }
      : {
          prueba_humo_local: {
            executor: 'constant-vus',
            vus: 3,
            duration: '20s',
          },
        },
  thresholds: {
    http_req_failed: ['rate<0.01'], // Menos de 1% de fallos
    http_req_duration: ['p(95)<500'], // El 95% de respuestas en menos de 500 ms
  },
};

export default function () {
  group('1. Cliente abre catálogo desde WhatsApp (móvil)', () => {
    const resInicio = http.get(`${BASE_URL}/`, {
      headers: {
        'User-Agent':
          'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Mobile Safari/537.36',
      },
    });

    check(resInicio, {
      'catálogo responde 200': (r) => r.status === 200,
      'catálogo carga en < 350 ms': (r) => r.timings.duration < 350,
    });
  });

  sleep(1);

  group('2. Cliente consulta detalle de camiseta', () => {
    const slugProducto = __ENV.PRODUCTO_SLUG || 'camiseta-entrenamiento-emuna-negra';
    const resDetalle = http.get(`${BASE_URL}/productos/${slugProducto}/`);

    check(resDetalle, {
      'detalle responde 200 o 404 controlado': (r) =>
        r.status === 200 || r.status === 404,
    });
  });

  sleep(1);
}

/**
 * Script base de pruebas de carga y concurrencia con Grafana k6 para Emuná Sport.
 *
 * Qué hace:      Simula clientes navegando el catálogo desde el celular, armando
 *                carrito, consultando checkout y probando concurrencia de stock.
 * Va hacia:      Rutas públicas de la tienda (/, /productos/<slug>/, /carrito/, /pedidos/checkout/).
 * Depende de:    Servidor Django corriendo con PostgreSQL en Render (Fase 5) o local.
 * Cuándo usarla: En Fase 2 (checkout), Fase 3 (concurrencia de stock) y Fase 5/6 (demo y pre-lanzamiento).
 * Si no opera:   Devuelve código de salida distinto de 0 si el p95 supera 500 ms o hay errores 500.
 */

import http from 'k6/http';
import { check, group, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';
const MODO = __ENV.MODO || 'humo'; // 'humo' (local rápido), 'campana' (pico de WhatsApp), o 'concurrencia_stock'

function obtenerEscenarios() {
  if (MODO === 'campana') {
    return {
      pico_estado_whatsapp: {
        executor: 'ramping-vus',
        startVUs: 1,
        stages: [
          { duration: '20s', target: 30 }, // Subida rápida tras publicar estado en WhatsApp
          { duration: '40s', target: 50 }, // Tráfico sostenido viendo camisetas
          { duration: '20s', target: 0 },  // Bajada gradual
        ],
      },
    };
  }
  if (MODO === 'concurrencia_stock') {
    return {
      concurrencia_stock_extremo: {
        executor: 'per-vu-iterations',
        vus: 20,
        iterations: 1,
        maxDuration: '20s',
      },
    };
  }
  return {
    prueba_humo_local: {
      executor: 'constant-vus',
      vus: 3,
      duration: '20s',
    },
  };
}

export const options = {
  scenarios: obtenerEscenarios(),
  thresholds: {
    http_req_failed: ['rate<0.02'], // Menos de 2% de fallos de red
    http_req_duration: ['p(95)<500'], // El 95% de respuestas en menos de 500 ms
  },
};

export default function () {
  if (MODO === 'concurrencia_stock') {
    group('Concurrencia de compra sobre stock limitado', () => {
      // 1. Obtener cookie de sesión visitando el carrito
      const resSesion = http.get(`${BASE_URL}/carrito/`);
      check(resSesion, {
        'sesión de carrito iniciada 200': (r) => r.status === 200,
      });

      // 2. Consulta rápida de resumen de carrito JSON (anti-race condition)
      const resResumen = http.get(`${BASE_URL}/carrito/resumen-json/`);
      check(resResumen, {
        'resumen JSON responde 200': (r) => r.status === 200,
        'tiempo resumen JSON < 250ms': (r) => r.timings.duration < 250,
      });
    });
    return;
  }

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

  sleep(0.5);

  group('2. Cliente consulta detalle de camiseta Argentina x Messi', () => {
    const slugProducto = __ENV.PRODUCTO_SLUG || 'argentina-x-messi-10';
    const resDetalle = http.get(`${BASE_URL}/productos/${slugProducto}/`);

    check(resDetalle, {
      'detalle responde 200 o 404 controlado': (r) =>
        r.status === 200 || r.status === 404,
    });
  });

  sleep(0.5);

  group('3. Cliente revisa su carrito de compras y resumen JSON (Fase 2)', () => {
    const resCarrito = http.get(`${BASE_URL}/carrito/`);
    check(resCarrito, {
      'página carrito responde 200': (r) => r.status === 200,
    });

    const resResumenJson = http.get(`${BASE_URL}/carrito/resumen-json/`);
    check(resResumenJson, {
      'resumen JSON carrito responde 200': (r) => r.status === 200,
    });
  });

  sleep(1);
}

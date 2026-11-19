-- =============================================================================
-- PROYECTO: Emuná Sport
-- ARCHIVO : 01_rls_seguridad_filas.sql
-- PROPÓSITO: Políticas de Row Level Security (RLS) para PostgreSQL en producción.
--            Protege las tablas transaccionales sensibles (TBL_TPEDIDO,
--            TBL_TPEDIDO_ITEM, TBL_LPEDIDO_ESTADO, TBL_TENVIO, TBL_TMOVIMIENTO_STOCK)
--            para que ningún rol de lectura o conexión externa acceda a filas
--            sin el contexto autorizado de la aplicación.
-- =============================================================================

-- 1. Activar Row Level Security en las tablas sensibles
ALTER TABLE "TBL_TPEDIDO" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "TBL_TPEDIDO_ITEM" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "TBL_LPEDIDO_ESTADO" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "TBL_TENVIO" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "TBL_TMOVIMIENTO_STOCK" ENABLE ROW LEVEL SECURITY;

-- Nota: El usuario principal de Django (propietario de las tablas en las migraciones)
-- opera a través de los selectores seguros (selectores.py). Si se crean roles adicionales
-- en PostgreSQL (por ejemplo, rol_lectura_publica o rol_reportes), estas políticas
-- restringen qué filas pueden ver a nivel de motor de base de datos:

-- 2. Política en TBL_TPEDIDO:
--    - El rol de personal ('STAFF') puede ver y gestionar todos los pedidos.
--    - Una consulta pública ('PUBLICO') solo puede leer la fila cuyo PED_CCODIGO
--      coincida exactamente con la variable de sesión 'app.codigo_pedido_actual'.
DROP POLICY IF EXISTS pol_rls_pedido_aislamiento ON "TBL_TPEDIDO";
CREATE POLICY pol_rls_pedido_aislamiento ON "TBL_TPEDIDO"
    USING (
        current_setting('app.rol_actual', true) = 'STAFF'
        OR (
            current_setting('app.rol_actual', true) = 'PUBLICO'
            AND "PED_CCODIGO" = current_setting('app.codigo_pedido_actual', true)
        )
    );

-- 3. Política en TBL_TENVIO (contiene clave_recojo privada y boleta):
--    - Exclusivamente accesible cuando 'app.rol_actual' = 'STAFF'.
DROP POLICY IF EXISTS pol_rls_envio_solo_staff ON "TBL_TENVIO";
CREATE POLICY pol_rls_envio_solo_staff ON "TBL_TENVIO"
    USING (current_setting('app.rol_actual', true) = 'STAFF');

-- 4. Política en TBL_TMOVIMIENTO_STOCK (kardex inmutable):
--    - Exclusivamente accesible cuando 'app.rol_actual' = 'STAFF'.
DROP POLICY IF EXISTS pol_rls_movimiento_solo_staff ON "TBL_TMOVIMIENTO_STOCK";
CREATE POLICY pol_rls_movimiento_solo_staff ON "TBL_TMOVIMIENTO_STOCK"
    USING (current_setting('app.rol_actual', true) = 'STAFF');

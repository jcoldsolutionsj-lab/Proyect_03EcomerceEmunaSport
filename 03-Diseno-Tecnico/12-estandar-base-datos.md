# 12 – Estándar de base de datos

Adaptación a Emuná Sport del manual **«Estándares Área de Desarrollo»** (Atento Colombia, ed. 1.6). El PDF original está en `03-Diseno-Tecnico/estandares/estandares-area-desarrollo-2.pdf`.

> [!NOTE]
> **Decisiones confirmadas por Jonathan (2026-11-03):**
> 1. Tanto el **código Python** como los **nombres físicos de la base de datos** van en **español**.
> 2. Las tablas, columnas, vistas e índices van en **MAYÚSCULAS** siguiendo el estándar `TBL_`.
> 3. La fuente única del diccionario es `base-datos/generar_diccionario.py`, que valida las reglas y genera `diccionario-datos.md`, `diccionario-datos.xlsx` y `modelo-er.md`.

## 1. Estándar de nombres

### 1.1 Base de datos
Formato `CAMPAÑA_CLIENTE` en MAYÚSCULAS y singular: **`TIENDA_WEB_EMUNA_SPORT`** (en Render el proveedor asigna el nombre).

### 1.2 Tablas
Formato: `TBL_` + letra de convención + cuerpo en **MAYÚSCULAS**, **singular** y **español**, separado por `_`.

| Letra | Tipo de tabla | Tablas en Emuná Sport |
|---|---|---|
| `R` | Referencia / maestro | `TBL_RCONFIGURACION_TIENDA`, `TBL_RMETODO_PAGO`, `TBL_RCATEGORIA`, `TBL_RPRODUCTO`, `TBL_RIMAGEN_PRODUCTO`, `TBL_RVARIANTE`, `TBL_RREGLA_PRECIO` |
| `T` | Transacción | `TBL_TMOVIMIENTO_STOCK`, `TBL_TPEDIDO`, `TBL_TPEDIDO_ITEM`, `TBL_TENVIO` |
| `L` | Log (bitácora) | `TBL_LPEDIDO_ESTADO` |
| `H` | Histórico | `TBL_HPEDIDO` (`django-simple-history`) |

### 1.3 Columnas
Formato: `PPP_` + letra de tipo + cuerpo en **MAYÚSCULAS**, singular y español.
- `PPP` = sigla única de **3 letras** de la tabla (`CTI`, `MPA`, `CAT`, `PRO`, `IMA`, `VAR`, `REG`, `MOV`, `PED`, `ITE`, `PES`, `HPE`, `ENV`).
- Letra de tipo: `N` numérico (enteros, llaves y `numeric(10,2)`), `C` carácter, `D` fecha o fecha-hora, `B` binario, `O` booleano.
- Llave primaria: `PPP_NID` (ej. `PED_NID`).
- Llave foránea: **conserva el nombre de la llave primaria** que referencia (ej. `TBL_TPEDIDO_ITEM` tiene `PED_NID` y `VAR_NID`). Hacia `auth_user` se usa `USU_NID_<ROL>` (ej. `USU_NID_CREADO_POR`).

### 1.4 Otros objetos y scripts
| Objeto | Formato | Ejemplo |
|---|---|---|
| Vista | `VW_` + cuerpo (query en minúsculas) | `VW_RESUMEN_PEDIDO` |
| Función | `FUN_` + cuerpo | `FUN_TOTAL_PEDIDO` |
| Trigger | `TRG_` + `INS`/`UPD`/`DEL` + cuerpo | `TRG_UPD_MOVIMIENTO_STOCK_BLOQUEO` |
| Índice / Único / Check | sufijo `_IX`, `_UK`, `_CK` | `TBL_TPEDIDO_PED_CCODIGO_UK` |
| Script puntual | `base-datos/scripts/s_emuna_<tema>_ddmmaaaa.sql` | `s_emuna_ajustes_03112026.sql` |
| Script completo BD | `base-datos/scripts-bd/sbd_ddmmaaaa.sql` | `sbd_03112026.sql` |

Reglas en scripts SQL: palabras reservadas en minúsculas, objetos y alias en MAYÚSCULAS (el alias es la sigla de 3 letras de la tabla), **prohibido usar cursores**, fechas mostradas como `dd/mm/aaaa` y cabecera obligatoria con autor, fecha, propósito y modificaciones.

```sql
select PED."PED_CCODIGO", ITE."ITE_CNOMBRE_PRODUCTO", ITE."ITE_NCANTIDAD"
from "TBL_TPEDIDO" PED
inner join "TBL_TPEDIDO_ITEM" ITE on PED."PED_NID" = ITE."PED_NID"
where PED."PED_CESTADO" = 'PAGADO'
```
*(En PostgreSQL los identificadores en MAYÚSCULAS van entre comillas dobles en consultas SQL escritas a mano; el ORM de Django las pone automáticamente).*

## 2. Adaptaciones a Django + PostgreSQL
1. **Sin procedimientos almacenados para lógica de negocio:** toda la lógica vive en `servicios.py` y `selectores.py` para poder probarla con `pytest`.
2. **Triggers solo para invariantes:** por ejemplo, impedir `UPDATE` o `DELETE` en `TBL_TMOVIMIENTO_STOCK` y `TBL_LPEDIDO_ESTADO`.
3. **Contraseñas con hash (PBKDF2 de Django)** y cadena de conexión en variable de entorno (`DATABASE_URL`).
4. **Tablas internas de Django (`auth_*`, `django_*`)** conservan su nombre original para no romper migraciones del framework.
5. **Verificación automática:** `python 03-Diseno-Tecnico/base-datos/generar_diccionario.py` valida todas las tablas y columnas y regenera el Markdown, el Excel y el diagrama ER. En la Fase 0 se agrega además un test de `pytest` que inspecciona los modelos de Django.

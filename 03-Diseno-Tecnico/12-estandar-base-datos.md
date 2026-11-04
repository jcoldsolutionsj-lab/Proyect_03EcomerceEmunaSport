# 12 – Estándar de base de datos

Adaptación a Emuná Sport del manual **«Estándares Área de Desarrollo»** (Atento Colombia, ed. 1.6). El PDF original está en `03-Diseno-Tecnico/estandares/estandares-area-desarrollo-2.pdf`. Este documento dice **qué se adopta tal cual, qué se adapta y por qué**, porque el proyecto usa Django (ORM) y PostgreSQL, y el manual está pensado para SQL Server con procedimientos almacenados.

> [!NOTE]
> Los nombres **físicos** (los que se ven en PostgreSQL) siguen este estándar. Los nombres en **Python** (clases y campos de Django) siguen la regla del proyecto: inglés y estilo Django. El puente es `db_table` y `db_column` en cada modelo. El diccionario completo está en `base-datos/diccionario-datos.md`.

## 1. Lo que se adopta tal cual

### 1.1 Tablas
Formato: `TBL_` + una letra de convención + cuerpo. Todo en **MAYÚSCULAS**, **singular**, palabras separadas por `_`, sin espacios ni caracteres especiales.

| Letra | Tipo de tabla | Uso en Emuná Sport |
|---|---|---|
| `T` | Transacción | Pedidos, ítems, envíos, movimientos de stock |
| `R` | Referencia / maestro | Categorías, productos, variantes, precios, ajustes, métodos de pago |
| `H` | Histórico | Historial de cambios de pedidos (`django-simple-history`) |
| `L` | Log | Bitácora de cambios de estado |
| `U` | Unión (muchos a muchos) | Aún no hay; reservada |
| `A` | Auditoría | Reservada |
| `C` / `D` / `#` / `RP` | Carga / depuración / temporal / repositorio | Reservadas |

Ejemplos: `TBL_TORDER`, `TBL_RPRODUCT`, `TBL_LORDER_STATUS`.

### 1.2 Columnas
Formato: `PPP_` + letra de tipo + cuerpo. Todo en **MAYÚSCULAS**, singular.
- `PPP` = sigla de **3 letras** de la tabla (ver diccionario; no puede repetirse entre tablas).
- Letra de tipo: `N` numérico, `C` carácter, `D` fecha, `B` binario, `O` booleano.
- Llave primaria: cuerpo `ID`. Ejemplo: `ORD_NID`.
- Una llave foránea **conserva el nombre de la llave primaria** que referencia. Ejemplo: `TBL_TORDER_ITEM` tiene `ORD_NID` (pedido) y `VAR_NID` (variante).
- Si una tabla referencia **dos veces** a la misma tabla, se agrega una palabra clave al final: `USR_NID_CREATED_BY`.

### 1.3 Otros objetos
| Objeto | Formato | Ejemplo |
|---|---|---|
| Vista | `VW_` + cuerpo (MAYÚSCULAS, singular); el `select` va en minúsculas | `VW_ORDER_SUMMARY` |
| Función | `FUN_` + cuerpo | `FUN_ORDER_TOTAL` |
| Trigger | `TRG_` + tipo (`INS`, `UPD`, `DEL`) + cuerpo | `TRG_UPD_STOCK_MOVEMENT_BLOCK` |
| Procedimiento | `SPR_` + tipo (`GET`, `INS`, `UPD`, `DEL`, combinados en orden alfabético) + cuerpo | `SPR_GET_ORDER_BY_CODE` |
| Parámetros | `@PI_`, `@PO_`, `@PIO_` + letra de tipo + cuerpo | `@PI_NID_ORDER` |
| Variables | `@` + letra de tipo + cuerpo | `@DCURRENT_DATE` |
| Índice | sufijo `IX` | `TBL_TORDER_ORD_CSTATUS_ORD_DCREATED_AT_IX` |
| Llave primaria | sufijo `PK` | `TBL_TORDER_PK` |
| Llave foránea | sufijo `FK` | `TBL_TORDER_ITEM_ORD_NID_FK` |

### 1.4 Scripts SQL
- Palabras reservadas de SQL en **minúsculas**; objetos (tablas, columnas) según este estándar.
- **Alias en MAYÚSCULAS**, y el alias de la tabla es su sigla de 3 letras. Todas las tablas cruzadas llevan alias.
- **Prohibido usar cursores.**
- Consultas bien tabuladas.
- Fechas en formato **dd/mm/aaaa** al mostrarse. En la base se guardan como `DATE` o `TIMESTAMPTZ`, nunca como texto.
- Todo objeto o script lleva el comentario de cabecera:

```sql
/*---------------------------------------------------------------------------------------------
  Autor           : Nombre del autor
  Fecha Creación  : dd/mm/aaaa
  Propósito       : Frase breve sobre el propósito central
  Entradas        : Lista de datos de entrada con su descripción
  Salidas         : Lista de datos de salida con su descripción
  Consideraciones : Validaciones o efectos importantes
  Modificaciones  :
    Fecha modificación dd/mm/aaaa – Responsable
    Cambio realizado : explicación (se lleva el historial)
-----------------------------------------------------------------------------------------------*/
```

Ejemplo de consulta con el estándar:

```sql
select ORD.ORD_CCODE, ORI.ORI_CPRODUCT_NAME, ORI.ORI_NQUANTITY
from TBL_TORDER ORD
inner join TBL_TORDER_ITEM ORI on ORD.ORD_NID = ORI.ORD_NID
where ORD.ORD_CSTATUS = 'PAID'
```

### 1.5 Archivos de scripts
| Carpeta | Contenido | Nombre del archivo |
|---|---|---|
| `base-datos/scripts/` | Scripts puntuales (ajustes, datos, correcciones) | `s_emuna_<tema>_ddmmaaaa.sql` — ej. `s_emuna_ajustes_03112026.sql` |
| `base-datos/scripts-bd/` | Script **completo** de la base, uno por cada paso a producción | `sbd_ddmmaaaa.sql` — ej. `sbd_03112026.sql` |
| `base-datos/modelo-er.md` | Modelo Entidad-Relación (Mermaid, en lugar de Visio) | — |

### 1.6 Versionado `X.Y.Z`
- `X` cambia al iniciar una nueva evolución del sistema; `Y` para cambios internos que no afectan la interfaz; `Z` para correcciones y parches. Al subir `X` o `Y`, los números siguientes vuelven a 0.
- La primera versión en producción es **1.1.0**.
- Etapas: **alfa** (se construye, Fases 0 a 4) → **beta** (Richard prueba en el piloto, Fase 5) → **estable** (producción, Fase 6).
- Cada versión se marca con una etiqueta git `vX.Y.Z` y se anota en `00-Gestion/11-decisiones-cambios.md`.

## 2. Lo que se adapta (con motivo)

| Punto del manual | Adaptación | Motivo |
|---|---|---|
| Procedimientos almacenados para la lógica (`SPR_`) | **No se usan** para lógica de negocio. La lógica vive solo en `services.py` y `selectors.py`. | Es regla obligatoria del proyecto y permite probarla con `pytest`. El formato `SPR_` queda reservado por si algún día hace falta. |
| Triggers y funciones | Se permiten **solo** para proteger invariantes de datos (ej.: que `TBL_TSTOCK_MOVEMENT` no se edite ni se borre). | Una regla de integridad debe cumplirse aunque alguien toque la base directamente. |
| Cifrado de login y clave (1.2.2) | Las contraseñas se guardan con **hash** (PBKDF2 de Django), no cifradas. | El hash es más seguro porque no es reversible. |
| Cifrado de la cadena de conexión | Va en **variables de entorno** (`DATABASE_URL`), nunca en el repositorio. | Regla de seguridad del proyecto. |
| Nombre de la base: `CAMPAÑA_CLIENTE` | Propuesta local: `TIENDA_WEB_EMUNA_SPORT`. En Render el proveedor asigna el nombre. | Render no permite elegirlo libremente. |
| Fechas `dd/mm/aaaa` | Solo para **mostrar** (plantillas, PDF, scripts). | El tipo de dato es fecha, no texto. |
| Tablas del propio Django (`auth_*`, `django_*`) | Se **dejan con su nombre**. | Pertenecen al framework; renombrarlas rompe las actualizaciones. |
| Llave foránea hacia usuario | `USR_NID_<ROL>` aunque la llave de `auth_user` se llama `id`. | `auth_user` es del framework (punto anterior). |
| Nombres de llaves PK y FK | Django les pone nombre automático. Los índices y restricciones propias sí se nombran con el estándar. | Limitación del ORM. Renombrar PK y FK con una migración queda como pendiente. |
| Idioma de los cuerpos | **Inglés**, igual que el código. El diccionario trae la descripción en español. | Regla del proyecto (código en inglés) y menos traducción entre capas. |
| Nombres largos | Máximo **63 caracteres** (límite de PostgreSQL). | Si un nombre se pasa, se abrevia el cuerpo y se anota en el diccionario. |

> [!IMPORTANT]
> PostgreSQL pasa a minúsculas los nombres sin comillas. Como el estándar exige MAYÚSCULAS, los nombres se crean **entre comillas** (Django lo hace solo). En herramientas externas (pgAdmin, scripts a mano) hay que escribirlos así: `select "ORD_CCODE" from "TBL_TORDER"`. Está anotado como decisión pendiente en el doc 11 por si se prefiere minúsculas.

## 3. Cómo se aplica en Django
1. Cada modelo declara `db_table` y cada campo `db_column` con el nombre físico del diccionario.
2. Un modelo base en `core` (con `created_at` y `updated_at` → `PPP_DCREATED_AT`, `PPP_DUPDATED_AT`) evita repetir lo común.
3. Un test de `pytest` recorre todos los modelos propios y falla si una tabla o columna no cumple el patrón (prefijo `TBL_`, sigla única de 3 letras, letra de tipo válida, longitud ≤ 63). Así el estándar se **verifica solo**.
4. Las tablas históricas de `django-simple-history` se nombran con `table_name='TBL_H…'`.
5. Cada release genera `scripts-bd/sbd_ddmmaaaa.sql` (volcado completo del esquema) y se guarda en el repositorio.

## 4. Relación con otros documentos
- Modelo lógico: `04-modelo-de-datos.md` (qué datos hay y qué reglas cumplen).
- Este documento y el diccionario: **cómo se llaman** esos datos en la base.
- Si cambia el modelo lógico, se actualiza el diccionario y se anota en el doc 11.

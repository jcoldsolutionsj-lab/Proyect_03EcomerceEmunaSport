# Modelo Entidad-Relación

> Generado por `generar_diccionario.py`. **No editar a mano.**

Con los nombres físicos del estándar (`../12-estandar-base-datos.md`). Detalle de columnas en `diccionario-datos.md`. `AUTH_USER` es la tabla `auth_user` de Django.

```mermaid
erDiagram
  TBL_RCATEGORIA ||--o{ TBL_RPRODUCTO : "clasifica"
  TBL_RPRODUCTO ||--o{ TBL_RIMAGEN_PRODUCTO : "tiene fotos"
  TBL_RPRODUCTO ||--o{ TBL_RVARIANTE : "tiene variantes"
  TBL_RPRODUCTO ||--o{ TBL_RREGLA_PRECIO : "tiene precios por mayor"
  TBL_RVARIANTE ||--o{ TBL_TMOVIMIENTO_STOCK : "mueve stock"
  TBL_RVARIANTE ||--o{ TBL_TPEDIDO_ITEM : "se vende en"
  TBL_TPEDIDO ||--|{ TBL_TPEDIDO_ITEM : "contiene"
  TBL_TPEDIDO ||--o{ TBL_TMOVIMIENTO_STOCK : "origina"
  TBL_TPEDIDO ||--o{ TBL_LPEDIDO_ESTADO : "registra estados"
  TBL_TPEDIDO ||--o| TBL_TENVIO : "se envía con"
  TBL_TPEDIDO ||--o{ TBL_HPEDIDO : "historial"
  TBL_RMETODO_PAGO |o--o{ TBL_TPEDIDO : "se paga con"
  AUTH_USER ||--o{ TBL_TMOVIMIENTO_STOCK : "registra"
  AUTH_USER ||--o{ TBL_LPEDIDO_ESTADO : "cambia"
  AUTH_USER |o--o{ TBL_TPEDIDO : "registra ventas presenciales"

  TBL_RCONFIGURACION_TIENDA {
    bigint CTI_NID PK
    varchar CTI_CNOMBRE
    varchar CTI_CNUMERO_WHATSAPP
    varchar CTI_CTEXTO_PIE
    integer CTI_NUMBRAL_STOCK_BAJO
    boolean CTI_OMOSTRAR_MARCAS
    integer CTI_NDIAS_SIN_VENTAS
    integer CTI_NHORAS_PEDIDO_PENDIENTE
  }
  TBL_RMETODO_PAGO {
    bigint MPA_NID PK
    varchar MPA_CTIPO UK
    varchar MPA_CTITULAR
    varchar MPA_CNUMERO_CUENTA
    varchar MPA_CIMAGEN_QR
    boolean MPA_OACTIVO
    integer MPA_NORDEN
  }
  TBL_RCATEGORIA {
    bigint CAT_NID PK
    varchar CAT_CNOMBRE
    varchar CAT_CSLUG UK
    integer CAT_NORDEN
    boolean CAT_OACTIVA
  }
  TBL_RPRODUCTO {
    bigint PRO_NID PK
    bigint CAT_NID FK
    varchar PRO_CNOMBRE
    varchar PRO_CSLUG UK
    varchar PRO_CSKU UK
    text PRO_CDESCRIPCION
    varchar PRO_CMARCA
    numeric PRO_NPRECIO_UNIDAD
    numeric PRO_NPRECIO_ANTERIOR
    boolean PRO_OACTIVO
    boolean PRO_ODESTACADO
  }
  TBL_RIMAGEN_PRODUCTO {
    bigint IMA_NID PK
    bigint PRO_NID FK
    varchar IMA_CRUTA_ORIGINAL
    varchar IMA_CRUTA_MINIATURA
    varchar IMA_CRUTA_DETALLE
    varchar IMA_CTEXTO_ALT
    integer IMA_NORDEN
    boolean IMA_OPRINCIPAL
  }
  TBL_RVARIANTE {
    bigint VAR_NID PK
    bigint PRO_NID FK
    varchar VAR_CTALLA
    varchar VAR_CCOLOR
    varchar VAR_CMODELO
    varchar VAR_CSKU UK
    integer VAR_NCANTIDAD_STOCK
    integer VAR_NUMBRAL_STOCK_BAJO
    boolean VAR_OACTIVA
  }
  TBL_RREGLA_PRECIO {
    bigint REG_NID PK
    bigint PRO_NID FK
    integer REG_NCANTIDAD_MINIMA
    numeric REG_NPRECIO_UNIDAD
  }
  TBL_TMOVIMIENTO_STOCK {
    bigint MOV_NID PK
    bigint VAR_NID FK
    varchar MOV_CTIPO
    integer MOV_NCANTIDAD
    varchar MOV_CMOTIVO
    bigint PED_NID FK
    bigint USU_NID_CREADO_POR FK
  }
  TBL_TPEDIDO {
    bigint PED_NID PK
    varchar PED_CCODIGO UK
    varchar PED_CESTADO
    varchar PED_CORIGEN
    varchar PED_CCLIENTE_NOMBRE
    varchar PED_CCLIENTE_DNI
    varchar PED_CCLIENTE_TELEFONO
    varchar PED_CTIPO_ENTREGA
    varchar PED_CAGENCIA
    varchar PED_CAGENCIA_CIUDAD
    varchar PED_CAGENCIA_REFERENCIA
    varchar PED_CPUNTO_ENCUENTRO
    timestamptz PED_DENTREGA_PROGRAMADA
    numeric PED_NSUBTOTAL
    numeric PED_NCOSTO_ENVIO
    numeric PED_NTOTAL
    bigint MPA_NID FK
    bigint USU_NID_CREADO_POR FK
    text PED_CNOTAS
    timestamptz PED_DFECHA_COTIZADO
    timestamptz PED_DFECHA_PAGADO
    timestamptz PED_DFECHA_ENVIADO
    timestamptz PED_DFECHA_ENTREGADO
    timestamptz PED_DFECHA_CIERRE
  }
  TBL_TPEDIDO_ITEM {
    bigint ITE_NID PK
    bigint PED_NID FK
    bigint VAR_NID FK
    varchar ITE_CNOMBRE_PRODUCTO
    varchar ITE_CSKU
    varchar ITE_CTALLA
    varchar ITE_CCOLOR
    numeric ITE_NPRECIO_UNIDAD
    integer ITE_NCANTIDAD
    numeric ITE_NSUBTOTAL
  }
  TBL_LPEDIDO_ESTADO {
    bigint PES_NID PK
    bigint PED_NID FK
    varchar PES_CESTADO_ANTERIOR
    varchar PES_CESTADO_NUEVO
    bigint USU_NID_CAMBIADO_POR FK
    varchar PES_CNOTA
  }
  TBL_HPEDIDO {
    bigint HPE_NID PK
    bigint PED_NID FK
  }
  TBL_TENVIO {
    bigint ENV_NID PK
    bigint PED_NID FK,UK
    varchar ENV_CAGENCIA
    varchar ENV_CNUMERO_ORDEN_AGENCIA
    varchar ENV_CCLAVE_RECOJO
    varchar ENV_CIMAGEN_BOLETA
    numeric ENV_NCOSTO_FLETE
    varchar ENV_CQUIEN_PAGA
    boolean ENV_OCOBRADO
    timestamptz ENV_DFECHA_DESPACHO
    text ENV_CNOTAS
  }
  AUTH_USER {
    bigint id PK
    varchar username
  }
```

## Notas
- `TBL_HPEDIDO` es una simplificación: `django-simple-history` la genera con sus propias columnas.
- `TBL_TPEDIDO_ITEM` guarda **copias** del nombre, talla y precio; su relación con `TBL_RVARIANTE` es protegida.
- `TBL_TENVIO` existe solo para pedidos con entrega `AGENCIA`.
- `TBL_RCONFIGURACION_TIENDA` no se relaciona con otras tablas.

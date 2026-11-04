# Modelo Entidad-Relación

Con los nombres físicos del estándar (`../12-estandar-base-datos.md`). Detalle de columnas en `diccionario-datos.md`. `AUTH_USER` es la tabla `auth_user` de Django.

```mermaid
erDiagram
  TBL_RCATEGORY ||--o{ TBL_RPRODUCT : "clasifica"
  TBL_RPRODUCT ||--o{ TBL_RPRODUCT_IMAGE : "tiene fotos"
  TBL_RPRODUCT ||--o{ TBL_RVARIANT : "tiene variantes"
  TBL_RPRODUCT ||--o{ TBL_RPRICE_RULE : "tiene precios por mayor"
  TBL_RVARIANT ||--o{ TBL_TSTOCK_MOVEMENT : "mueve stock"
  TBL_RVARIANT ||--o{ TBL_TORDER_ITEM : "se vende en"
  TBL_TORDER ||--|{ TBL_TORDER_ITEM : "contiene"
  TBL_TORDER ||--o{ TBL_TSTOCK_MOVEMENT : "origina"
  TBL_TORDER ||--o{ TBL_LORDER_STATUS : "registra estados"
  TBL_TORDER ||--o| TBL_TSHIPMENT : "se envía con"
  TBL_TORDER ||--o{ TBL_HORDER : "historial"
  AUTH_USER ||--o{ TBL_TSTOCK_MOVEMENT : "crea"
  AUTH_USER ||--o{ TBL_LORDER_STATUS : "cambia"

  TBL_RSTORE_SETTING {
    bigint STO_NID PK
    varchar STO_CNAME
    varchar STO_CWHATSAPP_NUMBER
    int STO_NLOW_STOCK_THRESHOLD
    boolean STO_OSHOW_BRANDS
  }
  TBL_RPAYMENT_METHOD {
    bigint PAY_NID PK
    varchar PAY_CTYPE
    varchar PAY_CHOLDER_NAME
    varchar PAY_CACCOUNT_NUMBER
    varchar PAY_CQR_IMAGE
    boolean PAY_OACTIVE
  }
  TBL_RCATEGORY {
    bigint CAT_NID PK
    varchar CAT_CNAME
    varchar CAT_CSLUG
    boolean CAT_OACTIVE
  }
  TBL_RPRODUCT {
    bigint PRD_NID PK
    bigint CAT_NID FK
    varchar PRD_CNAME
    varchar PRD_CSKU UK
    numeric PRD_NUNIT_PRICE
    boolean PRD_OACTIVE
  }
  TBL_RPRODUCT_IMAGE {
    bigint PIM_NID PK
    bigint PRD_NID FK
    varchar PIM_CORIGINAL_PATH
    boolean PIM_OPRIMARY
  }
  TBL_RVARIANT {
    bigint VAR_NID PK
    bigint PRD_NID FK
    varchar VAR_CSIZE
    varchar VAR_CSKU UK
    int VAR_NSTOCK_QUANTITY
  }
  TBL_RPRICE_RULE {
    bigint PRU_NID PK
    bigint PRD_NID FK
    int PRU_NMIN_QUANTITY
    numeric PRU_NUNIT_PRICE
  }
  TBL_TSTOCK_MOVEMENT {
    bigint SMO_NID PK
    bigint VAR_NID FK
    bigint ORD_NID FK
    bigint USR_NID_CREATED_BY FK
    varchar SMO_CTYPE
    int SMO_NQUANTITY
  }
  TBL_TORDER {
    bigint ORD_NID PK
    varchar ORD_CCODE UK
    varchar ORD_CSTATUS
    varchar ORD_CCUSTOMER_DNI
    varchar ORD_CDELIVERY_TYPE
    numeric ORD_NSUBTOTAL
    numeric ORD_NSHIPPING_COST
    numeric ORD_NTOTAL
  }
  TBL_TORDER_ITEM {
    bigint ORI_NID PK
    bigint ORD_NID FK
    bigint VAR_NID FK
    varchar ORI_CPRODUCT_NAME
    numeric ORI_NUNIT_PRICE
    int ORI_NQUANTITY
    numeric ORI_NSUBTOTAL
  }
  TBL_LORDER_STATUS {
    bigint OSL_NID PK
    bigint ORD_NID FK
    bigint USR_NID_CHANGED_BY FK
    varchar OSL_CFROM_STATUS
    varchar OSL_CTO_STATUS
  }
  TBL_HORDER {
    bigint HOR_NID PK
    bigint ORD_NID FK
  }
  TBL_TSHIPMENT {
    bigint SHI_NID PK
    bigint ORD_NID FK
    varchar SHI_CAGENCY_ORDER_NUMBER
    varchar SHI_CPICKUP_KEY
    numeric SHI_NFREIGHT_COST
    varchar SHI_CPAYER
  }
  AUTH_USER {
    bigint id PK
    varchar username
  }
```

## Notas
- `TBL_RSTORE_SETTING` y `TBL_RPAYMENT_METHOD` no se relacionan con otras tablas.
- `TBL_HORDER` en el diagrama es una simplificación: `django-simple-history` la genera con sus propias columnas (`history_id`, `history_date`…).
- `TBL_TORDER_ITEM` guarda **copias** del nombre, talla y precio; su relación con `TBL_RVARIANT` es protegida, para no perder el vínculo.

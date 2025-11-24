📦 Inventory Service – Documentación Oficial

Microservicio encargado de gestionar inventarios tanto en sucursales como en almacenes, garantizando integridad, control por empresa, validación de permisos y sincronización con el servicio de productos.

Este servicio forma parte del ecosistema:

Auth Service (usuarios, roles, permisos)

Company Service (sucursales, almacenes)

Products Service (productos, unidades, categorías)

Inventory Service ← (este documento)

🚀 Características del Servicio

Inventario por Sucursal

Inventario por Almacén

Sincronización con productos y validación por empresa

Acciones CRUD protegidas por:

permisos (read, create, update, delete)

reglas de empresa

rol es_dueno o usuarios permitidos

Endpoints devuelven objetos completos, no solo IDs

Soporte multialmacén y multisucursal

Integra middlewares de:

autenticación por JWT (Auth Service)

autorización por permisos

🏗 Arquitectura del Servicio
inventory-service/
│── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── deps.py            # permisos, validación empresa, usuario actual
│   ├── routers/
│   │   ├── sucursal_inventory.py
│   │   └── almacen_inventory.py
│   ├── schemas/
│   │   ├── sucursal_inventory.py
│   │   └── almacen_inventory.py
│   └── models/
│       ├── sucursal_inventory.py
│       └── almacen_inventory.py
│
├── requirements.txt
└── README.md

🗃 Estructura de Base de Datos
📌 Tabla sucursal_inventario
Campo	Tipo	Descripción
productos_id_producto	int	FK Producto
sucursales_id_sucursal	int	FK Sucursal
cantidad	int	Stock actual
stock_minimo	int	Stock mínimo permitido
stock_maximo	int	Stock máximo permitido
ultima_actualizacion	timestamp	Última modificación

PK: (productos_id_producto, sucursales_id_sucursal)

📌 Tabla almacen_inventario
Campo	Tipo	Descripción
productos_id_producto	int	FK Producto
almacenes_id_almacen	int	FK Almacén
cantidad	int	Stock actual
stock_minimo	int	Stock mínimo
stock_maximo	int	Stock máximo
ultima_actualizacion	timestamp	Última modificación

PK: (productos_id_producto, almacenes_id_almacen)

🔐 Seguridad y Permisos

Cada endpoint valida:

Usuario autenticado

Usuario pertenece a la empresa objetivo

Si NO es dueño (es_dueno = false) entonces debe tener:

Recurso	Acciones requeridas
sucursal_inventario	create, read, update, delete
almacen_inventario	create, read, update, delete

El sistema usa:

verify_permission(user, "create", "sucursal_inventario")


Y similares para almacén.

🔥 Endpoints – Sucursales
✔ Listar inventario de sucursal

GET /api/v1/sucursales/{id_sucursal}/inventario

Respuesta:
[
  {
    "producto": {
      "id_producto": 3,
      "nombre": "Collar Premium",
      "codigo_sku": "COL-PR-001",
      "precio": 35.50
    },
    "cantidad": 50,
    "stock_minimo": 5,
    "stock_maximo": 200,
    "ultima_actualizacion": "2025-11-24T12:45:00Z"
  }
]

✔ Crear inventario en sucursal

POST /api/v1/sucursales/{id_sucursal}/inventario

Body:

{
  "productos_id_producto": 3,
  "cantidad": 10,
  "stock_minimo": 2,
  "stock_maximo": 100
}

✔ Actualizar inventario

PATCH /api/v1/sucursales/{id_sucursal}/inventario/{id_producto}

Body:

{
  "cantidad": 55
}

✔ Eliminar inventario

DELETE /api/v1/sucursales/{id_sucursal}/inventario/{id_producto}

🏬 Endpoints – Almacenes
✔ Listar inventario de almacén

GET /api/v1/almacenes/{id_almacen}/inventario

✔ Crear inventario

POST /api/v1/almacenes/{id_almacen}/inventario

✔ Actualizar inventario

PATCH /api/v1/almacenes/{id_almacen}/inventario/{id_producto}

✔ Eliminar inventario

DELETE /api/v1/almacenes/{id_almacen}/inventario/{id_producto}
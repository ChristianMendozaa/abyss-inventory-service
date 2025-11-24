# app/schemas/almacen_inventario.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AlmacenInventarioBase(BaseModel):
    cantidad: int = Field(..., ge=0)
    stock_minimo: int = Field(..., ge=0)
    stock_maximo: int = Field(..., ge=0)


class AlmacenInventarioCreate(AlmacenInventarioBase):
    productos_id_producto: int


class AlmacenInventarioUpdate(BaseModel):
    cantidad: Optional[int] = Field(None, ge=0)
    stock_minimo: Optional[int] = Field(None, ge=0)
    stock_maximo: Optional[int] = Field(None, ge=0)


class AlmacenInventarioResponse(BaseModel):
    """
    Respuesta para listar inventario de almacén con info de producto.
    """
    model_config = ConfigDict(from_attributes=True)

    productos_id_producto: int
    almacenes_id_almacen: int

    cantidad: int
    stock_minimo: int
    stock_maximo: int
    ultima_actualizacion: datetime

    # Datos extra del producto
    producto_nombre: str
    producto_codigo_sku: str

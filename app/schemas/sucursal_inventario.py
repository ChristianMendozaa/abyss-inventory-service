# app/schemas/sucursal_inventario.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SucursalInventarioBase(BaseModel):
    cantidad: int = Field(..., ge=0)
    stock_minimo: int = Field(..., ge=0)
    stock_maximo: int = Field(..., ge=0)


class SucursalInventarioCreate(SucursalInventarioBase):
    productos_id_producto: int


class SucursalInventarioUpdate(BaseModel):
    cantidad: Optional[int] = Field(None, ge=0)
    stock_minimo: Optional[int] = Field(None, ge=0)
    stock_maximo: Optional[int] = Field(None, ge=0)


class SucursalInventarioResponse(BaseModel):
    """
    Respuesta para listar inventario de sucursal con info de producto.
    """
    model_config = ConfigDict(from_attributes=True)

    productos_id_producto: int
    sucursales_id_sucursal: int

    cantidad: int
    stock_minimo: int
    stock_maximo: int
    ultima_actualizacion: datetime

    # Datos extra del producto
    producto_nombre: str
    producto_codigo_sku: str

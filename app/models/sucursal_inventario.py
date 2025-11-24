# app/models/sucursal_inventario.py
from sqlalchemy import Column, Integer, DateTime, ForeignKey, func
from app.database import Base


class SucursalInventario(Base):
    __tablename__ = "sucursal_inventario"

    productos_id_producto = Column(
        Integer,
        ForeignKey("productos.id_producto"),
        primary_key=True,
    )
    sucursales_id_sucursal = Column(
        Integer,
        ForeignKey("sucursales.id_sucursal"),
        primary_key=True,
    )

    cantidad = Column(Integer, nullable=False)
    stock_minimo = Column(Integer, nullable=False)
    stock_maximo = Column(Integer, nullable=False)
    ultima_actualizacion = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

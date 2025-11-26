# app/models/almacen_inventario.py
from sqlalchemy import Column, Integer, DateTime, func
from app.database import Base


class AlmacenInventario(Base):
    __tablename__ = "almacen_inventario"

    productos_id_producto = Column(
        Integer,
        primary_key=True,
    )
    almacenes_id_almacen = Column(
        Integer,
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

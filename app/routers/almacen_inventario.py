# app/routers/almacen_inventario.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.database import get_db
from app.deps import require_permission, CurrentUser
from app.models.almacen_inventario import AlmacenInventario
from app.schemas.almacen_inventario import (
    AlmacenInventarioCreate,
    AlmacenInventarioUpdate,
    AlmacenInventarioResponse,
)

router = APIRouter(prefix="/almacenes", tags=["almacen_inventario"])


# ========= HELPERS =========

async def _check_almacen_belongs_to_company(
    db: AsyncSession, almacen_id: int, empresa_id: int
):
    sql = text(
        """
        SELECT 1
        FROM almacenes
        WHERE id_almacen = :almacen_id
          AND empresas_id_empresa = :empresa_id
        """
    )
    res = await db.execute(
        sql, {"almacen_id": almacen_id, "empresa_id": empresa_id}
    )
    if not res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found in your company",
        )


async def _check_producto_belongs_to_company(
    db: AsyncSession, producto_id: int, empresa_id: int
):
    sql = text(
        """
        SELECT 1
        FROM productos
        WHERE id_producto = :producto_id
          AND empresas_id_empresa = :empresa_id
        """
    )
    res = await db.execute(
        sql, {"producto_id": producto_id, "empresa_id": empresa_id}
    )
    if not res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product does not belong to your company or does not exist",
        )


# ========= ENDPOINTS =========

@router.get(
    "/{almacen_id}/inventario",
    response_model=List[AlmacenInventarioResponse],
)
async def list_inventario_almacen(
    almacen_id: int,
    current_user: CurrentUser = Depends(
        require_permission("read", "almacen_inventario")
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista el inventario de un almacén de la empresa actual
    devolviendo info de producto.
    """
    await _check_almacen_belongs_to_company(
        db, almacen_id, current_user.empresa.id_empresa
    )

    sql = text(
        """
        SELECT
          ai.productos_id_producto,
          ai.almacenes_id_almacen,
          ai.cantidad,
          ai.stock_minimo,
          ai.stock_maximo,
          ai.ultima_actualizacion,
          p.nombre AS producto_nombre,
          p.codigo_sku AS producto_codigo_sku
        FROM almacen_inventario ai
        JOIN productos p
          ON p.id_producto = ai.productos_id_producto
        WHERE ai.almacenes_id_almacen = :almacen_id
          AND p.empresas_id_empresa = :empresa_id
        ORDER BY p.nombre
        """
    )

    result = await db.execute(
        sql,
        {
            "almacen_id": almacen_id,
            "empresa_id": current_user.empresa.id_empresa,
        },
    )

    rows = result.mappings().all()
    return [
        AlmacenInventarioResponse(
            productos_id_producto=r["productos_id_producto"],
            almacenes_id_almacen=r["almacenes_id_almacen"],
            cantidad=r["cantidad"],
            stock_minimo=r["stock_minimo"],
            stock_maximo=r["stock_maximo"],
            ultima_actualizacion=r["ultima_actualizacion"],
            producto_nombre=r["producto_nombre"],
            producto_codigo_sku=r["producto_codigo_sku"],
        )
        for r in rows
    ]


@router.post(
    "/{almacen_id}/inventario",
    response_model=AlmacenInventarioResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_inventario_almacen(
    almacen_id: int,
    payload: AlmacenInventarioCreate,
    current_user: CurrentUser = Depends(
        require_permission("create", "almacen_inventario")
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Crea un registro de inventario para un producto en un almacén.
    """
    empresa_id = current_user.empresa.id_empresa

    await _check_almacen_belongs_to_company(db, almacen_id, empresa_id)
    await _check_producto_belongs_to_company(
        db, payload.productos_id_producto, empresa_id
    )

    q_exist = select(AlmacenInventario).where(
        AlmacenInventario.productos_id_producto == payload.productos_id_producto,
        AlmacenInventario.almacenes_id_almacen == almacen_id,
    )
    res = await db.execute(q_exist)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inventory for this product in this warehouse already exists",
        )

    inv = AlmacenInventario(
        productos_id_producto=payload.productos_id_producto,
        almacenes_id_almacen=almacen_id,
        cantidad=payload.cantidad,
        stock_minimo=payload.stock_minimo,
        stock_maximo=payload.stock_maximo,
    )
    db.add(inv)
    await db.commit()
    await db.refresh(inv)

    sql_prod = text(
        """
        SELECT nombre, codigo_sku
        FROM productos
        WHERE id_producto = :producto_id
        """
    )
    res_p = await db.execute(
        sql_prod, {"producto_id": payload.productos_id_producto}
    )
    prod = res_p.mappings().one()

    return AlmacenInventarioResponse(
        productos_id_producto=inv.productos_id_producto,
        almacenes_id_almacen=inv.almacenes_id_almacen,
        cantidad=inv.cantidad,
        stock_minimo=inv.stock_minimo,
        stock_maximo=inv.stock_maximo,
        ultima_actualizacion=inv.ultima_actualizacion,
        producto_nombre=prod["nombre"],
        producto_codigo_sku=prod["codigo_sku"],
    )


@router.patch(
    "/{almacen_id}/inventario/{producto_id}",
    response_model=AlmacenInventarioResponse,
)
async def update_inventario_almacen(
    almacen_id: int,
    producto_id: int,
    payload: AlmacenInventarioUpdate,
    current_user: CurrentUser = Depends(
        require_permission("update", "almacen_inventario")
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Actualiza cantidad / stocks de un producto en un almacén.
    """
    empresa_id = current_user.empresa.id_empresa

    await _check_almacen_belongs_to_company(db, almacen_id, empresa_id)
    await _check_producto_belongs_to_company(db, producto_id, empresa_id)

    q = select(AlmacenInventario).where(
        AlmacenInventario.productos_id_producto == producto_id,
        AlmacenInventario.almacenes_id_almacen == almacen_id,
    )
    res = await db.execute(q)
    inv = res.scalar_one_or_none()
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory record not found",
        )

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(inv, field, value)

    await db.commit()
    await db.refresh(inv)

    sql_prod = text(
        """
        SELECT nombre, codigo_sku
        FROM productos
        WHERE id_producto = :producto_id
        """
    )
    res_p = await db.execute(sql_prod, {"producto_id": producto_id})
    prod = res_p.mappings().one()

    return AlmacenInventarioResponse(
        productos_id_producto=inv.productos_id_producto,
        almacenes_id_almacen=inv.almacenes_id_almacen,
        cantidad=inv.cantidad,
        stock_minimo=inv.stock_minimo,
        stock_maximo=inv.stock_maximo,
        ultima_actualizacion=inv.ultima_actualizacion,
        producto_nombre=prod["nombre"],
        producto_codigo_sku=prod["codigo_sku"],
    )


@router.delete(
    "/{almacen_id}/inventario/{producto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_inventario_almacen(
    almacen_id: int,
    producto_id: int,
    current_user: CurrentUser = Depends(
        require_permission("delete", "almacen_inventario")
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Elimina un registro de inventario de almacén.
    """
    await _check_almacen_belongs_to_company(
        db, almacen_id, current_user.empresa.id_empresa
    )

    q = select(AlmacenInventario).where(
        AlmacenInventario.productos_id_producto == producto_id,
        AlmacenInventario.almacenes_id_almacen == almacen_id,
    )
    res = await db.execute(q)
    inv = res.scalar_one_or_none()
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory record not found",
        )

    await db.delete(inv)
    await db.commit()
    return None

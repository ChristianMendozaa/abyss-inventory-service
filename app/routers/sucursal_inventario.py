# app/routers/sucursal_inventario.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.database import get_db
from app.deps import require_permission, CurrentUser
from app.models.sucursal_inventario import SucursalInventario
from app.schemas.sucursal_inventario import (
    SucursalInventarioCreate,
    SucursalInventarioUpdate,
    SucursalInventarioResponse,
)

router = APIRouter(prefix="/sucursales", tags=["sucursal_inventario"])


# ========= HELPERS =========

async def _check_sucursal_belongs_to_company(
    db: AsyncSession, sucursal_id: int, empresa_id: int
):
    sql = text(
        """
        SELECT 1
        FROM sucursales
        WHERE id_sucursal = :sucursal_id
          AND empresas_id_empresa = :empresa_id
        """
    )
    res = await db.execute(
        sql, {"sucursal_id": sucursal_id, "empresa_id": empresa_id}
    )
    if not res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found in your company",
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
    "/{sucursal_id}/inventario",
    response_model=List[SucursalInventarioResponse],
)
async def list_inventario_sucursal(
    sucursal_id: int,
    current_user: CurrentUser = Depends(
        require_permission("read", "sucursal_inventario")
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista el inventario de una sucursal de la empresa actual,
    devolviendo datos del producto.
    """
    await _check_sucursal_belongs_to_company(
        db, sucursal_id, current_user.empresa.id_empresa
    )

    sql = text(
        """
        SELECT
          si.productos_id_producto,
          si.sucursales_id_sucursal,
          si.cantidad,
          si.stock_minimo,
          si.stock_maximo,
          si.ultima_actualizacion,
          p.nombre AS producto_nombre,
          p.codigo_sku AS producto_codigo_sku
        FROM sucursal_inventario si
        JOIN productos p
          ON p.id_producto = si.productos_id_producto
        WHERE si.sucursales_id_sucursal = :sucursal_id
          AND p.empresas_id_empresa = :empresa_id
        ORDER BY p.nombre
        """
    )

    result = await db.execute(
        sql,
        {
            "sucursal_id": sucursal_id,
            "empresa_id": current_user.empresa.id_empresa,
        },
    )

    rows = result.mappings().all()
    return [
        SucursalInventarioResponse(
            productos_id_producto=r["productos_id_producto"],
            sucursales_id_sucursal=r["sucursales_id_sucursal"],
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
    "/{sucursal_id}/inventario",
    response_model=SucursalInventarioResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_inventario_sucursal(
    sucursal_id: int,
    payload: SucursalInventarioCreate,
    current_user: CurrentUser = Depends(
        require_permission("create", "sucursal_inventario")
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Crea un registro de inventario para un producto en una sucursal.
    """
    empresa_id = current_user.empresa.id_empresa

    await _check_sucursal_belongs_to_company(db, sucursal_id, empresa_id)
    await _check_producto_belongs_to_company(
        db, payload.productos_id_producto, empresa_id
    )

    # Verificar que no exista ya
    q_exist = select(SucursalInventario).where(
        SucursalInventario.productos_id_producto == payload.productos_id_producto,
        SucursalInventario.sucursales_id_sucursal == sucursal_id,
    )
    res = await db.execute(q_exist)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inventory for this product in this branch already exists",
        )

    inv = SucursalInventario(
        productos_id_producto=payload.productos_id_producto,
        sucursales_id_sucursal=sucursal_id,
        cantidad=payload.cantidad,
        stock_minimo=payload.stock_minimo,
        stock_maximo=payload.stock_maximo,
    )
    db.add(inv)
    await db.commit()
    await db.refresh(inv)

    # Traer datos del producto para la respuesta
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

    return SucursalInventarioResponse(
        productos_id_producto=inv.productos_id_producto,
        sucursales_id_sucursal=inv.sucursales_id_sucursal,
        cantidad=inv.cantidad,
        stock_minimo=inv.stock_minimo,
        stock_maximo=inv.stock_maximo,
        ultima_actualizacion=inv.ultima_actualizacion,
        producto_nombre=prod["nombre"],
        producto_codigo_sku=prod["codigo_sku"],
    )


@router.patch(
    "/{sucursal_id}/inventario/{producto_id}",
    response_model=SucursalInventarioResponse,
)
async def update_inventario_sucursal(
    sucursal_id: int,
    producto_id: int,
    payload: SucursalInventarioUpdate,
    current_user: CurrentUser = Depends(
        require_permission("update", "sucursal_inventario")
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Actualiza cantidad / stocks de un producto en una sucursal.
    """
    empresa_id = current_user.empresa.id_empresa

    await _check_sucursal_belongs_to_company(db, sucursal_id, empresa_id)
    await _check_producto_belongs_to_company(db, producto_id, empresa_id)

    q = select(SucursalInventario).where(
        SucursalInventario.productos_id_producto == producto_id,
        SucursalInventario.sucursales_id_sucursal == sucursal_id,
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

    # Datos de producto
    sql_prod = text(
        """
        SELECT nombre, codigo_sku
        FROM productos
        WHERE id_producto = :producto_id
        """
    )
    res_p = await db.execute(sql_prod, {"producto_id": producto_id})
    prod = res_p.mappings().one()

    return SucursalInventarioResponse(
        productos_id_producto=inv.productos_id_producto,
        sucursales_id_sucursal=inv.sucursales_id_sucursal,
        cantidad=inv.cantidad,
        stock_minimo=inv.stock_minimo,
        stock_maximo=inv.stock_maximo,
        ultima_actualizacion=inv.ultima_actualizacion,
        producto_nombre=prod["nombre"],
        producto_codigo_sku=prod["codigo_sku"],
    )


@router.delete(
    "/{sucursal_id}/inventario/{producto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_inventario_sucursal(
    sucursal_id: int,
    producto_id: int,
    current_user: CurrentUser = Depends(
        require_permission("delete", "sucursal_inventario")
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Elimina un registro de inventario de sucursal.
    """
    await _check_sucursal_belongs_to_company(
        db, sucursal_id, current_user.empresa.id_empresa
    )

    q = select(SucursalInventario).where(
        SucursalInventario.productos_id_producto == producto_id,
        SucursalInventario.sucursales_id_sucursal == sucursal_id,
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

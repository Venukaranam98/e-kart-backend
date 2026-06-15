from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db

from models import (
    User,
    Product,
    Order
)

from routers.auth import get_current_admin

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

@router.get("/dashboard")
def admin_dashboard(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):

    total_users = db.query(User).count()

    total_products = db.query(Product).count()

    total_orders = db.query(Order).count()

    total_revenue = sum(
        order.total_price
        for order in db.query(Order).all()
    )

    return {
        "total_users": total_users,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": total_revenue
    }
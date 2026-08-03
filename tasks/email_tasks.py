import os
import logging
from datetime import datetime
from services.email_service import email_service
from database import SessionLocal
from models import User, Order, Address

logger = logging.getLogger(__name__)

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@ekarthub.com")


def send_welcome_email(user_id: int, email: str, username: str, created_at: str = None):
    logger.info(f"[BackgroundTask Executing] send_welcome_email | User ID: {user_id} | Email: {email}")
    
    date_str = created_at or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    context = {
        "user_id": user_id,
        "email": email,
        "username": username,
        "created_at": date_str
    }
    
    try:
        email_service.send_email(
            to_email=email,
            subject="Welcome to EKARTHUB 🎉",
            template_name="emails/welcome.html",
            context=context
        )
        logger.info(f"[BackgroundTask Success] send_welcome_email | User ID: {user_id} | Email: {email}")
    except Exception as exc:
        logger.error(f"[BackgroundTask Error] send_welcome_email | User ID: {user_id} | Error: {exc}")


def send_order_confirmation(order_id: int):
    logger.info(f"[BackgroundTask Executing] send_order_confirmation | Order ID: {order_id}")
    
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            logger.error(f"[BackgroundTask Error] Order #{order_id} not found.")
            return
            
        user = db.query(User).filter(User.id == order.user_id).first()
        if not user or not user.email:
            logger.error(f"[BackgroundTask Error] User for Order #{order_id} not found or has no email.")
            return

        items = []
        for item in order.items:
            prod = item.product
            items.append({
                "title": prod.title if prod else "Product",
                "quantity": item.quantity,
                "price": prod.price if prod else 0
            })

        # Fetch address if present
        addr_obj = db.query(Address).filter(Address.user_id == user.id).first()
        address_str = f"{addr_obj.full_name}, {addr_obj.address_line}, {addr_obj.city}, {addr_obj.state} - {addr_obj.pincode}" if addr_obj else "Shipping Address on file"

        context = {
            "order_id": order.id,
            "username": user.username,
            "items": items,
            "total_price": order.total_price,
            "address": address_str,
            "payment_method": "Online / Card / UPI",
            "estimated_delivery": "3-5 Business Days"
        }

        email_service.send_email(
            to_email=user.email,
            subject=f"EKARTHUB Order Confirmation - #{order.id}",
            template_name="emails/order_confirmation.html",
            context=context
        )
        logger.info(f"[BackgroundTask Success] send_order_confirmation | User ID: {user.id} | Email: {user.email}")
    except Exception as exc:
        logger.error(f"[BackgroundTask Error] send_order_confirmation | Order ID: {order_id} | Error: {exc}")
    finally:
        db.close()


def send_order_shipped(order_id: int, tracking_id: str = "EKART-TRK-9821", courier: str = "Express Logistics", expected_delivery: str = "2-3 Days"):
    logger.info(f"[BackgroundTask Executing] send_order_shipped | Order ID: {order_id}")
    
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order or not order.user:
            return
        
        context = {
            "order_id": order.id,
            "username": order.user.username,
            "tracking_id": tracking_id,
            "courier": courier,
            "expected_delivery": expected_delivery
        }

        email_service.send_email(
            to_email=order.user.email,
            subject=f"Your EKARTHUB Order #{order.id} Has Been Shipped",
            template_name="emails/order_shipped.html",
            context=context
        )
        logger.info(f"[BackgroundTask Success] send_order_shipped | Order ID: {order_id} | Email: {order.user.email}")
    except Exception as exc:
        logger.error(f"[BackgroundTask Error] send_order_shipped | Order ID: {order_id} | Error: {exc}")
    finally:
        db.close()


def send_out_for_delivery(order_id: int, tracking_id: str = "EKART-TRK-9821", courier: str = "Express Logistics", expected_delivery: str = "Today"):
    logger.info(f"[BackgroundTask Executing] send_out_for_delivery | Order ID: {order_id}")
    
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order or not order.user:
            return
        
        context = {
            "order_id": order.id,
            "username": order.user.username,
            "tracking_id": tracking_id,
            "courier": courier,
            "expected_delivery": expected_delivery
        }

        email_service.send_email(
            to_email=order.user.email,
            subject=f"Your EKARTHUB Order #{order.id} is Out For Delivery",
            template_name="emails/out_for_delivery.html",
            context=context
        )
        logger.info(f"[BackgroundTask Success] send_out_for_delivery | Order ID: {order_id} | Email: {order.user.email}")
    except Exception as exc:
        logger.error(f"[BackgroundTask Error] send_out_for_delivery | Order ID: {order_id} | Error: {exc}")
    finally:
        db.close()


def send_order_delivered(order_id: int, delivered_date: str = None):
    logger.info(f"[BackgroundTask Executing] send_order_delivered | Order ID: {order_id}")
    
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order or not order.user:
            return
        
        items = [{
            "title": item.product.title if item.product else "Product",
            "quantity": item.quantity
        } for item in order.items]

        date_str = delivered_date or datetime.utcnow().strftime("%B %d, %Y")

        context = {
            "order_id": order.id,
            "username": order.user.username,
            "delivered_date": date_str,
            "items": items,
            "total_price": order.total_price
        }

        email_service.send_email(
            to_email=order.user.email,
            subject=f"Your EKARTHUB Order #{order.id} Has Been Delivered",
            template_name="emails/order_delivered.html",
            context=context
        )
        logger.info(f"[BackgroundTask Success] send_order_delivered | Order ID: {order_id} | Email: {order.user.email}")
    except Exception as exc:
        logger.error(f"[BackgroundTask Error] send_order_delivered | Order ID: {order_id} | Error: {exc}")
    finally:
        db.close()


def send_order_cancelled(order_id: int, refund_status: str = "Initiated", reason: str = "Customer request"):
    logger.info(f"[BackgroundTask Executing] send_order_cancelled | Order ID: {order_id}")
    
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order or not order.user:
            return

        context = {
            "order_id": order.id,
            "username": order.user.username,
            "refund_status": refund_status,
            "reason": reason
        }

        email_service.send_email(
            to_email=order.user.email,
            subject=f"EKARTHUB Order #{order.id} Cancelled",
            template_name="emails/order_cancelled.html",
            context=context
        )
        logger.info(f"[BackgroundTask Success] send_order_cancelled | Order ID: {order_id} | Email: {order.user.email}")
    except Exception as exc:
        logger.error(f"[BackgroundTask Error] send_order_cancelled | Order ID: {order_id} | Error: {exc}")
    finally:
        db.close()


def send_password_reset(user_id: int, email: str, username: str, reset_token: str, expires_in_minutes: int = 15):
    print("========== PASSWORD RESET TASK STARTED ==========")
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    reset_url = f"{frontend_url}/reset-password?token={reset_token}"

    context = {
        "user_id": user_id,
        "email": email,
        "username": username,
        "reset_url": reset_url,
        "expires_in_minutes": expires_in_minutes
    }

    try:
        email_service.send_email(
            to_email=email,
            subject="Reset your EKARTHUB password",
            template_name="emails/forgot_password.html",
            context=context
        )
        logger.info(f"[BackgroundTask Success] send_password_reset | User ID: {user_id} | Email: {email}")
    except Exception as exc:
        logger.error(f"[BackgroundTask Error] send_password_reset | User ID: {user_id} | Error: {exc}", exc_info=True)


def send_password_changed(user_id: int, email: str, username: str, change_time: str = None):
    logger.info(f"[BackgroundTask Executing] send_password_changed | User ID: {user_id} | Email: {email}")
    
    time_str = change_time or datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")

    context = {
        "user_id": user_id,
        "email": email,
        "username": username,
        "change_time": time_str
    }

    try:
        email_service.send_email(
            to_email=email,
            subject="Your password has been changed",
            template_name="emails/password_changed.html",
            context=context
        )
        logger.info(f"[BackgroundTask Success] send_password_changed | User ID: {user_id} | Email: {email}")
    except Exception as exc:
        logger.error(f"[BackgroundTask Error] send_password_changed | User ID: {user_id} | Error: {exc}")


def send_login_alert(user_id: int, email: str, username: str, browser: str, device: str, login_time: str = None):
    logger.info(f"[BackgroundTask Executing] send_login_alert | User ID: {user_id} | Email: {email}")
    
    time_str = login_time or datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")

    context = {
        "user_id": user_id,
        "email": email,
        "username": username,
        "browser": browser,
        "device": device,
        "login_time": time_str
    }

    try:
        email_service.send_email(
            to_email=email,
            subject="New Security Alert: Successful Login to EKARTHUB",
            template_name="emails/login_alert.html",
            context=context
        )
        logger.info(f"[BackgroundTask Success] send_login_alert | User ID: {user_id} | Email: {email}")
    except Exception as exc:
        logger.error(f"[BackgroundTask Error] send_login_alert | User ID: {user_id} | Error: {exc}")


def send_low_stock_alert(product_id: int, title: str, current_stock: int):
    logger.info(f"[BackgroundTask Executing] send_low_stock_alert | Product ID: {product_id} | Stock: {current_stock}")
    
    context = {
        "product_id": product_id,
        "product_title": title,
        "current_stock": current_stock
    }

    try:
        email_service.send_email(
            to_email=ADMIN_EMAIL,
            subject=f"⚠️ Low Stock Alert: {title} ({current_stock} units left)",
            template_name="emails/low_stock.html",
            context=context
        )
        logger.info(f"[BackgroundTask Success] send_low_stock_alert | Product ID: {product_id} | Admin Email: {ADMIN_EMAIL}")
    except Exception as exc:
        logger.error(f"[BackgroundTask Error] send_low_stock_alert | Product ID: {product_id} | Error: {exc}")

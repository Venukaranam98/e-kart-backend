from fastapi import FastAPI,Depends

from database import engine

from sqlalchemy.orm import Session

from database import get_db

import models

from routers import admin

from routers import (
    products,
    auth,
    cart,
    orders,
    payments
)


from routers import address

import os

from fastapi.middleware.cors import CORSMiddleware

import razorpay

from dotenv import load_dotenv

from pydantic import BaseModel

from models import User

load_dotenv()

class OrderRequest(BaseModel):
    amount: int

client = razorpay.Client(
    auth=(
        os.getenv("RAZORPAY_KEY_ID"),
        os.getenv("RAZORPAY_KEY_SECRET")
    )
)


app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "https://e-kart-one.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(auth.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(address.router)
app.include_router(admin.router)

models.Base.metadata.create_all(bind=engine)

@app.get("/")
def home():
    return {
        "message": "E-KART Backend Running"
    }

@app.post("/create-order")
def create_order(data: OrderRequest):
    order = client.order.create({
        "amount": data.amount * 100,
        "currency": "INR",
        "payment_capture": 1
    })

    return order

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()

    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin
        }
        for user in users
    ]
from fastapi import FastAPI

from database import engine

import models

from routers import (
    products,
    auth,
    cart,
    orders,
    payments
)

from fastapi.staticfiles import StaticFiles

import os


os.makedirs(
    "uploads",
    exist_ok=True
)


app = FastAPI()


app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)


app.include_router(products.router)
app.include_router(auth.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(payments.router)


models.Base.metadata.create_all(bind=engine)


@app.get("/")

def home():

    return {

        "message": "E-KART Backend Running"

    }

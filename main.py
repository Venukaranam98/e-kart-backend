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

from fastapi.middleware.cors import CORSMiddleware


os.makedirs(
    "uploads",
    exist_ok=True
)


app = FastAPI()

origins = [

    
    "https://annette-nondesignate-cryptically.ngrok-free.dev",
    "http://localhost:5173",
]



app.add_middleware(

    CORSMiddleware,

    allow_origins=origins,

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)


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

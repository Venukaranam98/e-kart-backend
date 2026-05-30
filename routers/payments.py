from fastapi import APIRouter

import razorpay

import os

from dotenv import load_dotenv

from pydantic import BaseModel


load_dotenv()


router = APIRouter()


client = razorpay.Client(

    auth=(

        os.getenv("RAZORPAY_KEY_ID"),

        os.getenv("RAZORPAY_KEY_SECRET")

    )

)

class PaymentSchema(BaseModel):
    amount: int

@router.post("/create-payment-order")
def create_payment_order(data: PaymentSchema):

    payment_order = client.order.create({

        "amount": data.amount*100,

        "currency": "INR",

        "payment_capture": 1

    })


    return payment_order

@router.post(

    "/verify-payment",

    tags=["Payments"]

)

def verify_payment(

    razorpay_order_id: str,

    razorpay_payment_id: str,

    razorpay_signature: str

):

    try:

        client.utility.verify_payment_signature({

            "razorpay_order_id": razorpay_order_id,

            "razorpay_payment_id": razorpay_payment_id,

            "razorpay_signature": razorpay_signature

        })


        return {

            "message": "Payment verified successfully"

        }


    except:

        return {

            "message": "Payment verification failed"

        }
from pydantic import BaseModel


class ProductSchema(BaseModel):

    title: str

    description: str

    price: float

    image: str

    category: str


class UserSchema(BaseModel):

    username: str

    email: str

    password: str


class UserResponse(BaseModel):

    id: int

    username: str

    email: str


    class Config:

        from_attributes = True

class LoginSchema(BaseModel):

    email: str

    password: str

class CartSchema(BaseModel):

    product_id: int

    quantity: int

class UpdateCartSchema(BaseModel):

    quantity: int

class ReviewSchema(BaseModel):

    comment: str

    rating: int
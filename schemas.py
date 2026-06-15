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


class ProductResponse(BaseModel):

    id: int

    title: str

    description: str

    price: float

    image: str

    category: str


    class Config:

        from_attributes = True


class ReviewResponse(BaseModel):

    id: int

    comment: str

    rating: int


    class Config:

        from_attributes = True


class CartResponse(BaseModel):

    cart_id: int

    product_title: str

    price: float

    image: str

    category: str

    quantity: int


class AddressSchema(BaseModel):
    full_name: str
    phone: str
    address_line: str
    city: str
    state: str
    pincode: str

class AdminDashboardResponse(BaseModel):
    total_users: int
    total_products: int
    total_orders: int
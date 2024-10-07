from fastapi import FastAPI,Query
from pymongo import MongoClient
from pydantic import BaseModel,EmailStr
from typing import Optional
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # List of allowed origins
    allow_credentials=True,  # Allows credentials (such as cookies, authorization headers, etc.) to be sent in cross-origin requests
    allow_methods=["*"],  # Allows all methods (such as GET, POST, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
    expose_headers=["*"]
)


Mongo_Details = "mongodb+srv://amanvivekanand:aman994909@cluster0.nszektx.mongodb.net/"
client = MongoClient(Mongo_Details)

db = client.Hotel_Booking


#-------------------------------------------------------registration-----------------------------------------------------------#
registr_col = db.hotel_registr_col

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class userschema(BaseModel):
    full_name : str
    email : EmailStr
    phone_no : int
    password : str
    confirm_password : str
    role : Optional[str] = "customer"



def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password,hashed_password)

def creating_customerid():
        counter = registr_col.find_one_and_update(
        {'_id': 'admin_id'},
        {'$inc': {'sequence_value': 1}},
        upsert=True,
        return_document=True
        )
        return counter['sequence_value']

@app.post("/customer_register", tags=["customer"])
def create_user(user:userschema):
    sequence_value = creating_customerid()
    Cust_id = f"CustomerId{sequence_value:04d}"


    document = user.dict()
    document.update({
        "customer_id": Cust_id,
        "password" : get_password_hash(user.password),
        "confirm_password" : get_password_hash(user.confirm_password),
     })

    registr_col.insert_one(document)
    document["_id"] = str(document["_id"])
    return document
     

@app.post("/login_customer" , tags=["customer"])
def logging(email: str = Query(...,), password : str = Query(...,)):
    db_user = registr_col.find_one({"email": email})
    if db_user and verify_password(password, db_user["password"]):
         return f"Message: Login Successfull"
    else:
         return f"Message: Account Does not Exist"
     

#-----------------------------------------------------------------------forgot password--------------------------------------------------------------------------------#

class Changepassword(BaseModel):
     password:str
     confirm_password:str


@app.patch("/changepassword", tags=["customer"])
def changepassword(changepassword: Changepassword, email:EmailStr = Query(...,)):
     if registr_col.find_one({"email":email}):
          document = changepassword.dict()
          document.update({
               "password":get_password_hash(changepassword.password),
               "confirm_password" : get_password_hash(changepassword.confirm_password)
          })
          registr_col.find_one_and_update({"email":email},{"$set":document })
          return f"Message : Password Changed Sucessfull"
     else:
          return f"Message : Email Id Does Not Exist"
     

@app.get("/get all register users", tags=["customer"])
def get_all_user():
    documents =  registr_col.find()
    all_users = []
    
    for document in documents:
        document["_id"] = str(document["_id"])  # Convert ObjectId to string
        all_users.append(document)  # Add the processed document to the list
    
    return all_users
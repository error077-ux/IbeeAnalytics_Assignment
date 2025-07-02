from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import pandas as pd
import io
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import json
import jwt
from passlib.context import CryptContext

# Import database functions from our database.py file
from database import (
    init_db,
    insert_data_row,
    get_all_data,
    get_data_by_id,
    insert_log_entry,
    get_all_logs,
    hash_password,
    get_user_by_username,
    create_user
)

# Initialize the database (ensures tables exist)
init_db()

# --- Pydantic Models for User Authentication ---
class User(BaseModel):
    username: str

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserCreate(BaseModel): # Model for user registration input
    username: str
    password: str

# --- ADDED: Pydantic Model for AI Assistant Question Input ---
class QuestionInput(BaseModel):
    question: str
# --- END ADDED SECTION ---

# --- JWT Configuration ---
SECRET_KEY = "your-jwt-super-secret-key-that-is-very-long-and-random-and-secure" # <--- CHANGE THIS!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- JWT Token Functions ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.PyJWTError:
        raise credentials_exception
    user = get_user_by_username(token_data.username)
    if user is None:
        raise credentials_exception
    return user

app = FastAPI(
    title="Data Upload and Query API",
    description="A simple backend system to upload CSV files, validate data, store it, and query it, with basic API logging.",
    version="1.0.0"
)

# --- Middleware for API Logging ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log every incoming HTTP request and its response details.
    Logs include timestamp, method, path, status code, and response time.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000 # Convert to milliseconds

    # Log the request details
    insert_log_entry(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        response_time_ms=process_time
    )
    return response

# --- Root Endpoint ---
@app.get("/", summary="Root endpoint", response_description="Welcome message")
async def read_root():
    """
    A simple welcome message for the API.
    """
    return {"message": "Welcome to the Data Upload and Query API! Use /docs for API documentation."}

# --- User Registration Endpoint ---
@app.post("/register/", response_model=User, summary="Register a new user", response_description="Registered user details")
async def register_user(user_data: UserCreate):
    """
    Registers a new user with a unique username and password.
    Password will be hashed before storing.
    """
    existing_user = get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")

    hashed_pwd = hash_password(user_data.password)
    user_id = create_user(user_data.username, hashed_pwd)

    if user_id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to register user due to a database error.")

    return User(username=user_data.username)

# --- User Login Endpoint ---
@app.post("/token", response_model=Token, summary="Login and get access token", response_description="Access token for authentication")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticates a user with username and password and returns an access token.
    Use this token in the 'Authorization: Bearer YOUR_TOKEN' header for protected endpoints.
    """
    user = get_user_by_username(form_data.username)
    if not user or hash_password(form_data.password) != user["hashed_password"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- CSV Upload Endpoint ---
@app.post("/upload-csv/", summary="Upload CSV File", response_description="Confirmation of successful upload and data storage")
async def upload_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Uploads a CSV file, performs basic validation, and stores its data in the database.
    (Requires a valid access token in the 'Authorization: Bearer' header)
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only CSV files are allowed.")

    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))

        if df.isnull().values.any():
            raise HTTPException(status_code=400, detail="CSV contains missing values. Please ensure all cells are filled.")

        rows_inserted = 0
        for index, row in df.iterrows():
            row_dict = row.to_dict()
            insert_data_row(file.filename, row_dict)
            rows_inserted += 1

        return JSONResponse(
            status_code=200,
            content={"message": f"CSV file '{file.filename}' uploaded and {rows_inserted} rows stored successfully."}
        )

    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="Uploaded CSV file is empty.")
    except pd.errors.ParserError:
        raise HTTPException(status_code=400, detail="Could not parse CSV file. Please check its format.")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Could not decode CSV file. Ensure it's UTF-8 encoded.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# --- Query Data Endpoints (Public) ---
@app.get("/data/", response_model=List[Dict[str, Any]], summary="Get All Stored Data", response_description="List of all stored CSV rows")
async def get_data():
    """
    Retrieves all data rows that have been uploaded and stored in the database.
    Each row includes its ID, original filename, the row data (as a dictionary), and upload timestamp.
    """
    data = get_all_data()
    return data

@app.get("/data/{item_id}", response_model=Dict[str, Any], summary="Get Data by ID", response_description="A single stored CSV row")
async def get_single_data(item_id: int):
    """
    Retrieves a specific data row by its unique ID.
    Returns a 404 error if the item is not found.
    """
    data_item = get_data_by_id(item_id)
    if not data_item:
        raise HTTPException(status_code=404, detail="Item not found.")
    return data_item

# --- Query Logs Endpoint ---
@app.get("/logs/", response_model=List[Dict[str, Any]], summary="Get All API Logs", response_description="List of all API request logs")
async def get_logs(
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves all API request logs stored in the database.
    (Requires a valid access token in the 'Authorization: Bearer' header)

    Logs include timestamp, HTTP method, request path, response status code, and response time.
    """
    logs = get_all_logs()
    return logs

# --- AI Assistant Endpoint (Rule-Based Data Retrieval) ---
@app.post("/ask-data-ai/", summary="Ask AI about Stored Data", response_description="AI's answer to the question about the data")
async def ask_data_ai(
    question_data: QuestionInput, # Uses QuestionInput MODEL
    current_user: User = Depends(get_current_user)
):
    """
    Asks a rule-based assistant a question about the currently stored CSV data.
    It attempts to identify keywords in your question to retrieve specific data points.
    (Requires a valid access token in the 'Authorization: Bearer' header)

    - **Input**: A JSON object with a 'question' key, e.g., `{"question": "What is the price of apple?"}`
    - **Output**: The extracted data point or a message if not found.
    """
    user_question = question_data.question.lower()
    if not user_question:
        raise HTTPException(status_code=400, detail="Please provide a 'question' in the request body.")

    all_data_rows = get_all_data()

    if not all_data_rows:
        return JSONResponse(
            status_code=200,
            content={"answer": "No data has been uploaded yet. Please upload a CSV first."}
        )

    attribute_keywords = {
        "price": ["price", "cost", "value"],
        "quantity": ["quantity", "number", "amount"],
        "stock": ["stock", "inventory", "available"],
        "warehouse": ["warehouse", "location", "where"],
        "product_name": ["product", "item", "name"],
        "item_name": ["item", "name", "product"]
    }

    found_item_name = None
    found_attribute = None

    for item_row in all_data_rows:
        row_data = item_row.get('row_data', {})
        for key_candidate in ['item_name', 'product_name']:
            if key_candidate in row_data and isinstance(row_data[key_candidate], str):
                data_item_name = row_data[key_candidate].lower()
                if data_item_name in user_question:
                    found_item_name = data_item_name
                    break
        if found_item_name:
            break

    for attr, keywords in attribute_keywords.items():
        for keyword in keywords:
            if keyword in user_question:
                found_attribute = attr
                break
        if found_attribute:
            break

    if not found_item_name and not found_attribute:
        return JSONResponse(
            status_code=200,
            content={"answer": "I could not understand which item or attribute you are asking about. Please rephrase your question more directly (e.g., 'What is the price of Apple?')."}
        )
    elif not found_item_name:
         return JSONResponse(
            status_code=200,
            content={"answer": f"I understand you are asking about '{found_attribute}', but I couldn't identify the specific item. Please mention the item name (e.g., Apple, T-Shirt)."}
        )
    elif not found_attribute:
        return JSONResponse(
            status_code=200,
            content={"answer": f"I understand you are asking about '{found_item_name}', but I couldn't identify what attribute (e.g., price, quantity, stock) you want to know. Please specify."}
        )

    retrieved_value = "Not found"
    for item_row in all_data_rows:
        row_data = item_row.get('row_data', {})
        item_match = False
        if 'item_name' in row_data and isinstance(row_data['item_name'], str) and row_data['item_name'].lower() == found_item_name:
            item_match = True
        elif 'product_name' in row_data and isinstance(row_data['product_name'], str) and row_data['product_name'].lower() == found_item_name:
            item_match = True

        if item_match:
            if found_attribute in row_data:
                retrieved_value = row_data[found_attribute]
                break

    if retrieved_value != "Not found":
        answer = f"The {found_attribute} of {found_item_name} is: {retrieved_value}"
    else:
        answer = f"I could not find the {found_attribute} for {found_item_name} in the uploaded data."

    return JSONResponse(
        status_code=200,
        content={"question": user_question, "answer": answer}
    )

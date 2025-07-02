# IbeeAnalytics_Assignment 🙂
**Assignment Title:** Data Upload and Query API with Basic Logging
# Description Of Assignment
This project is a FastAPI-based backend system designed for managing tabular data (CSV files), logging API requests, and providing a simple rule-based AI assistant to query the stored data. It uses SQLite for data persistence and includes basic static username/password authentication.
# Task Completed 
![image](https://github.com/user-attachments/assets/507caf9b-eb80-462e-94fa-4bb616f7bbf7)
# Technologies Used
- FastAPI: High-performance web framework for building APIs.
- Uvicorn: ASGI server to run the FastAPI application.
- Pandas: For efficient CSV parsing and data handling.
- SQLite: Lightweight, file-based SQL database for data persistence.
- Pydantic: For data validation and settings management.
# Setup Instructions
**1. Clone the Repository**
| Action | Command | 
|----------|----------|
| Clone Repository | git clone https://github.com/error077-ux/IbeeAnalytics_Assignment.git | 

**2. Install Dependencies**
- Open the vs terminal
- In that we have to install the dependencies

| Action | Command | 
|----------|----------|
| Install Dependencies | pip install -r requirements.txt | 

**3. Run The Backend Server**
- Open the vs terminal
- In the terminal move to the file path where your project is runing

| Action | Command | 
|----------|----------|
| Runing Backend  | uvicorn main:app --reload |

**4. API Documentation (Swagger UI)**
 - You can access the interactive API documentation (Swagger UI) in your web browser: **http://127.0.0.1:8000/docs**

![Screenshot 2025-07-02 220555](https://github.com/user-attachments/assets/a93efec0-1250-4f77-a09c-1d29fdc7fdde)

**5. Authentication**a
- To upload the csv file and check we need a authorization

| Username | Password | 
|----------|----------|
|  admin | password |

**(Note: I have used the static userid and password so that kindly you the given user id and password.If you would like to change then in the main.py file change the required userid and password)**

![Screenshot 2025-07-02 220627](https://github.com/user-attachments/assets/5e60d69e-f59f-4f10-b085-1f39c0ae0431)

**How to Authenticate in Swagger UI:**
- Go to the API documentation (http://127.0.0.1:8000/docs).
- Click the "Authorize" button at the top right of the page.
- A dialog box will appear prompting for "Username" and "Password".
- Enter admin for the Username and password for the Password.
- Click "Sign In" or "Authorize". The padlock icon should now appear "locked", indicating successful authentication.

**6. API Endpoints (or) Web Explanation** 🥳

**A) Root Endpoint**
****************
**GET /**
- Description: A simple welcome message for the API.
- Authentication: None (Public)

**B) CSV Upload**
****************
**POST /upload-csv/**
- Description: Uploads a CSV file, validates its content, and stores each row in the database.
- Authentication: Required (Basic Auth)
- Input: file (type: file) - Select your CSV file.
**(Note: In the project folder itself i have an example data so that you can use that or if you want to change other you can edit in that csv file itself)**

![Screenshot 2025-07-02 220657](https://github.com/user-attachments/assets/7ac7a218-fce9-45ea-ab66-eae3cdbfdd29)

![Screenshot 2025-07-02 220712](https://github.com/user-attachments/assets/27099aa8-afce-4dee-85ff-2899a5ea4f46)

![Screenshot 2025-07-02 220752](https://github.com/user-attachments/assets/679cc7cc-3337-49eb-9611-2d3ccbca8844)

![Screenshot 2025-07-02 220808](https://github.com/user-attachments/assets/967c477b-f533-4209-a8c6-7f970844ec17)


**C) Get All Stored Data**
***************************
**GET /data/**
- Description: Retrieves all data rows that have been uploaded and stored.
- Authentication: None (Public)

![Screenshot 2025-07-02 220833](https://github.com/user-attachments/assets/941cfca5-fe3d-48d3-97dd-26d07ad1df7f)

![Screenshot 2025-07-02 220852](https://github.com/user-attachments/assets/0cc5c72b-fd9a-4062-a758-b6078b43454b)

**D) Get Data by ID**
*********************
**GET /data/{item_id}**

- Description: Retrieves a specific data row by its unique ID.
- Authentication: None (Public)
- Parameters: item_id (type: integer) - The ID of the data row.

![Screenshot 2025-07-02 220929](https://github.com/user-attachments/assets/f06374b8-1672-4bef-8156-5414fe5823bd)

![Screenshot 2025-07-02 221012](https://github.com/user-attachments/assets/b79df7d8-c4c5-4fe6-9612-e278c45ba472)

**E) Get All API Logs**
***********************
**GET /logs/**

- Description: Retrieves all API request logs stored in the database.
- Authentication: Required (Basic Auth)

![Screenshot 2025-07-02 221309](https://github.com/user-attachments/assets/59ea6139-0b76-4480-b8aa-84bd65574a5e)

![Screenshot 2025-07-02 221322](https://github.com/user-attachments/assets/0e39f23d-4d32-4df6-ac05-c0f93c9f9525)

**F) Ask AI about Stored Data (Rule-Based)**
********************************************
**POST /ask-data-ai/**

- Description: Asks a rule-based assistant a question about the currently stored CSV data. It identifies keywords to retrieve specific data points.
- Authentication: Required (Basic Auth)

Input (JSON Body):

{
  "question": "string"
}

![Screenshot 2025-07-02 221036](https://github.com/user-attachments/assets/5c04f14e-0593-4945-a27e-af1481bc5099)

![Screenshot 2025-07-02 221233](https://github.com/user-attachments/assets/b2991dcd-a8b1-41c2-9dc8-35d129d5cb91)

![Screenshot 2025-07-02 221247](https://github.com/user-attachments/assets/49030a98-8397-4e2f-ba06-66de8cbfd681)

- Example Usage:

    - {"question": "What is the price of apple?"}
    - {"question": "Give me the quantity of banana."}
    - {"question": "Where is the hat located?"}

Output: The extracted data point or a message if the information is not found/understood.💯

**Assignment by**
- Name : Aniruth S
- College : SRM Institute of Science and Technology
- Reg no : RA2211030050043
- Gmail : as6110@srmist.edu.in




   

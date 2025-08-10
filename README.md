# Todo FastAPI DynamoDB Application

A simple TODO application backend built with **FastAPI** and **AWS DynamoDB** as the database.  
This project demonstrates how to build a RESTful API with authentication and user management using FastAPI, async DynamoDB calls, and JWT tokens.

---

## Features

- User registration and login with JWT-based authentication
- Password hashing with bcrypt
- User profile endpoint with role-based access control
- CRUD operations for Todo items (you can expand this part)
- Async interaction with DynamoDB using `aioboto3`
- Secure token generation and validation with `python-jose`
- Role-based access control middleware

---

## Tech Stack

- Python 3.9+
- FastAPI
- DynamoDB (AWS)
- aioboto3 (async AWS SDK for Python)
- passlib (password hashing)
- python-jose (JWT token handling)
- Uvicorn (ASGI server)

---

## Getting Started

### Prerequisites

- Python 3.9 or higher
- AWS credentials configured (for DynamoDB access)
- Create table users, todos in dynamodb
- DynamoDB table created with necessary indexes (`username-index`, `email-index`)

### Installation



```bash
1. Clone the repository:
git clone https://github.com/Mahmudulmadu/Todo-FastAPI-Dynamodb.git
cd Todo-FastAPI-Dynamodb
Create and activate a virtual environment:

2. Run command
python -m venv .venv
source .venv/bin/activate   # On Windows use `.venv\Scripts\activate`
Install dependencies:

3. install dependencies
pip install -r requirements.txt
Set environment variables (optional):

4. connect aws
export SECRET_KEY="your-secret-key"
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
5. Run the app:


uvicorn main:app --reload

```
## API Endpoints
Auth
POST /auth/signup — Register a new user

POST /auth/token — Login and receive access token

## User
GET /profile — Get current user profile (requires JWT token)

## Notes
Make sure your DynamoDB table is configured with the proper indexes for username and email.

This project uses async AWS SDK (aioboto3) for better performance.

## License
This project is licensed under the MIT License.

## Author
Mahmudul Hasan


Feel free to open issues or submit pull requests for improvements!

---
See Video --> https://drive.google.com/file/d/19hD7pES5kg8pmRb2h3dnKbL7J_9ftHtW/view?usp=sharing






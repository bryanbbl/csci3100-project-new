# Project Setup Instructions

Follow these steps to prepare your environment, start the server, and access the webpage.

## Prerequisites

1. **Install Homebrew** (if not already installed):
    pip install homebrew

2. **Install MongoDB Community Edition**:
    brew update
    brew tap mongodb/brew
    brew install mongodb-community

3. **Start MongoDB Service**:
    brew services start mongodb-community

4. **Install Required Python Packages**: Navigate to the project directory and install the dependencies listed in `requirements.txt`:
   
    pip3 install -r requirements.txt

## Starting the Server

1. Navigate to the backend directory:
    cd backend

2. Start the Flask server:
    python3 app.py

3. The server will start on `http://127.0.0.1:5000`.

## Accessing the Webpage

1. Open a web browser.
2. Navigate to `http://127.0.0.1:5000`.
3. You should see the login page of the application.

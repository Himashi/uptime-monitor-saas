# Uptime & API Health Monitor Micro-SaaS

A robust, asynchronous backend service built with **FastAPI**, **SQLAlchemy**, and **HTTPX** designed to monitor website uptimes, log response times, and handle API health checks.

## 🚀 Features
* **Asynchronous Monitoring:** Uses `httpx` to check multiple endpoints concurrently without blocking server threads.
* **Database Management:** Uses SQLAlchemy with SQLite/PostgreSQL to track users, monitored targets, and historical uptime logs.
* **RESTful Architecture:** Complete with Pydantic data validation and automatic interactive documentation.

## 🛠️ Tech Stack
* **Python 3.10+**
* **FastAPI**
* **SQLAlchemy**
* **Httpx**
* **Uvicorn**

## 📦 Getting Started Locally
1. Clone the repository:

Create and activate a virtual environment:
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

Install dependencies:
pip install -r requirements.txt

Run the server:
uvicorn app.main:app --reload

Open your browser and navigate to http://127.0.0.1:8000/docs to test the API.
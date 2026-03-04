# Cytoscape App Store – Local Development Setup

## Requirements

- Python 3.9+
- pip
- virtual environment
- MySQL
- Xapian

The project currently runs on **Django 4.2**.

---

## 1. Clone the Repository

git clone https://github.com/cytoscape/appstore.git
cd appstore

---

## 2. Create Virtual Environment

python3 -m venv venv
source venv/bin/activate

---

## 3. Install Dependencies

Install all required Python packages:

pip install -r requirements.txt

---

## 4. Install Xapian (search backend)

./install_xapian.sh 1.4.5

---

## 5. Run Database Migrations

python manage.py migrate

---

## 6. Run the Development Server

python manage.py runserver

The server will start at:

http://127.0.0.1:8000/

---

## 7. Run Unit Tests

To verify the setup works correctly:

make test

or

python manage.py test
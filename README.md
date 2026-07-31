# 🏠 SMART URS — Smart Urban Residential Services

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge\&logo=python)
![Django](https://img.shields.io/badge/Django-5.x-092E20?style=for-the-badge\&logo=django)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge\&logo=postgresql)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge\&logo=sqlite)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-7952B3?style=for-the-badge\&logo=bootstrap)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge\&logo=redis)
![WebSockets](https://img.shields.io/badge/WebSockets-RealTime-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

###  A Full-Stack Intelligent Home Service Marketplace Platform

*"Connecting customers with trusted professionals through real-time booking, smart provider assignment, secure payments, and live communication."*

</div>

---

#  Overview

SMART URS (Smart Urban Residential Services) is a modern full-stack service marketplace inspired by platforms like **Urban Company**.

The platform enables customers to discover, book, pay for, and track home services while allowing service providers to manage bookings, availability, earnings, and customer interactions through a dedicated dashboard.

The application combines real-time communication, secure online payments, intelligent provider assignment, analytics dashboards, and scalable backend architecture to deliver a production-ready booking experience.

---

# Key Features

## Customer Portal

* 🔐 Secure User Authentication
* 🏠 Browse Multiple Service Categories
* 🔍 Smart Search & Filters
* ❤️ Favorite Services
* 🤖 Personalized Recommendations
* 📅 Book Services
* 📍 Google Maps Location Selection
* 💬 Real-Time Chat
* 🔔 Instant Notifications
* 💳 Secure Razorpay Payments
* 📄 PDF Invoice Download
* ⭐ Reviews & Ratings
* 📜 Booking History

---

##  Provider Portal

* Provider Authentication
* Dedicated Provider Dashboard
* Booking Management
* Accept / Reject Requests
* Availability Slot Management
* Profile Management
* Earnings Dashboard
* Customer Communication
* Rating Management

---

## 🛠 Admin Dashboard

* User Management
* Provider Management
* Service Management
* Booking Management
* Payment Monitoring
* Revenue Dashboard
* Analytics Dashboard
* Notification Management
* Review Management

---

#  Advanced Features

##  Real-Time Communication

* Django Channels
* WebSockets
* Redis

Provides

* Instant Chat
* Live Notifications
* Real-Time Booking Updates

---

##  Payment Gateway

Integrated with Razorpay

Supports

* UPI
* Google Pay
* PhonePe
* Paytm
* Credit Cards
* Debit Cards
* Wallets
* EMI

---

## 📄 Automatic Invoice Generation

* PDF Invoice Generation
* Download Invoice
* Booking Summary
* Payment Details

---

## 📍 Google Maps Integration

* Location Selection
* Address Validation
* Service Location Tracking

---

##  Background Task Processing

Built using

* Celery
* Redis

Handles

* Email Notifications
* Booking Updates
* Reminder Emails
* Invoice Generation

without blocking user requests.

---

## Smart Provider Assignment

Automatically assigns providers based on

* Service Category
* Availability
* Experience
* Ratings

This minimizes manual intervention and improves booking efficiency.

---

#  System Architecture

```text
                    Customer
                        │
                        ▼
               Frontend (HTML/CSS/JS)
                        │
                        ▼
                Django Backend (MVC)
                        │
      ┌─────────────────┼──────────────────┐
      ▼                 ▼                  ▼
 PostgreSQL         Django REST API      SQLite (Development)
      │
      ▼
    Redis
      │
 ┌────┴─────┐
 ▼          ▼
Celery   Django Channels
 ▼          ▼
Emails   WebSockets
 ▼          ▼
Invoices  Real-Time Chat
           Notifications
```

---

# 🛠 Tech Stack

## Frontend

* HTML5
* CSS3
* Bootstrap 5
* JavaScript

---

## Backend

* Python
* Django
* Django REST Framework

---

## Database

* PostgreSQL (Production)
* SQLite (Development)

---

## Real-Time

* Django Channels
* WebSockets
* Redis

---

## Background Processing

* Celery
* Redis

---

## Payment

* Razorpay

---

## Maps

* Google Maps API

---

## Reports

* ReportLab

---

## Charts

* Chart.js

---

## Deployment

* Render
* GitHub

---

# 📂 Project Structure

```bash
SMART_URS/
│
├── core/
├── accounts/
├── bookings/
├── providers/
├── payments/
├── notifications/
├── chat/
├── templates/
├── static/
├── media/
├── requirements.txt
├── manage.py
└── README.md
```

---

# 📌 Booking Workflow

```text
Browse Services
        │
        ▼
Select Service
        │
        ▼
Choose Date & Time
        │
        ▼
Smart Provider Assignment
        │
        ▼
Payment
        │
        ▼
Booking Confirmed
        │
        ▼
Real-Time Notifications
        │
        ▼
Service Completed
        │
        ▼
Invoice Generated
        │
        ▼
Review & Rating
```

---

#  Features Overview

| Module                    | Status |
| ------------------------- | ------ |
| Authentication            | ✅      |
| Booking System            | ✅      |
| Provider Dashboard        | ✅      |
| Admin Dashboard           | ✅      |
| Booking History           | ✅      |
| Search & Filters          | ✅      |
| Favorites                 | ✅      |
| Reviews & Ratings         | ✅      |
| Notifications             | ✅      |
| Real-Time Chat            | ✅      |
| WebSockets                | ✅      |
| Django Channels           | ✅      |
| Redis                     | ✅      |
| Celery                    | ✅      |
| Google Maps               | ✅      |
| Razorpay Payments         | ✅      |
| PDF Invoice               | ✅      |
| Analytics Dashboard       | ✅      |
| Smart Provider Assignment | ✅      |
| Availability Management   | ✅      |

---

#  Installation

```bash
git clone https://github.com/pavitrasv02/SMART_URS.git

cd SMART_URS

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate

python manage.py runserver
```

---

# ⚙ Environment Variables

```env
SECRET_KEY=

DEBUG=True

DATABASE_URL=

REDIS_URL=

EMAIL_HOST=

EMAIL_PORT=

EMAIL_HOST_USER=

EMAIL_HOST_PASSWORD=

RAZORPAY_KEY_ID=

RAZORPAY_KEY_SECRET=

GOOGLE_MAPS_API_KEY=
```


# 💡 Future Enhancements

* AI-Based Service Recommendations
* Demand Prediction
* Mobile Application
* Multi-Language Support
* Voice Assistant
* Push Notifications
* AI Chatbot
* Route Optimization
* Microservices Architecture
* Docker & Kubernetes Deployment

---

# 👨‍💻 Author

**Pavitra S V**

Computer Science Engineering Student

Passionate about

* Full Stack Development
* Artificial Intelligence
* Cloud Computing
* Scalable Backend Systems

---

# ⭐ If you found this project useful

Please consider giving this repository a ⭐ on GitHub.

---

<div align="center">

### 🚀 SMART URS

**Smart Services. Smarter Living.**

Made with ❤️ using Django, Python, PostgreSQL & Modern Web Technologies.

</div>

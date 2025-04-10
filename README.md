E-commerce API

Overview

This project is a RESTful API for an E-commerce platform, built using Django REST Framework (DRF). It provides functionalities for product management, order processing, authentication, and authorization.

Features

Authentication & Authorization

User registration & login

JWT-based authentication

Role-based access control (Admin, Customer)

Password reset via email (Mailtrap integration)

Product Management

Add, update, and delete products (Admin only)

View product details and list products (Public)

Product search and filtering

Order Management

Place an order

Update or delete an order (Authorized users only)

View order details and history

Reviews & Ratings

Add, update, and delete product reviews

Rate products

View average ratings

Security Features

Secure authentication with JWT

Password hashing

Rate limiting to prevent abuse

Tech Stack

Backend: Django, Django REST Framework

Database: MySQL

Authentication: JWT (Django Simple JWT)

Email Service: Mailtrap (for password reset emails)

Deployment: Docker, Gunicorn, Nginx
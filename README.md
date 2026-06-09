# Disaster Resource Management System

## Overview
The Disaster Resource Management System is a web-based application developed to facilitate efficient distribution of resources during disaster situations. The platform connects donors and affected individuals, allowing resources such as food, water, medicines, and shelter materials to be requested and donated through a centralized system.

The project aims to improve disaster response by prioritizing urgent requests, matching available resources with needs, and ensuring transparency through admin verification.

---

## Features

- User Registration and Login
- Donor and Seeker Management
- Resource Request Submission
- Resource Donation Submission
- Smart Resource Matching
- Urgency-Based Prioritization
- Admin Verification System
- Centralized Data Management
- Resource Tracking and Status Updates

---

## System Workflow

1. Users register as a Donor or Seeker.
2. Seekers submit resource requests.
3. Donors provide available resources.
4. Data is stored in the MySQL database.
5. The system matches requests based on:
   - Location
   - Resource Type
   - Quantity Availability
   - Urgency Level
6. Admin verifies requests and donations.
7. Verified users can coordinate resource distribution.

---

## Technologies Used

- Frontend: HTML, CSS
- Backend: Python, Flask
- Database: MySQL

---

## Project Structure

```text
Disaster-Resource-Management-System/
│
├── static/
│   ├── css/
│   ├── images/
│   └── js/
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── donor.html
│   ├── seeker.html
│   └── admin.html
│
├── app.py
├── database.sql
├── requirements.txt
└── README.md

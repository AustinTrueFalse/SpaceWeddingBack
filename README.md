# Event Management Backend

**IN DEVELOPMENT NOW!!!**

A modern backend service designed to support a web application for creating, inviting, and tracking events.  
This backend is built on Python and integrates with Firebase for authentication, user management, and data storage.

---

## ✨ Key Features

- **User Authentication**  
  Supports email/password sign-in, Google OAuth sign-in, and session management via cookies and tokens.

- **User Registration**  
  Handles user registration with username uniqueness checks and stores user profiles in Firestore.

- **Event Management APIs**  
  Create, update, and manage event data with customizable details such as date, time, location, and description.

- **Invitation System**  
  Send invitations, manage guest RSVP statuses, and track responses.

- **Token Management**  
  Secure handling of Firebase ID tokens and refresh tokens for session persistence and security.

---

## 🛠️ Tech Stack

- Python (Flask or your chosen framework)
- Firebase Authentication & Firestore
- Requests (for Firebase REST API integration)
- JSON Web Token (JWT) verification via Firebase Admin SDK

---

## 📦 How to run

1. Install dependencies:

```bash
pip install -r requirements.txt

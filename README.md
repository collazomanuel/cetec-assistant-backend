# CETEC Assistant Backend

FastAPI backend for a university AI assistant application with Google authentication and role-based access control. Developed by the CETEC (Centro de Tecnología Educativa y Comunicación) at the Faculty of Engineering, University of Buenos Aires, for use by university students.

<div align="center">
  <img src="https://user-images.githubusercontent.com/75450615/228704389-a2bcdf3e-d4d6-4236-b1c6-57fd9e545625.png#gh-dark-mode-only" width="50%" align="center">
</div>

## Tech Stack

- **FastAPI** - Web framework
- **MongoDB** - Database (via pymongo)
- **Google Auth** - Authentication via Google ID tokens
- **Python 3.11+** - Modern Python with type hints

## Setup

1. Create and activate virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
```

Edit `.env`:
```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=cetec_assistant
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

4. Run:
```bash
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`

## Project Structure

```
app/
├── main.py              # FastAPI app with exception handlers
├── config.py            # Settings via pydantic-settings
├── database.py          # MongoDB connection and indexes
├── dependencies.py      # Auth dependencies and role checks
├── exceptions.py        # Custom exceptions
├── routers/
│   ├── health.py        # Health check endpoint
│   └── users.py         # User management endpoints
├── models/
│   ├── user.py          # User Pydantic models
│   └── log.py           # Log entry model
└── services/
    ├── auth.py          # Google token verification
    ├── user.py          # User CRUD operations
    └── log.py           # Event logging service
```

## Authentication

All endpoints except `/health` require a Google ID token in the Authorization header:

```
Authorization: Bearer <google_id_token>
```

Use [`dev_tools/token_helper.html`](dev_tools/token_helper.html) to obtain tokens for testing.

## Roles & Permissions

Three hierarchical roles:

- **admin** - Full access, can manage users
- **professor** - Access to professor and student endpoints
- **student** - Access to student endpoints only

Users must be created by an admin before they can authenticate.

## API Endpoints

### Health
- `GET /health` - Health check with database connectivity status (no auth)

### Users
- `GET /users/me` - Get current user info (any authenticated user)
- `GET /users` - List all users (admin)
- `GET /users?email=x` - Get specific user (admin)
- `POST /users` - Create user (admin)
- `PATCH /users` - Update user name/roles (admin)
- `DELETE /users` - Delete user (admin, cannot delete self)

## Event Logging

All authentication attempts and user management actions are logged to the `logs` collection:

- `auth_success` / `auth_failure` - Authentication events
- `user_created` / `user_updated` / `user_deleted` - Admin actions

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

Import [`postman_collection.json`](postman_collection.json) into Postman. Update the `google_id_token` variable with a token from the dev tools helper.

## Database Collections

**users**
```json
{
  "email": "user@example.com",
  "name": "User Name",
  "roles": ["student"]
}
```

**logs**
```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "event_type": "auth_success",
  "user_email": "user@example.com",
  "details": {},
  "level": "info"
}
```

![Footer](https://user-images.githubusercontent.com/75450615/175360883-72efe4c4-1f14-4b11-9a7c-55937563cffa.png)

# CETEC Assistant Backend

FastAPI backend for a university AI assistant application with Google authentication and role-based access control. Developed by the CETEC (Centro de Tecnología Educativa y Comunicación) at the Faculty of Engineering, University of Buenos Aires, for use by university students.

<div align="center">
  <img src="https://user-images.githubusercontent.com/75450615/228704389-a2bcdf3e-d4d6-4236-b1c6-57fd9e545625.png#gh-dark-mode-only" width="50%" align="center">
</div>

## Tech Stack

- **FastAPI** - Web framework
- **MongoDB** - Database (via pymongo)
- **AWS S3** - Document storage
- **Qdrant** - Vector database for semantic search
- **Sentence Transformers / OpenAI** - Text embedding models
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

Edit `.env` with your actual credentials:
```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=cetec_assistant
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-s3-bucket-name
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-qdrant-api-key  # Optional for local Qdrant
QDRANT_COLLECTION_NAME=cetec_documents
EMBEDDING_PROVIDER=local  # or "openai"
EMBEDDING_MODEL=all-MiniLM-L6-v2  # or "text-embedding-3-small" for OpenAI
OPENAI_API_KEY=your-openai-api-key  # Required if using OpenAI embeddings
CHUNK_SIZE=1000
CHUNK_OVERLAP=150
```

**⚠️ SECURITY WARNING:** Never commit the `.env` file to version control. It contains sensitive credentials that should remain private. The `.env` file is already in `.gitignore` to prevent accidental commits.

4. Run:
```bash
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`

## Project Structure

```
app/
├── main.py              # FastAPI app with lifespan management
├── config.py            # Settings via pydantic-settings
├── database.py          # MongoDB connection and indexes
├── dependencies.py      # Auth dependencies and DI
├── exceptions.py        # Custom exceptions
├── handlers.py          # Exception handlers
├── routers/
│   ├── health.py        # Health check endpoint
│   ├── users.py         # User management endpoints
│   ├── courses.py       # Course management endpoints
│   ├── documents.py     # Document management endpoints
│   └── ingestions.py    # Document ingestion endpoints
├── models/
│   ├── user.py          # User Pydantic models
│   ├── course.py        # Course Pydantic models
│   ├── document.py      # Document Pydantic models
│   ├── ingestion.py     # Ingestion job models
│   └── log.py           # Log entry model
└── services/
    ├── auth.py          # Google token verification
    ├── user.py          # User CRUD operations
    ├── course.py        # Course CRUD operations
    ├── document.py      # Document CRUD operations
    ├── ingestion.py     # Ingestion job processing
    ├── s3.py            # AWS S3 operations
    ├── pdf.py           # PDF text extraction
    ├── embedder.py      # Text embedding models
    ├── qdrant.py        # Vector database operations
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

### Courses
- `GET /courses` - List all courses (student+)
- `GET /courses?code=x` - Get specific course by code (student+)
- `POST /courses` - Create course (professor+)
- `PATCH /courses` - Update course code/name/description (professor+)
- `DELETE /courses` - Delete course (professor+)

### Documents
- `GET /documents?course_code=x` - List documents for a course (professor+)
- `GET /documents?document_id=x` - Get document with presigned download URL (professor+)
- `POST /documents` - Upload document to course (professor+, multipart/form-data)
- `DELETE /documents` - Delete document (professor+, body: document_id)

### Ingestions
- `POST /ingestions/start` - Start a document ingestion job (professor+)
- `GET /ingestions/list?course_code=x` - List ingestion jobs for a course (student+)
- `GET /ingestions/status?job_id=x` - Get ingestion job status (student+)
- `POST /ingestions/cancel` - Cancel a running ingestion job (professor+)
- `POST /ingestions/retry` - Retry a failed ingestion job (professor+)

**Ingestion Modes:**
- `NEW` - Process only newly uploaded documents
- `SELECTED` - Process specific documents by ID
- `ALL` - Process all documents in the course
- `REINGEST` - Reprocess already ingested documents

## Event Logging

All authentication attempts and management actions are logged to the `logs` collection:

- `auth_success` / `auth_failure` - Authentication events
- `user_created` / `user_updated` / `user_deleted` - User management actions
- `course_created` / `course_updated` / `course_deleted` - Course management actions
- `document_uploaded` / `document_accessed` / `document_deleted` / `documents_listed` - Document management actions
- `ingestion_job_created` / `ingestion_job_completed` / `ingestion_job_failed` / `ingestion_job_canceled` - Ingestion job lifecycle
- `ingestion_document_failed` / `vector_cleanup_failed` - Ingestion processing errors

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

Import [`dev_tools/postman_collection.json`](dev_tools/postman_collection.json) into Postman. Update the `google_id_token` variable with a token from the dev tools helper.

## Database Collections

**users**
```json
{
  "email": "user@example.com",
  "name": "User Name",
  "roles": ["student"]
}
```

**courses**
```json
{
  "code": "CS101",
  "name": "Introduction to Computer Science",
  "description": "Fundamentals of programming and algorithms"
}
```

**documents**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "course_code": "CS101",
  "filename": "lecture-notes.pdf",
  "s3_key": "documents/CS101/550e8400-e29b-41d4-a716-446655440000/lecture-notes.pdf",
  "upload_timestamp": "2024-01-01T00:00:00Z",
  "uploaded_by": "professor@example.com",
  "file_size": 1024000,
  "content_type": "application/pdf"
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

**ingestion_jobs**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "course_code": "CS101",
  "status": "RUNNING",
  "mode": "NEW",
  "document_ids": null,
  "docs_total": 5,
  "docs_done": 2,
  "vectors_created": 150,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:05:00Z",
  "created_by": "professor@example.com",
  "error_message": null,
  "retry_count": 0,
  "max_retries": 3
}
```

![Footer](https://user-images.githubusercontent.com/75450615/175360883-72efe4c4-1f14-4b11-9a7c-55937563cffa.png)

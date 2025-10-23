# ParishChat Database Architecture & User Management API

## Overview

This document defines the **PostgreSQL database schema**, **data relationships**, and **API endpoints** that support:

- Multi-tenant setup (many parishes per app)
- User management (registration, login, roles)
- Document tracking
- Basic chat history
- Feedback and audit logging

The design supports scaling later to multiple parishes, background jobs, and fine-grained role control — while keeping MVP complexity manageable.

---

## Database Overview

### Core Concepts
| Concept | Description |
|----------|--------------|
| **Parish** | Represents a single tenant (church) with its own content, admins, and users. |
| **User** | Anyone interacting with the system. Has a role and is assigned to one parish. |


---

## PostgreSQL Schema

### 1. `parishes`
Holds top-level tenant info.

| Column | Type | Description |
|---------|------|--------------|
| id | SERIAL PRIMARY KEY | Unique parish id |
| name | TEXT | Parish name |
| slug | TEXT UNIQUE | URL-safe identifier (e.g. "st-johns-boston") |
| address | TEXT | Optional |
| created_at | TIMESTAMP DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMP DEFAULT now() | Last update |

---

### 2. `users`

| Column | Type | Description |
|---------|------|--------------|
| id | SERIAL PRIMARY KEY |
| parish_id | INT REFERENCES parishes(id) ON DELETE CASCADE |
| email | TEXT UNIQUE NOT NULL |
| hashed_password | TEXT NOT NULL |
| name | TEXT |
| role | TEXT CHECK (role IN ('superadmin', 'parish_admin', 'uploader', 'parishioner')) DEFAULT 'parishioner' |
| is_active | BOOLEAN DEFAULT TRUE |
| created_at | TIMESTAMP DEFAULT now() |

#### Roles:
- `superadmin`: global control, can manage parishes.
- `parish_admin`: manages parish users and uploads.
- `uploader`: can upload docs for the parish. (Maybe? guess it can't hurt to add)
- `parishioner`: can read, ask questions, and give feedback.

---


## Suggested Indexes

```sql
CREATE INDEX idx_users_parish_id ON users(parish_id);
CREATE INDEX idx_docs_parish_id ON documents(parish_id);
```

---

## API Endpoints (User & Tenant Management)

### 1. Auth & User Management

#### `POST /api/auth/register`
Registers a new user (only `superadmin` or `parish_admin` can create others).

**Request JSON**
```json
{
  "email": "jane@stjohns.org",
  "password": "securepass",
  "name": "Jane Doe",
  "parish_id": 1,
  "role": "uploader"
}
```

**Response**
```json
{
  "id": 12,
  "email": "jane@stjohns.org",
  "role": "uploader"
}
```

---

#### `POST /api/auth/login`
Returns JWT access token.

**Request**
```json
{
  "email": "jane@stjohns.org",
  "password": "securepass"
}
```

**Response**
```json
{
  "access_token": "eyJhbGciOiJIUzI1...",
  "token_type": "bearer"
}
```

---

#### `GET /api/users/me`
Get current user (requires token).

**Response**
```json
{
  "id": 12,
  "email": "jane@stjohns.org",
  "parish_id": 1,
  "role": "uploader"
}
```

---

#### `GET /api/users`
List users for a parish (admin only).

**Response**
```json
[
  {
    "id": 1,
    "email": "father.mike@stjohns.org",
    "role": "parish_admin"
  },
  {
    "id": 2,
    "email": "mary@stjohns.org",
    "role": "uploader"
  }
]
```

---

#### `PATCH /api/users/{user_id}`
Update role, name, or active status.

---

#### `DELETE /api/users/{user_id}`
Soft-delete or deactivate user.

---

### 2. Parish Management (Superadmin only)

#### `POST /api/parishes`
Create a new parish tenant.

**Request**
```json
{
  "name": "St. John's Parish",
  "slug": "st-johns-boston",
  "address": "123 Main St, Boston, MA"
}
```

**Response**
```json
{
  "id": 1,
  "name": "St. John's Parish",
  "slug": "st-johns-boston"
}
```

---

#### `GET /api/parishes`
List all parishes (superadmin only).

---

#### `GET /api/parishes/{slug}`
Public info endpoint for visitors or parishioners.

---

## Authentication & Authorization Layer

- Use **JWT-based auth** (FastAPI + `fastapi-users` or manual Pydantic schema + dependency).
- Include `role` and `parish_id` in JWT claims.
- Custom dependency like:

```python
from fastapi import Depends, HTTPException
from jose import jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGO])
    user_id = payload.get("sub")
    # Query DB for user
    ...
    return user
```

Then enforce role checks:

```python
def require_admin(user=Depends(get_current_user)):
    if user.role not in ["superadmin", "parish_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
```

---

## Integration Points with Other Services

- **S3**: `documents.s3_key` links to uploads.
- **OpenSearch**: link indexed docs back to `documents.id`.
- **ChatSessions**: record each user’s chat for transparency.
- **Feedback**: tie user quality feedback into admin dashboards.

---

## Future Extensions

- Add `ingest_jobs` table for background processing.
- Add `permissions` table for more granular role-based actions.
- Add `audit_log` table for compliance.

---

## Example SQL Bootstrapping Script

```sql
CREATE TABLE parishes (
  id SERIAL PRIMARY KEY,
  name TEXT,
  slug TEXT UNIQUE,
  address TEXT,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  parish_id INT REFERENCES parishes(id),
  email TEXT UNIQUE NOT NULL,
  hashed_password TEXT NOT NULL,
  name TEXT,
  role TEXT DEFAULT 'parishioner',
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  parish_id INT REFERENCES parishes(id),
  uploader_id INT REFERENCES users(id),
  title TEXT,
  s3_key TEXT,
  source_type TEXT,
  uploaded_at TIMESTAMP DEFAULT now(),
  status TEXT DEFAULT 'uploaded',
  opensearch_doc_count INT DEFAULT 0
);
```

---

## Summary

This Postgres layer provides:

- **Multi-tenant data partitioning** (via `parish_id`)
- **Role-based user management**
- **Trackable document ingestion**
- **Expandable chat/feedback schema**
- **Integration hooks** for S3 and OpenSearch

---

## Next Steps

- Implement ORM models (SQLAlchemy)
- Add Alembic migrations
- Add FastAPI routes + role-based dependencies
- Wire `/api/upload` to link uploaded docs to `documents` table
- Wire `/api/query` to log sessions and chat messages

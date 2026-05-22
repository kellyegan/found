# [[IMGORG]] - Phase 1 Specification

---

[[IMGORG - Phase 1 TDD Build Plan]]

## Core API engine (backend)

### Version

Phase 1

### Purpose

Provide a local model, database and  REST API for managing a large personal image reference library. It will also handle generation and retrieval of thumbnail cache.

The system stores metadata and organizational information while leaving original image files in their existing locations.

The backend is intended to support:

- Desktop GUI applications
- Future browser extensions
- Future automation tools
- Future AI-assisted features

The backend will be implemented as a local service using FastAPI and SQLite.

---

# Technology Stack

## Language

Python 3.13+

---

## Core Packages

### API Framework

- FastAPI

Purpose:

- REST API
- Request validation
- OpenAPI documentation
- Dependency injection

---

### Data Models / ORM

- SQLModel

Purpose:

- ORM layer
- Pydantic validation
- Database schema definition

---

### Database

- SQLite

Purpose:

- Local embedded database
- Single-user optimized
- No external service required

---

### Database Migration

- Alembic

Purpose:

- Schema versioning
- Database migrations

---

### ASGI Server

- Uvicorn

Purpose:

- Local API hosting

---

### Background Tasks

Phase 1 Recommendation:

- FastAPI BackgroundTasks for simple jobs

Future:

- Dedicated job queue if needed

---

### Image Processing

- Pillow

Purpose:

- Metadata extraction
- Thumbnail generation
- Dimension detection
- MIME verification

---

### File Hashing

Python Standard Library

- hashlib

Purpose:

- SHA256 generation
- Duplicate detection

---

### Configuration

- Pydantic Settings

Purpose:

- Environment configuration
- Path management

---

# Supported File Types

Phase 1

| Type | Extension  |
| ---- | ---------- |
| JPEG | .jpg .jpeg |
| PNG  | .png       |
| WebP | .webp      |
| TIFF | .tif .tiff |

Unsupported imports should be rejected.

---

# Architecture Overview

```text
Frontend GUI
      │
      ▼
FastAPI REST API
      │
 ┌────┴────┐
 │         │
 ▼         ▼
SQLite   Thumbnail Cache
```

Images remain on disk and are never copied into application storage.

---

# Database Design

## Image

Primary image record.

### Fields

| Field          | Type     |
| -------------- | -------- |
| id             | UUID     |
| filename       | String   |
| path           | String   |
| width          | Integer  |
| height         | Integer  |
| file_size      | Integer  |
| mime_type      | String   |
| created_date   | DateTime |
| modified_date  | DateTime |
| imported_date  | DateTime |
| sha256_hash    | String   |
| thumbnail_path | String   |
| file_status    | Enum     |

---

### Constraints

Path must be unique.

```text
UNIQUE(path)
```

Hash should be indexed.

```text
INDEX(sha256_hash)
```

---

### File Status Enum

```text
available
missing
inaccessible
```

---

## Tag

Content descriptors.

### Fields

| Field | Type   |
| ----- | ------ |
| id    | UUID   |
| name  | String |

---

### Constraints

Tag names stored lowercase.

Unique:

```text
UNIQUE(name)
```

---

## ImageTag

Many-to-many relationship.

### Fields

| Field    |
| -------- |
| image_id |
| tag_id   |

Composite unique key.

---

## Category

Broad classification buckets.

### Fields

| Field       | Type   |
| ----------- | ------ |
| id          | UUID   |
| name        | String |
| description | String |

---

### Constraints

```text
UNIQUE(name)
```

---

## ImageCategory

Many-to-many relationship.

### Fields

| Field       |
| ----------- |
| image_id    |
| category_id |

Composite unique key.

---

## Collection

User-created image groups.

### Fields

| Field        | Type     |
| ------------ | -------- |
| id           | UUID     |
| name         | String   |
| description  | String   |
| created_date | DateTime |

---

### Constraints

```text
UNIQUE(name)
```

---

## CollectionImage

Ordered image membership.

### Fields

| Field         |
| ------------- |
| collection_id |
| image_id      |
| sort_order    |

---

## ImportJob

Tracks bulk imports.

### Fields

| Field              | Type     |
| ------------------ | -------- |
| id                 | UUID     |
| status             | Enum     |
| total_files        | Integer  |
| processed_files    | Integer  |
| successful_imports | Integer  |
| duplicate_paths    | Integer  |
| duplicate_hashes   | Integer  |
| failed_imports     | Integer  |
| created_date       | DateTime |
| completed_date     | DateTime |

---

### Status Enum

```text
queued
running
completed
failed
cancelled
```

---

# Thumbnail Cache Design

## Storage

Filesystem cache.

Example:

```text
data/
└── thumbnails/
    ├── a1/
    │   └── hash.jpg
    ├── b2/
    │   └── hash.jpg
```

---

## Thumbnail Size

Single size.

Recommended:

```text
512 x 512
```

Maintains aspect ratio.

---

## Generation

Generated automatically during import.

Performed in background job.

---

# Duplicate Detection

## Rule 1

Duplicate path.

Condition:

```text
path already exists
```

Result:

Reject import.

---

## Rule 2

Duplicate hash.

Condition:

```text
sha256 already exists
```

Result:

Flag for user review.

Import record not created until resolved.

---

# API Design

Base path:

```text
/api/v1
```

---

# Images

## List Images

```http
GET /images
```

### Query Parameters

| Parameter  | Type   |
| ---------- | ------ |
| offset     | int    |
| limit      | int    |
| tag        | string |
| category   | string |
| collection | UUID   |

---

### Response

Paginated image list.

---

## Get Image

```http
GET /images/{image_id}
```

Returns image metadata.

---

## Delete Image

```http
DELETE /images/{image_id}
```

Removes database record only.

Original file remains untouched.

---

## Get Thumbnail

```http
GET /images/{image_id}/thumbnail
```

Returns thumbnail binary.

Content-Type:

```text
image/jpeg
```

---

## Check File Status

```http
POST /images/{image_id}/verify
```

Verifies file exists.

Updates file_status.

---

# Bulk Import

## Create Import Job

```http
POST /images/import
```

### Request

```json
{
  "paths": ["/path/file1.jpg", "/path/file2.png"]
}
```

Returns job identifier.

---

## Get Import Job

```http
GET /jobs/{job_id}
```

Returns progress information.

---

## List Jobs

```http
GET /jobs
```

Returns recent import jobs.

---

# Tags

## List Tags

```http
GET /tags
```

---

## Create Tag

```http
POST /tags
```

---

## Update Tag

```http
PUT /tags/{tag_id}
```

---

## Delete Tag

```http
DELETE /tags/{tag_id}
```

---

## Add Tags To Image

```http
POST /images/{image_id}/tags
```

---

## Replace Image Tags

```http
PUT /images/{image_id}/tags
```

---

## Remove Tag From Image

```http
DELETE /images/{image_id}/tags/{tag_id}
```

---

# Categories

## List Categories

```http
GET /categories
```

---

## Create Category

```http
POST /categories
```

---

## Update Category

```http
PUT /categories/{category_id}
```

---

## Delete Category

```http
DELETE /categories/{category_id}
```

---

## Assign Categories

```http
POST /images/{image_id}/categories
```

---

## Replace Categories

```http
PUT /images/{image_id}/categories
```

---

## Remove Category

```http
DELETE /images/{image_id}/categories/{category_id}
```

---

# Collections

## List Collections

```http
GET /collections
```

---

## Create Collection

```http
POST /collections
```

---

## Update Collection

```http
PUT /collections/{collection_id}
```

---

## Delete Collection

```http
DELETE /collections/{collection_id}
```

---

## Get Collection Images

```http
GET /collections/{collection_id}/images
```

Returns ordered images.

---

## Add Images To Collection

```http
POST /collections/{collection_id}/images
```

---

## Remove Image

```http
DELETE /collections/{collection_id}/images/{image_id}
```

---

## Reorder Collection

```http
PUT /collections/{collection_id}/order
```

Updates sort_order values.

---

# API Response Standard

Every response should follow a common envelope.

Success:

```json
{
  "success": true,
  "data": {}
}
```

Error:

```json
{
  "success": false,
  "error": {
    "code": "duplicate_hash",
    "message": "Image already exists."
  }
}
```

---

# Project Structure

```text
backend/
│
├── app/
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── images.py
│   │       ├── tags.py
│   │       ├── categories.py
│   │       ├── collections.py
│   │       └── jobs.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── constants.py
│   │   └── database.py
│   │
│   ├── models/
│   │   ├── image.py
│   │   ├── tag.py
│   │   ├── category.py
│   │   ├── collection.py
│   │   └── job.py
│   │
│   ├── schemas/
│   │   ├── image.py
│   │   ├── tag.py
│   │   ├── category.py
│   │   ├── collection.py
│   │   └── job.py
│   │
│   ├── services/
│   │   ├── image_service.py
│   │   ├── tag_service.py
│   │   ├── category_service.py
│   │   ├── collection_service.py
│   │   ├── import_service.py
│   │   ├── thumbnail_service.py
│   │   └── metadata_service.py
│   │
│   ├── repositories/
│   │   ├── image_repository.py
│   │   ├── tag_repository.py
│   │   ├── category_repository.py
│   │   ├── collection_repository.py
│   │   └── job_repository.py
│   │
│   ├── workers/
│   │   └── import_worker.py
│   │
│   ├── utils/
│   │   ├── hashing.py
│   │   ├── filesystem.py
│   │   └── thumbnails.py
│   │
│   └── main.py
│
├── data/
│   ├── database.db
│   └── thumbnails/
│
├── migrations/
│
├── tests/
│
├── .env
│
├── requirements.txt
│
└── README.md
```

# Non-Functional Requirements

### Performance

- Support at least 50,000 image records
- Thumbnail generation must not block API requests
- Image list endpoints should default to pagination

### Reliability

- Database integrity maintained on import failures
- Import jobs recover gracefully from individual file failures
- Invalid image files logged and skipped

### Security

- API bound to localhost only
- No authentication required in Phase 1
- No filesystem access outside explicitly requested import paths

### Extensibility

Database and API design must support future addition of:

- Source URLs
- Ratings
- Favorites
- Notes
- Relinking tools
- Perceptual hashing
- Similar-image search
- Browser extension integration
- Canvas/moodboard functionality
- Additional asset formats (SVG, PSD, PDF)

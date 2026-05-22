# IMGORG - Phase 1 Test Slices

Below is a **Test-Driven Development (TDD) build order for Phase 1**, designed specifically for your system (FastAPI + SQLModel + SQLite + filesystem thumbnails + import jobs).

The key idea is:

> You build the system in vertical slices, where every slice is driven by tests that define behavior first.

This avoids building “layers in isolation” that don’t integrate cleanly later.

---

# Phase 1 TDD Build Plan (Step-by-Step)

## Overall Strategy

You will iterate through 6 vertical slices:

1. Core project + DB foundation
2. Image CRUD + schema correctness
3. Import pipeline + duplicate logic
4. Thumbnail system
5. Tag / category / collection system
6. Import jobs + pagination + filtering

Each slice follows:

> **Write tests → implement minimal code → refine → expand tests**

---

# SLICE 0 — Project Foundation (Setup Tests First)

## Goal

Prove the system can:

- Start FastAPI
- Connect to SQLite
- Create tables

---

## Write Tests First

### Test: API health check

- `GET /health` returns `{ "status": "ok" }`

### Test: DB connection

- create a simple record in test DB
- retrieve it successfully

---

## Implementation Tasks

- FastAPI app scaffold
- SQLModel setup
- database session dependency
- base router structure
- `/health` endpoint

---

## Done When

- API starts in tests
- SQLite test DB works
- health check passes

---

# SLICE 1 — Image Model + CRUD (Core Entity)

## Goal

Establish the core “Image” concept.

---

## Write Tests First

### Test: Create image

- POST `/images`
- returns image with ID
- stores metadata correctly

### Test: Get image

- GET `/images/{id}` returns correct record

### Test: List images

- GET `/images?offset=0&limit=10`

### Test: Delete image

- DELETE removes DB record only

---

## Implementation Tasks

- Image SQLModel schema
- Image repository
- Image service
- API endpoints

---

## Done When

- You can fully CRUD images via API
- Pagination works

---

# SLICE 2 — File System + Metadata Extraction

## Goal

Connect database records to real image files.

---

## Write Tests First

### Test: metadata extraction

- given image file
- width, height, mime, size extracted correctly

### Test: invalid file

- unsupported file rejected

### Test: missing file detection

- image record marked `missing`

---

## Implementation Tasks

- metadata service (Pillow)
- file validation layer
- file status enum

---

## Done When

- system correctly reads real images from disk
- invalid files are rejected safely

---

# SLICE 3 — Import Pipeline (MOST IMPORTANT SLICE)

## Goal

Build full import workflow with duplicate handling.

---

## Write Tests First

### Test: import single image

- POST `/images/import`
- image appears in DB
- metadata is correct

---

### Test: duplicate path rejection

- import same file twice
- second attempt rejected

---

### Test: duplicate hash handling

- copy file to new location
- import again
- hash conflict detected

expected result:

- conflict response returned
- no duplicate record created

---

### Test: bulk import

- multiple files imported in one job
- partial failure does not break job

---

## Implementation Tasks

- Import service
- Hashing logic (SHA256)
- Duplicate detection
- Import job model
- background processing (FastAPI BackgroundTasks)

---

## Done When

- Bulk import works reliably
- duplicate logic is enforced correctly
- job system tracks progress

---

# SLICE 4 — Thumbnail System

## Goal

Create fast image preview system.

---

## Write Tests First

### Test: thumbnail creation

- import image
- thumbnail exists on disk

---

### Test: thumbnail retrieval

- GET `/images/{id}/thumbnail`
- returns valid image response

---

### Test: cache reuse

- second request does NOT regenerate thumbnail

---

### Test: missing thumbnail recovery

- delete thumbnail file
- API regenerates it automatically

---

## Implementation Tasks

- thumbnail service (Pillow resize)
- filesystem cache structure
- thumbnail path resolver
- API endpoint streaming binary image

---

## Done When

- thumbnails always exist or self-heal
- performance is fast for repeated requests

---

# SLICE 5 — Tags, Categories, Collections

## Goal

Add organization system.

---

## Write Tests First

### Tags

- create tag
- assign tag to image
- enforce case-insensitive uniqueness

---

### Categories

- create category
- assign multiple categories per image
- prevent duplicates

---

### Collections

- create collection
- add images to collection
- enforce ordering (sort_order)
- reorder collection images

---

## Implementation Tasks

- join tables
- relationship management
- API endpoints
- normalization logic for tags

---

## Done When

- images can be organized in 3 independent systems:
  - tags (content)
  - categories (classification)
  - collections (curated sets)

---

# SLICE 6 — Import Jobs + Pagination + Filtering

## Goal

Make system scalable and usable at 50k images.

---

## Write Tests First

### Test: job lifecycle

- queued → running → completed

---

### Test: pagination

- offset/limit works correctly
- stable ordering

---

### Test: filtering

- filter by tag
- filter by category
- filter by collection

---

## Implementation Tasks

- job status tracking
- query builder for filters
- optimized indexes in SQLite
- API enhancements

---

## Done When

- system handles large datasets cleanly
- import jobs are trackable
- frontend-ready query system exists

---

# Supporting Testing Loop (IMPORTANT RULE)

For every slice:

### Step A — Write failing test

Defines behavior

### Step B — Implement minimal code

Only enough to pass

### Step C — Refactor

Clean architecture

### Step D — Expand tests

Add edge cases

---

# Recommended Build Order Timeline

## Week 1

- Slice 0 (foundation)
- Slice 1 (image CRUD)

## Week 2

- Slice 2 (filesystem integration)
- Slice 3 (import system)

## Week 3

- Slice 4 (thumbnails)
- Slice 5 (tags/categories/collections)

## Week 4

- Slice 6 (jobs + scaling + filtering)

---

# Key Architectural Insight

This TDD plan is designed around one principle:

> The import pipeline is the “heart” of the system.

Everything else depends on it:

- thumbnails depend on import
- tagging depends on image existence
- collections depend on image stability
- filtering depends on correct indexing

So Slice 3 is intentionally the most detailed and important.

---

[[IMGORG - Test list]]

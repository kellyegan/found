# FOUND

**Found** is a local image reference and inspiration library designed for artists, designers, and creators who collect large numbers of images for research and creative work. Rather than copying image files into a managed library, the system indexes images in their existing locations and stores metadata like tags, categories and collections as well as generating thumbnails in a local database. This allows users to build and browse large collections of reference material while keeping full control of their original files.

## Features

- Imports imags without copying them into a central library
- Duplication detection for images using SHA256 checksums
- Thumbnail generation
- Mark images by tag, collection or category for multiple ways of organizing
- API makes tool easy to extend

## Architecture

- FastAPI REST API
- SQLite database using SQLModel
- Filesystem-based thumbnail cache
- Desktop GUI frontend (planned)

## Installing

```bash
make setup
```

## Running

### Full application

```bash
pyenv activate found_env
python -m frontend
```

### Backend only

```bash
cd backend
uvicorn app.main:app --reload
```

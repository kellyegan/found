# [[IMGORG]]: Overview

## Problem

I have a large collection of tens of thousands of images I have collected over the years. These images are largely reference images I use for inspiration and discovery but also for design and drawing reference as well as visual research and image dataset creation. I need an application to effectively search, manage, discover and explore this expanding collection of images.

Some images are for inspiration while others might relate to specific projects or to document some ephemeral element of digital existence. Others might be part of a visual research or an image dataset intended for analysis of machine learning or other image processing needs.

## Goals

- Be able to effectively use my collection of 50,000 images for artistic inspiration and discovery.
- Access the images for specific uses like drawing and design reference
- Retrieve source material quickly and easily
- Conduct visual research by comparing and collecting images for different projects
- Image dataset editing and tagging for machine learning and other image processing needs
- Easily manage images and import them without creating duplicates or lost images

## Out of scope

This tool should focus on discovery, inspiration and visual research as opposed to editing or photographic processing workflow. This isn't a tool for managing images like Adobe Lightroom or DigiKam.

## System architecture

The tool should consist of a core engine which manages the collection and a graphical interface with multiple ways to interact with the images. The tool should maintain a lightweight linked database leaving the images in their source location. In a later phase the tool may have extensions and additional tools for integration with other applications (browsers), visualization and AI analysis.

### Phase 1: Core API engine

- **Model and database:** A lightweight, local database to store image paths, hashes (for duplicate detection), and metadata.
- **Image not stored centrally:** Original image files remain in their existing locations
- **API Layer:** A RESTful API (localhost) to facilitate communication between the file system, the UI, and browser extensions and to allow interface with other independent tools.
- **Thumbnail cache:** Fast browsing through cached thumbnails

### Phase 2: Graphical User Interface for interacting

- **Desktop application:** to manage the images, import, browse, tag and organize. Communicates exclusively through the API.
- **Thumbnail browsing:** The desktop GUI's main interface is a grid of thumbnails for browsing with the ability to filter, and preview individual images.
- **Image viewer:** Large image viewer to look at individual images.
- **Importing interface:** It will also provide support for managing imports, making decisions about duplicates and providing bulk actions on imports like tagging and metadata.
- **Mood board:** An "infinite canvas" (similar to PureRef) where users can drag indexed images to create spatial arrangements.
- **Slideshow:** For general viewing or timed for drawing reference

### Phase 3: AI, extensions & visualization

- **Inspiration logic:** A randomization algorithm that can be weighted by "stale" images (those not viewed recently) or specific tag clusters.
- **Embeddings engine:** Use a local CLIP (OpenCLIP) model to generate high-dimensional vectors for every image. LanceDB for storing data.
- **Semantic search:** Ability to query by natural language (e.g., "blue brutalist architecture") via vector similarity.
- **Visual similarity:** Find "more like this" by comparing vector distances.
- **Augmentation:** Automatic generation of "candidate tags" (AI-suggested) that the user can manually approve or refine.
- **Visualization:** A t-SNE or UMAP visualization mode to cluster 50k images on a 2D map based on visual features. We will use the `UMAP-learn` library.
- **New tab extension:** A browser extension (Chrome/Firefox) that fetches a random image + metadata from the local API to display on every new tab.

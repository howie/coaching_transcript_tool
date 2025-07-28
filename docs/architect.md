# CoachAssistant System Architecture

This document outlines the hybrid architecture used to build **CoachAssistant**, a SaaS product deployed at `service.doxa.com.tw` under Doxa Studio.

---

## 🔧 Architecture Overview

CoachAssistant uses a **hybrid Python backend**:

* **Flask** — for rendering HTML pages and serving the frontend interface
* **FastAPI** — for handling backend APIs, transcript conversion, and future AI tools (async and OpenAPI ready)

---

## 📁 Folder Structure

```
/app
  /frontend     ← Flask app (Jinja templates, static UI)
  /api          ← FastAPI app (mounted under /api)
  /templates    ← HTML templates (Jinja2)
  /static       ← JS, CSS assets
main.py         ← ASGI entry point using FastAPI + Flask mounting
```

---

## 🛏️ Application Behavior

### 🔺 Flask (`/`)

* Handles:

  * Main web interface (`/dashboard`, `/transcript-converter`)
  * Template rendering (via Jinja2)
* UI Elements:

  * Top navigation bar with user info & logout (placeholder)
  * Collapsible left sidebar:

    * Transcript Converter
    * ICF Marker Analysis *(Coming Soon)*
    * Insights *(Coming Soon)*

### 🔹 FastAPI (`/api`)

* Mounted under `/api` via `main.py`
* Handles core backend services:

  * `POST /api/convert-transcript` — accepts `.vtt` or `.srt`, returns `.xlsx`
  * `GET /api/job-status/{id}` — (optional) polling for async tasks
* Features:

  * Built-in Pydantic-based validation
  * Interactive docs at `/api/docs`
  * Scalable to future GPT & AI-powered features

---

## 🎨 Design Theme

* **Dark mode** layout
* Primary color: Deep Blue `#1C2E4A`
* Accent color: Warm Yellow `#F5C451`
* Font: **Noto Sans** or **Helvetica Neue**
* Layout style inspired by cloud dashboards (e.g., Render.com)

---

## 🛋️ Tech Stack

* **Flask** for frontend rendering
* **FastAPI** for API services (ASGI-based)
* **python-dotenv** for environment configuration
* **aiofiles** / background tasks for async file handling

---

## 🚜 Deployment Notes

* Runs as a single ASGI app (Flask + FastAPI)
* Ready for Replit or Docker deployment
* Flask handles UI, FastAPI handles async AI services
* Flexible: future services can gradually migrate to FastAPI

---

## 🌐 URL Routes

| Path                      | Method   | Handler                              |
| ------------------------- | -------- | ------------------------------------ |
| `/`                       | GET      | Flask: dashboard (temp)              |
| `/dashboard`              | GET      | Flask: main UI                       |
| `/transcript-converter`   | GET/POST | Flask: upload UI                     |
| `/api/convert-transcript` | POST     | FastAPI: transcript to Excel         |
| `/api/job-status/{id}`    | GET      | FastAPI: async job status (optional) |

---

## 🔄 Next Steps

* Implement OAuth2 login page using Authlib *(move to later phase)*
* Build file upload endpoint with async handling
* Connect GPT & Excel output generation in FastAPI
* Deploy on Replit with proper ASGI app

---

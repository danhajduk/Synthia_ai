# Synthia — Modular Local Smart Assistant

Synthia is a **local, modular, task‑based virtual assistant** with a plugin-style addon system.  
Think “Home Assistant + Modular AI + Automations,” but purpose-built and lightweight.

This README describes **the architecture as it exists today**, including the backend, addon system, and frontend integration.

---

# 🚀 Current System Overview

Synthia consists of:

- **Core Backend (FastAPI, Python)**  
- **Frontend UI (React + Vite)**  
- **Modular Addons**, each living under:
  ```
  /addons/<addon-id>/
      manifest.json
      backend/
          addon.py
          setup.py (optional)
      frontend/
          ...
  ```

Addons may provide:

- LLM capabilities  
- Voice interfaces  
- Knowledge sources (Gmail, Calendar, etc.)  
- Automation / action systems  
- UI components  

---

# 📦 Addon Manifest (Current Spec)

Each addon declares its capabilities through `manifest.json`:

```json
{
  "id": "hello-action",
  "name": "Hello Action Runner",
  "version": "0.1.0",
  "types": ["action"],
  "description": "Demo action addon.",
  "frontend": {
    "basePath": "/addons/hello-action",
    "hasSettingsPage": true,
    "showInSidebar": true,
    "showOnFrontpage": true,
    "summaryComponent": "HelloActionSummary",
    "summarySize": "sm"
  },
  "backend": {
    "entry": "./backend/addon.py",
    "setup": "./backend/setup.py",
    "healthPath": "/health",
    "requiresConfig": []
  }
}
```

Backend manifest extension added:

- `"setup"` — optional script executed at install-time  
- `"healthPath"` — backend declares its health endpoint  

---

# 🧠 Addon Lifecycle States

Synthia currently tracks addons through four states:

| State       | Meaning |
|-------------|---------|
| **available** | Addon exists on disk but not installed |
| **installed** | Install completed, but backend not loaded or unhealthy |
| **ready**     | Backend successfully loaded and mounted |
| **error**     | Setup failed or health check failed |

Lifecycle is automatically computed using:

- Installed store (`installed_store.json`)
- Loaded backend routers
- (future) health checking

---

# 🔧 Backend Architecture

### ✔ Manifest Discovery

Backend scans:

```
/addons/*/manifest.json
```

Loads them into Pydantic `AddonManifest` models.

### ✔ Addon Registry API

Endpoints:

```
GET /api/addons/registry
GET /api/addons/registry/{id}
GET /api/addons/status
```

### ✔ Installation Flow (current)

- `POST /api/addons/install/<id>`
- Validates presence of manifest
- Writes to installed_store
- Executes optional `setup.py` in a subprocess
- Reloads backend routers

### ✔ Backend Autoloader

Each backend must expose:

```python
addon = BackendAddon(meta=..., router=...)
```

The router is mounted automatically under:

```
/api/addons/<addon-id>/*
```

Successful mount = addon becomes `"ready"`.

---

# 🎨 Frontend Architecture (Current)

### ✔ Sidebar Navigation

Frontend uses:

```
src/navigation/navRegistry.ts
```

Plus dynamically loaded addon pages.

### ✔ Addon Registry Page (`/addons`)

Displays:

- Name, version, description  
- Types (LLM, UI, Voice, etc.) with icons  
- Lifecycle state badge  
- Install / Uninstall buttons  
- "Open" button for frontend addons  

Updates every **10 seconds** via `useAddonStatus()` hook.

### ✔ Route Integration

Addons with `frontend.basePath` become navigable pages.

---

# 🏗 Project Structure Today

```
Synthia/
    addons/
        hello-action/
            manifest.json
            backend/
                addon.py
                setup.py
            frontend/
    backend/
        app/
            addons/
                registry.py
                loader.py
                runtime.py
                models.py
                installed_store.py
                router.py
            main.py
    frontend/
        src/
            pages/
            components/
            hooks/
            navigation/
    scripts/
        backend.sh
    TODO.md
    README.md
```

---

# 🤖 What Synthia Can Do Right Now

- Load manifests  
- Register addons  
- Install addons  
- Run setup scripts  
- Autoload backend routers  
- Expose dynamic APIs  
- Power a UI showing addon status  
- Provide working bundle of demo addons (`hello-*`)  

You now have:
- A **plugin framework**
- A **runtime loader**
- A **UI dashboard**
- A **state machine for addons**

---

# 🚧 Next Steps

See `TODO.md` for the detailed roadmap:

- Health checks  
- Auto-frontend registration  
- Git/ZIP addon installation  
- Config system  
- Hot reload  
- Marketplace support  
- Capability-based routing (LLM/Voice/Knowledge)  

---

# ❤️ Author Notes

This codebase is evolving FAST — intentionally.  
You’re building an actual ecosystem, not a toy project.  
And the foundation you now have is *solid*.

Whenever you're ready for the next evolution, I’ll be right here.

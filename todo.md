# TODO: Synthia Addon System Roadmap
*Structured next-steps for backend + frontend integration.*

---

## ✅ Core Completed
- Addon manifest loader  
- Addon registry API  
- Install / uninstall basic flow  
- Backend module autoload + router mounting  
- UI registry page + lifecycle display  
- Lifecycle: available → installed → ready  

---

## 🚧 Next Steps (Planned)

### 1. Health Checks (Backend + UI) ✅ Completed
- Add periodic `/health` probing for each backend addon  
- Update lifecycle based on health results  
- Expose health details in `AddonRuntimeState`  
- Display errors and warnings in UI card  
- Add last-checked timestamp  

---

### 2. Setup Script Execution 
- Support manifest field `"setup": "./backend/setup.py"`  ✅ Done!
- Execute setup in isolated subprocess  ✅ Done!
- Collect stdout/stderr + exit code  ✅ Done!
- Update lifecycle to `error` if setup fails  
- Provide UI feedback (toast / card badge)  
- Define setup contract ( ) ✅ Done!

---

### 3. ZIP / Git Installation Methods
- `/api/addons/install/upload-zip`  
- Extract into `/addons/<id>/`  
- Validate manifest  
- Run setup if present  
- Reload addon backend  
- Support Git install:
  ```json
  { "repo": "https://..." }
  ```

---

### 4. Automatic Frontend Registration
- Create endpoint `/api/addons/frontend-routes`  
- Each addon contributes:
  - route definition(s)  
  - optional settings page  
  - optional homepage widget  
- Frontend auto-builds navigation from this JSON  
- Sidebar updates dynamically without touching core files  

---

### 5. Addon Configuration System
- Support per-addon config store: `/var/synthia/addons/<id>/config.json`  
- Add backend routes:
  - `GET /api/addons/<id>/config`  
  - `POST /api/addons/<id>/config`  
- UI auto-renders config form fields based on manifest schema  
- Block setup/install if `requiresConfig` missing  

---

### 6. Hot Reloading of Addon Backends
- Watch `/addons/<id>/backend/`  
- Unmount + re-mount router on change  
- Provide UI notification (“Backend Reloaded”)  
- Optional: allow manual reload via UI button  

---

### 7. Extended Addon Capabilities
- LLM addons expose: `/complete`  
- Voice addons expose: `/stream` or `/listen`  
- Knowledge addons expose: `/query`, `/sync`  
- Action addons expose: `/run`, `/tasks`, `/events`  
- UI addons expose custom dashboard components  

---

## 🎯 Stretch Ideas (Future)
- Addon marketplace (local Git index)  
- Versioning + upgrade path  
- Addon dependency resolution  
- Addon signing + trust validation  
- Remote addons (LAN or cloud workers)  
- Sandboxed addon runtimes (Docker / Firecracker)  

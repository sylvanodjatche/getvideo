import os
import uuid
import threading
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
import httpx

from .config import settings
from .services.extractor import extractor_service
from .services.streamer import streamer_service, download_tasks
from .services.security import security_manager
from .services.analytics import analytics_service

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="GetVideo - Moteur universel d'extraction et de téléchargement multimédia HD."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "Content-Disposition"]
)

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    try:
        security_manager.check_user_agent(request)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

@app.get("/api/info")
async def get_media_info(request: Request, url: str = Query(..., description="URL du média à extraire")):
    client_ip = security_manager.get_client_ip(request)
    security_manager.check_rate_limit(client_ip)
    security_manager.validate_url(url)

    try:
        data = extractor_service.extract(url)
        # Tracking de l'analyse dans la base analytics
        analytics_service.track_event(event_type="analyze", platform=data.get("platform"))
        return JSONResponse(content={"status": "success", "data": data})
    except Exception as e:
        error_msg = str(e)
        if "Unsupported URL" in error_msg:
            raise HTTPException(status_code=400, detail="Cette plateforme ou cette URL n'est pas prise en charge.")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'extraction : {error_msg}")

@app.post("/api/start_download")
async def start_download(
    request: Request,
    media_url: str = Query(..., description="URL source"),
    format_id: str = Query(None, description="Sélecteur de format"),
    title: str = Query("getvideo_download", description="Nom du fichier"),
    ext: str = Query("mp4", description="Extension"),
    embed_subs: bool = Query(False, description="Intégrer les sous-titres")
):
    client_ip = security_manager.get_client_ip(request)
    security_manager.check_rate_limit(client_ip)
    security_manager.validate_url(media_url)

    task_id = str(uuid.uuid4())[:10]
    
    thread = threading.Thread(
        target=streamer_service.execute_download_task,
        args=(task_id, media_url, format_id, title, ext, embed_subs),
        daemon=True
    )
    thread.start()

    return {"status": "started", "task_id": task_id}

@app.get("/api/progress/{task_id}")
async def get_download_progress(task_id: str):
    if task_id not in download_tasks:
        raise HTTPException(status_code=404, detail="Tâche introuvable.")
    return JSONResponse(content=download_tasks[task_id])

@app.post("/api/cancel_download/{task_id}")
async def cancel_download(task_id: str):
    cancelled = streamer_service.cancel_task(task_id)
    return {"status": "cancelled" if cancelled else "not_found"}

@app.get("/api/download_file/{task_id}")
async def get_downloaded_file(task_id: str):
    try:
        task = download_tasks.get(task_id)
        if task and task.get("status") == "ready":
            # Tracking du téléchargement réussi avec volume exact
            filesize = task.get("filesize", 0)
            analytics_service.track_event(event_type="download", format_type=task.get("ext"), filesize=filesize)
        return streamer_service.serve_ready_file(task_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/stream")
async def stream_fallback(
    request: Request,
    media_url: str = Query(None),
    url: str = Query(None),
    format_id: str = Query(None),
    title: str = Query("getvideo_download"),
    ext: str = Query("mp4")
):
    target_url = media_url or url
    if not target_url:
        raise HTTPException(status_code=400, detail="URL requise.")

    task_id = str(uuid.uuid4())[:10]
    streamer_service.execute_download_task(task_id, target_url, format_id, title, ext)
    analytics_service.track_event(event_type="download", format_type=ext)
    return streamer_service.serve_ready_file(task_id)

@app.get("/api/subtitle")
async def download_subtitle(url: str = Query(..., description="URL du sous-titre")):
    security_manager.validate_url(url)
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            resp = await client.get(url)
            analytics_service.track_event(event_type="subtitle")
            return PlainTextResponse(resp.text, media_type="text/vtt")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Impossible de récupérer le sous-titre: {str(e)}")

# Endpoint des statistiques en temps réel pour le Dashboard
@app.get("/api/admin/stats")
async def get_admin_stats():
    return JSONResponse(content=analytics_service.get_dashboard_stats())

# Montage du frontend statique
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend"))
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    @app.get("/")
    async def serve_fallback():
        return {
            "message": "API GetVideo active. Dossier frontend introuvable.",
            "docs": "/docs"
        }

import os, uuid
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.responses import FileResponse
from livekit import api
import core

app = FastAPI(title="Iraqi AI Secretary")

@app.get("/api/token")
def token():
    room = f"secretary-{uuid.uuid4().hex[:8]}"   # غرفة جديدة = الوكيل ينضم تلقائياً
    jwt = (api.AccessToken(os.environ["LIVEKIT_API_KEY"], os.environ["LIVEKIT_API_SECRET"])
           .with_identity("ahmed").with_name("Ahmed")
           .with_grants(api.VideoGrants(room_join=True, room=room)).to_jwt())
    return {"token": jwt, "url": os.environ["LIVEKIT_URL"]}

@app.get("/api/appointments")
def appointments():
    with core.db() as c:
        rows = c.execute("SELECT id,title,date,time,notes FROM appointments WHERE status='active' ORDER BY date,time").fetchall()
    return [dict(r) for r in rows]

@app.get("/")
def index():
    return FileResponse("static/index.html")

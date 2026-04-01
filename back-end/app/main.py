from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.services.stt_service import stt_service
from app.api.websockets.stt import websocket_audio
from app.api.websockets.llm import websocket_llm

app = FastAPI(
    title="Shore STT API",
    description="Backend cho module Speech-To-Text",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_load_model():
    stt_service.load_model()


@app.get("/")
def read_root():
    return {"message": "Welcome to Shore STT FastAPI Backend"}


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "STT Backend is running"}


app.add_api_websocket_route("/ws/audio", websocket_audio)
app.add_api_websocket_route("/ws/llm", websocket_llm)
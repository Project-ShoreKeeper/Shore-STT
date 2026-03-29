from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Shore STT API", description="Backend cho module Speech-To-Text", version="1.0.0")

# Cấu hình CORS để frontend React có thể gọi API mà không bị lỗi
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Nên giới hạn domain trong môi trường production (ví dụ: ["http://localhost:5173"])
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Shore STT FastAPI Backend"}

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "STT Backend is running"}

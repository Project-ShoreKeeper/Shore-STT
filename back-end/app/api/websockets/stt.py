import json
import time
import numpy as np
from fastapi import WebSocket, WebSocketDisconnect
from app.services.stt_service import stt_service
from app.core.config import settings


async def websocket_audio(websocket: WebSocket):
    await websocket.accept()
    print("[STT] Client connected")

    session_config = {
        "language": "en",
        "sample_rate": settings.sample_rate,
    }

    try:
        while True:
            message = await websocket.receive()

            if "text" in message:
                await _handle_text(websocket, message["text"], session_config)

            elif "bytes" in message:
                await _handle_audio(websocket, message["bytes"], session_config)

    except WebSocketDisconnect:
        print("[STT] Client disconnected")
    except RuntimeError as e:
        if "disconnect" in str(e).lower():
            print("[STT] Client disconnected")
        else:
            print(f"[STT] Unexpected error: {e}")
    except Exception as e:
        print(f"[STT] Unexpected error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


async def _handle_text(
    websocket: WebSocket,
    raw: str,
    session_config: dict,
):
    try:
        data = json.loads(raw)
        msg_type = data.get("type", "")

        if msg_type == "config":
            session_config.update(data.get("data", {}))
            print(f"[STT] Config updated: {session_config}")
            await websocket.send_json({
                "type": "status",
                "message": f"Config updated: {session_config}",
            })
        else:
            print(f"[STT] Unknown message type: {data}")

    except json.JSONDecodeError:
        await websocket.send_json({
            "type": "error",
            "message": "Invalid JSON format",
        })


async def _handle_audio(
    websocket: WebSocket,
    audio_bytes: bytes,
    session_config: dict,
):
    start_time = time.time()
    sample_rate = session_config.get("sample_rate", settings.sample_rate)

    audio_float32 = np.frombuffer(audio_bytes, dtype=np.float32)
    duration_sec = len(audio_float32) / sample_rate

    if len(audio_float32) == 0:
        await websocket.send_json({"type": "error", "message": "Empty audio received"})
        return

    audio_rms = np.sqrt(np.mean(audio_float32 ** 2))
    if audio_rms < 0.001:
        print(f"[STT] Silence detected (RMS={audio_rms:.6f}), skipping")
        await websocket.send_json({
            "type": "transcript",
            "text": "",
            "isFinal": True,
            "data": {"skipped": True, "reason": "silence"},
        })
        return

    print(f"[STT] Audio received: {len(audio_float32)} samples ({duration_sec:.2f}s)")

    stt_result = await stt_service.transcribe_async(
        audio=audio_float32,
        language=session_config.get("language", "en"),
    )

    await websocket.send_json({
        "type": "transcript",
        "text": stt_result["text"],
        "isFinal": True,
        "data": {
            "duration": round(duration_sec, 2),
            "processing_time": round(time.time() - start_time, 3),
            "language": stt_result["language"],
            "language_prob": stt_result["language_prob"],
            "segments": stt_result["segments"],
        },
    })
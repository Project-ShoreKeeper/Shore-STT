import uuid
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from app.services.llm_service import llm_service
#from app.services.session_manager import session_manager

async def websocket_llm(websocket: WebSocket):
    await websocket.accept()

    sid = str(uuid.uuid4())
    session = session_manager.get_or_create(sid)
    cancel_event = asyncio.Event()

    await websocket.send_json({"type": "session_init", "session_id": sid})

    async def stream_and_send(transcript: str):
        cancel_event.clear()
        session.is_speaking = True
        collected = []

        try:
            async for sentence in llm_service.stream_sentences(
                transcript=transcript,
                history=session.recent(),
            ):
                if cancel_event.is_set():
                    break
                collected.append(sentence)
                await websocket.send_json({
                    "type": "sentence",
                    "text": sentence,
                    "session_id": sid,
                })

            if not cancel_event.is_set() and collected:
                full = " ".join(collected)
                session.add_turn("assistant", full)
                await websocket.send_json({
                    "type": "done",
                    "full_text": full,
                    "session_id": sid,
                })

        except Exception as e:
            await websocket.send_json({"type": "error", "message": str(e)})
        finally:
            session.is_speaking = False

    stream_task: asyncio.Task | None = None

    try:
        while True:
            msg = await websocket.receive_json()
            msg_type = msg.get("type", "")

            if msg_type == "transcript":
                text = msg.get("text", "").strip()
                if not text:
                    continue
                session.add_turn("user", text)
                if stream_task and not stream_task.done():
                    cancel_event.set()
                    await asyncio.sleep(0.05)
                stream_task = asyncio.create_task(stream_and_send(text))

            elif msg_type == "interrupt":
                cancel_event.set()
                await websocket.send_json({"type": "interrupted"})

            elif msg_type == "clear_history":
                session.clear()
                await websocket.send_json({"type": "history_cleared"})

    except WebSocketDisconnect:
        cancel_event.set()
        session_manager.delete(sid)
import io
import asyncio
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
from app.core.config import settings


class TTSService:
    def __init__(self):
        self._kokoro: Kokoro | None = None

    def load_model(self):
        """Gọi 1 lần lúc startup — load model vào RAM/VRAM."""
        print("[TTS] Loading Kokoro ONNX model...")
        self._kokoro = Kokoro(
            model=settings.KOKORO_MODEL_PATH,
            voices=settings.KOKORO_VOICES_PATH,
        )
        print("[TTS] Model loaded.")

    @property
    def kokoro(self) -> Kokoro:
        if self._kokoro is None:
            raise RuntimeError("TTS model not loaded. Call load_model() first.")
        return self._kokoro

    def _text_to_pcm(self, text: str, voice: str, speed: float) -> bytes:
        """
        Chạy inference đồng bộ → trả về raw PCM WAV bytes.
        Hàm này sẽ được chạy trong threadpool để không block event loop.
        """
        samples, sample_rate = self.kokoro.create(
            text=text,
            voice=voice,
            speed=speed,
            lang="en-us",
        )
        # Chuyển numpy float32 → WAV bytes trong memory
        buffer = io.BytesIO()
        sf.write(buffer, samples, sample_rate, format="WAV", subtype="PCM_16")
        buffer.seek(0)
        return buffer.read()

    async def synthesize(
        self,
        text: str,
        voice: str | None = None,
        speed: float | None = None,
    ) -> bytes:
        """
        Async wrapper — chạy inference trong threadpool.
        Trả về WAV bytes, frontend/websocket nhận và phát thẳng.
        """
        voice = voice or settings.KOKORO_VOICE
        speed = speed or settings.KOKORO_SPEED

        loop = asyncio.get_event_loop()
        wav_bytes = await loop.run_in_executor(
            None,                    # dùng default ThreadPoolExecutor
            self._text_to_pcm,
            text,
            voice,
            speed,
        )
        return wav_bytes

    async def synthesize_streaming(
        self,
        sentences: list[str],
        voice: str | None = None,
        speed: float | None = None,
    ):
        """
        Yield WAV bytes từng câu — dùng khi nhận sentence stream từ LLM.
        Frontend nhận từng chunk và phát ngay, không đợi toàn bộ text.
        """
        for sentence in sentences:
            if not sentence.strip():
                continue
            wav_bytes = await self.synthesize(sentence, voice, speed)
            yield wav_bytes


tts_service = TTSService()
"""
STT Service sử dụng Faster-Whisper
Chạy inference trên CPU (hoặc GPU nếu có CUDA).

Model được load 1 lần duy nhất khi server khởi động,
tái sử dụng cho tất cả các request (singleton).
"""

import numpy as np
from faster_whisper import WhisperModel
from typing import Optional
import asyncio
import time

# ─── Cấu hình mặc định ───

# Model size: tiny < base < small < medium < large-v3
# "base" cân bằng giữa tốc độ và chính xác, phù hợp tiếng Việt
MODEL_SIZE = "base"

# Compute type: "int8" nhanh nhất trên CPU, "float16" cho GPU
# Trên CPU không hỗ trợ float16 → dùng int8 hoặc float32
COMPUTE_TYPE = "int8"

# Device: "cpu" hoặc "cuda" (nếu có NVIDIA GPU + CUDA toolkit)
DEVICE = "cpu"


class STTService:
    """
    Service quản lý mô hình Faster-Whisper cho Speech-To-Text.

    Sử dụng:
        stt = STTService()
        stt.load_model()
        result = stt.transcribe(audio_float32, language="vi")
    """

    def __init__(
        self,
        model_size: str = MODEL_SIZE,
        device: str = DEVICE,
        compute_type: str = COMPUTE_TYPE,
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model: Optional[WhisperModel] = None
        self._is_loaded = False

    def load_model(self) -> None:
        """
        Load mô hình Whisper vào bộ nhớ.
        Gọi 1 lần duy nhất khi server khởi động.
        """
        if self._is_loaded:
            print(f"[STT] Model '{self.model_size}' đã được load trước đó.")
            return

        print(f"[STT] Đang tải model '{self.model_size}' "
              f"(device={self.device}, compute={self.compute_type})...")

        start = time.time()
        self.model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
        )
        elapsed = time.time() - start

        self._is_loaded = True
        print(f"[STT] Model đã sẵn sàng! (tải trong {elapsed:.1f}s)")

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    def transcribe(
        self,
        audio: np.ndarray,
        language: str = "vi",
        beam_size: int = 5,
        temperature: float = 0.0,
        initial_prompt: Optional[str] = None,
    ) -> dict:
        """
        Chạy STT trên đoạn audio (đồng bộ).

        Args:
            audio:          numpy Float32 array, sample rate 16kHz, mono
            language:       Mã ngôn ngữ ("vi", "en", "auto" để tự phát hiện)
            beam_size:      Beam search width (cao hơn = chính xác hơn nhưng chậm hơn)
            temperature:    Nhiệt độ sampling (0.0 = greedy, deterministic)
            initial_prompt: Gợi ý ngữ cảnh cho model (tên riêng, từ chuyên ngành)

        Returns:
            dict: {
                "text": str,           # Kết quả transcript
                "language": str,       # Ngôn ngữ phát hiện được
                "language_prob": float, # Xác suất ngôn ngữ
                "segments": list,      # Chi tiết từng đoạn (start, end, text)
            }
        """
        if not self._is_loaded or self.model is None:
            raise RuntimeError("Model chưa được load. Gọi load_model() trước.")

        # Nếu language = "auto", để Whisper tự detect
        lang_param = None if language == "auto" else language

        segments, info = self.model.transcribe(
            audio,
            language=lang_param,
            beam_size=beam_size,
            temperature=temperature,
            initial_prompt=initial_prompt,
            vad_filter=False,  # Đã có VAD từ frontend, không cần VAD của Whisper
            word_timestamps=False,  # Tắt để tăng tốc, bật nếu cần highlight từng từ
        )

        # Lấy toàn bộ segments (generator → list)
        segment_list = []
        full_text_parts = []

        for seg in segments:
            segment_list.append({
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": seg.text.strip(),
            })
            full_text_parts.append(seg.text.strip())

        full_text = " ".join(full_text_parts)

        return {
            "text": full_text,
            "language": info.language,
            "language_prob": round(info.language_probability, 3),
            "segments": segment_list,
        }

    async def transcribe_async(
        self,
        audio: np.ndarray,
        language: str = "vi",
        beam_size: int = 5,
        temperature: float = 0.0,
        initial_prompt: Optional[str] = None,
    ) -> dict:
        """
        Wrapper async cho transcribe().
        Chạy inference trong thread pool để không block event loop của FastAPI.
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,  # Dùng default ThreadPoolExecutor
            lambda: self.transcribe(
                audio=audio,
                language=language,
                beam_size=beam_size,
                temperature=temperature,
                initial_prompt=initial_prompt,
            ),
        )
        return result


# ─── Singleton Instance ───
# Import stt_service từ file này để dùng chung 1 instance duy nhất
stt_service = STTService()

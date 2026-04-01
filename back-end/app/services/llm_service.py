from openai import AsyncOpenAI
from typing import AsyncIterator
from app.core.config import settings
from app.utils.text_utils import clean_for_tts, split_sentences

SYSTEM_PROMPT = """You are a voice assistant. Keep responses conversational and concise.
Rules:
- 1-3 sentences per response unless asked to elaborate
- No markdown, bullet points, or special characters
- Spell out numbers and abbreviations
- No filler phrases like "Certainly!" or "Great question!"
- Respond directly and naturally as if speaking"""

class LLMService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.GROQ_BASE_URL,
        )
        self.model = settings.GROQ_MODEL

    async def stream_sentences(
        self,
        transcript: str,
        history: list[dict],
    ) -> AsyncIterator[str]:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history[-settings.max_history_turns:],
            {"role": "user", "content": transcript},
        ]

        buffer = ""
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            temperature=0.6,
            max_tokens=256,
            presence_penalty=0.1,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if not delta:
                continue

            buffer += clean_for_tts(delta)
            parts = split_sentences(buffer)

            if len(parts) > 1:
                for sentence in parts[:-1]:
                    if sentence:
                        yield sentence
                buffer = parts[-1]

        if buffer.strip():
            yield buffer.strip()

llm_service = LLMService()
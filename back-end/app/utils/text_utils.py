import regex as re

_ABBREV = r'(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc|approx|dept|est|govt)'
SENTENCE_END = re.compile(
    rf'(?<!{_ABBREV})(?<=[.!?])\s+(?=[A-Z])'
    r'|(?<=[.!?…])\s*\n+'
)

def clean_for_tts(text: str) -> str:
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'#+\s*', '', text)
    text = re.sub(r'`+[^`]*`+', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

def split_sentences(text: str) -> list[str]:
    parts = SENTENCE_END.split(text)
    return [p.strip() for p in parts if p.strip()]
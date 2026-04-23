from app.brain_mapper import get_brain_scores


def chunk_text(text: str, words_per_chunk: int = 150) -> list[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), words_per_chunk):
        chunks.append(" ".join(words[i : i + words_per_chunk]))
    return chunks[:15]


def process_text(text: str) -> dict:
    chunks = chunk_text(text)
    scores = get_brain_scores(texts=chunks)
    return {"type": "text", "scores": scores, "meta": {"char_count": len(text)}}

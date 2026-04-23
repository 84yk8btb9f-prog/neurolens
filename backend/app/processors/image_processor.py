from PIL import Image
from app.brain_mapper import get_brain_scores


def process_image(file_path: str) -> dict:
    image = Image.open(file_path).convert("RGB")
    scores = get_brain_scores(image=image)
    return {"type": "image", "scores": scores, "meta": {"path": file_path}}

import base64
from typing import List

def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def decode_base64_to_image(base64_string: str) -> bytes:
    return base64.b64decode(base64_string)

def format_context(texts: List[str], images: List[str], tables: List[str]) -> dict:
    return {
        "texts": texts,
        "images": images,
        "tables": tables
    }

def serialize_context(context):
    return {
        "text_chunks": [chunk.to_dict() if hasattr(chunk, 'to_dict') else str(chunk) for chunk in context['texts']],
        "images": [image.to_dict() if hasattr(image, 'to_dict') else str(image) for image in context['images']],
        "tables": [table.to_dict() if hasattr(table, 'to_dict') else str(table) for table in context.get('tables', [])]
    }

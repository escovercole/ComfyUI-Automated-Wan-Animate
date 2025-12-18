import os

def is_image(filename: str) -> bool:
    return filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))

def is_video(filename: str) -> bool:
    return filename.lower().endswith((".mp4", ".mov", ".avi", ".mkv"))

def list_valid(folder: str, rule) -> list:
    return sorted(
        os.path.join(folder, f) for f in os.listdir(folder)
        if rule(f)
    )

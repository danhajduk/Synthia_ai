from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

def publish_placeholder(out_path: Path, title: str = "Synthia Visuals", subtitle: str = "Placeholder") -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (1280, 720), color=(20, 20, 24))
    draw = ImageDraw.Draw(img)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Simple text without external fonts (keeps it portable)
    draw.text((40, 40), title, fill=(230, 230, 235))
    draw.text((40, 90), subtitle, fill=(180, 180, 190))
    draw.text((40, 140), f"Generated: {now}", fill=(140, 140, 150))
    draw.text((40, 200), "Renderer: weather_scene (engine not wired yet)", fill=(140, 140, 150))

    img.save(out_path, quality=92)

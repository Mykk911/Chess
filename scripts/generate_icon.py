from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main() -> None:
    out_dir = Path("assets")
    out_dir.mkdir(parents=True, exist_ok=True)

    size = 256
    img = Image.new("RGBA", (size, size), (18, 18, 18, 255))
    draw = ImageDraw.Draw(img)

    # Board-like rounded square background
    pad = 20
    draw.rounded_rectangle(
        [(pad, pad), (size - pad, size - pad)],
        radius=36,
        fill=(36, 36, 36, 255),
        outline=(210, 180, 140, 255),
        width=8,
    )

    # Knight symbol in center
    symbol = "♞"
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 150)
    except OSError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), symbol, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) // 2
    y = (size - text_h) // 2 - 8

    draw.text((x, y), symbol, font=font, fill=(240, 217, 181, 255))

    png_path = out_dir / "chess_icon.png"
    ico_path = out_dir / "chess_icon.ico"
    img.save(png_path)
    img.save(ico_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])

    print(f"Generated: {png_path}")
    print(f"Generated: {ico_path}")


if __name__ == "__main__":
    main()

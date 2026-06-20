"""工具函数"""

import pandas as pd
from pathlib import Path


def create_comparison_gif(
    original_df: pd.DataFrame,
    cleaned_df: pd.DataFrame,
    output_path: str | Path,
    duration: int = 1000,
) -> None:
    """生成清洗前后对比GIF"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise ImportError("需要安装 Pillow: pip install Pillow")

    def df_to_image(df: pd.DataFrame, title: str, width: int = 800) -> "Image.Image":
        rows = min(len(df), 10)
        cols = min(len(df.columns), 6)

        # 图片参数
        row_height = 40
        padding = 20
        header_height = 60
        height = header_height + (rows + 1) * row_height + padding * 2

        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", 20)
            small_font = ImageFont.truetype("arial.ttf", 12)
        except OSError:
            font = ImageFont.load_default()
            small_font = font

        draw.text((padding, padding), title, fill="black", font=font)

        y = header_height
        col_width = (width - padding * 2) // cols
        for j, col in enumerate(df.columns[:cols]):
            x = padding + j * col_width
            draw.text((x + 5, y), str(col)[:15], fill="blue", font=small_font)

        for i in range(rows):
            y = header_height + (i + 1) * row_height
            for j, col in enumerate(df.columns[:cols]):
                x = padding + j * col_width
                val = str(df.iloc[i][col])[:15]
                if pd.isna(df.iloc[i][col]):
                    draw.text((x + 5, y), "NaN", fill="red", font=small_font)
                else:
                    draw.text((x + 5, y), val, fill="black", font=small_font)

        stats_y = header_height + (rows + 1) * row_height
        stats = f"{len(df)} rows, {len(df.columns)} cols | missing: {int(df.isnull().sum().sum())}"
        draw.text((padding, stats_y), stats, fill="gray", font=small_font)

        return img

    img1 = df_to_image(original_df, "Before")
    img2 = df_to_image(cleaned_df, "After")

    img1.save(
        output_path,
        save_all=True,
        append_images=[img2],
        duration=duration,
        loop=0,
    )


def format_number(num: int) -> str:
    """格式化数字，添加千位分隔符"""
    return f"{num:,}"

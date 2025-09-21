# utils/image_processor.py
"""
画像処理ユーティリティ
"""
from PIL import Image
import os


def resize_product_image(image_path, max_width=400, max_height=400):
    """商品画像のリサイズ"""
    try:
        with Image.open(image_path) as img:
            # アスペクト比を保持してリサイズ
            img.thumbnail((max_width, max_height), Image.LANCZOS)
            
            # JPEG形式で保存（アルファチャンネルがある場合は白背景に変換）
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            img.save(image_path, 'JPEG', quality=85, optimize=True)
            return True
    except Exception as e:
        print(f"画像処理エラー: {e}")
        return False


def create_thumbnail(image_path, thumbnail_path, size=(150, 150)):
    """サムネイル画像作成"""
    try:
        with Image.open(image_path) as img:
            img.thumbnail(size, Image.LANCZOS)
            
            # 透明背景を白に変換
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            img.save(thumbnail_path, 'JPEG', quality=80)
            return True
    except Exception as e:
        print(f"サムネイル作成エラー: {e}")
        return False

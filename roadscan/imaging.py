"""Decode bounded image uploads in memory; never retain source metadata."""
import io

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError
from PIL.Image import open as pillow_open


def decode_image(raw: bytes, max_pixels: int = 25_000_000):
    # Detector libraries patch Image.open; uploads must keep Pillow's supported decoders.
    try:
        with pillow_open(io.BytesIO(raw), formats=('JPEG', 'PNG', 'WEBP')) as image:
            if image.format not in ('JPEG', 'PNG', 'WEBP'):
                raise ValueError('Unsupported image')
            if image.width * image.height > max_pixels:
                raise ValueError('Too many pixels')
            image.verify()
        with pillow_open(io.BytesIO(raw), formats=('JPEG', 'PNG', 'WEBP')) as image:
            return ImageOps.exif_transpose(image).convert('RGB')
    except (UnidentifiedImageError, ValueError, OSError, Image.DecompressionBombError) as exc:
        raise HTTPException(415, 'Invalid image or image dimensions exceed the limit') from exc

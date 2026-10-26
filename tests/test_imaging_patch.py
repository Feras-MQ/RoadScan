import io

import pytest
from fastapi import HTTPException
from PIL import Image

from roadscan.imaging import decode_image


def test_upload_decoder_is_unaffected_by_detector_image_patch(monkeypatch):
    data = io.BytesIO()
    Image.new('RGB', (12, 8), 'red').save(data, format='PNG')

    def detector_fallback(*args, **kwargs):
        raise ModuleNotFoundError("No module named 'pi_heif'", name='pi_heif')

    monkeypatch.setattr(Image, 'open', detector_fallback)
    with decode_image(data.getvalue()) as image:
        assert image.size == (12, 8)
        assert image.getpixel((0, 0)) == (255, 0, 0)
    with pytest.raises(HTTPException) as error:
        decode_image(b'not an image')
    assert error.value.status_code == 415

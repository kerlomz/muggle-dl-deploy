#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import io
import base64
import urllib.parse
from PIL import Image, ImageOps, PngImagePlugin


class DisplayUtils:

    @staticmethod
    def encode_pil_to_base64(pil_image):
        with io.BytesIO() as output_bytes:

            # Copy any text-only metadata
            use_metadata = False
            metadata = PngImagePlugin.PngInfo()
            for key, value in pil_image.info.items():
                if isinstance(key, str) and isinstance(value, str):
                    metadata.add_text(key, value)
                    use_metadata = True

            pil_image.save(
                output_bytes, "PNG", pnginfo=(metadata if use_metadata else None)
            )
            bytes_data = output_bytes.getvalue()
        base64_str = str(base64.b64encode(bytes_data), "utf-8")
        base64_str = "\n".join([base64_str[i:i + 128] for i in range(0, len(base64_str), 128)])
        encoded_str = urllib.parse.quote(base64_str)
        return "data:image/png;base64," + encoded_str

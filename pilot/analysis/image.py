import logging
from wand.image import Image

def analyze_image(filename, foreign_keys=None):
    img = Image(filename=filename)
    image_metadata = {
        'name': 'Image Metadata',
        'width': img.width,
        'height': img.height,
        'colorspace': img.colorspace,
        'format': img.format,
        }
    return image_metadata

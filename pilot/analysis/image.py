from PIL import Image


def analyze_image(filename, foreign_keys=None):
    img = Image.open(filename)
    image_metadata = {
        'name': 'Image Metadata',
        'width': img.width,
        'height': img.height,
        'colorspace': img.mode,
        'format': img.format,
        'format_description': img.format_description,
        }
    return image_metadata

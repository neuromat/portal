import io
from random import randint

from PIL import Image


def generate_image_file(width, height, filename):
    """
    Generates an image file with a random color
    :param filename with image extension
    :param width
    :param height
    :return: image file
    """
    file = io.BytesIO()
    image = Image.new(
        'RGB', size=(width, height),
        color=(randint(0, 256), randint(0, 256), randint(0, 256))
    )
    file.name = filename
    image.save(file)
    file.seek(0)
    return file

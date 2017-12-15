import io
from random import randint
from PIL import Image
from faker import Factory


def generate_image_file(width=None, height=None, filename=None):
    """
    Generates an image file with random color
    :param filename with image extension
    :param width
    :param height
    :return: image file
    """
    faker = Factory.create()

    file = io.BytesIO()
    image = Image.new(
        'RGB', size=(width or 500, height or 500),
        color=(randint(0, 256), randint(0, 256), randint(0, 256))
    )
    file.name = filename or faker.word() + '.jpg'
    image.save(file)
    file.seek(0)
    return file

import logging
import os

import PIL.Image
import numpy as np
from skimage import img_as_float


def alpha_composite(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    """Composition of 2 RGBA images

    The algorithm comes from http://en.wikipedia.org/wiki/Alpha_compositing
    """
    # http://stackoverflow.com/a/3375291/190597
    out = np.empty(src.shape, dtype='float')
    alpha = np.index_exp[:, :, 3:]
    rgb = np.index_exp[:, :, :3]
    src_a = src[alpha] / 255.0
    dst_a = dst[alpha] / 255.0

    out[alpha] = src_a + dst_a * (1. - src_a)
    old_setting = np.seterr(invalid='ignore')

    out[rgb] = (src[rgb] * src_a + dst[rgb] * dst_a * (1. - src_a)) / out[alpha]

    np.seterr(**old_setting)

    out[alpha] *= 255
    np.clip(out, 0, 255)
    # astype('uint8') maps np.nan (and np.inf) to 0
    out = out.astype('uint8')
    return out


def paste_watermark(image: PIL.Image.Image, watermark: PIL.Image.Image, save_path: str):
    min_image_dimension = min(image.size)
    watermark_length = int(min_image_dimension / 4.)

    watermark_size = (watermark_length, watermark_length)
    watermark = watermark.resize(watermark_size, PIL.Image.ANTIALIAS)

    foreground_shape = (image.size[1], image.size[0], 4)

    top_margin = int(5 * image.size[1] / 6.)

    foreground_array = np.zeros(foreground_shape, dtype=np.uint8)
    foreground_array[top_margin - watermark_length:top_margin, :watermark_length, :] = np.array(watermark)

    image_array = np.array(image)
    background_rgb = img_as_float(image_array[..., :-1])
    mean = np.mean(background_rgb[top_margin - watermark_length:top_margin, :watermark_length, :])
    if mean < 0.4:
        foreground_alpha = foreground_array[..., -1:]
        foreground_rgb = foreground_array[..., :-1]
        foreground_rgb = 255 - foreground_rgb
        foreground_array = np.dstack((foreground_rgb, foreground_alpha))

    marked_image = alpha_composite(foreground_array, image_array)
    PIL.Image.fromarray(marked_image, mode='RGBA').save(save_path)


def mark_images(path: str, watermark_path: str):
    watermark = PIL.Image.open(watermark_path)
    for folder, _, files in os.walk(path):
        for file_path in files:
            if file_path.endswith('.jpg'):
                path = os.path.join(folder, file_path)
                image = PIL.Image.open(path)
                image = image.convert('RGBA')
                save_path = path.replace('.jpg', '.png')
                logging.info(save_path)
                paste_watermark(image, watermark=watermark, save_path=save_path)

import os
from PIL import Image
import math


def calc_width_height(width, height, min_size, zoom_rate):
    w = int(width * zoom_rate)
    h = int(height * zoom_rate)
    if w * h < min_size:
        w = int(math.sqrt(min_size * w / h))
        h = int(min_size / w)
    return (w, h)


def process_file(src_file, dst_file, min_size, zoom_rate):
    with Image.open(src_file) as img:
        original_width, original_height = img.size
        (dst_width, dst_height) = calc_width_height(original_width, original_height, min_size, zoom_rate)
        img.thumbnail((dst_width, dst_height))
        img.save(dst_file, quality=100)


def process_dir(dir_name, sub_dir_name, zoom_rate):
    num = 0
    min_width = int(7360 * zoom_rate)
    min_height = int(4912 * zoom_rate)
    min_size = min_width * min_height
    sub_dir = dir_name + os.sep + sub_dir_name
    if not os.path.exists(sub_dir):
        os.mkdir(sub_dir)
    for p, _, files in os.walk(dir_name):
        if p != dir_name:
            continue
        for f in files:
            if f.lower().endswith(".jpg") or f.lower().endswith(".png"):
                src_file = p + "/" + f
                dst_file = sub_dir + "/" + f
                print(f"Processing file '{f}' ...")
                process_file(src_file, dst_file, min_size, zoom_rate)
                num = num + 1
    return num

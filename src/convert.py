"""Resize and crop images to square, save as tiff."""
from __future__ import division, print_function
import os
from multiprocessing.pool import Pool

import click
import numpy as np
from PIL import Image, ImageFilter

import datax

N_PROC = 2

def convert(fname, crop_size):
    img = Image.open(fname)

    blurred = img.filter(ImageFilter.BLUR)
    ba = np.array(blurred)
    h, w, _ = ba.shape

    if w > 1.2 * h:
        left_max = ba[:, : w // 32, :].max(axis=(0, 1)).astype(int)
        right_max = ba[:, - w // 32:, :].max(axis=(0, 1)).astype(int)
        max_bg = np.maximum(left_max, right_max)

        foreground = (ba > max_bg + 10).astype(np.uint8)
        bbox = Image.fromarray(foreground).getbbox()

        if bbox is None:
            print('bbox none for {} (???)'.format(fname))
        else:
            left, upper, right, lower = bbox
            # if we selected less than 80% of the original 
            # height, just crop the square
            if right - left < 0.8 * h or lower - upper < 0.8 * h:
                print('bbox too small for {}'.format(fname))
                bbox = None
    else:
        bbox = None

    if bbox is None:
        bbox = square_bbox(img)

    cropped = img.crop(bbox)
    resized = cropped.resize([crop_size, crop_size])
    return resized


def square_bbox(img):
    w, h = img.size
    left = max((w - h) // 2, 0)
    upper = 0
    right = min(w - (w - h) // 2, w)
    lower = h
    return (left, upper, right, lower)


def convert_square(fname, crop_size):
    img = Image.open(fname)
    bbox = square_bbox(img)
    cropped = img.crop(bbox)
    resized = cropped.resize([crop_size, crop_size])
    return resized


def get_convert_fname(fname, extension, directory, convert_directory):
    return fname.replace('png', extension).replace(directory, 
                                                    convert_directory)


def process(args):
    fun, arg = args
    directory, convert_directory, fname, crop_size, extension = arg
    convert_fname = get_convert_fname(fname, extension, directory, 
                                      convert_directory)
    print(convert_fname)
    if not os.path.exists(convert_fname):
        print("here")
        img = fun(fname, crop_size)
        save(img, convert_fname)


def save(img, fname):
    img.save(fname, quality=97)

@click.command()
@click.option('--directory', default='data/train', show_default=True,
              help="Directory with original images.")
@click.option('--convert_directory', default='data/train_tiny', show_default=True,
              help="Where to save converted images.")
@click.option('--test', is_flag=True, default=False, show_default=True,
              help="Convert images one by one and examine them on screen.")
@click.option('--crop_size', default=256, show_default=True,
              help="Size of converted images.")
@click.option('--extension', default='tiff', show_default=True,
              help="Filetype of converted images.")
def main(directory, convert_directory, test, crop_size, extension):
    print("Ver")
    try:
        os.mkdir(convert_directory)
    except OSError:
        pass

    filenames = [os.path.join(dp, f) for dp, dn, fn in os.walk(directory)
                 for f in fn if f.endswith('png') or f.endswith('tiff')] 
    # print(filenames)
    # filenames = sorted(filenames[:10])
    filenames = filenames[:10]
    print(filenames)

    if test:
        names = data.get_names(filenames)
        # print(names)
        y = data.get_labels(names)
        print(y)
        for f, level in zip(filenames, y):
            if level == 1:
                try:
                    img = convert(f, crop_size)
                    img.show()
                    Image.open(f).show()
                    real_raw_input = vars(__builtins__).get('raw_input',input)
                    real_raw_input('enter for next')
                except KeyboardInterrupt:
                    exit(0)

    print("Resizing images in {} to {}, this takes a while."
          "".format(directory, convert_directory))

    n = len(filenames)
    print("******************Number of Files: ", n)
    print("Filenames: ",filenames)
    # process in batches, sometimes weird things happen with Pool on my machine
    # batchsize = 500
    # batches = n // batchsize + 1
    # pool = Pool(N_PROC)

    # args = []

    # for f in filenames:
    #     args.append((convert, (directory, convert_directory, f, crop_size, 
    #                        extension)))
    # print(args)
    # for i in range(batches):
    #     print("batch {:>2} / {}".format(i + 1, batches))
    #     pool.map(process, args[i * batchsize: (i + 1) * batchsize])

    # pool.close()

    # print('done')

if __name__ == '__main__':
    main()

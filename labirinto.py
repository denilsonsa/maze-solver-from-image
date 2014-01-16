#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:ts=4 sw=4 et

from __future__ import division
from __future__ import print_function

from PIL import Image

WALL = (0, 0, 0)
SPACE = (255, 255, 255)
RED = (255, 0, 0)


def pixel_preprocessing(pix):
    '''Maps pixel values to other values. Should be passed to Image.point().
    '''

    if pix > 127:
        return 255
    else:
        return 0


def find_white_border(data, size):
    '''Finds how large the white border is (for auto-cropping).

    Args:
    data -- pixel data, as returned by list(Image.getdata())
    size -- (width, height) tuple
    '''

    def find_white_lines(data, start, length, expr1, expr2, step):
        '''Internal logic for finding white lines.

        This logic is repeated for all 4 edges of the image.

        Returns the number of white lines found.

        Args:
        data   -- pixel data, as returned by list(Image.getdata())
        start  -- integer, usually zero
        length -- number of possible lines (i.e. abort when value is reached)
        expr1  -- lambda for returning the beginning of the indexed line
        expr1  -- lambda for returning the end of the indexed line
        step   -- step for the pixel data slice
        '''
        index = start
        while index < length:
            line = data[expr1(index):expr2(index):step]
            if all(pix == (255, 255, 255) for pix in line):
                index += 1
            else:
                break
        return index

    width, height = size

    top    = find_white_lines(data, 0, height,
                              lambda index: (index) * width,
                              lambda index: (index + 1) * width, 1)
    bottom = find_white_lines(data, 0, height,
                              lambda index: (height - 1 - index) * width,
                              lambda index: (height - 1 - index + 1) * width, 1)
    left    = find_white_lines(data, 0, width,
                              lambda index: index,
                              lambda index: index + height * width, width)
    right   = find_white_lines(data, 0, width,
                              lambda index: width - 1 - index,
                              lambda index: width - 1 - index + height * width, width)

    return top, bottom, left, right


def main():
    # Preparations before running this script:
    # $ pdfimages -j Desafio-labirinto-Desenvolvedor.pdf foo
    # $ mv foo-002.ppm labirinto.ppm
    # $ rm -f foo-*.ppm
    # Optional (just to save space):
    # $ convert labirinto.ppm labirinto.png

    img = Image.open('labirinto.png')

    # This script expects RGB images. Let's convert it.
    img = img.convert('RGB')

    # Preprocessing the image, essentially removing JPG artifacts by
    # thresholding, and thus reducing the number of colors.
    img = img.point(pixel_preprocessing)
    img.save('preprocessed.png')

    data = list(img.getdata())

    # Auto-cropping the white border.
    top, bottom, left, right = find_white_border(data, img.size)
    print('White border detected: top={0} bottom={1} left={2} '
            'right={3}'.format(top, bottom, left, right))

if __name__ == "__main__":
    main()

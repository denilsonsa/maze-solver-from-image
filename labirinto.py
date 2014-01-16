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


def find_white_border(img):
    '''Finds how large the white border is (for auto-cropping).
    '''

    width, height = img.size
    data = img.getdata()

    top, bottom, left, right = 0, 0, 0, 0

    # This piece of 4 copy-pasted blocks could be rewritten as a single
    # function receiving some lambda expressions...
    while top < height:
        line = data[(top)*width : (top+1)*width : 1]
        if all(pix == WHITE for pix in line):
            top += 1
        else:
            break

    while bottom < height:
        line = data[(height-1-bottom)*width : (height-bottom)*width : 1]
        if all(pix == WHITE for pix in line):
            bottom += 1
        else:
            break


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

if __name__ == "__main__":
    main()

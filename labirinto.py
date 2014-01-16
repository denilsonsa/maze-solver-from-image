#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:ts=4 sw=4 et

from __future__ import division
from __future__ import print_function

from PIL import Image


def pixel_preprocessing(pix):
    '''Maps pixel values to other values. Should be passed to Image.point().
    '''

    if pix > 127:
        return 255
    else:
        return 0


def find_white_border(img):
    '''Finds how large the white border is (for auto-cropping).'''

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

    data = list(img.getdata())
    width, height = img.size

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


def find_walls(img):
    '''Analyzes pixel data and finds out the X,Y coordinates of the wall grid.

    Returns two lists:
    - a list of Y coordinates for horizontal walls
    - a list of X coordinates for vertical walls
    '''

    data = list(img.getdata())
    width, height = img.size

    # Number of black pixels per each line and column.
    blacks_per_line = [
            sum(pix == (0, 0, 0) for pix in data[i * width:(i + 1) * width])
            for i in range(height)]
    blacks_per_col = [
            sum(pix == (0, 0, 0) for pix in data[i:i + height * width:width])
            for i in range(width)]

    # For the proposed input image, non-wall lines have at most 14% black
    # pixels, while wall lines have at least 49%. Thus, the 33% threshold seems
    # reasonable. Although this wall-detection code works fine for randomly
    # generated labyrinths, it is still possible to craft a labyrinth that will
    # break this logic.

    threshold = width/3.0
    wall_rows = [i for i, amount in enumerate(blacks_per_line) if amount > threshold]
    #wall_rows = [i for i in range(height) if blacks_per_line[i] > threshold]

    threshold = height/3.0
    wall_cols = [i for i, amount in enumerate(blacks_per_col) if amount > threshold]

    return wall_rows, wall_cols


def main():
    # TODO: Receive the filename from the command line.
    # TODO: Make the comment below a --help output.
    #
    # Preparations before running this script:
    # $ pdfimages -j Desafio-labirinto-Desenvolvedor.pdf foo
    # $ mv foo-002.ppm labirinto.ppm
    # $ rm -f foo-*.ppm
    # Optional (just to save space):
    # $ convert labirinto.ppm labirinto.png
    #
    # This script expects a labyrinth picture such as:
    # - It is a rectangular grid.
    # - Walls are black.
    # - Empty space is white.
    # - Walls are always perfectly aligned with the grid
    # - Walls are 1 pixel thick.
    # - Each wall is a few pixels away from each other (i.e. each cell is a few
    #   pixels wide).

    img = Image.open('labirinto.png')

    # This script expects RGB images. Let's convert it.
    img = img.convert('RGB')

    # Preprocessing the image, essentially removing JPG artifacts by
    # thresholding, and thus reducing the number of colors.
    img = img.point(pixel_preprocessing)
    img.save('01-preprocessed.png')

    # Auto-cropping the white border.
    width, height = img.size
    top, bottom, left, right = find_white_border(img)
    print('White border detected: top={0} bottom={1} left={2} '
            'right={3}'.format(top, bottom, left, right))
    img = img.crop((left, top, width - right, height - bottom))
    width, height = img.size
    img.save('02-autocropped.png')

    wall_rows, wall_cols = find_walls(img)
    print(wall_rows)
    print(wall_cols)

if __name__ == "__main__":
    main()

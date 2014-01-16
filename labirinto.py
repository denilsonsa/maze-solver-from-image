#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:ts=4 sw=4 et

from __future__ import division
from __future__ import print_function

import argparse
import textwrap
from PIL import Image


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=textwrap.dedent('''
        Given a rectangular maze as an image, this script will parse the image
        and solve the maze.

        This script was written by Denilson Sá <denilsonsa@gmail.com> as a
        challenge to solve a maze that was supplied as a PDF file.

        Preparations before running this script:
        $ pdfimages -j Desafio-labirinto-Desenvolvedor.pdf foo
        $ mv foo-002.ppm maze.ppm
        $ rm -f foo-*.ppm
        Optional (just to save space):
        $ convert maze.ppm maze.png
        '''),
        epilog=textwrap.dedent('''
        This script expects a maze picture such as:
        - It is a rectangular grid.
        - Empty space is white.
        - Walls are black.
        - Walls are always perfectly aligned with the grid.
        - Walls are 1 pixel thick.
        - Each wall is a few pixels away from each other (i.e. each cell is a
          few pixels wide).
        - A cell is considered special (i.e. the start/finish) if the middle
          pixels are neither white nor black. The color must be saturated
          enough to survive the preprocessing phase. Colors such as #FF0000 are
          good choices.
        '''),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '-i', '--save-intermediate',
        action='store_true',
        help='''
        save intermediate images as 01-preprocessed.png and 02-autocropped.png
        '''
    )
    parser.add_argument(
        '-v', '--verboseness',
        action='store',
        type=int,
        choices=[0, 1, 2, 3],
        # 0: Only the solution
        # 1: + the input maze
        # 2: + the number of dead-ends removed
        #    + the message 'does not contain cycles'
        # 3: + the maze after each dead-end removal iteration
        #    + the maze after removing the cycles.
        default=1,
        help='''
        control how much information will be printed at the output
        '''
    )
    parser.add_argument(
        'imgfile',
        action='store',
        type=argparse.FileType('rb'),
        help='the picture of the maze'
    )

    args = parser.parse_args()
    return args


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

    top = find_white_lines(
        data, 0, height,
        lambda index: (index) * width,
        lambda index: (index + 1) * width, 1)
    bottom = find_white_lines(
        data, 0, height,
        lambda index: (height - 1 - index) * width,
        lambda index: (height - 1 - index + 1) * width, 1)
    left = find_white_lines(
        data, 0, width,
        lambda index: index,
        lambda index: index + height * width, width)
    right = find_white_lines(
        data, 0, width,
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
    # Booleans are essentially integers in Python, so I can just sum them up.
    blacks_per_line = [
        sum(pix == (0, 0, 0) for pix in data[i * width:(i + 1) * width])
        for i in range(height)]
    blacks_per_col = [
        sum(pix == (0, 0, 0) for pix in data[i:i + height * width:width])
        for i in range(width)]

    # For the proposed input image, non-wall lines have at most 14% black
    # pixels, while wall lines have at least 49%. Thus, the 33% threshold seems
    # reasonable. Although this wall-detection code works fine for randomly
    # generated mazes, it is still possible to craft a mazes that will break
    # this logic.

    threshold = width/3.0
    wall_rows = [i for i, amount in enumerate(blacks_per_line)
                 if amount > threshold]
    #wall_rows = [i for i in range(height) if blacks_per_line[i] > threshold]

    threshold = height/3.0
    wall_cols = [i for i, amount in enumerate(blacks_per_col)
                 if amount > threshold]

    return wall_rows, wall_cols


class Cell(object):
    def __init__(self, up=True, down=True, left=True, right=True,
                 special=False):
        # True if we can move up/down/left/right.
        # Up/down and left/right are redundant, since there are no one-way
        # passages. However, adding them as attributes makes the code a bit
        # more readable.
        self.up = up
        self.down = down
        self.left = left
        self.right = right
        self.special = special

    def __repr__(self):
        return 'Cell({up}, {down}, {left}, {right}, {special})'.format(
            dir(self))

    def __unicode__(self):
        table = u'░╵╷│╴┘┐┤╶└┌├─┴┬┼▓╹╻┃╸┛┓┫╺┗┏┣━┻┳╋'
        return table[self.exits_as_number]

    @property
    def exits_as_number(self):
        return (self.up << 0 | self.down << 1 | self.left << 2 |
                self.right << 3 | self.special << 4)

    @property
    def exits(self):
        '''Returns the number of exits from this cell.'''
        return self.up + self.down + self.left + self.right + self.special

    @exits.setter
    def exits(self, value):
        if value != 0:
            raise NotImplementedError('You can only assign the value zero.')
        self.up = False
        self.down = False
        self.left = False
        self.right = False
        self.special = False

    @staticmethod
    def maze_as_unicode(maze):
        '''Receives a list of list of Cells and returns a unicode string.'''
        return u'\n'.join(
            u''.join(unicode(cell) for cell in line)
            for line in maze)


def build_maze_from_image(img):
    wall_rows, wall_cols = find_walls(img)

    # Measured in cells.
    width = len(wall_cols) - 1
    height = len(wall_rows) - 1
    maze = [[Cell() for i in range(width)] for j in range(height)]

    for i in range(width):
        for j in range(height):
            x = wall_cols[i]
            xn = wall_cols[i+1]
            y = wall_rows[j]
            yn = wall_rows[j+1]

            # Looking at the middle pixel of the wall. If it is black, there is
            # a wall there.
            if img.getpixel(((x+xn)//2, y)) == (0, 0, 0):
                maze[j][i].up = False
            if img.getpixel(((x+xn)//2, yn)) == (0, 0, 0):
                maze[j][i].down = False
            if img.getpixel((x, (y+yn)//2)) == (0, 0, 0):
                maze[j][i].left = False
            if img.getpixel((xn, (y+yn)//2)) == (0, 0, 0):
                maze[j][i].right = False

            # Looking at the middle pixel of the cell. If it is neither white
            # nor black, it is special.
            if img.getpixel(((x+xn)//2, (y+yn)//2)) not in [
                    (0, 0, 0), (255, 255, 255)]:
                maze[j][i].special = True

    return maze


def cut_dead_ends(maze, verboseness=0):
    '''Receives a list of list of Cells, find dead-ends and remove them.

    Verboseness can be:
    0: Nothing is printed.
    1: The number of dead-ends found on each passage is printed.
    2: The number of dead-ends and the maze are printed.
    '''

    height = len(maze)
    width = len(maze[0])

    # List of (x, y) coordinates for each dead-end.
    dead_ends = []
    for i in range(width):
        for j in range(height):
            if maze[j][i].exits == 1:
                dead_ends.append((i, j))

    num_dead_ends_over_time = []

    while dead_ends:
        if verboseness == 1:
            num_dead_ends_over_time.append(len(dead_ends))
        elif verboseness == 2:
            print('Cutting {0} dead-ends.'.format(len(dead_ends)))

        old_dead_ends = dead_ends
        dead_ends = []

        for x, y in old_dead_ends:
            cell = maze[y][x]
            directions = [
                ('up', 'down', 0, -1),
                ('down', 'up', 0, +1),
                ('left', 'right', -1, 0),
                ('right', 'left', +1, 0),
            ]
            for dir, revdir, xdelta, ydelta in directions:
                if getattr(cell, dir):
                    setattr(cell, dir, False)
                    x2 = x + xdelta
                    y2 = y + ydelta
                    if 0 <= x2 < width and 0 <= y2 < height:
                        other_cell = maze[y2][x2]
                        setattr(other_cell, revdir, False)
                        if other_cell.exits == 1:
                            dead_ends.append((x2, y2))

        if verboseness == 2:
            print(Cell.maze_as_unicode(maze))

    if verboseness == 1 and num_dead_ends_over_time:
        print('Cutting dead-ends: {0}'.format(
            ', '.join(num_dead_ends_over_time)))


def main():
    options = parse_arguments()
    img = Image.open(options.imgfile)

    # This script expects RGB images. Let's convert it.
    img = img.convert('RGB')

    # Preprocessing the image, essentially removing JPG artifacts by
    # thresholding, and thus reducing the number of colors.
    img = img.point(pixel_preprocessing)
    if options.save_intermediate:
        img.save('01-preprocessed.png')

    # Auto-cropping the white border.
    width, height = img.size
    top, bottom, left, right = find_white_border(img)
    #print('White border detected: top={0} bottom={1} left={2} '
    #      'right={3}'.format(top, bottom, left, right))
    img = img.crop((left, top, width - right, height - bottom))
    width, height = img.size
    if options.save_intermediate:
        img.save('02-autocropped.png')

    # Building a maze of cells from the image pixels.
    maze = build_maze_from_image(img)
    if options.verboseness >= 1:
        print('Raw maze:')
        print(Cell.maze_as_unicode(maze))

    # Solving the maze.
    cut_dead_ends(maze, options.verboseness - 1)

    if options.verboseness >= 0:
        print('Solution:')
        print(Cell.maze_as_unicode(maze))

    # Checking for cycles. After removing the special attribute of the cells
    # and running the solver again, all cells should have no exits. Otherwise,
    # there is a cycle.
    for line in maze:
        for cell in line:
            if cell.special:
                cell.special = False
    cut_dead_ends(maze)

    if any(cell.exits != 0 for cell in line for line in maze):
        if options.verboseness >= 0:
            print('This maze contains cycles.')
    else:
        if options.verboseness >= 2:
            print('This maze does not contain cycles.')
    if options.verboseness >= 3:
        print(Cell.maze_as_unicode(maze))


if __name__ == '__main__':
    main()

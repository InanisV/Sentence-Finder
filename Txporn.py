#! /usr/bin/env python
# -*- coding: utf-8 -*-
import os
import textwrap
import unicodedata
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageColor import getrgb


class Txporn(object):

    def __init__(self, input_text: str, output_name: str, font='arial', font_size=20,
                 color='black', out_dir=r'./', text_transparency=0.0):
        self.input_text = input_text
        self.font = font
        self.size = font_size
        self.color = color
        self.text_transparency = text_transparency
        self.out_dir = out_dir
        self.output_name = output_name
        self.DPI = (100, 100)

    @staticmethod
    def count_char(text):
        count = 0
        for c in text:
            if unicodedata.east_asian_width(c) in ["F", "W", "A"]:
                count += 1
            else:
                count += .5
        return count

    def convert(self):
        fontsize = self.size
        font = ImageFont.truetype(font=self.font, size=fontsize)
        lines = textwrap.wrap(self.input_text, width=40)
        y_text, max_width = 0, 0
        for line in lines:
            width, height = font.getsize(line)
            y_text += height
            if width > max_width:
                max_width = width
        interval = y_text/len(lines)

        length = self.count_char(self.input_text)
        width_p = int(fontsize / 72. * self.DPI[0] * length)
        height_p = int(fontsize / 72. * self.DPI[1])
        color_rgba = getrgb(self.color) + (int((1. - self.text_transparency) * 255),)

        # write text
        img = Image.new('RGB', (max_width, y_text+10), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        lines = textwrap.wrap(self.input_text, width=40)
        y_text = 0
        for line in lines:
            draw.text((0, y_text), line, font=font, fill=color_rgba)
            y_text += interval
        # draw.text((0, 0), self.input_text, font=font, fill=color_rgba)

        # remove margin
        crop = img.split()[-1].getbbox()
        img = img.crop(crop)

        # make directory
        dir_path = self.out_dir
        if dir_path:
            if not os.path.isdir(dir_path):
                os.makedirs(dir_path)

        output_path = os.path.join(dir_path, self.output_name + ".png")
        img.save(output_path, dpi=self.DPI)


# def parse_argument():
#     parser = argparse.ArgumentParser("txporn", add_help=True)
#     parser.add_argument("--text", "-t", help="input text", type=str)
#     parser.add_argument("--font", "-f", help="font name or font file path", type=str, default="Meiryo")
#     parser.add_argument("--font_size", "-s", help="font size", type=int, default=20)
#     parser.add_argument("--color", "-c", help="text color(color name or color code, e.g. #ffffff)", default="black")
#     parser.add_argument("--text_transparency", "-a", help="text transparency (0 ~ 1)", type=float, default=0)
#     parser.add_argument("--output_dir_path", "-o", help="output dirctory path", type=str, default="./")
#     args = parser.parse_args()
#     return args
#
#
#
#
#
if __name__ == '__main__':
    new = Txporn(
        "It is encouraging to find at the present day so much interest in religious idealism, "+
        "and it is proved by Eucken beyond the possibility of doubt that "+
        "without some form of such idealism no individual or nation can realise its deepest potencies.",
        font='TEMPSITC.TTF', text_transparency=0)
    new.convert()

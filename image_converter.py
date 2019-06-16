import os
from PIL import Image

def to_grayscale(infile, outfile='result.pgm'):
    im = Image.open(infile)
    g_im = im.getchannel('G')
    g_im.save(outfile,'PPM')
    im.close()
    g_im.close()

def to_png(infile, outfile='result.png'):
    im = Image.open(infile)
    im.save(outfile,'PNG')
    im.close()

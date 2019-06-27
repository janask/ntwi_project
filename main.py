import json
import xlrd
import os
from PIL import Image
from image_converter import to_grayscale, to_png
import subprocess

#load config
with open('config.json') as conf_file:  
    config = json.load(conf_file)
algorithms = config['algorithms']
#load images patches and types
img_desc = xlrd.open_workbook(config['images_description']).sheet_by_index(0)
images = []
for row in range(3, img_desc.nrows):
    images.append({'name': img_desc.cell_value(row,0), 'photo': bool(img_desc.cell_value(row,1))})

for img in images:
    #prepare images
    path = os.path.join(config['images_path'], img['name'])
    to_grayscale(path)
    to_png('result.pgm')
    #measure original size [pixels]
    img_size = Image.open('result.pgm').size
    img_size = img_size[0]*img_size[1]
    for alg in algorithms:
        #prepare commands
        command = os.path.join(config['algorithms_path'], alg['path'], alg['encode'])
        if alg['png_required']:
            command = command.format(infile='result.png', outfile='compressed')
        else:
            command = command.format(infile='result.pgm', outfile='compressed')
        #compress (TODO time measuring)
        subprocess.call(command, shell=True)
        #measure new size [bytes]
        cmpr_size = os.stat('compressed').st_size
        #decompress (TODO time measuring)
        command = os.path.join(config['algorithms_path'], alg['path'], alg['decode'])
        command = command.format(infile='compressed', outfile='decompressed')
        subprocess.call(command, shell=True)
        input('Next')


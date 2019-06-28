import json
import xlrd
import os
from PIL import Image
from image_converter import to_grayscale, to_png
import subprocess
import time

def loadImagesDetailsFromDescription():
    img_desc = xlrd.open_workbook( description_path ).sheet_by_index(0)
    images = []
    for row in range(3, img_desc.nrows):
        images.append({'path': img_desc.cell_value(row,0), 'photo': bool(img_desc.cell_value(row,1))})
    return images

def getCurrentDirPathFor(item):
    currentPath = os.getcwd()
    return os.path.join( currentPath, item)

def countTime(command, repeatCount):
    total_time = 0

    for iteration in range(0, repeatCount + 1):
        start = time.time()
        subprocess.call(command, shell=True)
        #skip first compression
        if iteration is not 0:
            total_time += time.time() - start

    return total_time / repeatCount

def getInfileExtension(png_required):
    return ['pgm', 'png'][png_required]

#load config
with open('config.json') as conf_file:  
    config = json.load(conf_file)

description_path = getCurrentDirPathFor( config['images_description'] )
images_path = getCurrentDirPathFor( config['images_dir'] )
algorithms_path = getCurrentDirPathFor( config['algorithms_dir'] )

log = {}

for (index, imageDetails) in enumerate( loadImagesDetailsFromDescription() ):
    #dev purpose ONLY -- skip after 5th image
    if index is 5:
        break
    
    #prepare images
    realImagePath = os.path.join(images_path, imageDetails['path'])
    to_grayscale(realImagePath)
    to_png('result.pgm')

    #measure original size [pixels]
    img_size = Image.open('result.pgm').size
    initial_img_size = img_size[0] * img_size[1]

    for algorithm in config['algorithms']:
        extension = getInfileExtension( algorithm['png_required'] )
        compressCommand = os.path.join(algorithms_path, algorithm['path'], algorithm['encode']).format( infile='result.{0}'.format(extension), outfile='compressed' )

        compress_time = countTime(compressCommand, 5)
        compressed_img_size = os.stat('compressed').st_size

        decompressCommand = os.path.join(algorithms_path, algorithm['path'], algorithm['decode']).format(infile='compressed', outfile='decompressed')
        decompressTime = countTime(decompressCommand, 5)

        currentImageName = str(imageDetails['path']).split('\\')[-1]
        algorithmName = str(algorithm['name']).encode('utf-8')

        if algorithmName not in log:
            log[algorithmName] = {}
        
        log[algorithmName][currentImageName] = {
            "initialSize": initial_img_size,
            "compressTime": compress_time,
            "decompressTime": decompressTime,
            "compressedSize": compressed_img_size
        }

#you can mark breakpoint on it :)
pass
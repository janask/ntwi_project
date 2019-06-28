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
    if index is 2:
        break
    
    #prepare images
    realImagePath = os.path.join(images_path, imageDetails['path'])
    to_grayscale(realImagePath)
    to_png('result.pgm')

    for algorithm in config['algorithms']:
        extension = getInfileExtension( algorithm['png_required'] )
        input_file = 'result.{0}'.format(extension)
        initial_img_size =  os.stat(input_file).st_size
        compressCommand = os.path.join(algorithms_path, algorithm['path'], algorithm['encode']).format( infile=input_file, outfile='compressed' )

        compress_time = countTime(compressCommand, 5)
        compressed_img_size = os.stat('compressed').st_size

        decompressCommand = os.path.join(algorithms_path, algorithm['path'], algorithm['decode']).format(infile='compressed', outfile='decompressed')
        decompressTime = countTime(decompressCommand, 5)

        currentImageName = str(imageDetails['path']).split('\\')[-1]
        algorithmName = str(algorithm['name']).encode('utf-8')

        if algorithmName not in log:
            log[algorithmName] = {
                "photo": {},
                "other": {}
            }
        
        photoType = ["other", "photo"][ imageDetails["photo"] ]

        log[algorithmName][photoType][currentImageName] = {
            "initialSize": initial_img_size, #bytes
            "compressTime": compress_time,
            "decompressTime": decompressTime,
            "compressedSize": compressed_img_size #bytes
        }

import xlwt
report = xlwt.Workbook()

for algorithmName, photoTypes in log.iteritems():
    currentSheet = report.add_sheet(algorithmName)
    for index_type, [photoTypeName, images] in enumerate( photoTypes.iteritems() ):
      for index_image, [imageName, imageDetails] in enumerate( images.iteritems() ):
          compressionLevel = float(imageDetails['compressedSize']) / float(imageDetails['initialSize'])
          compressTime = round(imageDetails['compressTime'], 5)
          decompressTime = round(imageDetails['decompressTime'], 5)
          currentSheet.write( (index_type + 1) * index_image, 0, imageName)
          currentSheet.write( (index_type + 1) * index_image, 1, compressTime)
          currentSheet.write( (index_type + 1) * index_image, 2, decompressTime)
          currentSheet.write( (index_type + 1) * index_image, 3, imageDetails['compressedSize'])
          currentSheet.write( (index_type + 1) * index_image, 4, imageDetails['initialSize'])
          currentSheet.write( (index_type + 1) * index_image, 5, compressionLevel)

report.save('output.xls')
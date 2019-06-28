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
        print( time.time() - start )
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

for algorithmName, photoTypes in log.items():
    row = 0
    lastTableIndex = 3
    currentSheet = report.add_sheet(algorithmName)
    for photoTypeName, images in photoTypes.items():
      currentSheet.write( row, 0, photoTypeName )
      row = row + 1
      currentSheet.write( row, 0, "Nazwa obrazu" )
      currentSheet.write( row, 1, "Czas kompresji [s]" )
      currentSheet.write( row, 2, "Czas dekompresji [s]" )
      currentSheet.write( row, 3, "Rozmiar przed kompresja [B]" )
      currentSheet.write( row, 4, "Rozmiar po kompresji [B]" )
      currentSheet.write( row, 5, "Poziom kompresji wartosci bazowej [%]" )
      row = row + 1
      for imageName, imageDetails in images.items():
          compressTime = round(imageDetails['compressTime'], 5)
          decompressTime = round(imageDetails['decompressTime'], 5)
          compressedSize = imageDetails['compressedSize']
          initialSize = imageDetails['initialSize']
          compressionLevel = ( float(compressedSize) / float(initialSize) ) * 100

          currentSheet.write( row, 0, imageName )
          currentSheet.write( row, 1, compressTime )
          currentSheet.write( row, 2, decompressTime )
          currentSheet.write( row, 3, initialSize )
          currentSheet.write( row, 4, compressedSize )
          currentSheet.write( row, 5, compressionLevel )
          row = row + 1
      currentSheet.write( row, 0, "Srednia: " )
      currentSheet.write( row, 1, xlwt.Formula("SUM(B{0}:B{1})/{2}".format(lastTableIndex, row, row - lastTableIndex + 1)) )
      currentSheet.write( row, 2, xlwt.Formula("SUM(C{0}:C{1})/{2}".format(lastTableIndex, row, row - lastTableIndex + 1)) )
      currentSheet.write( row, 3, xlwt.Formula("SUM(D{0}:D{1})/{2}".format(lastTableIndex, row, row - lastTableIndex + 1)) )
      currentSheet.write( row, 4, xlwt.Formula("SUM(E{0}:E{1})/{2}".format(lastTableIndex, row, row - lastTableIndex + 1)) )
      currentSheet.write( row, 5, xlwt.Formula("SUM(F{0}:F{1})/{2}".format(lastTableIndex, row, row - lastTableIndex + 1)) )
      row = row + 1
      lastTableIndex = row + 3

report.save('output2.xls')
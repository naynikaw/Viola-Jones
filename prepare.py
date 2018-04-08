# 
# prepare.py
#   Prepare data for boostedcascade.
# 
# Author : Donny
# 

import numpy as np
import scipy.misc

import os
import math

def transformToData(image, wndW, wndH, padX, padY):
    """Scan the image and get subimage of size = [wndW, wndH],
       padding of each subimage is [padX, padY].
    """
    h, w = image.shape
    data = []
    for y in range(0,h-wndH,padY):
        for x in range(0,w-wndW,padX):
            data.append(image[y:y+wndH, x:x+wndW])
    return data

def generateNonface(srcpath, destpath, imgsize, scanpad=(48,48)):
    """Generate non-face images in srcpath, and save to destpath.
    """
    if not isinstance(imgsize, tuple):
        raise ValueError("imgsize must be tuple")
    if not isinstance(scanpad, tuple):
        raise ValueError("scanpad must be tuple")

    for file_or_dir in os.listdir(srcpath):
        abs_srcpath = os.path.abspath(os.path.join(srcpath, file_or_dir))
        abs_destpath = os.path.abspath(os.path.join(destpath, file_or_dir))

        if os.path.isdir(abs_srcpath):
            os.makedirs(abs_destpath, exist_ok=True)
            generateNonface(abs_srcpath, abs_destpath, imgsize, scanpad)
        else:
            if file_or_dir.endswith('.jpg'):
                print('Processing non-face image %s' % file_or_dir)
                image = scipy.misc.imread(abs_srcpath, flatten=False, mode='F')
                outname, ext = os.path.splitext(abs_destpath)
                data = transformToData(image, imgsize[0], imgsize[1], scanpad[0], scanpad[1])
                for ind in range(len(data)):
                    scipy.misc.imsave(outname + '-' + str(ind) + ext, data[ind])

def generateFace(srcpath, destpath, listpath, verbose=False):
    """Generate face images in srcpath, described by listfiles in listpath,
       and save to destpath.
    """
    cnt_miss = 0
    faceind = 0
    for facelist in os.listdir(listpath):
        if facelist.endswith('-ellipseList.txt'):
            print('Processing facelist %s' % facelist)
            abs_facelist = os.path.abspath(os.path.join(listpath,facelist))
            with open(abs_facelist) as f:
                allline = f.readlines()
                allline = [l.rstrip('\n') for l in allline]
                il = 0
                while il < len(allline):
                    imgfilename = allline[il]; il+=1
                    if not imgfilename:
                        break

                    if verbose: print('Processing face image %s.jpg' % imgfilename)
                    try:
                        image = scipy.misc.imread(os.path.join(srcpath,imgfilename + '.jpg'), mode='F')
                    except FileNotFoundError:
                        if verbose: print('Face image %s not found.' % imgfilename)
                        cnt_miss += 1
                        facecnt = int(allline[il]); il+=1+facecnt
                        continue
                        
                    height, width = image.shape
                    imgpad = int(max(height, width)/2)
                    image = np.pad(image, [(imgpad,imgpad), (imgpad,imgpad)],
                        mode='constant', constant_values=0) # Pad image

                    facecnt = int(allline[il]); il+=1
                    for i in range(facecnt):
                        ellipse = allline[il]; il+=1
                        major_radius, minor_radius, angle, ctx, cty, acc = \
                            map(float, ellipse.split())
                        radian = angle*math.pi/180
                        
                        # May get some noise around, but it's fine.
                        # There is noise when detecting.
                        h = int(math.cos(radian)*major_radius*2 + pad)
                        w = int(math.cos(radian)*minor_radius*2 + pad)
                        if h < w: h = w
                        else: w = h
                        y = int(cty - h/2 + imgpad)
                        x = int(ctx - w/2 + imgpad)

                        try:
                            outimgname = os.path.basename(imgfilename) + '-' + str(faceind) + '.jpg'
                            scipy.misc.imsave(os.path.join(destpath, outimgname),
                                image[y:y+h, x:x+w])
                            if verbose: print('Face image %s generated.' % outimgname)
                        except Exception as expt:
                            print(expt)
                            print(x,y,w,h, ' ',width, height)

                        faceind += 1
    
    faceind += 1
    print('Faces generation done with %d faces generated and %d faces lost.' % (faceind, cnt_miss))
    return faceind, cnt_miss

def stretchFace(srcpath, destpath, imgsize, verbose=False):
    """Stretch faces to 
    """
    print('Stretching faces...')
    for ognface in os.listdir(srcpath):
        if ognface.endswith('.jpg'):
            if verbose: print('Stretching face image %s' % ognface)
            image = scipy.misc.imread(os.path.join(srcpath, ognface), mode='F')
            image = scipy.misc.imresize(image, size=imgsize, mode='F')
            scipy.misc.imsave(os.path.join(destpath, ognface), image)
    print('Face stretching done.')

if __name__ == '__main__':
    DetectWndW = 24
    DetectWndH = 24
    DetectPadX = 12
    DetectPadY = 12
    ScanPadX = 48
    ScanPadY = 48

    generateNonface('db/non-faces', 'data/non-faces',
                    imgsize=(DetectWndW, DetectWndH),
                    scanpad=(ScanPadX, ScanPadY))
    generateFace('db/faces', 'db/pure-faces', 'db/FDDB-folds')
    stretchFace('db/pure-faces', 'data/faces',
                imgsize=(DetectWndW, DetectWndH))
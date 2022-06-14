# -*- coding: utf-8 -*-
"""
Created on Fri Oct  8 16:47:54 2021

@author: Manchun LEI
LASTIG, Univ. Gustave Eiffel, ENSG, IGN, F-94160 Saint-Mandé, France
Package name:
    none
Module name:
    shadow_mask_rgb_nir
    ------------
    Un exemple d'utilisation de shadow_mask sur image RVB
    
    python .\shadow_mask_rgb.py input=\InputImage ext=jp2 bits=8 jump=2 sub=10 hsteq=False output=\OutputResults
    
    Args:
    - `input`= nom du répertoire d'entrée. Les images RVB sont stockés dans 
               le sous-répertoire `\RVB` et les images PIR sont stockés dans 
               le sous-répertoire `\PIR`
    - `threshold_input`= nom du répertoire d'entrée pour le seuillage global. 
                         Les images RVB sont stockés dans le sous-répertoire 
                         `\RVB` et les images PIR sont stockés dans le 
                         sous-répertoire `\PIR` . 
                         A défaut, `threshold_input=input` 
    - `ext_rgb` et `ext_nir` =  extension des images RVB et PIR, 
               Attention: les noms d'image RVB et PIR doivent être identiques 
               sauf leur extension, par exemple `nom-RVB.jp2`  
               dans le répertoire `\InputImage\RVB\` et `nom-PIR.jp2`  
               dans le répertoire `\InputImage\PIR\`. 
               Cela permet au programme de repérer le couple d'images RVB/PIR. 
               défaut=.*
    - `bits`= profondeur de couleur,  8 ou 16, défaut=8
    - `jump`= intervalle pour la création de list d'image pour le seuillage 
              global. Le seuillage global n'a pas besoin de lire toutes les 
              images, donner un intervalle>1 permet de gagner du temps. 
              Si `threshold_input` est donné, `jump` est forcé à 1.
              défaut=1
    - `sub`= un autre intervalle pour le seuillage global. Le seuillage global 
             n'a pas besoin de lire tous les pixels d'une image, donner un 
             intervalle> permet de gagner du temps. default=10 
    - `hsteq`= option pour le seuillage global. Certaines images en 16bits 
               brute ont une plage de dynamique restreinte, si `hsteq=True` 
               applique une equalisation histogramme sur la luminosité `I` 
               afin d'améliorer le résultat de seuillage d'histogramme. 
               défaut=False
    - `method`= option pour sélectionner la méthode de seuillage global. 
                Il dispose les options `nagao` et `tsai`, défaut=nagao
    - `output`= nom du répertoire de sortie

Modification:
    2020-11-09: save the mask image in tif format 
    2022-06-13: - change the way to define the src_path_rgb and src_path_nir, the
                problem of '\' or '/' between windows and linux system
                - fixe bug 
                - add masked_image option for saving the shadow masked 8bits image,
                  default is False
                - add th option for user defined threshold value [th_shadow, 
                  th_water,th_vegetation] for rgb+nir image
"""

import os
import glob
import numpy as np
import cv2
import time
import shadow_mask as sm
from osgeo import gdal

def global_thresholding(src_path,pref_rgb,pref_nir,ext_rgb,ext_nir,bits,jump,sub,hsteq,method): 
    print('-------------------------')
    print('global thresholding start.')
    start_thresholding = time.time()
    # modification M.LEI 2022-06-13
    src_path_rgb = os.path.join(src_path,'RGB')
    src_path_nir = os.path.join(src_path,'IR')
    # end modification M.LEI 2022-06-13
    pattern = os.path.join(src_path_rgb,pref_rgb+'*'+ext_rgb)
    flist_rgb = np.array([f.replace("\\","/") for f in glob.glob(pattern)]) 
    flist_rgb = flist_rgb[0::jump]
    if len(flist_rgb)==0:
        print('global thresholding failed, no image found')
        return None
    print(len(flist_rgb),'images used:')
    flist_nir = []
    for file_rgb in flist_rgb:
        name = file_rgb[len(src_path_rgb+pref_rgb)+1:-len(ext_rgb)]
        file_nir = os.path.join(src_path_nir,pref_nir+name+ext_nir)
        file_nir =file_nir.replace("\\","/") #unix-windows problem
        flist_nir.append(file_nir)
        print('rgb: '+file_rgb[len(src_path_rgb)+1:])
        print('nir: '+file_nir[len(src_path_nir)+1:])

    #create bgrn_list
    bgrn_list = []                   
    for j in range(len(flist_rgb)):
        bgr = cv2.imread(flist_rgb[j],cv2.IMREAD_UNCHANGED)
        nir = cv2.imread(flist_nir[j],cv2.IMREAD_UNCHANGED)
        bgr_sub = bgr[0::sub,0::sub,:]
        nir_sub = nir[0::sub,0::sub]
        ny,nx,nb = bgr_sub.shape        
        bgrn = np.empty([ny,nx,nb+1],dtype=bgr_sub.dtype) 
        bgrn[:,:,0:3] = bgr_sub
        bgrn[:,:,3] = nir_sub
        bgrn_list.append(bgrn)
    
    th = sm.global_thresholding_bgrn(bgrn_list,bits,method,hsteq=hsteq)
    end_thresholding = time.time()
    print('temps pour le thresholding :', end_thresholding - start_thresholding)
    print('global threshoding end.')
    print('threshold of [shadow, water, vegetation]')
    print(th)
    print('-------------------------')
    return th


def shadow_mask(src_path,pref_rgb,pref_nir,ext_rgb,ext_nir,bits,hsteq,method,th,dst_path,masked_image):
    print('---------------------------------')
    print('|rgb-nir image shadow mask start|')
    print('---------------------------------')
    start_mask = time.time()
    # modification M.LEI 2022-06-13
    src_path_rgb = os.path.join(src_path,'RGB')
    src_path_nir = os.path.join(src_path,'IR')
    # end modification M.LEI 2022-06-13
    
    pattern = os.path.join(src_path_rgb,pref_rgb+'*'+ext_rgb)
    flist_rgb = np.array([f.replace("\\","/") for f in glob.glob(pattern)]) 
    flist_nir = []
    for file_rgb in flist_rgb:
        name = file_rgb[len(src_path_rgb+pref_rgb)+1:-len(ext_rgb)]
        file_nir = os.path.join(src_path_nir,pref_nir+name+ext_nir)
        file_nir =file_nir.replace("\\","/") #unix-windows problem
        flist_nir.append(file_nir)
        
    for j in range(len(flist_rgb)):       
        bgr = cv2.imread(flist_rgb[j],cv2.IMREAD_UNCHANGED)
        nir = cv2.imread(flist_nir[j],cv2.IMREAD_UNCHANGED)
        ny,nx,nb = bgr.shape        
        bgrn = np.empty([ny,nx,nb+1],dtype=bgr.dtype) 
        bgrn[:,:,0:3] = bgr
        bgrn[:,:,3] = nir
        #call shadow_mask_bgrn
        mask = sm.shadow_mask_bgrn(bgrn,th,bits,method,hsteq=hsteq)        
        # #save result
        name = flist_rgb[j][len(src_path_rgb)+1:-len(ext_rgb)]        
        maskfile = os.path.join(dst_path,'mask_'+name+'.tif')
        cv2.imwrite(maskfile,((1-mask)*255).astype(np.uint8))
        #add georef from original image to mask 
        georef_src = gdal.Open(flist_rgb[j])
        georef_dst = gdal.OpenShared(maskfile,gdal.GA_Update)
        geo_tsf = georef_src.GetGeoTransform()
        geo_proj = georef_src.GetProjection()
        georef_dst.SetGeoTransform(geo_tsf)
        georef_dst.SetProjection(geo_proj)
        print(name+' shadow mask done')
        if(masked_image):
            #save bgr_8bits with mask
            if bits==8:
                bgr8 = bgr.copy()
            elif bits==16:
                bgr8 = sm.linear_stretch_16bits_to_8bits(bgr,vmin=0,vmax=0.98)
            else:
                print('bits must = 8 or 16!')
            #Superpose mask on the original image
            val = [0,0,255]
            for i in range(3):
                v = bgr8[:,:,i]
                v[mask==1] = val[i]
                bgr8[:,:,i] = v        
            imfile = os.path.join(dst_path,'masked_'+name+'.jpg')
            cv2.imwrite(imfile,bgr8)
            print(name+' shadow masked image done')
    end_mask = time.time()
    print('temps pour le mask :', end_mask - start_mask) 
    print('---------------------------')
    print('|rgb image shadow mask end|')
    print('---------------------------')



def main(**kwargs):
    '''
        Description
    args:
        Description
    returns:
        Description
    '''
    if 'input' in kwargs:
        src_path = kwargs['input']
    else:
        src_path = ''
    if 'pref_nir' in kwargs:
        pref_nir = kwargs.get('pref_nir')
    else:
        pref_nir = ''
    if 'pref_rgb' in kwargs:
        pref_rgb = kwargs.get('pref_rgb')
    else:
        pref_rgb = ''
    if 'ext_rgb' in kwargs:
        ext_rgb = kwargs.get('ext_rgb')
    else:
        ext_rgb = '.*'
    if 'ext_nir' in kwargs:
        ext_nir = kwargs.get('ext_nir')
    else:
        ext_nir = '.*'
    if 'bits' in kwargs:
        bits = int(kwargs.get('bits'))
    else:
        bits = 8
    if 'jump' in kwargs:
        jump = int(kwargs.get('jump'))
    else:
        jump = 1
    if 'sub' in kwargs:
        sub = int(kwargs.get('sub'))
    else:
        sub = 10
    if 'hsteq' in kwargs:
        hsteq = kwargs.get('hsteq')
        if hsteq == 'True':
            hsteq = True
        else:
            hsteq = False
    else:
        hsteq = False
    if 'method' in kwargs:
        method = kwargs.get('method')
    else:
        method = 'nagao'
    if 'output' in kwargs:
        dst_path = kwargs.get('output')
    else:
        dst_path = ''
    if 'threshold_input' in kwargs:
        th_path = kwargs['threshold_input']
        jump = 1
    else:
        th_path = src_path
    if 'masked_image' in kwargs:
        masked_image = kwargs.get('masked_image')
        if masked_image == 'True':
            masked_image = True
        else:
            masked_image = False
    else:
        masked_image = False
    if 'th' in kwargs:
        th = [float(v) for v in kwargs.get('th')[1:-1].split(',')]
        if len(th)!=3:
            print('th if a list of 3 parameters [th_shadow,th_wat,th_veg]')
            th = None
    else:
        th = None
    
    print('input image path = ',src_path)
    print('threshold image path = ',th_path)
    print('nir file prefix key = '+pref_nir)
    print('rgb file prefix key = '+pref_rgb)
    print('rgb file key and extension = '+ext_rgb)
    print('nir file key and extension = '+ext_nir)
    print('color deep = ',bits)
    print('jump = ',jump)
    print('sub = ',sub)
    print('hsteq = ',hsteq)
    print('method = ',method)
    print('output path =',dst_path)
    print('output masked image =',masked_image)
    if(th):
        print('user defined threshold of [shadow, water, vegetation] =',th)
    elif th_path !='':
        th = global_thresholding(th_path,pref_rgb,pref_nir,ext_rgb,ext_nir,bits,jump,sub,hsteq,method)
    if dst_path !='' and th:
        shadow_mask(src_path,pref_rgb,pref_nir,ext_rgb,ext_nir,bits,hsteq,method,th,dst_path,masked_image)

if __name__ == '__main__':
    main(**dict([arg.split('=') for arg in os.sys.argv[1:]]))

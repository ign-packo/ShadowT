# -*- coding: utf-8 -*-
"""
Created on Thu Jul 29 12:51:53 2021

@author: Manchun LEI
LASTIG, Univ. Gustave Eiffel, ENSG, IGN, F-94160 Saint-Mandé, France
Package name:
    none
Module name:
    shadow_mask_rgb
    ------------
    Un exemple d'utilisation de shadow_mask sur image RVB
    
    python .\shadow_mask_rgb.py input=\InputImage ext=jp2 bits=8 jump=2 sub=10 hsteq=False output=\OutputResults
    
    Args:
    - `input`= nom du répertoire d'entrée
    - `ext`=  extension des images dans le répertoire d'entrée, défaut=.*
    - `bits`= profondeur de couleur,  8 ou 16, défaut=8
    - `jump`= intervalle pour la création de list d'image pour le seuillage 
              global. Le seuillage global n'a pas besoin de lire toutes les 
              images, donner un intervalle>1 permet de gagner du temps. 
              défaut=1
    - `sub`= un autre intervalle pour le seuillage global. Le seuillage global 
             n'a pas besoin de lire tous les pixels d'une image, donner un 
             intervalle> permet de gagner du temps. default=10 
    - `hsteq`= option pour le seuillage global. Certaines images en 16bits 
               brute ont une plage de dynamique restreinte, si `hsteq=True` 
               applique une equalisation histogramme sur la luminosité `I` 
               afin d'améliorer le résultat de seuillage d'histogramme. 
               défaut=False
    - `output`= nom du répertoire de sortie
        

"""

import os
import glob
import numpy as np
import cv2
import shadow_mask as sm
       

def global_thresholding(src_path,ext,bits,jump,sub,hsteq): 
    print('-------------------------')
    print('global thresholding start.')
    pattern = os.path.join(src_path,'*'+ext)
    flist = np.array([f.replace("\\","/") for f in glob.glob(pattern)])    
    flist = flist[0::jump]
    print(len(flist),'images used:')
    for file in flist:     
        print(file[len(src_path)+1:])
    # create bgr_list
    bgr_list = []
    for j in range(len(flist)):
        bgr = cv2.imread(flist[j],cv2.IMREAD_UNCHANGED)
        bgr_sub = bgr[0::sub,0::sub,:]
        bgr_list.append(bgr_sub)
    
    th = sm.global_thresholding_bgr(bgr_list,bits,hsteq=hsteq)
    print('global threshoding end. th =',th)
    print('----------------------------')
    return th

def shadow_mask(src_path,ext,bits,hsteq,th,dst_path):
    print('-----------------------------')
    print('|rgb image shadow mask start|')
    print('-----------------------------')
    pattern = os.path.join(src_path,'*'+ext)
    flist = np.array([f.replace("\\","/") for f in glob.glob(pattern)])
    for j in range(len(flist)):
        bgr = cv2.imread(flist[j],cv2.IMREAD_UNCHANGED)
        #call shadow_mask_bgr
        mask = sm.shadow_mask_bgr(bgr, th, bits,hsteq=hsteq)
        #save result
        name = flist[j][len(src_path)+1:-len(ext)-1]        
        maskfile = os.path.join(dst_path,'mask_'+name+'.jpg')
        cv2.imwrite(maskfile,((1-mask)*255).astype(np.uint8))
        print(name+' done')                
        #save bgr_8bits with mask
        if bits==8:
            bgr8 = bgr.copy()
        elif bits==16:
            bgr8 = sm.linear_stretch_16bits_to_8bits(bgr,vmin=0,vmax=0.98)
        else:
            print('bits must = 8 or 16!')
            
        val = [0,0,255]
        for i in range(3):
            v = bgr8[:,:,i]
            v[mask==1] = val[i]
            bgr8[:,:,i] = v        
        imfile = os.path.join(dst_path,'masked_'+name+'.jpg')
        cv2.imwrite(imfile,bgr8)
    print('--------------------------')
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
    if 'ext' in kwargs:
        ext = kwargs.get('ext')
    else:
        ext = '.*'
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
        hsteq = bool(kwargs.get('hsteq'))
    else:
        hsteq = False
    if 'output' in kwargs:
        dst_path = kwargs.get('output')
    else:
        dst_path = ''
    
    print('input image path = ',src_path)
    print('file extension = '+ext)
    print('color deep = ',bits)
    print('jump = ',jump)
    print('sub = ',sub)
    print('hsteq = ',hsteq)
    print('output path=',dst_path)
    if src_path !='':
        th = global_thresholding(src_path,ext,bits,jump,sub,hsteq)
        if dst_path !='':
            shadow_mask(src_path,ext,bits,hsteq,th,dst_path)
        
    
    
if __name__ == '__main__':
    main(**dict([arg.split('=') for arg in os.sys.argv[1:]]))

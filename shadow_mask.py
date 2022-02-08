# -*- coding: utf-8 -*-
"""
Created on Thu Jul 29 12:51:53 2021

@author: Manchun LEI
LASTIG, Univ. Gustave Eiffel, ENSG, IGN, F-94160 Saint-Mandé, France

Package name:
    none
Module name:
    shadow_mask
    ------------
    Création de masque d'ombre pour des images aériennes.
    L'image doit être au moin en couleur 3 canaux RVB, une bande en 
    proche-infrage (PIR) de plus serait encore mieux.    
    La profondeur de couleur des images peut être 16bits ou 8 bits.
           
    Les fonctions utiles sont:
        global_thresholding_bgr: seuillage global avec méthode Tsai06 (RVB)
        global_thresholding_nagao: seuillage global avec méthode Nagao79 (RVB+PIR)
        shadow_mask_bgr: creation de masque d'ombre avec la méthode Tsai06
        shadow_mask_nagao: creation de masque d'ombre avec la méthode Nagao79
        water_detection: seuillage global avec ndwi pour la detection des eaux
        vegetaiton_detection: seuillage global avec ndvi pour la détection 
                              des végétations
        global_thresholding_bgrn: processus pour le seuillage global RVB+PIR
        shadow_mask_bgrn: processus pour la masque d'ombre RVB+PIR
        
        
        hsi_ratio: calculer le rapport (H+1)/(I+1)
        nagao: calculer la luminosité pondérée d'image RVB-PIR
        hist_uniform: histogramme uniform
        hist_eq: histogramme egalisation
        hist_valleys: les indices des vallée dans la courbe d'histogramme
        otsu_threshoding: seuillage Otsu
        linear_stretch_16bits_to_8bits: transformation 16bits en 8 bits par 
                     l'etirement lineaire
        ndwi: indice d'eau
        ndvi: indice de végétation
    
    modification 2022-02-07: 
        correction of ndvi() and ndwi()
        detection and correction of zero value pixels, NaN problem
    modification 2022-02-08:
        correction of global_thresholding_nagao()
        change step value for histogram of 16bits Nagao image.
        Some 16bits image show a discontinuity in Nagao histogram, perhapes due
        to pre-precessing like histogram equalization. Increasing the step value
        improves the continuity of Nagao histogram.

"""

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks


_PMAX16 = 65000 #pixel value considered as max of 16 bits raw, to avoid invalid pixel
_PMAX8 = 255 #pixel value considered as max of 8 bits

def hsi_ratio(bgr,bits,hsteq=False):
    '''
    hsteq is an option for some raw 16bits images without pre-processing,
    because these images could have a very tight light intensity histogram.
    In this case, hist_eq allows stretching the inensity distribution for a
    good thresholding.
    -------------------
    args:
        bgr: image array [blue, green, red], 8bits or 16bits
        bits: =8 for 8bits image, =16 for 16bits image
        hsteq: =False, no histogrqm equalization by default
    output:
        R = (H+1)/(I'+1) ratio
        H: hue 
        I': is light intensity after normalization if hsteq==False
            is light intensity after hisotram equalization if hsteq==True
        
    '''
    if bits==8:
        PMAX = _PMAX8
    elif bits==16:
        PMAX = _PMAX16
    else:
        print('color depth must be 8 or 16!')
        
    b = bgr[:,:,0].astype(float)
    g = bgr[:,:,1].astype(float)
    r = bgr[:,:,2].astype(float)
    
    I = (b/3 + g/3 + r/3)
    
    f1 = [-1*np.sqrt(6)/6,-1*np.sqrt(6)/6, np.sqrt(6)/3]
    V1 = f1[0]*r+f1[1]*g+f1[2]*b
    
    f2 = [1/np.sqrt(6),-2/np.sqrt(6),0]
    V2 = f2[0]*r+f2[1]*g+f2[2]*b
    
    H = np.arctan2(V2,V1)
    H = np.degrees(H)
    H[H<0] = 360+H[H<0]
    
    if hsteq==False:
        In = I/PMAX
        R = (H+1)/(In+1)
    else:    
        Ieq = hist_eq(I,[0,PMAX])
        R = (H+1)/(Ieq+1)
    
    return R


def nagao(bgrn):
    '''NAGAO79, weighted light indensity 
    args:
        bgrn: image array [b,g,r,nir]
    returns
        nagao array

    '''
    return (bgrn[:,:,0].astype(float)+bgrn[:,:,1].astype(float)+\
            2*bgrn[:,:,2].astype(float)+2*bgrn[:,:,3].astype(float))/6
                        
def hist_uniform(v,bins_range,step=1):
    '''histogram with uniform bins values
    args:
        v: data array 
        bins_range: [min,max] range of bins
        step: bins step, default=1
    return:
        x: bins center
        hist: histogram
    '''
    bins = np.arange(bins_range[0],bins_range[1]+step,step)
    hist,bin_edges = np.histogram(v,bins=bins)
    x = (bin_edges[0:-1]+bin_edges[1:])/2
    return x,hist


def hist_eq(i,bins_range):
    '''histogram equalization
    args:
        i: input 2d array
    return:
        o: result
    '''
    v = i.copy()
    x,hist = hist_uniform(v,bins_range)            
    hist_norm = hist.ravel()/hist.sum()
    hist_cum = hist_norm.cumsum()        
    vmin1 = x[0]
    vmax1 = x[-1]
    v[v>vmax1] = vmax1
    v[v<vmin1] = vmin1    
    #convert data value to bins index
    idx = ((len(x)-1)*(v-vmin1)/(vmax1-vmin1)).astype(int)        
    v1 = hist_cum[idx]
    vmin = hist_cum[0]
    vmax = hist_cum[-1]
    o = (v1-vmin)/(vmax-vmin)  
        
    return o

def linear_stretch_16bits_to_8bits(bgr,vmin=0.0,vmax=0.98):
    '''convert 16bits raw image to 8 bits by linear stretch
    args:
        bgr: bgr image array
        vmin: min value of hist_cum >=0
        vmax: max value of hist_cum <=1, vmax must > vmin
    return:
        bgr_8bits
    '''
    bgr_8bits = np.empty(bgr.shape,dtype=np.uint8)
    for i in range(3):
        v = bgr[:,:,i].astype(np.float)       
        x,hist = hist_uniform(v,[0,_PMAX16])            
        hist_norm = hist.ravel()/hist.sum()
        hist_cum = hist_norm.cumsum()
        vmin1 = x[hist_cum>=vmin][0]
        vmax1 = x[hist_cum<=vmax][-1] 
        v[v>vmax1] = vmax1
        v[v<vmin1] = vmin1
        v = (v-vmin1)/(vmax1-vmin1)
        bgr_8bits[:,:,i] = v*255 
    
    return bgr_8bits


def otsu_thresholding(hist,bins):
    '''find the thresholding value index in bins from histogram
       by Otsu method. Copy from opencv doc
    -----------------
    args:
       hist: histogram
       bins: bin value
    returns:
        ith: the index of threshold, th = bins[ith]
    '''
    hist_norm = hist.ravel()/hist.sum()
    Q = hist_norm.cumsum()
    nb = len(bins)
    fn_min = np.inf
    ith = -1
    for i in range(1,nb):
        p1,p2 = np.hsplit(hist_norm,[i]) # probabilities
        q1,q2 = Q[i],Q[nb-1]-Q[i] # cum sum of classes
        if q1 < 1.e-6 or q2 < 1.e-6:
            continue
        b1,b2 = np.hsplit(bins,[i]) # weights
        # finding means and variances
        m1,m2 = np.sum(p1*b1)/q1, np.sum(p2*b2)/q2
        v1,v2 = np.sum(((b1-m1)**2)*p1)/q1,np.sum(((b2-m2)**2)*p2)/q2
        # calculates the minimization function
        fn = v1*q1 + v2*q2
        if fn < fn_min:
            fn_min = fn
            ith = i    
    
    return int(ith)

def global_thresholding_bgr(bgr_list,bits,hsteq=False):
    '''
    global thresholding for a set of bgr images, tsai06 method
    ---------------
    args:
        bgr_list: list of image bgr array 
        bits: color depth, 8 or 16
        hsteq: option, must use the same option for shadow_mask 
    return:
        th: Otsu threshod of (H+1)/(Ieq+1) ratio
    Note:
        The input bgr image could be sub-sampled to reduce the image size
    '''   
    R = []
    for bgr in bgr_list: 
        #tsai h-i ratio
        r = hsi_ratio(bgr,bits,hsteq=hsteq)
        R.append(r.flatten())
         
    R1 = [x for sub in R for x in sub]
    R = np.array(R1)   
    #otsu thresholding
    x,hist = hist_uniform(R,[0,360])
    ith = otsu_thresholding(hist, x)
    th = x[ith]       
    return th 
    

def shadow_mask_bgr(bgr,th_hi_ratio,bits,hsteq=False):
    '''shadow mask for only bgr image
    args:
        bgr: bgr 8 bits or 16bits image array
        th_hi_ratio: threshold of (h+1)/(i+1) ratio
        bits: color depth, 8 or 16
        hsteq: option, use the same option as global_thresholding
    return:
        mask: shadow mask
    '''
        
    R = hsi_ratio(bgr,bits,hsteq=hsteq)
    mask = R>th_hi_ratio
    return mask


def ndvi(bgrn):
    '''
    ndvi calculation, ndvi = (n-r)/(n+r)
    Args:
        bgrn - bgrn image array
    Returns:
        ndvi
    modification 2022-02-07
        detection and correction of zero value pixel
    '''
    r = bgrn[:,:,2].astype(float)
    n = bgrn[:,:,3].astype(float)
    t = n+r
    t[t<1] = 1
    return (n-r)/t

def ndwi(bgrn):
    '''
    ndwi calculation, ndwi = (g-n)/(g+n)
    Args:
        bgrn - bgrn image array
    Returns:
        ndwi
    modification 2022-02-07
        detection and correction of zero value pixel
    '''
    g = bgrn[:,:,1].astype(float)
    n = bgrn[:,:,3].astype(float)
    t = g+n
    t[t<1] = 1
    return (g-n)/t


def hist_valleys(hist):
    '''
    detect valleys of histogram curve
    ---------------------
    args: 
        hist: histogram curve 1d array
    return:
        [ith_first,ith_last]: the bins index of the valleys  
    '''
    #firt valley    
    peaks, _ = find_peaks(hist) 
    hist_inv = np.max(hist)-hist
    valleys,_ = find_peaks(hist_inv)
    
    valleys = valleys[valleys>peaks[0]]
    return valleys    
    
def global_thresholding_nagao(bgrn_list,bits):
    '''
    global thresholding from a set of bgrn images, nagao79 method for
    weighted light indensity shresholding.
    args:
        bgrn_list: list of bgrn images, band order is [blue,green,red,nir]
    returns:
        th_nagao: shadow thresholdng from bgrn image
    modification 2022-02-08
        change step value for 16bits image.
    ''' 
    if bits==8:
        PMAX = _PMAX8
        step = 1
    elif bits==16:
        PMAX = _PMAX16
        step = PMAX/1000
    else:
        print('color depth must be 8 or 16!')
    
    NG = []
    for bgrn in bgrn_list:
        ng_map = nagao(bgrn)
        NG.append(ng_map.flatten())
            
    NG1 = [x for sub in NG for x in sub]
    NG = np.array(NG1)      
    #first valley thresoding for NG   
    x,hist = hist_uniform(NG,[0,PMAX],step=step)
    #smooth hist curve
    hist = gaussian_filter1d(hist, 10, mode='nearest')
    #firt valley    
    valleys = hist_valleys(hist)
    ith_first = valleys[0]
    th_nagao = x[ith_first]    
    return th_nagao
    
def water_detection(bgrn_list):
    NDWI = []
    for bgrn in bgrn_list:
        ndwi_map = ndwi(bgrn)
        NDWI.append(ndwi_map.flatten())            
    NDWI1 = [x for sub in NDWI for x in sub]
    NDWI = np.array(NDWI1)       
    #histogram of NDWI
    vmin = np.min(NDWI)
    vmax = np.max(NDWI)   
    step = (vmax-vmin)/1000  
    x,hist = hist_uniform(NDWI,[vmin,vmax],step=step) 
    #smooth hist curve      
    hist = gaussian_filter1d(hist, 6, mode='nearest')
    #last valley  
    valleys = hist_valleys(hist)
    ith_last = valleys[-1]
    th_ndwi = x[ith_last]
    return th_ndwi


def vegetation_detection(bgrn_list):
    NDVI = []
    for bgrn in bgrn_list:
        ndvi_map = ndvi(bgrn)
        NDVI.append(ndvi_map)            
    NDVI1 = [x for sub in NDVI for x in sub]
    NDVI = np.array(NDVI1)
    #histogram of NDVI
    vmin = np.min(NDVI)
    vmax = np.max(NDVI)   
    step = (vmax-vmin)/1000  
    x,hist = hist_uniform(NDVI,[vmin,vmax],step=step)
    #smooth hist curve
    hist = gaussian_filter1d(hist, 6, mode='nearest')   
    #last valley  
    valleys = hist_valleys(hist)
    ith_last = valleys[-1]
    th_ndvi = x[ith_last]
    return th_ndvi

def shadow_mask_nagao(bgrn,th_nagao):
    '''shadow mask for bgrn image using nagao79 shreshodlding
    args:
        bgr: bgr 8 bits or 16bits image array
        th_nagao: threshold of nagao map
    return:
        mask: shadow mask, mask = nagao<th_nagao
    '''        
    ng_map = nagao(bgrn)
    mask = ng_map<th_nagao
    return mask


def global_thresholding_bgrn(bgrn_list,bits,method,hsteq=False):
    '''
    global thresholding from a set of bgrn images,
    args:
        bgrn_list: list of bgrn images, band order is [blue,green,red,nir]
        bits: int, 8 for 8bits and 16 for 16bits
        method:
            'tsai':   tsai06 method
            'nagao': nagao79 method
        hsteq: boolean, option for tsai method 
    returns:
        th = [th1,th_wat,th_veg]
        th1: shadow thresholdng from selected method
        th_wat: first valley of ndvi histogram for water detection 
        th_veg: last valley of ndvi histogram for vegetation detection
    ''' 
    if method=='tsai':
        bgr_list = []
        for bgrn in bgrn_list:
            bgr_list.append(bgrn[:,:,0:3])
        th1 = global_thresholding_bgr(bgr_list,bits,hsteq=hsteq)
    elif method=='nagao':
        th1 = global_thresholding_nagao(bgrn_list,bits)
    else:
        print("The available methods are:'bgr','nagao'")

    th_wat = water_detection(bgrn_list)
    th_veg = vegetation_detection(bgrn_list)
    return [th1,th_wat,th_veg]

def shadow_mask_bgrn(bgrn,th,bits,method,hsteq=False):
    '''shadow mask for bgrn [b,g,r,nir] image
    
    Args:
        bgrn (TYPE): bgrn 8bits or 16bits image array
        th (TYPE): []
        bits (TYPE): DESCRIPTION.

    Returns:
        mask: shadow mask
    '''
    if method=='tsai':
        bgr = bgrn[:,:,0:3]
        mask1 = shadow_mask_bgr(bgr,th[0],bits,hsteq)
    elif method=='nagao':
        mask1 = shadow_mask_nagao(bgrn,th[0])
    else:
        print("The available methods are:'bgr','nagao'")
        return None
    
    ndwi_map = ndwi(bgrn)    
    ndvi_map = ndvi(bgrn)
    mask_wat = ndwi_map>th[1]
    mask_veg = ndvi_map>th[2]
    #final shadow mask
    mask = mask1*(1-mask_wat)*(1-mask_veg)
    return mask


def main():
    '''
        Description
    args:
        Description
    returns:
        Description
    '''
    print("welcome to shadow mask")


    
if __name__ == '__main__':
    main()

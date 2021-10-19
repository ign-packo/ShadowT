"""
Created on Friday October 08 2021
@author: Yoann Apel 
"""

# This script compares differences on two different shadow masks

import os
import cv2
import numpy as np


### Read the two images masks to compare
def read_images(src_path_ref,src_path_test):
    mask_ref = cv2.imread(src_path_ref, 0) # Reference Mask, obtained with manual selection
    mask_test = cv2.imread(src_path_test, 0) # The mask to test with the reference mask
    return mask_ref, mask_test

### Dimensions of the image masks
def dimensions(mask_ref,mask_test):
    height_ref = mask_ref.shape[0]
    width_ref = mask_ref.shape[1]
    total_pixels_ref = width_ref * height_ref
    height_test = mask_test.shape[0]
    width_test = mask_test.shape[1]
    total_pixels_test = width_test * height_test
    return total_pixels_ref, total_pixels_test

### intialization of statistics
def statistics_calculation(mask_ref,mask_test):
    P = np.sum(mask_ref==0)          #ref positive numbers (shadow)
    N = np.sum(mask_ref==255)       #ref negative numbers (not shadow)
    PP = np.sum(mask_test==0)                                    #pred positive numbers
    PN = np.sum(mask_test==255)                                  #pred negative numbers
    TP = np.sum(np.logical_and(mask_ref==0,mask_test==0))        # Shadow for reference and test mask (true positive)
    TN = np.sum(np.logical_and(mask_ref==255,mask_test==255))    # Not shadow for reference and test mask (true negative
    FP = np.sum(np.logical_and(mask_ref==255,mask_test==0))      # Not shadow for reference and shadow for test mask (false positive)
    FN = np.sum(np.logical_and(mask_ref==0,mask_test==255))      # Shadow for reference and not shadow for test mask (false negative)
    return P, N, PP, PN, TP, TN, FP, FN

### Ratios calculation
def ratios(TP,TN,P,N):
    ACCP = TP/P
    ACCN = TN/N
    TPR = TP/P
    FNR = 1-TPR
    return ACCP, ACCN, FNR

if __name__ == '__main__':
    # Give the path and read images
    src_path_ref = os.sys.argv[1]
    src_path_test = os.sys.argv[2]
    mask_ref, mask_test=read_images(src_path_ref,src_path_test)

    total_pixels_ref, total_pixels_test = dimensions(mask_ref,mask_test)
    if total_pixels_ref == total_pixels_test : # Test if masks can be compared
    
        # Statistics calculation and display
        P, N, PP, PN, TP, TN,FP,FN = statistics_calculation(mask_ref, mask_test)
        print('PIXEL NUMBERS :  \nReference Positive pixels :', P,'\nReference Negative pixels :', N,'\nPrediction Positive pixels :', PP,'\nPrediction Negative pixels :' ,PN)
        print('True Positive pixels : ', TP, '\nFalse Positive pixels :', FP, '\nTrue Negative pixels :', TN, '\nFalse Negative pixels :', FN)
        print('well predicted numbers: True Positive + True Negative =',TP+TN)

        # Ratios calculation and display
        ACCP, ACCN, FNR = ratios(TP,TN,P,N)
        print('PERCENTAGES :')
        print('accuracy positive, ACCP = '+'{:<5.3f}%'.format(ACCP*100))
        print('accuracy negative, ACCN = '+'{:<5.3f}%'.format(ACCN*100))
        print('miss rate, FNR = '+'{:<5.3f}%'.format(FNR*100))
    
    # If it's not the same dimension, masks can't be compared
    else:
        print('Error, not the same dimension for the masks')

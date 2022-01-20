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
    shadow_mref = np.sum(mask_ref==0)                                        #pixel in shadow for the reference mask
    noshadow_mref = np.sum(mask_ref==255)                                    #pixel not in shadow for the reference mask
    shadow_mtest = np.sum(mask_test==0)                                      #pixel in shadow for the test mask
    noshadow_mtest = np.sum(mask_test==255)                                  #pixel not in shadow for the test mask
    true_shadow = np.sum(np.logical_and(mask_ref==0,mask_test==0))           #pixel in shadow for reference and test mask
    true_noshadow = np.sum(np.logical_and(mask_ref==255,mask_test==255))     #pixel not in shadow for reference and test mask 
    false_shadow = np.sum(np.logical_and(mask_ref==255,mask_test==0))        #pixel not in shadow for reference and shadow for test mask 
    false_noshadow = np.sum(np.logical_and(mask_ref==0,mask_test==255))      #pixel in shadow for reference and not shadow for test mask
    return shadow_mref, noshadow_mref, shadow_mtest, noshadow_mtest, true_shadow, true_noshadow, false_shadow, false_noshadow

### Ratios calculation
def ratios(true_shadow,true_noshadow,shadow_mref,noshadow_mref):
    accuracy_shadow = true_shadow/shadow_mref
    accuracy_noshadow = true_noshadow/noshadow_mref
    true_shadow_rate = true_shadow/shadow_mref
    miss_rate = 1-true_shadow_rate
    return accuracy_shadow, accuracy_noshadow, miss_rate

if __name__ == '__main__':
    # Give the path and read images
    src_path_ref = os.sys.argv[1]
    src_path_test = os.sys.argv[2]
    mask_ref, mask_test=read_images(src_path_ref,src_path_test)

    total_pixels_ref, total_pixels_test = dimensions(mask_ref,mask_test)
    if total_pixels_ref == total_pixels_test : # Test if masks can be compared
    
        shadow_mref, noshadow_mref, shadow_mtest, noshadow_mtest, true_shadow, true_noshadow, false_shadow, false_noshadow = statistics_calculation(mask_ref, mask_test)
        if (shadow_mref + noshadow_mref) != total_pixels_ref : # Test if the sum of shadow pixels and no shadow pixels is equal to the total of pixels
            print('The reference mask is composed of more than 2 values')
        elif shadow_mtest + noshadow_mtest != total_pixels_test :
            print('The test mask is composed of more than 2 values')
        else :
            # Statistics calculation and display
            print('PIXEL NUMBERS :  \nReference shadow pixels :', shadow_mref,'\nReference no shadow pixels :', noshadow_mref,'\nPrediction shadow pixels :', shadow_mtest,'\nPrediction no shadow pixels :' ,noshadow_mtest)
            print('True shadow pixels : ', true_shadow, '\nFalse shadow pixels :', false_shadow, '\nTrue no shadow pixels :', true_noshadow, '\nFalse shadow pixels :', false_noshadow)
            print('well predicted numbers: True shadow + True no shadow =',true_shadow+true_noshadow)

            # Ratios calculation and display
            accuracy_shadow, accuracy_noshadow, miss_rate = ratios(true_shadow,true_noshadow,shadow_mref,noshadow_mref)
            print('PERCENTAGES :')
            print('accuracy shadow = '+'{:<5.3f}%'.format(accuracy_shadow*100))
            print('accuracy no shadow = '+'{:<5.3f}%'.format(accuracy_noshadow*100))
            print('miss rate = '+'{:<5.3f}%'.format(miss_rate*100))
    
    # If it's not the same dimension, masks can't be compared
    else:
        print('Error, not the same dimension for the masks')

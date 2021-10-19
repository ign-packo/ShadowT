"""
Created on Friday October 08 2021
@author: Yoann Apel 
"""

# This script will compare differences on two differents shadow mask

import cv2

### Read the two images masks to compare
img_ref = cv2.imread('ReferenceMaskLake.png', 0) # Reference Mask, obtained with manual selection
img_test = cv2.imread('TestMask.png', 0) # The mask to test with the reference mask

### Dimensions of the image mask
height = img_ref.shape[0]
width = img_ref.shape[1]
total_pixels = width * height

### Counters of pixels
pixel_accurate = 0 # Same value for this pixel, on the shadow mask of reference and the shadow mask tested 
over_detection = 0 # For this pixel, There is a shadow detection on the tested mask and not on the reference mask 
under_detection = 0 # For this pixel, There is a shadow detection on the reference mask and not on the tested mask

### Accuracy of shadow detection calculation
for i in range (img_ref.shape[0]):
   for j in range (img_ref.shape[1]):
       if img_ref[i,j] == img_test[i,j]: # Same classification (shadow/not Shadow) between reference and tested mask for the pixel [i,j]
           pixel_accurate = pixel_accurate + 1
       elif img_test[i,j] == 255 : # Not the same classification (test mask == not shadow) and (reference mask == shadow) for the pixel [i,j]
             under_detection = under_detection + 1
       else : over_detection = over_detection + 1 # Not the same classification (test mask == shadow) and (reference mask == not shadow) for the pixel [i,j]

### Percentage of accuracy
pixel_accuracy_percentage = (pixel_accurate/total_pixels) * 100
over_detection_percentage = (over_detection/total_pixels) * 100
under_detection_percentage = (under_detection/total_pixels) * 100

# Display results
print ('Number of correct pixels :', pixel_accurate , 'out of ', total_pixels, ' of the image so', pixel_accuracy_percentage, '%')
print ('Number of under detected pixels:', under_detection, 'out of ', total_pixels, ' of the image so', under_detection_percentage, '%')
print ('Number of over detected pixels :', over_detection, 'out of ', total_pixels, ' of the image so', over_detection_percentage, '%')
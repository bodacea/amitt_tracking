''' Clustering received images

We'd like to see clusters in the images we download from e.g. Twitter.  We often get similar (but not quite the same) images - either because the images have been rezised, or they have text that's been chanced, they've been cropped etc.  

What would be good is to be able to cluster together the images that are *functionally* the same - e.g. they look the same to a human - so we can treat them as the same object when we look for how a narrative originates etc.  

We'd also like to see when an image diverges e.g. when text changes, or when new image types are made from an original one.  We expect these too to form clusters. 

There is plenty of work already on image understanding and clustering, e.g. 

clustering: https://learning.oreilly.com/library/view/programming-computer-vision/9781449341916/ch06.html
clustering through the 'objects' in the images: Amazon Rekognition
poor-man's clustering: use the filesizes to sort the images, and move quickly through the identical ones. 

But it would be good to have a way to move around a graph of image similarities, and see which are close, and which are distinct from each other.  THat would save us scrolling through 100s of images every time

'''

import imtools
from scipy.cluster.vq import *
import glob


# imlist = imtools.get_imlist('twitter_scraper_code/stopmandatoryvaccination/')
files = glob.glob('twitter_scraper_code/stopmandatoryvaccination/images/*.*')
files

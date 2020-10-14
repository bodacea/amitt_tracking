#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Run google search that doesn't care about repeated results to get list of sites associated with an input phrase.

'''

from googlesearch import search 
import pandas as pd
import re
from datetime import datetime
import os
import sys


#Make sure there's somewhere to put the data
if not os.path.exists('../data/googles'):
    os.makedirs('../data/googles')


def widegoogle(qterm, qsite=''):
	#query = '"{}" site:.com/terms'.format(qterm)
	query = '"{}" {}'.format(qterm, qsite)
	  
	js = [j for j in search(query, tld="com", num=1000, stop=None, pause=2.0,
	                        extra_params={'filter': '0'})]

	newsites = [re.findall('//(.*)/', x)[0] for x in js]
	df = pd.DataFrame(newsites, columns=['url']).sort_values('url')
	df.to_csv('../data/googles/googlesearch_{}.csv'.format(datetime.now().strftime('%Y-%m-%d-%H-%M')),
	          index=False)
	return df

if __name__ == '__main__':
 
    # Check that search terms were provided at the command line
    if (len(sys.argv) > 1):
        qterm = ' '.join(sys.argv[1:])
        df = widegoogle(qterm)
        print('{}'.format(df))
    else:
        print("No search terms provided. Exiting.")
        sys.exit(0)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import sys
import json
from snowflake import *
import glob


def get_timestamp(snowflake_id):
    timestamp, data_center, worker, sequence = melt(int(snowflake_id))
    # print('the tweet was created at {}'.format(local_datetime(timestamp)))
    return timestamp

def read_json(filename):
    with open(filename, "r", encoding="utf-8") as f:
          return json.loads(f.read())


def tweet_json_to_csv(jsonfile):
    ''' Get tweet data and grab basic timing data out of it'''
    
    tweetjson = read_json(jsonfile)
    print('{} has {} tweets'.format(jsonfile, len(tweetjson)))
    dftweets = pd.DataFrame(tweetjson, index=[0]).transpose().reset_index()
    dftweets.rename(index=str, columns={'index': 'tweet_url', 0: 'text'}, inplace=True)
    dftweets['user'] = dftweets['tweet_url'].str.split('/').str[3]
    dftweets['tweet_id'] = dftweets['tweet_url'].str.split('/').str[5]
    dftweets['timestamp'] = dftweets['tweet_id'].apply(get_timestamp)
    dftweets['datetime'] = pd.to_datetime(dftweets['timestamp'],unit='ms')
    dftweets['date'] = dftweets['datetime'].dt.date
    dftweets['hour'] = dftweets['datetime'].dt.hour
    dftweets['ymdh'] = dftweets['datetime'].dt.year*1000000 + dftweets['datetime'].dt.month*10000 + dftweets['datetime'].dt.day*100 +dftweets['datetime'].dt.hour
    
    csvfile = jsonfile[:jsonfile.rfind('.')] + '.csv'
    dftweets.to_csv(csvfile, index=False)

    return dftweets


def clean_datasets(targetdir):

    jsonfiles = glob.glob(targetdir + '/*tweets.json')
    if len(jsonfiles) > 0:
        csvfiles = glob.glob(targetdir + '/*tweets.csv')
    else:
        jsonfiles = glob.glob(targetdir + '/*/*tweets.json')
        csvfiles = glob.glob(targetdir + '/*/*tweets.csv')

    for jsonfile in jsonfiles:
        csvfile = jsonfile[:jsonfile.rfind('.')] + '.csv'
        if csvfile not in csvfiles:
            tweet_json_to_csv(jsonfile)

    return


# Main starts here
if __name__ == '__main__':

    # Check that search terms were provided at the command line
    if (len(sys.argv) <= 1):
        print("No search terms provided. Exiting.")
        sys.exit(0)


    # other arguments are the search terms
    target_list = sys.argv[1:] 
    num_targets = len(target_list)

    for count, targetdir in enumerate(target_list):

        print('{}/{} cleaning data in directory: {}'.format(count+1, num_targets, targetdir))
        clean_datasets(targetdir)


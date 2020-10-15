#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import Counter
from itertools import combinations
from twarc import Twarc
from datetime import datetime
import pandas as pd
import requests
import sys
import os
import shutil
import io
import re
import json

class TwitterRelationships():
# Cut-down code to get twitter relationships for a set of hashtags. 
# Adapted from https://labsblog.f-secure.com/2018/02/16/searching-twitter-with-twarc/

    def __init__(self, secretsfile='/Users/sara/twittersecrets.txt'):
 
        fsecret = open(secretsfile, 'r')
        secrets = fsecret.readline()
        access_token, access_token_secret, consumer_key, consumer_secret = \
            [x.strip() for x in secrets.split(',')]

        self.twarc = Twarc(consumer_key, consumer_secret, access_token, access_token_secret)

 
    # Helper functions for saving csv and formatted txt files 
    def write_data(self, data, filename, filetype='txt'): 
        with io.open(filename, "w", encoding="utf-8") as handle:
            if filetype == 'txt':
                for item, count in data.most_common():
                    handle.write(str(count) + "\t" + item + "\n")

            else: #write to csv
                handle.write(u"Source,Target,Weight\n")
                for source, targets in sorted(data.items()):
                    for target, count in sorted(targets.items()):
                        if source != target and source is not None and target is not None:
                            handle.write(source + u"," + target + u"," + str(count) + u"\n")
        return

 
    # Returns the screen_name of the user retweeted, or None
    def retweeted_user(self, status):
        if "retweeted_status" in status:
            orig_tweet = status["retweeted_status"]
            if "user" in orig_tweet and orig_tweet["user"] is not None:
                user = orig_tweet["user"]
                if "screen_name" in user and user["screen_name"] is not None:
                    return user["screen_name"]
        return

 
    # Returns a list of screen_names that the user interacted with in this Tweet
    def get_interactions(self, status):
        interactions = []
        if "in_reply_to_screen_name" in status:
            replied_to = status["in_reply_to_screen_name"]
            if replied_to is not None and replied_to not in interactions:
                interactions.append(replied_to)

        if "retweeted_status" in status:
            orig_tweet = status["retweeted_status"]
            if "user" in orig_tweet and orig_tweet["user"] is not None:
                user = orig_tweet["user"]
                if "screen_name" in user and user["screen_name"] is not None:
                    if user["screen_name"] not in interactions:
                        interactions.append(user["screen_name"])

        if "quoted_status" in status:
            orig_tweet = status["quoted_status"]
            if "user" in orig_tweet and orig_tweet["user"] is not None:
                user = orig_tweet["user"]
                if "screen_name" in user and user["screen_name"] is not None:
                    if user["screen_name"] not in interactions:
                        interactions.append(user["screen_name"])

        if "entities" in status:
            entities = status["entities"]
            if "user_mentions" in entities:
                for item in entities["user_mentions"]:
                    if item is not None and "screen_name" in item:
                        mention = item['screen_name']
                        if mention is not None and mention not in interactions:
                            interactions.append(mention)
        return interactions

 
    # Returns a list of hashtags found in the tweet
    def get_hashtags(self, status):
        hashtags = []
        if "entities" in status:
            entities = status["entities"]
            if "hashtags" in entities:
                for item in entities["hashtags"]:
                    if item is not None and "text" in item:
                        hashtag = item['text']
                        if hashtag is not None and hashtag not in hashtags:
                            hashtags.append(hashtag)
        return hashtags
 

    # Returns a list of URLs found in the Tweet
    def get_urls(self, status):
        urls = []
        if "entities" in status:
            entities = status["entities"]
            if "urls" in entities:
                for item in entities["urls"]:
                    if item is not None and "expanded_url" in item:
                        url = item['expanded_url']
                        if url is not None and url not in urls:
                            urls.append(url)
        return urls
 

    def get_image_urls(self, status):
        # Returns the URLs to any images found in the Tweet
        urls = []
        if "entities" in status:
            entities = status["entities"]
            if "media" in entities:
                for item in entities["media"]:
                    if item is not None:
                        if "media_url" in item:
                            murl = item["media_url"]
                            if murl not in urls:
                                urls.append(murl)
        return urls


    def fetch_images(self):
        # Iterate through image URLs, fetching each image if we haven't already
        pictures_dir = os.path.join(self.save_dir, self.dataname + '_' + "images")
        if not os.path.exists(pictures_dir):
            print("Creating directory: " + pictures_dir)
            os.makedirs(pictures_dir)        
        for url in self.all_image_urls:
            m = re.search("^http:\/\/pbs\.twimg\.com\/media\/(.+)$", url)
            if m is not None:
                filename = m.group(1)
                print("Getting picture from: " + url)
                save_path = os.path.join(pictures_dir, filename)
                if not os.path.exists(save_path):
                    response = requests.get(url, stream=True)
                    with open(save_path, 'wb') as out_file:
                        shutil.copyfileobj(response.raw, out_file)
                    del response

        return

    def writedf(self, dataset, name, columns):
        filename = os.path.join(self.save_dir, self.dataname + '_' + name)
        with io.open(filename, "w", encoding="utf-8") as handle:
            handle.write('\t'.join(columns) + u"\n")
            for row in dataset:
                handle.write('\t'.join(row) + u"\n")
        return

    def save_datasets(self, fetch_images=True):

        csv_outputs = {
            "user_user_graph.csv": self.user_user_graph,
            "user_hashtag_graph.csv": self.user_hashtag_graph,
            "hashtag_hashtag_graph.csv": self.hashtag_hashtag_graph}
        for name, dataset in csv_outputs.items():
            filename = os.path.join(self.save_dir, self.dataname + '_' + name)
            self.write_data(dataset, filename, 'csv')
 
        text_outputs = {
            "hashtags.txt": self.hashtag_frequency_dist,
            "influencers.txt": self.influencer_frequency_dist,
            "mentioned.txt": self.mentioned_frequency_dist,
            "urls.txt": self.url_frequency_dist}
        for name, dataset in text_outputs.items():
            filename = os.path.join(self.save_dir, self.dataname + '_' + name)
            self.write_data(dataset, filename, 'txt')


        self.writedf(self.url_refs, "url_refs.csv", ['url', 'tweeturl'])
        self.writedf(self.image_refs, "image_refs.csv", ['url', 'tweeturl'])
        self.writedf(self.tweets, "tweets.csv", ['url', 'screen_name', 'id', 'created_at', 'text'])

        if fetch_images:
            self.fetch_images()

        return

    def make_directories(self, target, rootdir='../data/twitter'):
        # Create a separate save directory for each search query
        # Since search queries can be a whole sentence, we'll check the length
        # and simply number it if the query is overly long

        self.dataname = datetime.now().strftime("%Y%m%d%H%M%S") + '_' + target.replace(" ", "_") 

        self.save_dir = rootdir
        if not os.path.exists(rootdir):
            os.makedirs(rootdir)
        if len(target) < 30:
            self.save_dir += "/" + self.dataname
        else:
            self.save_dir += "/target_" + str(count + 1)
        if not os.path.exists(self.save_dir):
            print("Creating directory: " + self.save_dir)
            os.makedirs(self.save_dir)

        return


    def get_target_data(self, target):

        # Variables for capturing stuff
        self.tweets_captured = 0
        self.influencer_frequency_dist = Counter()
        self.mentioned_frequency_dist = Counter()
        self.hashtag_frequency_dist = Counter()
        self.url_frequency_dist = Counter()
        self.user_user_graph = {}
        self.user_hashtag_graph = {}
        self.hashtag_hashtag_graph = {}
        self.all_image_urls = []
        self.tweets = []
        self.tweet_count = 0
        self.url_refs = []
        self.image_refs = []

        # Start the search
        for status in self.twarc.search(target):

            # Output some status as we go, so we know something is happening
            sys.stdout.write("\r")
            sys.stdout.flush()
            sys.stdout.write("Collected " + str(self.tweet_count) + " tweets.")
            sys.stdout.flush()
            self.tweet_count += 1
    
            screen_name = None
            if "user" in status:
                if "screen_name" in status["user"]:
                    screen_name = status["user"]["screen_name"]
 
            retweeted = self.retweeted_user(status)
            if retweeted is not None:
                self.influencer_frequency_dist[retweeted] += 1
            else:
                self.influencer_frequency_dist[screen_name] += 1
 
            # Tweet text can be in either "text" or "full_text" field...
            text = None
            if "full_text" in status:
                text = status["full_text"]
            elif "text" in status:
                text = status["text"]
 
            id_str = None
            if "id_str" in status:
                id_str = status["id_str"]
 
            # Assemble the URL to the tweet we received...
            tweet_url = None
            if id_str is not None and screen_name is not None:
                tweet_url = "https://twitter.com/" + screen_name + "/status/" + id_str
            # if tweet_url is not None and text is not None:
            #     self.tweets[tweet_url] = text
            created_at = None
            if "created_at" in status:
                created_at = status["created_at"]
            self.tweets += [[tweet_url, screen_name, id_str, created_at, text]] #capture everything
 
            # Record mapping graph between users
            interactions = self.get_interactions(status)
            if interactions is not None:
                for user in interactions:
                    self.mentioned_frequency_dist[user] += 1
                    if screen_name not in self.user_user_graph:
                        self.user_user_graph[screen_name] = {}
                    if user not in self.user_user_graph[screen_name]:
                        self.user_user_graph[screen_name][user] = 1
                    else:
                        self.user_user_graph[screen_name][user] += 1
 
            # Record mapping graph between users and hashtags
            hashtags = self.get_hashtags(status)
            if hashtags is not None:
                if len(hashtags) > 1:
                    hashtag_interactions = []

                    # This code creates pairs of hashtags in situations where multiple
                    # hashtags were found in a tweet
                    # This is used to create a graph of hashtag-hashtag interactions
                    for comb in combinations(sorted(hashtags), 2):
                        hashtag_interactions.append(comb)
                    if len(hashtag_interactions) > 0:
                        for inter in hashtag_interactions:
                            item1, item2 = inter
                            if item1 not in self.hashtag_hashtag_graph:
                                self.hashtag_hashtag_graph[item1] = {}
                            if item2 not in self.hashtag_hashtag_graph[item1]:
                                self.hashtag_hashtag_graph[item1][item2] = 1
                            else:
                                self.hashtag_hashtag_graph[item1][item2] += 1
                    for hashtag in hashtags:
                        self.hashtag_frequency_dist[hashtag] += 1
                        if screen_name not in self.user_hashtag_graph:
                            self.user_hashtag_graph[screen_name] = {}
                        if hashtag not in self.user_hashtag_graph[screen_name]:
                            self.user_hashtag_graph[screen_name][hashtag] = 1
                        else:
                            self.user_hashtag_graph[screen_name][hashtag] += 1
 
            urls = self.get_urls(status)
            if urls is not None:
                for url in urls:
                    self.url_refs += [[url, tweet_url]]
                    self.url_frequency_dist[url] += 1
 
            image_urls = self.get_image_urls(status)
            if image_urls is not None:
                for url in image_urls:
                    self.image_refs += [[url, tweet_url]]
                    if url not in self.all_image_urls:
                        self.all_image_urls.append(url)

        self.save_datasets(fetch_images=True)

        return

 

# Main starts here
if __name__ == '__main__':

    # Check that search terms were provided at the command line
    if (len(sys.argv) <= 1):
        print("No search terms provided. Exiting.")
        sys.exit(0)

    # First commandline argument is the date range for search a:b
    # Couldn't get from_date to work, but can get since_id.  We get what we get. 


    # other arguments are the search terms
    twitterRelationships = TwitterRelationships()
    target_list = sys.argv[1:] 
    num_targets = len(target_list)

    for count, target in enumerate(target_list):

        print('{}/{} searching on target: {}'.format(count+1, num_targets, target))
        twitterRelationships.make_directories(target)
        twitterRelationships.get_target_data(target)




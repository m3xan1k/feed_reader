import feedparser
import json
import os


feeds = ['https://habr.com/ru/rss/best/weekly/?fl=ru', 'https://pythondigest.ru/rss/']

def remove_images(feed):
    data = feed
    for item in data['entries']:
        if '<img' in item['summary']:
            print('img is here')
        item['summary'] = item['summary'].strip().replace('<img', '<img style="width:350px;height:250px;" ')
    return data

def parse_feeds(feeds):
    d = [feedparser.parse(feed) for feed in feeds]
    data = list(map(remove_images, d))
    return data


if __name__ == '__main__':
    pass
    
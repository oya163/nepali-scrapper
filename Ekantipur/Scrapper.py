# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import urllib.request
from urllib.parse import urlparse
import re
import json
import sys
import os
import requests

class ReadOnlyClass(type):
    def __setattr__(self, name, value):
        raise ValueError(name)


class Scrapper:
    __metaclass__ = ReadOnlyClass

    def __init__(self, news_link='', source=''):
        self.NEWS_LINK = news_link
        self.SOURCE = source
        self.dump = {
            'news_link' : self.NEWS_LINK,
            'source' : self.SOURCE,
            'category' : {
            }
        }
        
        
    def saveJson(self, filename=None):
        fname = filename if filename else self.SOURCE+'.json' 
        with open(fname, 'w', encoding='utf-8') as f:
            json.dump(self.dump, f, ensure_ascii=False, indent=4)
            

    def extractContent(self):
        r = urllib.request.urlopen(self.NEWS_LINK).read()
        soup = BeautifulSoup(r, 'html.parser')
        return self.parseContent(soup)

    def parseContent(self, content):
        self.extractCategory(content)

    def extractCategory(self, content):
        categoryOriginal = {}
        categories = {}

        for paragraph in content.find_all('a'):
            link = paragraph.get('href')
            
            if link is not None and 'https' in link:
                # To get all the main title page
                # There is break in paragraph text
                if paragraph.text == '':
                    break
                categoryOriginal[paragraph.get('href')] = paragraph.text

        self.extractHeadline(categoryOriginal)


    # retrieve headline for each category
    def extractHeadline(self, categoryList):

        for ind, (link, category) in enumerate(categoryList.items()):
            url = link
#             self.dump['category']
            
            r = urllib.request.urlopen(url).read()
            soup = BeautifulSoup(r, 'html.parser')

            headlineList = []
            for data in soup.find_all('div', {'class': ['teaser offset']}):
                if data.find('a') is not None:
                    # verify that it is content page
                    if 'html' in data.find('a').get('href'):
                        headlineList.append((category, data.find('a').get('href')))
            
            self.dump['category'][str(ind)]['content'] = self.newsContents(headlineList)

#             print(self.dump['content'])
                
            


    # retrieve the body for each headline
    def newsContents(self, headlineList):
        
        news_dump = {}
        for index, (category, half_link) in enumerate(headlineList):
            
            print ("*************** Category : {}, #: {} ********************".format(category, (index + 1)))
            url = ''
            
            # [1:] because of extra / in half_link
            url = url.join((self.NEWS_LINK, half_link[1:]))
            print("Link :", url)
            
            r = urllib.request.urlopen(url).read()
            soup = BeautifulSoup(r, 'html.parser')
            
            title_source = soup.find_all('div', {'class': ['article-header']})
            if title_source[0].find({'h1', 'h2'}) is not None:
                news_title = title_source[0].find({'h1', 'h2'}).text
            
            body_content = soup.find('article', {'class': ['normal']})
#             body_content = soup.find('div', {'class': ['description portrait']})

            news_body=' '
                
            if body_content:
                for body in body_content.findAll('p'):
                    # check if it the body is empty
                    # exclude the javascript inside <p></p> tag
                    # exclude the duplicates from appending
                    if str(body.text.encode('ascii', 'ignore'))!=""  \
                        and 'script' not in str(body) \
                        and body.text not in news_body:
                        news_body += body.text

                # Get date
                split_url = url.split('/')
                yy = split_url[-4]
                mm = split_url[-3]
                dd = split_url[-2]
                published_date = mm+dd+yy

                result = {
                    'title' : news_title,
                    'text' : news_body,
                    'url' : url,
                    'published_date' : published_date,
                }

                news_dump[str(index)] = result

                return news_dump
            else:
                return
            

def main():
    news_link = sys.argv[1]
    news_source_name = sys.argv[2]
    scrappy = Scrapper(news_link=news_link, source=news_source_name)
    scrappy.extractContent()
    scrappy.saveJson()

if __name__ == '__main__':
    main()

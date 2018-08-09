# -*- coding: UTF-8 -*-
import time

import xlwt

import requests

from bs4 import BeautifulSoup

class ReferenceSpider(object):
    def __init__(self, targeturl):
        self.maxtryloadnum = 3

        self.targeturl = targeturl
        self.targetheaders = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36',
        }

        self.crawlresult = {}
        self.crawlresult['url'] = targeturl
        self.crawlresult['id'] = ''
        self.crawlresult['doi'] = ''
        self.crawlresult['title'] = ''
        self.crawlresult['authors'] = []
        self.crawlresult['keywords'] = []
        self.crawlresult['abstract'] = '' 
        self.crawlresult['referitems'] = []

    def save_crawlresult(self, writer):
        selfid = self.crawlresult['id']

        title = self.crawlresult['title']

        doi = self.crawlresult['doi']

        url = self.crawlresult['url']

        authors = ''
        for au in self.crawlresult['authors']:
            authors += au + ','
        authors = authors[:-1]

        keywords = ''
        for kw in self.crawlresult['keywords']:
            keywords += kw + ','
        keywords = keywords[:-1]

        abstract = self.crawlresult['abstract']
        
        referitems = ''
        for referitem in self.crawlresult['referitems']:
            referitems += referitem + ';'
        referitems = referitems[:-1]

        data = []
        data.append(selfid)
        data.append(title)
        data.append(doi)
        data.append(url)
        data.append(authors)
        data.append(keywords)
        data.append(abstract)
        data.append(referitems)
        writer.writerow(data)

    def showgeneralinfo(self):
        # print self.crawlresult['id']
        print self.crawlresult['url']
        print self.crawlresult['title']
        print ''

    def loadpage(self):
        for t in range(self.maxtryloadnum):
            try:
                response = requests.get(self.targeturl, headers=self.targetheaders,timeout=10)
                page = response.content
                soup = BeautifulSoup(page, 'html.parser')
                return soup
            except:
                if t < (self.maxtryloadnum-1):  
                    continue
                else:
                    return 'failtoload' 

    def getcontent(self, soup):
        pass

    def getrefer(self, soup):
        pass

    def analyzepage(self):
        soup = self.loadpage()
        if soup == 'failtoload':
            print 'fail to load:'+self.targeturl
            return False
        self.getcontent(soup)
        self.getrefer(soup)
        return True
# -*- coding:utf-8 -*-
import re

import csv

import copy

import time

import requests

import threading

from bs4 import BeautifulSoup

from acmspider import ACMSpider

from ieeespider import IEEESpider

from springerspider import SpringerSpider

from sciencedirectspider import ScienceDirectSpider


class SpiderConfig(object):
    def __init__(self):
        self.config = {}
        self.config['keyword'] = ''
        self.config['depth'] = 0
        self.config['breadth'] = 0

        self.config['googlescholar_base'] = ''
        self.config['headers'] = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Host': 'c3.glgooo.top',
            'Referer': 'https://c3.glgooo.top/scholar/',
            'Upgrade-Insecure-Requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'
        }

        self.config['filename'] = time.strftime("%Y%m%d%H%M%S", time.localtime())

    def set_config(self, key, val):
        if key and val and key in self.config.keys():
            self.config[key] = val


class BaiduScholarThread(threading.Thread):
    def __init__(self, referitem):
        super(BaiduScholarThread, self).__init__()
        self.referitem = referitem
        self.referurl = ''

    def run(self):
        referitem = self.referitem
        url_search = 'http://xueshu.baidu.com/s?wd='
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Host': 'xueshu.baidu.com',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
        }
        wd = referitem.replace(' ', '+').replace(',', '%2C').replace(':', '%3A')
        bdurl = url_search + wd

        try:
            response = requests.get(bdurl, headers=headers, timeout=10)
            page = response.content
            soup = BeautifulSoup(page, 'html.parser')
        except:
            pass

        searchresults = soup.select('div[class="sc_content"]')
        for res in searchresults:
            title = res.select('h3 > a')
            if not title:
                continue
            else:
                title = title[0].text

            authors = []
            aus = res.select('a[data-click="{\'button_tp\':\'author\'}"]')
            for au in aus:
                author = au.text
                authors.append(author)
            
            try:
                pattern = re.compile(title, re.I|re.M)
                match1 = pattern.findall(referitem)
                match2 = True
            except:
                continue

            # for author in authors:
            #     pattern = re.compile(author, re.I|re.M)
            #     match = pattern.findall(referitem)
            #     if not match:
            #         match2 = False
            #         break

            if match1 and match2:
                url = ''
                source = res.select('a[class="v_source"]')
                for s in source:
                    sname = s['title']

                    if sname == 'Springer':
                        href = s['href']
                        flag = re.findall(r'http://link.springer.com/chapter/', href)
                        if flag:
                            href = href.replace(' ', '')
                            url = href
                            break

                    if sname == 'IEEEXplore':
                        href = s['href']
                        href = re.findall(r'document%2F.*?%2F', href)
                        if href:
                            ieeeid = href[0].replace('%2F', '').replace('document', '')
                            url = 'http://ieeexplore.ieee.org/abstract/document/'+ieeeid
                            break

                    if sname == 'ACM':
                        href = s['href']
                        href = re.findall(r'id%3D.*?%|id%3D.*?&', href)
                        if href:
                            acmid = href[0].replace('id%3D', '').replace('&', '').replace('%', '')
                            url = 'https://dl.acm.org/citation.cfm?id='+acmid
                            break

                    if sname == 'Elsevier':
                        href = s['href']
                        href = re.findall(r'pii%2F.*?&', href)
                        if href:
                            pii = href[0].replace('pii%2F', '').replace('&', '')
                            url = 'https://www.sciencedirect.com/science/article/pii/'+pii
                            break

                if url:
                    self.referurl = url
                    break


class ReferenceSpiderThread(threading.Thread):
    def __init__(self, referencespider, writer, lastroundflag):
        super(ReferenceSpiderThread, self).__init__()
        self.referencespider = referencespider
        self.writer = writer
        self.lastroundflag = lastroundflag
        self.referurls = []

    def get_referurls(self, referitems):
        threads = []
        for referitem in referitems:
            thread = BaiduScholarThread(referitem)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()
            referurl = thread.referurl
            if referurl:
                self.referurls.append(referurl)

    def run(self):
        loadflag = self.referencespider.analyzepage()
        
        if loadflag:
            self.referencespider.save_crawlresult(self.writer)

            self.referencespider.showgeneralinfo()

            if not self.lastroundflag:
                crawlresult = self.referencespider.crawlresult
                referitems = crawlresult['referitems']
                self.get_referurls(referitems)


class GoogleScholarSpider(object):
    def __init__(self, spiderconfig):
        self.spiderconfig = spiderconfig.config

        self.nextround_urls = {}
        self.nextround_urls['ScienceDirect'] = []
        self.nextround_urls['IEEE'] = []
        self.nextround_urls['Springer'] =[]
        self.nextround_urls['ACM'] = []

        self.urlcount = 0

        self.filename = self.spiderconfig['filename'] + '.csv'
        file = open(self.filename, 'wb')
        self.writer = csv.writer(file)

    def duplicate_thisround_urls(self, thisround_urls):
        duplicate = lambda x,y:x if y in x else x + [y]
        for db in ['ScienceDirect','IEEE','Springer','ACM']:
            urls = thisround_urls[db]
            urls = reduce(duplicate, [[], ] + urls)
            thisround_urls[db] = urls 
        return thisround_urls

    def reset_nextround_urls(self):
        self.nextround_urls.clear()
        self.nextround_urls['ScienceDirect'] = []
        self.nextround_urls['IEEE'] = []
        self.nextround_urls['Springer'] = []
        self.nextround_urls['ACM'] = []

    def sort_url(self, url):
        ispdf = re.findall(r'.pdf$', url)
        if ispdf:
            return 'other'

        sort = re.findall(r'www\.sciencedirect\.com', url)
        if sort:
            return 'ScienceDirect'

        sort = re.findall(r'ieeexplore\.ieee\.org', url)
        if sort:
            return 'IEEE'

        sort = re.findall(r'link\.springer\.com', url)
        if sort:
            return 'Springer'

        sort = re.findall(r'dl\.acm\.org', url)
        if sort:
            return 'ACM'

        return 'other'

    def generate_dbspider(self, db, url):
        if db == 'ScienceDirect':
            referencespider = ScienceDirectSpider(url)
            return referencespider

        if db == 'IEEE':
            referencespider = IEEESpider(url)
            return referencespider

        if db == 'Springer':
            referencespider = SpringerSpider(url)
            return referencespider

        if db == 'ACM':
            referencespider = ACMSpider(url)
            return referencespider

    def get_firstround_urls(self):
        url_base = self.spiderconfig['googlescholar_base']
        url_base += '&q=' + self.spiderconfig['keyword']
        url_base += '&start='

        isfull = 0
        pagenum = 0
        while True:
            print '检索第',pagenum+1,'页','进度:',self.urlcount,'/',self.spiderconfig['breadth']
            
            url = url_base + str(pagenum * 10)
            time.sleep(3)
            response = requests.get(url, headers=self.spiderconfig['headers'],timeout=10)
            page = response.content
            soup = BeautifulSoup(page, 'html.parser')

            gsrt_list = soup.select('.gs_rt > a')
            for gsrt in gsrt_list:
                if self.urlcount < self.spiderconfig['breadth']:
                    url = gsrt['href']
                    sort = self.sort_url(url)
                    if sort != 'other':
                        self.nextround_urls[sort].append(url)
                        self.urlcount += 1
                else:
                    isfull = 1
                    break

            if not gsrt_list or isfull:
                break

            pagenum += 1

    def crawl(self):
        self.get_firstround_urls()
        print '第一轮爬取完成'
        
        i = 0
        lastroundflag = False
        for crawldepth in range(1, self.spiderconfig['depth']+1):
            print '深度-',crawldepth,'开启'
            if crawldepth == self.spiderconfig['depth']:
                lastroundflag = True

            thisround_urls = copy.deepcopy(self.nextround_urls)
            thisround_urls = self.duplicate_thisround_urls(thisround_urls)
            self.reset_nextround_urls()

            threads = []

            for db in ['ScienceDirect','IEEE','Springer','ACM']:
                urls = thisround_urls[db]
                for url in urls:
                    referencespider = self.generate_dbspider(db, url)
                    thread = ReferenceSpiderThread(referencespider, self.writer, lastroundflag)
                    i+=1
                    print i,
                    thread.start()
                    threads.append(thread)
                    thread.join()
                    

            for thread in threads:
                thread.join()

            print '当前文献数量-',self.urlcount

            referurls = []
            for thread in threads:
                referurls.extend(thread.referurls)

            for referurl in referurls:
                referurl = referurl
                sort = self.sort_url(referurl)
                if sort != 'other':
                    self.nextround_urls[sort].append(referurl)
                    self.urlcount += 1
            
            print '下一轮文献数量-',len(referurls)

if __name__ == '__main__':
    import sys
    reload(sys)
    sys.setdefaultencoding('utf8')

    spiderconfig = SpiderConfig()
    spiderconfig.set_config('googlescholar_base', 'https://c3.glgooo.top/scholar?hl=zh-CN')
    spiderconfig.set_config('keyword', 'cloudcomputing')
    spiderconfig.set_config('breadth', 5)
    spiderconfig.set_config('depth', 3)

    spider = GoogleScholarSpider(spiderconfig)
    spider.crawl()
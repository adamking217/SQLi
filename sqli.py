#!/usr/bin/python
import time
import argparse
from DBDump import *
from WebCrawl import *
from MySQLTests import *
from functions import *

from termcolor import colored, cprint

dbdump = DBDump()
webcrawl = WebCrawl()
mysql = MySQLTests()
func = functions()

parser = argparse.ArgumentParser(prog='./sqli.py', usage='%(prog)s [-u URL]')
parser.add_argument('-u', '--url', dest='url', nargs='?', default="empty", help='Website domain for scanning (e.g. http://example.com)')
parser.add_argument('-l', '--level', dest='level', nargs='?', default="1", help='Scanning Level')
args = parser.parse_args()
inputURL = args.url
inputLVL = args.level

URLCrawl    = True
MySQLChecks = True
DataDump    = True

mysvulns = {}

def summary():
    end_time = round(time.time() - start_time, 2)
    for sqltype, total in iter(mysql.totalVulns.iteritems()):
        print colored("[*] [{3}] Completed: Total of {1} {0} vulnerabilities found in {2} seconds".format(sqltype, total, end_time, func.showTime()), "white")

def banner():
    banner =  "+-----------------------------------------------------------+\n"
    banner += "|                     SQLi Scanner v0.1                     |\n"
    banner += "|                       by Adam King                        |\n"
    banner += "+-----------------------------------------------------------+"
    print format(banner)
    if inputURL == 'empty':
        parser.print_help()
        exit(0)

def main():
    banner()
    if URLCrawl:
        print colored("[*] [{0}] Web Crawl Started".format(func.showTime()), "green")
        weburls = webcrawl.crawl(inputURL)
        print colored("[*] [{0}] Web Crawl Finished".format(func.showTime()), "green")
    if MySQLChecks:
        print colored("[*] [{0}] MySQL Tests Started".format(func.showTime()), "green")
        mysqlvulns =  mysql.start(inputLVL, weburls)
        print colored("[*] [{0}] MySQL Tests Finished".format(func.showTime()), "green")
    if DataDump:
        print colored("[*] [{0}] Data Dump Started".format(func.showTime()), "green")
        dbdump.start(mysqlvulns)
        #dbdump.display()
        print colored("[*] [{0}] Data Dump Finished".format(func.showTime()), "green")
    summary()

start_time = time.time()
main()        
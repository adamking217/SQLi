#!/usr/bin/python
import time
import argparse
import subprocess

from DBDump import *
from WebCrawl import *
from MySQLTests import *
from DirBrute import *
from functions import *
from BeautifulSoup import *

from termcolor import colored, cprint

dbdump = DBDump()
dirbrute = DirBrute()
webcrawl = WebCrawl()
mysql = MySQLTests()
func = functions()

parser = argparse.ArgumentParser(prog='./sqli.py', usage='%(prog)s [-u URL]')
parser.add_argument('-u', '--url', dest='url', nargs='?', default="empty", help='Website domain for scanning (e.g. http://example.com)')
parser.add_argument('-l', '--level', dest='level', nargs='?', default="1", help='Scanning Level')
parser.add_argument('-d', '--defaults', dest='defaults', nargs='?', default="1", help='Prompt for answers (1 = Yes, 0 = No)')
args = parser.parse_args()
inputURL = args.url
inputLVL = args.level
inputAnswers = args.defaults

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
    p = subprocess.Popen("git status", stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    p_status = p.wait()
    if "Your branch is up-to-date" not in output:
        print colored("[-] Please update your version by running 'git update'", "red")
        exit(0)
    print colored("[*] [{0}] Level :: {1}".format(func.showTime(), inputLVL), "green")
    if inputLVL >= "2":
        print colored("[*] [{0}] Dir Brute Started".format(func.showTime()), "green")
        dirs = dirbrute.start(inputURL, "dirs.txt")
        print colored("[*] [{0}] Dir Brute Finished".format(func.showTime()), "green")
    if URLCrawl:
        print colored("[*] [{0}] Web Crawl Started".format(func.showTime()), "green")
        weburls = webcrawl.crawl(inputURL)
        print colored("[*] [{0}] Web Crawl: Found {1} scripts".format(func.showTime(), len(weburls)), "cyan")
        print colored("[*] [{0}] Web Crawl Finished".format(func.showTime()), "green")
    if MySQLChecks:
        print colored("[*] [{0}] MySQL Tests Started".format(func.showTime()), "green")
        mysqlvulns =  mysql.start(inputLVL, weburls, inputAnswers)
        print colored("[*] [{0}] MySQL Tests Finished".format(func.showTime()), "green")
    if DataDump:
        print colored("[*] [{0}] Data Dump Started".format(func.showTime()), "green")
        dbdump.start(mysqlvulns)
        print colored("[*] [{0}] Data Dump Finished".format(func.showTime()), "green")
    summary()

start_time = time.time()
main()        
import urllib2
import urlparse
import time
import BeautifulSoup

from termcolor import colored, cprint

from functions import *
func = functions()

class DirBrute:

	def checkURL(self, url):
		try:
			content = urllib2.urlopen(url)
			respcode = content.getcode()
			if respcode == 200:
				return True;
			return False;
		except Exception:
			return False;			

	def start(self, weburl, dirfile):
		try:
			text_file = open(dirfile, "r")
			lines = text_file.readlines()
			text_file.close()
			found = 0
			for dirname in lines:
				dirname = dirname.replace("\r", "");
				dirname = dirname.replace("\n", "");
				newurl = weburl + dirname
				code = self.checkURL(newurl);
				if code:
					print colored("[-] Dir Brute - Found :: {0}".format(newurl), "cyan")
					found = found + 1
			print colored("[-] Dir Brute - Found {0} Dir(s)".format(found), "cyan")
		except Exception:
			print colored("[*] [{0}] Error opening file - {1}".format(func.showTime(), dirfile), "red")


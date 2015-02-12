from time import gmtime, strftime

class functions:

	def showTime(self):
		return strftime("%d/%m/%Y %H:%M:%S", gmtime())
import urllib2
'''
def foo(event):
	print event.char
from Tkinter import *
from PIL import Image, ImageTk
import urllib
url = 'http://pic.pimg.tw/luke7212/1375290771-510852523.jpg'
r = urllib.urlretrieve(url)
image = Image.open(r[0])
print image.size
root = Tk()
img = ImageTk.PhotoImage(image)
panel = Label(root, image = img, bg='black')
panel.pack(side = "bottom", fill = "both", expand = "yes")
root.bind('<Key>',foo)
root.mainloop()'''
url = 'http://www.8comic.com/105.html'
url = 'http://new.comicvip.com/show/cool-105.html?ch=31'
url = 'http://new.comicvip.com/show/cool-7340.html?ch=3'
# print urllib2.urlopen(url).read().decode('big5').encode('utf-8')
import re
ch = re.search('\?ch=(\d+)',url).groups()[0]
source = urllib2.urlopen(url).read().decode('big5').encode('utf-8')
chs,cs = re.search("<script>var chs=(\d+);.*?cs='([^']+)'",source).groups()
chs = int(chs)



url = 'http://www.8comic.com/7340.html'
class comicFetcher(object):
	homepage_format = 'http://www.8comic.com/%s.html'
	readpage_format = 'http://new.comicvip.com/show/cool-%s.html'#?ch=%s'
	def __init__(self,url):
		self.comic_code = re.search('/(\w+)\.html',url).groups()[0]
		overview = urllib2.urlopen(url).read().decode('big5').encode('utf-8')
		allbooks = re.findall('%s-(\d+)\.html.*?>([^<]+)'%self.comic_code,overview,re.S)
		self.allbooks = [(int(x[0]),x[1].strip()) if x[1].strip() else (x[0],'New') for x in allbooks]
		readpage = self.readpage_format%self.comic_code
		source = urllib2.urlopen(readpage).read().decode('big5').encode('utf-8')
		self.chs,self.cs = re.search("<script>var chs=(\d+);.*?cs='([^']+)'",source).groups()
		# for book in allbooks:

	def overview(self):
		return self.allbooks
	def getpages(self,ch):
		c = self.getc(ch)
		self.page_count = self.ss(c,7,3)
		return self.page_count
	def getc(self,ch):
		ch = str(ch)
		cc = len(self.cs)
		c = ''
		for i in range(cc/50):
			if self.ss(self.cs,i*50,4) == ch:
				c = self.ss(self.cs,i*50,50,50)
				ci = i
				break
		if not c:
			c = self.ss(self.cs,cc-50,50)
			ch = self.chs
		return c
	def getimgcode(self,ch,page):
		c = self.getc(ch)
		page_code = self.ss(c,self.mm(page)+10,3,50)+'.jpg'
		return page_code
	def ss(self,a,b,c,d=None):
		e = a[b:b+c]
		return e if d else re.sub('[a-z]','',e)
	def mm(self,page):
		r = (int(page-1)/10)%10 + (int(page-1)%10)*3
		return r

a = comicFetcher(url)
print a.getimgcode(3,21)
print a.getpages(3)
# print a.overview()

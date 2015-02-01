import urllib2,urllib
from Tkinter import *
from PIL import Image, ImageTk
import re
import cStringIO
import time
import tempfile
import os
class ComicBook(object):
	host = 'http://www.8comic.com'
	def __init__(self,intropage='0',bookname='',author='',intro=''):
		code = re.search('(\d+)',intropage)
		self.comic_code = code.groups()[0] if code else '0'
		self.introurl = host + '/html/%s.html'%self.comic_code
		self.previewurl = host + '/pics/0/%s.jpg'%self.comic_code
		self.bookname = bookname
		self.author = author
		self.intro = intro


class comicFetcher(object):
	hompage = 'http://www.8comic.com'
	homepage_format = 'http://www.8comic.com/%s.html'
	readpage_format = 'http://new.comicvip.com/show/cool-%s.html'#?ch=%s'
	
		
	def getallbooks(self,url):
		self.comic_code = re.search('/(\w+)\.html',url).groups()[0]
		overview = urllib2.urlopen(url).read().decode('big5').encode('utf-8')
		allbooks = re.findall('%s-(\d+)\.html.*?>([^<]+)'%self.comic_code,overview,re.S)
		self.allbooks = [(int(x[0]),x[1].strip()) if x[1].strip() else (int(x[0]),'New') for x in allbooks]
		readpage = self.readpage_format%self.comic_code
		source = urllib2.urlopen(readpage).read().decode('big5').encode('utf-8')
		self.chs,self.cs = re.search("<script>var chs=(\d+);.*?cs='([^']+)'",source).groups()
		for i in range(len(self.allbooks)):
			self.allbooks[i] += (int(self.getpages(self.allbooks[i][0])),)
		return self.allbooks
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
	def getimgurl(self,ch,page):
		c = self.getc(ch)
		page_code = self.ss(c,self.mm(page)+10,3,50)+'.jpg'
		imgurl = 'http://img'+self.ss(c,4,2)+'.8comic.com/'+self.ss(c,6,1)+'/'+self.comic_code+'/'+self.ss(c,0,4)+'/'+self.nn(page)+'_'+self.ss(c,self.mm(page)+10,3,50)+'.jpg';
		return imgurl
	def ss(self,a,b,c,d=None):
		e = a[b:b+c]
		return e if d else re.sub('[a-z]','',e)
	def mm(self,page):
		r = (int(page-1)/10)%10 + (int(page-1)%10)*3
		return r
	def nn(self,n):
		if n < 10:
			return '00%d'%n
		elif n < 100:
			return '0%d'%n
		return n

	def searchComic(self,big5title):
		u = '/member/search.aspx?k=%s&button=%%B7j%%B4M'%big5title
		header = {}
		header['Accept-Language'] = 'zh-TW,zh;q=0.8,en-US;q=0.6,en;q=0.4'
		req = urllib2.Request(url+u,headers=header)
		search_result = urllib2.urlopen(req).read().decode('big5').encode('utf-8')
		comic_title,author,intro = '','',''
		for x in re.findall("'(/html/\d+\.html)' >(.*?)</td>",search_result,re.S):
			code = x[0]
			comic_title,author,intro = [z for z in map(lambda l:re.sub('<.*?>','',l)+' ',[y for y in x[1].splitlines()]) if z.strip()]
			yield ComicBook(code,comic_title,author,intro)

class comicReader(object):
	def display(self,e,data):
		
		newframe = Toplevel()
		newframe.title(data[1])
		newframe.geometry('600x800')
		newframe.minsize(300,480)
		pagescount = Label(newframe, text='%s / %s'%(1,data[2]))

		imgpath = self.fetcher.getimgurl(data[0],1)
		imagedata = cStringIO.StringIO(urllib2.urlopen(imgpath).read())
		image = Image.open(imagedata)
		self.originalimg = image
		image = image.resize((600,780),Image.ANTIALIAS)
		photo = ImageTk.PhotoImage(image)
		theimg = Label(newframe,image=photo,height=780,width=600)
		theimg.image = photo
		theimg.pack()

		newframe.config(bg='black')
		newframe.bind('<Key>',lambda e,pagelabel=pagescount,imglabel=theimg,ch=data[0]:self.pagectrl(e,pagelabel,imglabel,ch))
		# newframe.bind('<Configure>',lambda e,imglabel=theimg:self.resize(e,imglabel))
		pagescount.pack()
		newframe.focus()
		newframe.mainloop()
	
	def key(self,e):
		if e.keycode == 27:
			exit()
	def resize(self,e,theimg):
		image = self.originalimg.resize((e.width,e.height-20),Image.ANTIALIAS)
		photo = ImageTk.PhotoImage(image)
		theimg.Config(image=photo)
		theimg.image = photo

	def pagectrl(self,e,pagelabel,imglabel,ch):
		now,bound = map(int,re.search('(\d+) / (\d+)',pagelabel.cget('text')).groups())
		changed = False
		if e.keycode == 37 or e.keycode ==33 or e.keycode==38:
			# left
			if now > 1:
				now -=1
				pagelabel.config(text='%d / %d'%(now,bound))
				changed = True
		elif e.keycode == 39 or e.keycode==34 or e.keycode==40:
			# right
			if now < bound:
				now +=1
				pagelabel.config(text='%d / %d'%(now,bound))
				changed = True
		elif e.keycode == 35:
			# end
			if now <bound:
				now = bound
				pagelabel.config(text='%d / %d'%(now,bound))
				changed = True
		elif e.keycode == 36:
			# home
			if now > 1:
				now = 1
				pagelabel.config(text='%d / %d'%(now,bound))
				changed = True
		if changed:
			imgpath = self.fetcher.getimgurl(ch,now)
			print imgpath
			pt = time.time()
			raw_data = urllib2.urlopen(imgpath).read()
			self.imagedata = cStringIO.StringIO(raw_data)
			print 'download cost :',time.time()-pt
			print 'pic size:',len(raw_data)
			image = Image.open(self.imagedata)
			self.originalimg = image
			image = image.resize((600,780),Image.ANTIALIAS)
			photo = ImageTk.PhotoImage(image)
			imglabel.config(image=photo)
			imglabel.image = photo

		print e.keycode
	def __init__(self,url):
		self.fetcher = comicFetcher(url)
		data = self.fetcher.overview()
		self.root = Tk()
		self.frame = Frame(self.root,bg='black')
		self.root.bind('<Key>',self.key)
		self.frame.pack()
		# data = [(0, '\xe7\xac\xac00\xe8\xa9\xb1', 35), (1, '\xe7\xac\xac01\xe8\xa9\xb1', 51), (2, '\xe7\xac\xac02\xe8\xa9\xb1', 41), (3, '\xe7\xac\xac03\xe8\xa9\xb1', 43), (4, '\xe7\xac\xac04\xe8\xa9\xb1', 45), (5, '\xe7\xac\xac05\xe8\xa9\xb1', 31), (6, '\xe7\xac\xac06\xe8\xa9\xb1', 34), (7, '\xe7\xac\xac07\xe8\xa9\xb1', 36), (8, '\xe7\xac\xac08\xe8\xa9\xb1', 34), (9, '\xe7\xac\xac09\xe8\xa9\xb1', 36), (10, '\xe7\xac\xac10\xe8\xa9\xb1', 42), (11, '\xe7\xac\xac11\xe8\xa9\xb1', 40), (12, '\xe7\xac\xac12\xe8\xa9\xb1', 43), (13, '\xe7\xac\xac13\xe8\xa9\xb1', 38), (14, '\xe7\xac\xac14\xe8\xa9\xb1', 31), (15, '\xe7\xac\xac15\xe8\xa9\xb1', 37), (16, '\xe7\xac\xac16\xe8\xa9\xb1', 31), (17, '\xe7\xac\xac17\xe8\xa9\xb1', 33), (18, '\xe7\xac\xac18\xe8\xa9\xb1', 39), (19, '\xe7\xac\xac19\xe8\xa9\xb1', 45), (20, '\xe7\xac\xac20\xe8\xa9\xb1', 31), (21, '\xe7\xac\xac21\xe8\xa9\xb1', 38), (22, '\xe7\xac\xac22\xe8\xa9\xb1', 45), (23, '\xe7\xac\xac23\xe8\xa9\xb1', 43), (24, '\xe7\xac\xac24\xe8\xa9\xb1', 43), (25, '\xe7\xac\xac25\xe8\xa9\xb1', 33), (26, '\xe7\xac\xac26\xe8\xa9\xb1', 42), (27, '\xe7\xac\xac27\xe8\xa9\xb1', 45), (28, '\xe7\xac\xac28\xe8\xa9\xb1', 44), (29, '\xe7\xac\xac29\xe8\xa9\xb1', 41), (30, '\xe7\xac\xac30\xe8\xa9\xb1', 42), (31, '\xe7\xac\xac31\xe8\xa9\xb1', 44), (32, '\xe7\xac\xac32\xe8\xa9\xb1', 43), (33, '\xe7\xac\xac33\xe8\xa9\xb1', 44), (34, '\xe7\xac\xac34\xe8\xa9\xb1', 43), (35, '\xe7\xac\xac35\xe8\xa9\xb1', 43), (36, '\xe7\xac\xac36\xe8\xa9\xb1', 45), (37, '\xe7\xac\xac37\xe8\xa9\xb1', 44), (38, '\xe7\xac\xac38\xe8\xa9\xb1', 44), (39, '\xe7\xac\xac39\xe8\xa9\xb1', 44), (40, '\xe7\xac\xac40\xe8\xa9\xb1', 44), (41, '\xe7\xac\xac41\xe8\xa9\xb1', 44), (42, '\xe7\xac\xac42\xe8\xa9\xb1', 41), (43, '\xe7\xac\xac43\xe8\xa9\xb1', 38), (44, '\xe7\xac\xac44\xe8\xa9\xb1', 44), (45, '\xe7\xac\xac45\xe8\xa9\xb1', 44), (46, '\xe7\xac\xac46\xe8\xa9\xb1', 45), (47, '\xe7\xac\xac47\xe8\xa9\xb1', 45), (48, '\xe7\xac\xac48\xe8\xa9\xb1', 45), (49, '\xe7\xac\xac49\xe8\xa9\xb1', 46), (50, '\xe7\xac\xac50\xe8\xa9\xb1', 44), (51, '\xe7\xac\xac51\xe8\xa9\xb1', 45), (52, '\xe7\xac\xac52\xe8\xa9\xb1', 45), (53, '\xe7\xac\xac53\xe8\xa9\xb1', 46), (54, '\xe7\xac\xac54\xe8\xa9\xb1', 42), (55, '\xe7\xac\xac55\xe8\xa9\xb1', 45), (56, '\xe7\xac\xac56\xe8\xa9\xb1', 45), (57, '\xe7\xac\xac57\xe8\xa9\xb1', 44), (58, '\xe7\xac\xac58\xe8\xa9\xb1', 46), (59, '\xe7\xac\xac59\xe8\xa9\xb1', 46), (60, '\xe7\xac\xac60\xe8\xa9\xb1', 46), (61, '\xe7\xac\xac61\xe8\xa9\xb1', 45), (62, '\xe7\xac\xac62\xe8\xa9\xb1', 41), (63, '\xe7\xac\xac63\xe8\xa9\xb1', 41), (64, '\xe7\xac\xac64\xe8\xa9\xb1', 45), (65, '\xe7\xac\xac65\xe8\xa9\xb1', 44), (8001, '\xe7\x95\xaa\xe5\xa4\x961', 17), (8002, 'New', 18)]
		for i in range(len(data)):
			l = Label(self.frame,text='%6s'%data[i][1],cursor='hand2',fg='blue',bg='black')
			l.grid(row=i/8,column=(i%8)+1)
			l.bind('<ButtonRelease-1>',lambda e,p=data[i]:self.display(e,p))
			l.bind('<Enter>',lambda e,d=l:d.config(bg='red'))
			l.bind('<Leave>',lambda e,d=l:d.config(bg='black'))
		self.root.mainloop()




url = 'http://www.8comic.com/105.html'
url = 'http://new.comicvip.com/show/cool-105.html?ch=31'
url = 'http://new.comicvip.com/show/cool-7340.html?ch=3'


url = 'http://www.8comic.com/7340.html'
# url = 'http://www.8comic.com/714.html'
# comicReader(url)
a = comicFetcher(url)
print a.overview()
# # print a.getimgcode(3,21)
# # print a.getpages(3)
# for x in a.overview():
# 	print x[1],x[2]

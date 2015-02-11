#encoding=utf-8
import urllib2,urllib
from Tkinter import *

from PIL import Image, ImageTk
import re
import cStringIO
import time
import os
import threading
import ttk
class ComicBook(object):
	host = 'http://www.8comic.com'
	def __init__(self,intropage='0',bookname='',roles='',intro=''):
		code = re.search('(\d+)',intropage)
		self.comic_code = code.groups()[0] if code else '0'
		self.introurl = self.host + '/html/%s.html'%self.comic_code
		self.previewurl = self.host + '/pics/0/%s.jpg'%self.comic_code
		self.bookname = self.__handle_htmlencoding(bookname)
		self.title = self.bookname.split('  ')[0]
		self.subtitle = self.bookname.split('  ')[1].strip()
		self.roles = self.__handle_htmlencoding(roles)
		self.intro = self.__handle_htmlencoding(intro)
	def __handle_htmlencoding(self,text):
		return re.sub('&#(\d+);',lambda e:unichr(int(e.group(1))).encode('utf-8'),text)



class comicFetcher(object):
	hompage = 'http://www.8comic.com'
	readpage_format = 'http://new.comicvip.com/show/%s%s.html'#?ch=%s'
	short_class = 'cool-'
	long_class = 'best-manga-'
	short_description = map(str,[4,6,12,22,1,17,19,21,2,5,7,9])
	long_description = map(str,[10,11,13,14,3,8,15,16,18,20])

	def getallbooks(self,url):
		self.comic_code = re.search('/(\w+)\.html',url).groups()[0]
		overview = urllib2.urlopen(url).read().decode('big5').encode('utf-8')
		allbooks = re.findall("%s-(\d+)\.html',(\d+).*?>([^<]+)"%self.comic_code,overview,re.S)
		self.allbooks = [(int(x[0]),x[2].strip().decode('utf-8'),x[1]) if x[2].strip() else (int(x[0]),'New') for x in allbooks]

		readpage = self.readpage_format%(self.long_class if self.allbooks[0][2] in self.long_description else self.short_class,self.comic_code)
		print 'readurl :',readpage
		source = urllib2.urlopen(readpage).read().decode('big5').encode('utf-8')
		self.chs,self.cs = re.search("<script>var chs=(\d+);.*?cs='([^']+)'",source).groups()
		for i in range(len(self.allbooks)):
			self.allbooks[i] += (int(self.getpages(self.allbooks[i][0])),)
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
		# u = '/member/search.aspx?k=%s'%(re.sub(ur'(.)',lambda m:'%s%s%s%s'%('%26','%23',str(ord(m.group(0))),'%3B'),big5title,re.U))
		header = {}
		header['Accept-Language'] = 'zh-TW,zh;q=0.8,en-US;q=0.6,en;q=0.4'
		req = urllib2.Request(self.hompage+u,headers=header)
		search_result = urllib2.urlopen(req).read().decode('big5','ignore').encode('utf-8')
		comic_title,author,intro = '','',''
		for x in re.findall("'(/html/\d+\.html)' >(.*?)</td>",search_result,re.S):
			code = x[0]
			a = [z for z in map(lambda l:re.sub('<.*?>','',l)+' ',[y for y in x[1].splitlines()])]
			comic_title,author,intro=a[0],a[1],a[3]
			# comic_title,author,intro=a if len(a)>2 else a[0],a[1],''
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

class CreateToolTip(object):
    '''
    create a tooltip for a given widget
    '''
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.close)
    def enter(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = Label(self.tw, text=self.text, justify='left',
                       background='gray', relief='solid', borderwidth=1,
                       font=("times", "18", "normal"))
        label.pack(ipadx=1)

    def close(self, event=None):
        if self.tw:
            self.tw.destroy()


class comicDownload(object):

	def __init__(self):
		self.fetcher = comicFetcher()
		self.lock = threading.Lock()
		self.bookstore=[]
		self.book_buttons = []
		self.root = Tk()
		self.root.wm_title("小孟愛看漫畫書")
		self.top_frame = ttk.Frame(self.root,relief=SUNKEN,height=100)
		self.top_frame.grid(row=0,column=0,rowspan=4,columnspan=4)
		self.top_frame.pack(fill=X)
		Label(self.top_frame,text='關鍵字:').pack(side=LEFT)
		self.searchname = StringVar()
		self.inpt = Entry(self.top_frame,width=29,textvariable=self.searchname)
		self.inpt.pack(side=LEFT,fill=X)
		self.btn = Button(self.top_frame,text=' 搜  尋 ',command=self.create_search_thread)
		self.btn.pack(side=LEFT,anchor=W,expand=True)
		

		self.canvas = Canvas(self.root,bg='black')
		# self.canvas.config(scrollregion=self.canvas.bbox("all"))
		self.vbar=Scrollbar(self.canvas,orient=VERTICAL)
		self.vbar.pack(side=RIGHT,fill=Y)
		self.vbar.config(command=self.canvas.yview)

		self.root.bind('<MouseWheel>',lambda e:self.ms(e,self.canvas))
		self.root.bind('<Key>',self.adjustyview)
		# self.frame = Frame(self.canvas)
		self.canvas.pack(side=LEFT,expand=True,fill=BOTH)
		self.root.grid_rowconfigure(0, weight=1)
		self.root.grid_columnconfigure(0, weight=1)

		self.book_frame = None
		# self.book_frame = Frame(self.canvas,bg='black')
		# self.book_frame.rowconfigure(1, weight=1)
		# self.book_frame.columnconfigure(1, weight=1)
		# self.canvas.create_window(0, 0, anchor=NW, window=self.book_frame)

		# self.frame.update_idletasks()

		self.inpt.focus()
		self.inpt.bind('<Key>',self.inpt_key_event)
		self.root.minsize(300,600)
		self.root.maxsize(300,600)
		self.root.mainloop()

	# def perform_download(label_ch,progressbar_ch,label_page,progressbar_page):
	# 	pass
	def inpt_key_event(self,e):
		if e.keysym == 'Return':
			self.create_search_thread()
			

	def perform_download(self,book):
		allbooks = self.fetcher.getallbooks(book.introurl)
		print allbooks
		self.label_ch.config(text='%s(%d / %d)'%(allbooks[0][1],1,len(allbooks)))
		self.label_page.config(text='%d / %d'%(1,allbooks[0][-1]))

		self.progressbar_ch['maximum'] = len(allbooks)
		if not os.path.exists(self.comicfolder):
			os.mkdir(self.comicfolder)
			
		nowch=1
		self.progressbar_page.start()
		for ch in allbooks:
			if allbooks[-1] == ch:
				self.progressbar_ch.step(0.999)
			else:
				self.progressbar_ch.step()
			self.label_ch.config(text='%s(%d / %d)'%(ch[1],nowch,len(allbooks)))
			# self.progressbar_page['maximum'] = ch[-1]
			
			path = os.path.join(self.comicfolder,ch[1])
			if not os.path.exists(path):
				os.mkdir(path)
			
			# self.progressbar_page['value'] = 0
			for page in range(1,ch[-1]+1):
				imgurl = self.fetcher.getimgurl(ch[0],page)
				filename = os.path.basename(imgurl)
				with open(os.path.join(path,filename),'wb') as f:
					f.write(urllib2.urlopen(imgurl).read())
				# if ch[-1] == page:
				# 	self.progressbar_page.step(0.999)
				# else:
				# 	self.progressbar_page.step()
				self.label_page.config(text='%d / %d'%(page,ch[-1]))
				time.sleep(0.1)
				pass
			# self.progressbar_page['value'] = ch[-1] - 0.001
			nowch+=1
		self.progressbar_page.stop()
	def progress(self,book=None):
		tl = Toplevel()
		tl.title('donwloading')
		# tl.geometry('300x100')
		tl.rowconfigure(5,weight=2)
		tl.columnconfigure(5,weight=2)
		self.comicfolder = os.path.join(os.getcwd(),book.bookname).strip().decode('utf-8').split('  ')[0]
		Label(tl,text=self.comicfolder).grid(row=0,column=0)
		progress_frame = Frame(tl)
		progress_frame.grid(row=1,column=0,sticky=W+N)
		self.progressbar_ch = ttk.Progressbar(progress_frame,orient=HORIZONTAL, length=200, mode='determinate')
		self.progressbar_ch.grid(row=0,column=0,pady=10,sticky=W)
		self.label_ch = Label(progress_frame,text= '')
		self.label_ch.grid(row=0,column=1,sticky=W,padx=10)

		self.progressbar_page = ttk.Progressbar(progress_frame,orient=HORIZONTAL, length=200, mode='indeterminate')
		self.progressbar_page.grid(row=3,column=0,pady=10,sticky=W)
		self.label_page = Label(progress_frame,text='')
		self.label_page.grid(row=3,column=1,sticky=W,padx=10)
		

		self.stopDownload = False
		
		threading.Thread(target=self.perform_download,args=([book])).start()
		tl.protocol("WM_DELETE_WINDOW", lambda :self.cancel_download(tl))
		tl.mainloop()

	def cancel_download(self,parent):
		self.stopDownload = True
		parent.destroy()
	def create_search_thread(self):
		if self.btn['state'] == 'normal':
			threading.Thread(target=self.create_button).start()

	def create_button(self):
		self.lock.acquire()
		self.btn.config(state='disabled',text='處理中')
		if self.book_frame:
			self.book_frame.destroy()
		self.book_frame = Frame(self.canvas,bg='black')
		self.book_frame.rowconfigure(1, weight=1)
		self.book_frame.columnconfigure(1, weight=1)
		self.canvas.create_window(0, 0, anchor=NW, window=self.book_frame)
		# self.canvas.update_idletasks()
		# a = self.inpt.get()
		a = self.searchname.get()
		self.searchname.set('')
		tmp = []
		for x in a:
			try:
				tmp.append(urllib.quote(x.encode('big5')))
			except:
				tmp.append(re.sub(ur'(.)',lambda m:'%s%s%s%s'%('%26','%23',str(ord(m.group(0))),'%3B'),x,re.U))
		search_name = ''.join(tmp)
		books = self.fetcher.searchComic(search_name)
		
		for book in books:
			print book.comic_code,book.title,book.roles,book.intro
			print book.previewurl,book.introurl
			tooltip_text = '''名稱：%s %s
人物：%s
內容簡介：%s'''%(book.title,book.subtitle,book.roles,book.intro)
			imagedata = cStringIO.StringIO(urllib2.urlopen(book.previewurl).read())
			image = Image.open(imagedata)
			photo = ImageTk.PhotoImage(image)
			self.bookstore.append((book,photo))
			show_book = Button(self.book_frame,image=photo,command=lambda ch=book:self.progress(ch))
			show_book.grid(ipadx=3,ipady=3,padx=8,pady=8)
			CreateToolTip(show_book,tooltip_text)
			self.book_buttons.append(show_book)
		self.lock.release()
		self.btn.config(state='normal',text = ' 搜  尋 ')
	def ms(self,e,widget=None):
		print widget.yview
		widget.yview('scroll',-1 if e.delta>0 else 1,'units')
	def adjustyview(self,e):
		if e.keysym == 'Down':
			self.canvas.yview('scroll',1,'units')
		elif e.keysym =='Up':
			self.canvas.yview('scroll',-1,'units')
		elif e.keysym == 'Next':
			self.canvas.yview('scroll',6,'units')
		elif e.keysym == 'Prior':
			self.canvas.yview('scroll',-6,'units')
		print e.keysym
comicDownload()

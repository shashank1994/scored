from selenium import webdriver
from bs4 import BeautifulSoup, SoupStrainer
import time, sys, os, difflib, fileinput, re, urllib2, cookielib, json, multiprocessing


if os.path.exists(os.getcwd()+'/seedList.txt'):
	os.remove(os.getcwd()+'/seedList.txt')
if os.path.exists(os.getcwd()+'/issuelist.txt'):
	os.remove(os.getcwd()+'/issuelist.txt')


class scored(object):
	def __init__(self, url, num, input):
		self.driver = webdriver.PhantomJS()
		#.clearCookies()
		#
		self.driver.set_window_size(1024, 768)
		self.driver.get(url)
		self.cj = cookielib.CookieJar()
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
		self.xpages = 10

		if num == 0:
			f = open(input, "r")
			print "Name of the file: ", f.name
			xpath_list = []
			for line in f:
				xpath_list.append(line)
			self.get_journal_list_by_xpath(url, xpath_list)
		elif num == 1:
			class_name = input
			self.get_journal_list_by_classtag(url, class_name)
		else:
			print "Please enter a legal input"

	def get_journal_list_by_xpath(url, xpath_list):

		journalDriver = webdriver.PhantomJS()
		journalDriver.get(url)



		for xpath in xpath_list:
			print xpath.get_attribute('href')
			soup = self.get_page_soup(xpath.get_attribute('href'))
		
			self.get_issues_list(soup, fname)

		self.driver.close()



	def get_html(self, link):
		''' reach html using urllib2 & cookies '''
		try:
			request = urllib2.Request(link)
			response = self.opener.open(request)
			time.sleep(5)
			self.cj.clear()
			return response.read()
		except:
			print 'unable to reach link'
			return False

	def get_page_soup(self, link, strain=None):
		''' return html using BS for a page '''
		print 'in get_page_soup ', link
		#need to check if soup returned or page not reachable
		html = self.get_html(link)

		if html:
			if strain:
				strainer = SoupStrainer(id=strain)
				try:
					return BeautifulSoup(html, parse_only=strainer)
				except:
					return False
			else:
				try:
					return BeautifulSoup(html)
				except:
					return False
		

	def get_issues_list(self, soup, filename, pubHouse=None):
		''' generate issuelist from all issues on a given page'''

		stopwords = ['facebook', 'twitter', 'youtube', 'linkedin', 'membership', 'subscribe', 'subscription', 'blog',\
					 'submit', 'contact', 'listserve', 'login', 'disclaim', 'editor', 'section', 'librarian', 'alert',\
					 '#', 'email', '?', 'copyright', 'license', 'charges', 'terms', 'mailto:', 'submission', 'author',\
					 'media', 'news']
		currLink = ''
		lastURL = ''
		penulURL = ''
		
		for link in soup.find_all('a'):
			if not pubHouse:
				pubHouse = 'http://'+link.get('href').split('http://')[1].split('/')[0]
			
			doi = self.link_has_doi(link.get('href'))

			try:
				allLines = [line.rstrip() for line in open(filename)]
			except:
				allLines = []
			
			with open(filename,'ab+') as f:
				currLink = self.get_link(link.get('href'), pubHouse)
				textDiff = self.compare_text(currLink, allLines)

				if 'issuelist.txt' in filename:
					if currLink.lower().startswith('http') or doi:
						if not(any(word in currLink.lower() for word in stopwords)):
							if textDiff == True:
								f.write('%s\n' %currLink)

							self.iterative_issues(soup, allLines, f, pubHouse)


				elif 'seedList.txt' in filename:
					if currLink.lower().startswith('http') or doi:	
						if not(any(word in currLink.lower() for word in stopwords)):
							if 'abs' in currLink.lower():
								f.write('%s\n' %currLink)
							elif 'full' in currLink.lower():
								if textDiff == True:
									f.write('%s\n' %currLink)
							
							self.iterative_issues(soup, allLines, f, pubHouse)
				else:
					if not(any(word in currLink.lower() for word in stopwords)):
						if textDiff == True:
							f.write('%s\n' %currLink)
							self.iterative_issues(soup, allLines, f, pubHouse)

	def iterative_issues(self, soup, issuelist, f, pubHouse):
		''' keeps diving down on issues pages until article page is reached'''
		print 'in iterative_issues_search: ', issuelist
		issues = []
		allIssuesList = []
		allIssuesList = issuelist 
		issues = issuelist

		volumes = soup.find_all(class_=re.compile("olumes")) #add the all issues option here?
		if volumes:
			for v in volumes:
				links = v.findAll('a')
				for a in links:
					if a.get('href'):
						currLink = self.get_link(a.get('href'),pubHouse)
						textDiff = self.compare_text(currLink, allIssuesList)
						if textDiff == True:
							f.write('%s\n' %currLink)
							issues.append(currLink)
							allIssuesList.append(currLink)
						else:
							textDiff = self.compare_text(currLink, issues)
										
			
	def get_link (self, link, pubHouse):
		''' utility function for generating an absolute link if necessary '''
		if not link.lower().startswith('http'):
			if pubHouse:
				return pubHouse+link
		else:
			return link

	def link_has_doi (self, link):
		''' utility function to check if a link is a doi link '''
		if not link.lower().startswith('http'):
			if 'doi/' in link:
				return True
			elif any([self.is_number(i) for i in link.split('/')]):
				return True
			else:
				return False

	def is_number(self,s):
		''' utility function to check if a string is a decimal number'''
		try:
			float(s)
			if '.' in s:
				return True
			else: 
				return False
		except ValueError:
			return False


	def compare_text(self, url, urlList):
		''' check for link in a urlList '''

		textDiff = ''
		diffList = []

		if urlList == [] or len(urlList) < 2:
			return True

		elif filter(lambda x: url in x, urlList):
			return False

		else:
			for i in urlList:
				textDiff = ''
				for _,s in enumerate(difflib.ndiff(url, i)):
					if s[0] == ' ': continue
					elif s[0] == '+': textDiff += s[2]
				diffList.append(textDiff)
			
			for diff in diffList:
				if diff == None or ('abs' in diff.lower() and len(diff) <= 9):
					return False
				

		return True

	
	def get_articles_list(self, page, issuelist=None):
		''' generate the journals lists from the issues list '''
		
		soup = self.get_page_soup(page)
		fname = 'seedList.txt'
		issues = []
		again = True
		pubHouse = 'http://'+page.split('http://')[1].split('/')[0]
		self.get_issues_list(soup,fname, pubHouse)


	def get_meta_data(self, soup):
		''' get page metadata using BS'''

		metaDict = {}
		authors = []
		pubdate = []
		subject = []
		keywords = []
		format = ''
		fileType = ''
		doiidentifier = ''
		pubidentifier = ''
		source = ''
		title = ''
		rights = ''
		contentType = ''

		try:
			allMeta = soup.findAll('meta')
		except:
			print 'no metaData'
			return False

		for tag in allMeta:
			if tag.get('name'):
				if 'creator' in tag.get('name').lower() or 'author' in tag.get('name').lower():
					authors.append(tag.get('content'))

				if 'type' in tag.get('name').lower():
					fileType = tag.get('content')
				
				if 'subject' in tag.get('name').lower():
					subjet.append(tag.get('content'))

				if 'keyword' in tag.get('name').lower():
					keywords.append(tag.get('content'))

				if 'format' in tag.get('name').lower():
					format = tag.get('content')

				if 'title' in tag.get('name').lower():
					title = tag.get('content')

				if 'source' in tag.get('name').lower():
					source = tag.get('content')

				if 'rights' in tag.get('name').lower():
					rights = tag.get('content')

				if 'date' in tag.get('name').lower():
					pubdate.append(tag.get('content'))
					try:
						pubdate.append(tag.get('scheme'))
					except:
						continue

				if 'identifier' in tag.get('name').lower():
					try:
						if 'doi' in tag.get('scheme').lower():
							doiidentifier = tag.get('content')
					except:
						continue

					try:
						if 'publisher' in tag.get('scheme').lower():
							pubidentifier = tag.get('content')
					except:
						continue

		return {'metaAuthors':authors,
					'date':pubdate,
					'subject':subject,
					'keywords':keywords,
					'format':format,
					'fileType':fileType,
					'doi':doiidentifier,
					'pubid':pubidentifier,
					'source':source,
					'metaTitle':title,
					'rights':rights,
					'contentType':contentType}

	
	def get_full_text(self, page):
		''' Extract the data from a page '''
		metaDict = {}
		contentDict = {}
		abstract = ''
		authors = []
		affilations = []

		soup = self.get_page_soup(page)
		metaDict = self.get_meta_data(soup)

		print 'text from: ', page

		if not os.path.exists(os.getcwd()+'/jsonFilesAMS'):
			os.makedirs(os.getcwd()+'/jsonFilesAMS')

		contentDict['id'] = page

		try:
			for i in soup.find_all(class_=re.compile("^abstr")):
				abstract += i.find('p').text.encode('utf-8')
		except:
			print 'Abstract was not found on this page'

		try:
			title = soup.find_all(class_=re.compile("itle"))
			contentDict['title'] = title.text.encode('utf-8')
		except:
			print 'Title was not found on this page'
			contentDict['title'] = 'Null'

		try:
			ack = soup.find_all(class_=re.compile("cknowledgement"))
			contentDict['acknowledgement'] = ack.text.encode('utf-8')
		except:
			print 'Acknowledgements not found on this page'
			contentDict['acknowledgement'] = 'Null'

		try:
			for x in soup.find_all(class_=re.compile("uthor")):
				try:
					for k in x.find_all('strong'):
						authors.append(k.text.encode('utf-8'))
				except:
					continue
				try:
					y = x.find_all('p')
					if not authors:
						for z in y:
							authors.append(z.text.encode('utf-8'))
					else:
						for z in y:
							affilations.append(z.text.encode('utf-8'))
				except:
					continue
		except:
			print 'Citation Authors info not found on this page'
			contentDict['citation_authors'] = 'Null'

		contentDict['abstract'] = abstract
		contentDict['citation_authors'] = authors
		contentDict['citation_affilations'] = affilations

		if metaDict:
			contentDict.update(metaDict)

		if abstract:
			filenameJSON = os.getcwd()+ '/jsonFilesAMS/'+ page.split('://')[1].replace('/','-').replace('.','-') +'.json'
			
			with open(filenameJSON, 'w+') as f:
				json.dump(contentDict, f)


def main():
	print 'Extracting Data from Journals...'

	ametsocURL = 'http://journals.ametsoc.org'
	aguURL = 'http://agupubs.onlinelibrary.wiley.com/agu'
	journals = scrapeAMSJournal(ametsocURL)
	journals.info_from_ams() 
	#journals = scrapeAMSJournal(aguURL)
	#journals.info_from_agu() 

if __name__ == '__main__':
    main()
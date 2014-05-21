# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin
import urllib2,urllib,cgi, re
import HTMLParser
import xbmcaddon
import json
import traceback
import os
import cookielib
from BeautifulSoup import BeautifulStoneSoup, BeautifulSoup, BeautifulSOAP
import datetime
import sys
import time
import CustomPlayer
import random

try:
	import livetvcaptcha
except: pass

__addon__       = xbmcaddon.Addon()
__addonname__   = __addon__.getAddonInfo('name')
__icon__        = __addon__.getAddonInfo('icon')
addon_id = 'plugin.video.shahidmbcnet'
selfAddon = xbmcaddon.Addon(id=addon_id)
addonPath = xbmcaddon.Addon().getAddonInfo("path")
addonArt = os.path.join(addonPath,'resources/images')
#communityStreamPath = os.path.join(addonPath,'resources/community')
communityStreamPath = os.path.join(addonPath,'resources')
communityStreamPath =os.path.join(communityStreamPath,'community')

COOKIEFILE = communityStreamPath+'/livePlayerLoginCookie.lwp'
profile_path =  xbmc.translatePath(selfAddon.getAddonInfo('profile'))

def PlayStream(sourceEtree, urlSoup, name, url):
	try:
		playpath=urlSoup.chnumber.text
		pDialog = xbmcgui.DialogProgress()
		pDialog.create('XBMC', 'Communicating with Livetv')
		pDialog.update(40, 'Attempting to Login')
		
		retryPlay=True
		while retryPlay:
			retryPlay=False
			liveTvPremiumCode=selfAddon.getSetting( "liveTvPremiumCode" )
			liveTvNonPremiumCode=selfAddon.getSetting( "liveTvNonPremiumCode" )
			lastWorkingCode=selfAddon.getSetting( "lastLivetvWorkingCode" )
			usingLastWorkingCode=False
			disableFreeForNow=True# Tick tock tick tock.. you were lucking that you didn't play the game. but no more games anymore :(
			#dont worry, its still disable
			if liveTvPremiumCode=="":
				if lastWorkingCode=="" and liveTvNonPremiumCode=="":
					timeD = 2000  #in miliseconds
					line1="Login disabled, use Non Premium code"
					xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(__addonname__,line1, timeD, __icon__))
					return False
				if lastWorkingCode=="" and liveTvNonPremiumCode=="" : #stop free account
					if shouldforceLogin():
						print 'performing login'
						if not performLogin():
							timeD = 1000  #in miliseconds
							line1="Login failed-still trying"
							xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(__addonname__,line1, timeD, __icon__))
						else:
							
							print 'login worked!'

					else:
						print 'not performing login, reusing cache'
					code=getcode();
					if code==None:
							timeD = 2000  #in miliseconds
							line1="Unable to get the code-livetv down? or something changed"
							xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(__addonname__,line1, timeD, __icon__))
							return False
				else:
					print 'using last working code',lastWorkingCode
					if not lastWorkingCode=="":
						code=lastWorkingCode
						usingLastWorkingCode=True
					else:
						code=liveTvNonPremiumCode
					
			else:
				print 'using premium code',lastWorkingCode
				code=liveTvPremiumCode

			print 'firstCode',code
			


			liveLink= sourceEtree.findtext('rtmpstring')
			pDialog.update(80, 'Login Completed, now playing')
			print 'rtmpstring',liveLink
			if liveTvPremiumCode=="":
				liveLink=liveLink%(playpath,code)
				#liveLink="rtmp://tdsiptv.ddns.me/live/%s?code=%s"%(playpath,code)
			else:
				liveLink="rtmp://tdsiptv.ddns.me/live/%s?code=%s"%(playpath,liveTvPremiumCode)
			name+='-LiveTV'
			print 'liveLink',liveLink
			listitem = xbmcgui.ListItem( label = str(name), iconImage = "DefaultVideo.png", thumbnailImage = xbmc.getInfoImage( "ListItem.Thumb" ), path=liveLink )
			pDialog.close()
			player = CustomPlayer.MyXBMCPlayer()
			start = time.time()
			#xbmc.Player().play( liveLink,listitem)
			player.play( liveLink,listitem)
			while player.is_active:
				xbmc.sleep(200)
			#return player.urlplayed
			#done = time.time()
			done = time.time()
			elapsed = done - start
			if player.urlplayed and elapsed>=3:
				selfAddon.setSetting( id="lastLivetvWorkingCode" ,value=code)
				return True
			else:
				selfAddon.setSetting( id="lastLivetvWorkingCode" ,value="")
				retryPlay=usingLastWorkingCode
		return False
	except:
		traceback.print_exc(file=sys.stdout)    
	return False    

codepages=['http://www.livetv.tn/2M-Maroc-en-direct-live.html','http://www.livetv.tn/Al-Masria-en-direct-live.html','http://www.livetv.tn/Al-Shar9ia-en-direct-live.html','http://www.livetv.tn/Al-Maghrebia-en-direct-live.html','http://www.livetv.tn/Al-Sumaria-en-direct-live.html','http://www.livetv.tn/MBC-4-en-direct-live.html']
codepage=random.choice(codepages)

def getcode():
	try:
		#url = urlSoup.url.text
		print 'codepage',codepage
		cookieJar=getCookieJar()
		link=getUrl(codepage,cookieJar)
		link=javascriptUnEscape(link)
		captcha=None
		originalcaptcha=False
		match =re.findall('<img src=\"(\/simple-php-captcha\.php\?_CAPTCHA\&.*?)\">', link) #keep doing it :), you think i will get bored? lols
		if len(match)>0:
			captcha="http://www.livetv.tn"+match[0]
		else:
			#print link
			captcha=None
			if 'capimg.php?do=show' in link:
				match='capimg.php?do=show'
			#match =re.findall('<img src="(.*?)"/>', link) #keep doing it :), you think i will get bored? lols
			if len(match)>0:
				captcha="http://www.livetv.tn/"+match
				originalcaptcha=True
		
		solution=None

		if captcha:
			local_captcha = os.path.join(profile_path, "captchaC.img" )
			localFile = open(local_captcha, "wb")
			print ' c capurl',captcha
			localFile.write(getUrl(captcha,cookieJar))
			localFile.close()
			cap="";#cap=parseCaptcha(local_captcha)
			if originalcaptcha:
				cap=parseCaptcha(local_captcha)
			print 'parsed cap',cap
			if cap=="":
				solver = InputWindow(captcha=local_captcha)
				solution = solver.get()
			else:
				solution=cap



		if solution:
			#do captcha post
			
			postVar=re.findall('input\s*.*name=\"(.*?)\".*autof', link)[0]#on man! find something which is not possible in python!
																		#if you think i would give up due to changes... then you don't know me
																		#hint! dont focus on the addon, focus on your setup, there are better ways to defeat me!
																		# let me know if you need help!
			postVar2=re.findall('input type=\"text\" name=\"(.*?)\"', link) #additional textbox
			post={postVar:solution}
			print 'pst',post
			if len(postVar2)>0:
				if postVar2[0] not in post:
					post[postVar2[0]]=""
			print 'pst',post
			post = urllib.urlencode(post)

			#ck = cookielib.Cookie(version=0, name='name', value='value', port=None, port_specified=False, domain='www.livetv.tn', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
			#cookieJar.set_cookie(ck)
			#for index, cookie in enumerate(cookieJar):
			#	print index, ' : ', cookie
			headers=[('Referer',codepage)]
			#post
			postPage=re.findall('<form .*?action=\"(.*?)\"', link)
			if postPage and len(postPage)>0 and len(postPage[0]):
				postPage=postPage[0]
				if not postPage.startswith("http"):
					if postPage.startswith('/'):
						postPage=('http://www.livetv.tn'+postPage) ## You only going to make this perfect haha
					else:
						postPage=('http://www.livetv.tn/'+postPage) ## i will follow you, so keep doing it
			else:
				postPage=codepage
                
			print 'postPage',postPage

			link=getUrl(postPage,cookieJar,post,headers=headers)
			if link=="":
				link=getUrl(codepage,cookieJar)
			link=javascriptUnEscape(link)
		code =re.findall('code=(.*?)[\'\"]', link)
		if (not code==None) and len(code)>0:
			#print 'print link is ',link
			code=code[0]
			return code
		else:
			print link
			return None
	except:
		traceback.print_exc(file=sys.stdout)
	return None

def javascriptUnEscape(str):
	js=re.findall('unescape\(\'(.*?)\'',str)
	print 'js',js
	if (not js==None) and len(js)>0:
		for j in js:
			print urllib.unquote(j)
			str=str.replace(j ,urllib.unquote(j))
	return str

def parseCaptcha(filePath):
	retVal=""
	try:

		retVal=livetvcaptcha.getString(filePath)
		print 'the captcha val is',retVal
	except:  traceback.print_exc(file=sys.stdout)
	return retVal
def getUrl(url, cookieJar=None,post=None, timeout=20, headers=None):


	cookie_handler = urllib2.HTTPCookieProcessor(cookieJar)
	opener = urllib2.build_opener(cookie_handler, urllib2.HTTPBasicAuthHandler(), urllib2.HTTPHandler())
	#opener = urllib2.install_opener(opener)
	req = urllib2.Request(url)
	req.add_header('User-Agent','Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.154 Safari/537.36')
	if headers:
		for h,hv in headers:
			req.add_header(h,hv)

	response = opener.open(req,post,timeout=timeout)
	link=response.read()
	response.close()
	return link;

    
def getCookieJar():
	cookieJar=None
	


	try:
		cookieJar = cookielib.LWPCookieJar()
		cookieJar.load(COOKIEFILE,ignore_discard=True)
	except: 
		cookieJar=None
	
	if not cookieJar:
		cookieJar = cookielib.LWPCookieJar()
	
	return cookieJar

	
def performLogin():
	cookieJar=getCookieJar()
	
	html_text=getUrl("http://www.livetv.tn/login.php",cookieJar)
	

	if 1==2: #future planning
		postPage=re.findall('<form .*?action=\"(.*?)\"', html_text)
		if postPage and len(postPage)>0 and len(postPage[0]):
			postPage=postPage[0]
			if not postPage.startswith("http"):
				if postPage.startswith('/'):
					postPage=('http://www.livetv.tn'+postPage) ## You only going to make this perfect haha
				else:
					postPage=('http://www.livetv.tn/'+postPage) ## i will follow you, so keep doing it
		else:
			postPage='http://www.livetv.tn/login.php'
				
	
	cookieJar.save (COOKIEFILE,ignore_discard=True)
	print 'cookie jar saved',cookieJar

	if 1==2: #old captcha
		if 'capimg.php?do=show' in html_text:
		#match =re.findall('src=\"(capimg.*?)\"\/', html_text)
			match=['capimg.php?do=show']
		if len(match)>0:
			captcha="http://www.livetv.tn/"+match[0]
		else:
			captcha=None
		

			
		if captcha:
			local_captcha = os.path.join(profile_path, "captcha.img" )
			localFile = open(local_captcha, "wb")
			print 'capurl',captcha
			localFile.write(getUrl(captcha,cookieJar))
			localFile.close()
			cap=parseCaptcha(local_captcha)
			print 'login parsed cap',cap

			if 1==2:#cap=="" or not len(cap)==4:
				solver = InputWindow(captcha=local_captcha)
				solution = solver.get()
			else:
				solution=cap

				
	

	recapChallenge=""
	solution=""
	cap_reg="<iframe src=\"(.*?noscript\?.*?)\&?\""
	match =re.findall(cap_reg, html_text)
	captcha=False
	if match and len(match)>0: #new shiny captcha!
		captcha_url=match[0]
		captcha=True
		
		cap_chall_reg='recaptcha_challenge_field\" value=\"(.*?)\"'
		cap_image_reg='<img.*?src=\"(.*?)\"'
		captcha_script=getUrl(captcha_url)
		recapChallenge=re.findall(cap_chall_reg, captcha_script)[0]
		captcha_image_url=re.findall(cap_image_reg, captcha_script)[0]
		if not captcha_image_url.startswith("http"):
			captcha_image_url='http://www.google.com/recaptcha/api/'+captcha_image_url
		local_captcha = os.path.join(profile_path, "captcha.img" )
		localFile = open(local_captcha, "wb")
		localFile.write(getUrl(captcha_image_url))
		localFile.close()
		solver = InputWindow(captcha=local_captcha)
		solution = solver.get()
	
	
	if solution or captcha==None:

		print 'performing login'
		userName=selfAddon.getSetting( "liveTvLogin" )
		password=selfAddon.getSetting( "liveTvPassword")
		if captcha:
			post={'pseudo':userName,'epass':password,'recaptcha_challenge_field':recapChallenge,'recaptcha_response_field':solution}
		else:
			post={'pseudo':userName,'epass':password}
		print 'post',post
		post = urllib.urlencode(post)
		
		postpage=re.findall('<form.?action=\"(.*?)\"',html_text)
		
		link=getUrl(postpage[0],cookieJar,post)
		
		return shouldforceLogin(cookieJar, link)==False
	else:
		return False


def shoudforceLogin2():
    try:
#        import dateime
        lastUpdate=selfAddon.getSetting( "lastLivetvLogin" )
        print 'lastUpdate',lastUpdate
        do_login=False
        now_datetime=datetime.datetime.now()
        if lastUpdate==None or lastUpdate=="":
            do_login=True
        else:
            print 'lastlogin',lastUpdate
            try:
                lastUpdate=datetime.datetime.strptime(lastUpdate,"%Y-%m-%d %H:%M:%S")
            except TypeError:
                lastUpdate = datetime.datetime.fromtimestamp(time.mktime(time.strptime(lastUpdate, "%Y-%m-%d %H:%M:%S")))
        
            t=(now_datetime-lastUpdate).seconds/60
            print 'lastUpdate',lastUpdate,now_datetime
            print 't',t
            if t>15:
                do_login=True
        print 'do_login',do_login
        return do_login
    except:
        traceback.print_exc(file=sys.stdout)
    return True

def shouldforceLogin(cookieJar=None, currentPage=None):
    try:
        url=codepage
        if not cookieJar:
            cookieJar=getCookieJar()
        if currentPage==None:
            html_txt=getUrl(url,cookieJar)
        else:
            html_txt=currentPage
            print 'html_txt',currentPage
            
        if '<a  href="http://www.livetv.tn/login.php">' in html_txt:
            return True
        else:
            return False
    except:
        traceback.print_exc(file=sys.stdout)
    return True
    
class InputWindow(xbmcgui.WindowDialog):
    def __init__(self, *args, **kwargs):
        self.cptloc = kwargs.get('captcha')
        self.img = xbmcgui.ControlImage(335,30,624,80,self.cptloc)
        self.addControl(self.img)
        self.kbd = xbmc.Keyboard()

    def get(self):
        self.show()
        time.sleep(3)        
        self.kbd.doModal()
        if (self.kbd.isConfirmed()):
            text = self.kbd.getText()
            self.close()
            return text
        self.close()
        return False

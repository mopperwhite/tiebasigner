#!/usr/bin/env python
#encoding=UTF-8
#  
#  Copyright 2014 MopperWhite <mopperwhite@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

#~ from PyQt4.QtGui import QApplication
#~ from PyQt4.QtCore import QObject,QUrl,QString,SIGNAL,QObject
#~ from PyQt4.QtWebKit import QWebView
#~ from PyQt4.QtNetwork import QNetworkCookieJar,QNetworkCookie
import cookielib,os,time,urllib2,urllib,json,re,random,sys
import BeautifulSoup as BS
from xml.etree import ElementTree as ET
from colorama import Fore,Style
import yaml
HEADER={
                "Accept":"text/html,*/*;q=0.8",
#                "Accept-Encoding":"gzip,deflate,sdch",
                "Accept-Language":"zh-CN,zh;q=0.8",
                "Cache-Control":"max-age=0",
                "Connection":"keep-alive",
                "Host":"tb.himg.baidu.com",
                "Referer":None,
                "User-Agent":"Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36",
                }
TIME_OUT=20
def urlopen(url,cookiejar=None,sleeping_time=0):
        header={
"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
#"Accept-Encoding":"gzip,deflate,sdch",
"Accept-Language":"zh-CN,zh;q=0.8",
"Connection":"keep-alive",
"User-Agent":"Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36",
}
        req = urllib2.Request(url,None,header)
        if cookiejar is None:
                opener=urllib2.build_opener()
        else:
                opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))
        return opener.open(req,None,TIME_OUT)
        time.sleep(sleep_time)
def post_url(url,cookiejar,post_dict,referer=""):
        header={
"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
"Accept-Encoding":"deflate,sdch",
"Accept-Language":"zh-CN,zh;q=0.8",
"Connection":"keep-alive",
"User-Agent":"Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36",
}
        d=urllib.urlencode(post_dict)
        req = urllib2.Request(url,None,header)
        opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))
        return opener.open(req,d,TIME_OUT)
        
        

def get_username(cookie_file):
        mcj=cookielib.MozillaCookieJar(cookie_file)
        mcj.load()
        soup=BS.BeautifulSoup(urlopen("http://wapp.baidu.com/",mcj).read())
        if soup.body.div.text==u'登录&#160;注册':
                raise Exception("Not logged in yet.")
        else:
                return re.search(u"(.*)的i贴吧",soup.body.div.text).group(1)

def check_login(cookie_file):
        mcj=cookielib.MozillaCookieJar(cookie_file)
        mcj.load()
        soup=BS.BeautifulSoup(urlopen("http://wapp.baidu.com/",mcj).read())
        #~ print soup.body.div.text
        if soup.body.div.text==u'登录&#160;注册':
                return None
        else:
                return mcj
#~ def initial_login(cookie_file):
        #~ app=QApplication([])
        #~ window=LoginWebView("http://passport.baidu.com",cookie_file)
        #~ window.login()
        #~ app.exec_()
        #~ return window.cookiejar
def login(cookie_file):
        if os.path.exists(cookie_file):
                check=check_login(cookie_file)
                if check is not None:
                        return check
        return None
        #~ return initial_login(cookie_file)

def sign_all_tieba(name,cj):
        logging=yaml.load(open("logging.yaml"))
        if name not in logging:
                logging[name]={}
        today=time.strftime("%Y%m%d")
        if today not in logging[name]:
                logging[name][today]=[]
        mainsoup=BS.BeautifulSoup(urlopen("http://tieba.baidu.com/mo/q---D911C290B25D3B4777AC40593A557281%3AFG%3D1--1-3-0--2--wapp_1404445098952_929/m?tn=bdFBW",cj).read())
        table=mainsoup.find("table",{"class":"tb"})
        l=table.findAll("tr")
        for i in range(len(l)):
                t=l[i]
                if t.td.a.text in logging[name][today]:
                        print t.td.a.text,"(%d/%d)"%(i+1,len(l)),Fore.GREEN,u"\t[已签过]",Fore.WHITE
                else:
                        print t.td.a.text,"(%d/%d)"%(i+1,len(l)),"..."
                        url="http://tieba.baidu.com/mo/"+t.td.a.get("href")
                        sub_soup=BS.BeautifulSoup(urlopen(url,cj).read())
                        div=sub_soup.find("div",{"class":"bc"})
                        if div is None:
                                print Fore.RED+u"\t\t[失踪]"+Fore.WHITE
                                continue
                        td=div.find("td",{"style":"text-align:right;"})
                        if td is None:
                                print Fore.RED+u"\t\t[失败.](可能不是会员)"+Fore.WHITE
                                i=0
                        elif td.text==u"已签到":
                                print Fore.GREEN+u"\t\t[已签到.]"+Fore.WHITE
                                #~ print sub_soup.body.div.div.table.tr.td.a.text
                                logging[name][today].append(t.td.a.text)
                                i=random.randint(2,3)
                        else:
                                urlopen("http://tieba.baidu.com"+td.a.get("href"),cj)
                                i=random.randint(3,5)
                                print Fore.GREEN+u"\t\t[成功!]"+Fore.WHITE
                                #~ print sub_soup.body.div.div.table.tr.td.a.text
                                logging[name][today].append(t.td.a.text)
                        if td is not None:
                                print u'                <'+re.search(ur"\(等级(\d+?)\)$",sub_soup.body.div.div.tr.td.text).group(1)+u'级>'
                        print  u"\t\t等待...",i,u"秒"
                        time.sleep(i)
                yaml.safe_dump(logging,open("logging.yaml",'w'),default_flow_style=False,allow_unicode=True)

if __name__=='__main__':
        dt=yaml.load(open("usernames.yaml"))
        l=dt["usernames"]
        if not os.path.exists("logging.yaml"):
                print "Logging file built."
                yaml.safe_dump({},open("logging.yaml",'w'),default_flow_style=False,allow_unicode=True)
        l_=[]
        for name in l:
                print "Logging in",Style.BRIGHT+name+Style.NORMAL,"...",
                cookiefile=dt["dir"]+os.sep+name+".cookies"
                cookie=login(cookiefile)
                if cookie is None:
                        print Fore.RED,u'[失败]',Fore.WHITE
                else:
                        print Fore.GREEN,u'[成功]',Fore.WHITE
                        l_.append((name,cookie))
        for i in range(len(l_)):
                name,cookie=l_[i]
                print Style.BRIGHT+u"正在处理",name,"(%d/%d)"%(i+1,len(l_))+Style.NORMAL
                #~ cookiefile="cookies/"+name+".cookies"
                #~ cookie=login(cookiefile)
                sign_all_tieba(name,cookie)

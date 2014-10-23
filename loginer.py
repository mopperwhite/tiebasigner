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

from PyQt4.QtGui import QApplication,QWidget,QPushButton,QHBoxLayout,QVBoxLayout,QMessageBox,QListWidget,QListWidgetItem,QDialog,QLabel,QLineEdit,QColor,QProgressDialog
from PyQt4.QtCore import QObject,QUrl,QString,SIGNAL,Qt,QDateTime,QThread,pyqtSignal,pyqtSlot,SLOT
from PyQt4.QtWebKit import QWebView
from PyQt4.QtNetwork import QNetworkCookieJar,QNetworkCookie
import cookielib,os,time,urllib2,urllib,json,re,random,gzip
import yaml
from StringIO import StringIO
import BeautifulSoup as BS
from xml.etree import ElementTree as ET
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

class LoginWebView(QWebView):
        def __init__(self,url,cookie_file,parent=None):
                super(QWebView,self).__init__(parent)
                self._url=url
                self._cookie_file=cookie_file
        def login(self):
                if not os.path.exists(self._cookie_file):
                        self.__qncj=QNetworkCookieJar()
                else:
                        self.__qncj=self._MozillaCookieJar_to_QnetworkCookieJar(self._cookie_file)
                self.page().networkAccessManager().setCookieJar(self.__qncj)
                self.setUrl(QUrl(self._url))
                self.show()
        def getcookiejar(self):
                self.cookiejar=self._QNetworkCookieJar_to_MozillaCookieJar(self.__qncj,self._cookie_file)
                return self.cookiejar
        @staticmethod
        def _QNetworkCookieJar_to_MozillaCookieJar(qncj,cookie_file):
                f=open(cookie_file,'w')
                print >>f,"# Netscape HTTP Cookie File"
                print >>f,"# http://curl.haxx.se/rfc/cookie_spec.html"
                print >>f,"# This is a generated file!  Do not edit."
                print >>f
                for c in qncj.allCookies():
                        domain=unicode(QString(c.domain()))
                        initial_dot=unicode(domain.startswith(".")).upper()
                        path=unicode(QString(c.path()))
                        isSecure=str(c.isSecure()).upper()
                        expires=unicode(c.expirationDate().toTime_t())
                        name=unicode(QString(c.name()))
                        value=unicode(QString(c.value()))
                        print >>f, "\t".join([ domain,initial_dot,path,isSecure,expires,name,value ])
                f.close()
                mcj=cookielib.MozillaCookieJar(cookie_file)
                mcj.load()
                return mcj
        @staticmethod
        def _MozillaCookieJar_to_QnetworkCookieJar(cookie_file):
                def line2qcookie(line):
                        domain,initial_dot,path,isSecure,expires,name,value=line.split()
                        isSecure=(isSecure=="TRUE")
                        dt=QDateTime()
                        dt.setTime_t(int(expires))
                        expires=dt
                        c=QNetworkCookie()
                        c.setDomain(domain)
                        c.setPath(path)
                        c.setSecure(isSecure)
                        c.setExpirationDate(expires)
                        c.setName(name)
                        c.setValue(value)
                        return c
                cj=QNetworkCookieJar()
                if os.path.exists(cookie_file):
                        cj.setAllCookies([line2qcookie(line) for line in open(cookie_file)  if not line.startswith("#") and line and not line.isspace()])
                        #~ print cj.allCookies()
                else:
                        raise IOError("File not found: %s"%cookie_file)
                return cj
                
class LoginWindow(QDialog):
        def __init__(self,url,cookiefile,parent=None):
                super(QDialog,self).__init__(parent)
                self.setWindowTitle(u"编辑Cookies")
                self.cookiejar=None
                self.layout=QVBoxLayout(self)
                self.menu_layout=QHBoxLayout()
                #~ self.messagebox=QMessageBox(self)
                
                self.ok_button=QPushButton(u"完成")
                self.cancel_button=QPushButton(u"取消")
                
                self.layout.addLayout(self.menu_layout)
                self.view=LoginWebView(url,cookiefile)
                self.view.login()
                self.layout.addWidget(self.view)
                
                self.menu_layout.addWidget(self.ok_button)
                self.menu_layout.addWidget(self.cancel_button)
                
                QObject.connect(self.ok_button,SIGNAL("clicked()"),self.ok)
                QObject.connect(self.cancel_button,SIGNAL("clicked()"),self.cancel)
                #~ QObject.connect(self,SIGNAL("closed()"),self.cancel)

        def ok(self):
                self.cookiejar=self.view.getcookiejar()
                self.close()
        def cancel(self):
                self.close()
        
        def login(self):
                self.exec_()
                return self.cookiejar
                

class LoginListWindow(QDialog):
        class _Dialog(QDialog):
                def __init__(self,parent=None):
                        super(QDialog,self).__init__(parent)
                        self.value=''
                        self.edit=QLineEdit()
                        self.layout=QHBoxLayout(self)
                        self.button_layout=QVBoxLayout()
                        self.setWindowTitle(u"输入名字")
                        self.ok_button=QPushButton(u"确定")
                        self.cancel_button=QPushButton(u"取消")
                        self.layout.addWidget(self.edit)
                        self.layout.addLayout(self.button_layout)
                        self.button_layout.addWidget(self.ok_button)
                        self.button_layout.addWidget(self.cancel_button)
                        QObject.connect(self.ok_button,SIGNAL("clicked()"),self.ok)
                        QObject.connect(self.cancel_button,SIGNAL("clicked()"),self.close)
                def ok(self):
                        self.value=unicode(self.edit.text())
                        self.close()
                def getvalue(self,value):
                        self.value=value
                        self.edit.setText(value)
                        self.exec_()
                        return self.value
        class _Item(QListWidgetItem):
                def __init__(self,name,url,cookiefile=None,parent=None):
                        super(QListWidgetItem,self).__init__(name,parent)
                        #~ super(QObject,self).__init__(parent)
                        self.loggedin=False
                        #~ print name,cookiefile
                        self.cookiefile=cookiefile=name+".cookies" if cookiefile is None else cookiefile
                        self.name=name
                        self.cookiejar=None
                        self.view=LoginWindow(url,cookiefile)
                        self.view.setWindowTitle(u"登录:"+name)
                        self.dialog=LoginListWindow._Dialog(parent)
                        self.show_msg=pyqtSlot(unicode,unicode)
                        #~ self.connect(self,SIGNAL("show_msg(unicode,unicode)"),self,SLOT("showMessage(unicode,unicode)"))
                def login(self):
                        #~ print True
                        #~ self.emit(SIGNAL("send_msg"),u"logging")
                        self.showLogging()
                        #~ print self.cookiefile
                        cj=check_login(self.cookiefile)
                        if cj is None:
                                cj=self.view.login()
                        uname=get_username_by_cookiejar(cj,ignore=True)
                        if uname:
                                self.showSecceeded("%s<%s>"%(self.name,uname))
                                #~ self.emit(SIGNAL("send_msg"),u"succeeded",u"%s<%s>"%(self.name,uname))
                                self.loggedin=True
                                self.cookiejat=cj
                                return cj
                        else:
                                self.showFailed()
                                #~ self.emit(SIGNAL("send_msg"),u"failed")
                                return None
                def editName(self):
                        self.name=self.dialog.getvalue(self.name)
                        self.setText(self.name)
                        return self.name
                def editCookies(self):
                        self.cookiejar=self.view.login()
                        return self.cookiejar
                @pyqtSlot(unicode,unicode)
                def showMessage(self,type_,name):
                        print type_
                        {
                                'logging':self.showLogging,
                                'secceeded':self.showSecceeded,
                                'failed':self.showFailed,
                        }[type_](name)
                def showLogging(self,name=None):
                        self.setText((name if name is not None else self.name)+u"[登录中]")
                        self.setTextColor(QColor("yellow"))
                def showSecceeded(self,name=None):
                        self.setText((name if name is not None else self.name)+u"[成功]")
                        self.setTextColor(QColor("green"))
                def showFailed(self,name=None):
                        self.setText((name if name is not None else self.name)+u"[失败]")
                        self.setTextColor(QColor("red"))
        class _Thread(QThread):
                def __init__(self,func,*args,**kwargs):
                        self.func=func
                        self.args=args
                        self.kwargs=kwargs
                        super(QThread,self).__init__(None)
                def run(self):
                        self.func(*self.args,**self.kwargs)
                
                
        def __init__(self,url,dirpath=None,parent=None):
                super(QDialog,self).__init__(parent)
                if dirpath is not None and not os.path.exists(dirpath):os.mkdir(dirpath)
                self.url=url
                
                self.progress_dialog=QProgressDialog()
                self.progress_dialog.setWindowTitle(u"登录中")
                self.progress_dialog.setLabelText(u"登录中")
                self.loading_dialog=QDialog(self)
                
                self.dirpath=dirpath
                self.list=QListWidget()
                self.layout=QHBoxLayout(self)
                self.button_layout=QVBoxLayout()
                self.layout.addWidget(self.list)
                self.layout.addLayout(self.button_layout)
                self.add_button=QPushButton(u"添加")
                self.edit_name_button=QPushButton(u"设置名字")
                self.edit_cookies_button=QPushButton(u"设置Cookies")
                self.delete_button=QPushButton(u"删除")
                self.refresh_button=QPushButton(u"刷新")
                self.button_layout.addWidget(self.add_button)
                self.button_layout.addWidget(self.delete_button)
                self.button_layout.addWidget(self.refresh_button)
                self.button_layout.addWidget(self.edit_name_button)
                self.button_layout.addWidget(self.edit_cookies_button)
                QObject.connect(self.add_button,SIGNAL("clicked()"),self._add)
                QObject.connect(self.edit_name_button,SIGNAL("clicked()"),self.edit_name)
                QObject.connect(self.edit_cookies_button,SIGNAL("clicked()"),self.edit_cookies)
                QObject.connect(self.delete_button,SIGNAL("clicked()"),self._delete)
                QObject.connect(self.refresh_button,SIGNAL("clicked()"),self.login)
                #~ self.load()
        def edit_name(self):
                return [i.editName() for i in self.list.selectedItems()]
        def edit_cookies(self):
                return [i.editCookies() for i in self.list.selectedItems()]
        def login(self):
                return [self.list.item(i).login() for i in self.progress_iter(range(self.list.count()),u"登录")]
        def _add(self):
                self.add(self._Dialog(self).getvalue(unicode(self.list.count())),login=True)
        def _delete(self):
                i=self.list.currentRow()
                item=self.list.takeItem(i)
                if os.path.exists(item.cookiefile):
                        os.remove(item.cookiefile)
                
        def add(self,name,cookiefile=None,login=False):
                item=LoginListWindow._Item(name,self.url,('' if self.dirpath is None else self.dirpath+os.sep)+name+".cookies" if cookiefile is None else cookiefile)
                self.list.addItem(item)
                if login:
                        item.login()
        def load(self,list_=None,dir_=None):
                dir_=self.dirpath if dir_ is None else dir_
                list_=os.listdir(dir_) if list_ is None else list_
                for f in self.progress_iter(list_,u'载入文件'):
                        p=dir_+os.sep+f+".cookies"
                        n=os.path.splitext(f)[0]
                        self.add(n,p)
                self.login()
                #~ print list(self)
        def load_from_yaml(self,yaml_file,dir_=None):
                dt=yaml.load(open(yaml_file))
                self.load(dt["usernames"],dt["dir"])
        def load_asynchronously(self,dir_=None):
                self.thread=self._Thread(self.load,dir_)
                #~ print True
                self.thread.start()
        def progress_iter(self,list_,title=u'更新中'):
                len_=len(list_)
                self.loading_dialog.setWindowTitle(title)
                self.progress_dialog.setWindowTitle(title)
                self.progress_dialog.setLabelText(title)
                self.progress_dialog.setMaximum(len_)
                self.progress_dialog.show()
                #~ self.loading_dialog.show()
                #~ self.loading_dialog.close()
                for i in xrange(len_):
                        self.progress_dialog.setValue(i+1)
                        self.progress_dialog.show()
                        #~ print i,'/',len_
                        yield list_[i]
                self.progress_dialog.close()
        def load_and_show(self,list_=None,dir_=None):
                self.load(list_,dir_)
                self.show()
        def __iter__(self):
                return ( re.search(r"^(.+?)(<.*>)?(\[.*\])?$",unicode(self.list.item(i).text())).group(1) for i in range(self.list.count()))
        #~ def __dict__(self):
                #~ return { self.list.item(i).name:self.list.item(i).cookiejar for i in range(self.list.count())}


class YamlLoginWindow(LoginListWindow):
        def __init__(self,url,yaml_file,parent=None):
                self.yaml_file=yaml_file
                data=yaml.load(open(yaml_file))
                LoginListWindow.__init__(self,url,data["dir"],parent)
        def save(self):
                yaml.safe_dump(
                                dict(
                                        dir=self.dirpath,
                                        usernames=list(self),
                                )
                                ,open(self.yaml_file,'w'),allow_unicode=True,default_flow_style=False)
        def closeEvent(self,ev):
                self.save()
        def load(self,list_=None,dir_=None):
                #~ dir_=self.dirpath if dir_ is None else dir_
                list_=yaml.load(open(self.yaml_file))["usernames"] if list_ is None else list_
                LoginListWindow.load(self,list_,dir_)



def urlopen(    url,
                        cookiejar=None,
                        sleeping_time=0,
                        post={},
                        get={},
                        header={
                                "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                                #"Accept-Encoding":"gzip,deflate,sdch",
                                "Accept-Language":"zh-CN,zh;q=0.8",
                                "Connection":"keep-alive",
                                "User-Agent":"Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36",
                                },
                        gzip_=False,
                        ):
        if get:
                getd=urllib.urlencode(get)
                url+=('' if url.endswith("?") else "?")+getd
        postd=urllib.urlencode(post)
        req = urllib2.Request(url,None,header)
        if cookiejar is None:
                opener=urllib2.build_opener()
        else:
                opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))
        
        if gzip_:
                ufile=opener.open(req,postd,TIME_OUT)
                fileobj=StringIO()
                fileobj.write(ufile.read())
                fileobj.seek(0)
                gzip_file = gzip.GzipFile(fileobj=fileobj)
                return gzip_file
        else:
                return opener.open(req,postd,TIME_OUT)     


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

def get_username_by_cookiejar(cookiejar,ignore=False):
        soup=BS.BeautifulSoup(urlopen("http://wapp.baidu.com/",cookiejar).read())
        if soup.body.div.text==u'登录&#160;注册':
                if ignore:
                        return None
                else:
                        raise Exception("Not logged in yet.")
        else:
                return re.search(u"(.*)的i贴吧",soup.body.div.text).group(1)

def check_login(cookie_file):
        if not os.path.exists(cookie_file):return None
        mcj=cookielib.MozillaCookieJar(cookie_file)
        mcj.load()
        soup=BS.BeautifulSoup(urlopen("http://wapp.baidu.com/",mcj).read())
        print soup.body.div.text
        if soup.body.div.text==u'登录&#160;注册':
                return None
        else:
                return mcj



def check_login_by_cookiejar(cj):
        soup=BS.BeautifulSoup(urlopen("http://wapp.baidu.com/",cj).read())
        if soup.body.div.text==u'登录&#160;注册':
                return None
        else:
                return re.search(u"(.*)的i贴吧",soup.body.div.text).group(1)

def initial_login(cookie_file):
        app=QApplication([])
        window=LoginWebView("http://passport.baidu.com",cookie_file)
        window.login()
        app.exec_()
        return window.cookiejar
def login(cookie_file):
        if os.path.exists(cookie_file):
                check=check_login(cookie_file)
                if check is not None:
                        return check
        return initial_login(cookie_file)

def wap_submit_co(kz,cookiejar,text):
        page_url="http://tieba.baidu.com/mo/q---D911C290B25D3B4777AC40593A557281%3AFG%3D1--1-3-0----wapp_1404445098952_929/m?kz="+str(kz)
        submit_url="http://tieba.baidu.com/mo/q---D911C290B25D3B4777AC40593A557281%3AFG%3D1--1-3-0--2--wapp_1404445098952_929/submit"
        pagedata=urlopen(page_url,cookiejar).read()
        soup=BS.BeautifulSoup(pagedata)
        form=soup.find("form",{"method":"post"})
        post_dict=[(h.get("name"),h.get("value").encode("utf-8")) for h in form.findAll("input",{"type":"hidden"})]
        post_dict.append(("co",text.encode("utf-8")))
        post_dict.append(("sub1",u"回贴".encode("utf-8")))
        return post_url(submit_url,cookiejar,post_dict,page_url)

def reply_wap_reply(kz,pid,cookiejar,text):
        page_url="http://tieba.baidu.com/mo/q---D911C290B25D3B4777AC40593A557281%%3AFG%%3D1--1-3-0--2--wapp_1404445098952_929/flr?pid=%s&kz=%s"%(pid,kz)
        submit_url="http://tieba.baidu.com/mo/q---D911C290B25D3B4777AC40593A557281%3AFG%3D1--1-3-0--2--wapp_1404445098952_929/submit"
        pagedata=urlopen(page_url,cookiejar).read()
        soup=BS.BeautifulSoup(pagedata)
        form=soup.find("form",{"method":"post"})
        post_dict=[(h.get("name"),h.get("value").encode("utf-8")) for h in form.findAll("input",{"type":"hidden"})]
        post_dict.append(("co",text.encode("utf-8")))
        post_dict.append(("sub1",u"回贴".encode("utf-8")))
        return post_url(submit_url,cookiejar,post_dict,page_url)


GETTHREADS_OUTPUT=True
GETTHREADS_SLEEPINGTIME=1
def get_threads_output(*args):
        if GETTHREADS_OUTPUT:
                for o in args:print o,
                print
def get_wap_comment(div):
        text=div.text
        username=div.findAll("a")[-2:-1:][0].text
        return dict(text=text,attr=dict(username=username))
def get_wap_comment_page(post_id,kz,page):
        url="http://tieba.baidu.com/mo/q---D911C290B25D3B4777AC40593A557281%%3AFG%%3D1--1-3-0--2--wapp_1404445098952_929/flr?pid=%d&kz=%d&fpn=%d"%(post_id,kz,page)
        print "         ",url
        soup=BS.BeautifulSoup(urlopen(url,sleeping_time=GETTHREADS_SLEEPINGTIME).read())
        return map(get_wap_comment,soup.findAll("div",{"class":"i"}))
def get_wap_comments(post_id,kz,comment_num):
        l=[       get_wap_comment_page(post_id,kz,page+1) for page in range(comment_num/10+1) if comment_num!=0]
        if len(l)<=1:return l
        else:return reduce(lambda x,y:x+y,  l  )
def get_web_reply(div,kz):
        dic=json.loads(div.get("data-field").replace("&quot;",'"'))
        author_d=dic["author"]
        content_d=dic["content"]
        attr=dict( 
                username=author_d["user_name"],
                userid=author_d["user_id"],
                usersex=author_d["user_sex"],
                level=author_d["level_id"],
                level_name=author_d["level_name"],
                portrait=author_d["portrait"],
                exp=author_d["cur_score"],
                bawu=author_d["bawu"],
                comment_num=content_d["comment_num"],#楼中楼数量
                timestamp=time.mktime(time.strptime(content_d["date"],"%Y-%m-%d %H:%M")),#时间戳
                post_id=content_d["post_id"],)
        text_div=div.find("div",{"id":"post_content_%d"%attr["post_id"]})
        text=text_div.text
        comments=get_wap_comments(attr["post_id"],kz,attr["comment_num"])
        return dict(text=text,comments=comments,attr=attr)
def get_web_thread_page(kz,page):
        url="http://tieba.baidu.com/p/%s?pn=%d"%(kz,page)
        print url
        pagedata=urllib2.urlopen(url).read()#,sleeping_time=GETTHREADS_SLEEPINGTIME).read()
        time.sleep(GETTHREADS_SLEEPINGTIME)
        page_check=int(re.search(ur'回复贴，共<span class="red">(\d*)<\/span>页'.encode("gbk"),pagedata).group(1))
        if page_check<page:return None
        #~ get_threads_output(pagedata)##
        open("cutout.html",'w').write(pagedata)
        soup=BS.BeautifulSoup(pagedata)
        title=soup.find("h1",{"class":"core_title_txt  "}).text
        print "                 ", len(soup.findAll("div",{"class":"l_post  l_post_bright"}))
        replies=[get_web_reply(div,kz) for div in soup.findAll("div",{"class":"l_post  l_post_bright"})]
        return dict(title=title,replies=replies)
def get_web_thread(kz):
        def threads_list_iter():
                p=1
                while True:
                        l=get_web_thread_page(kz,p)
                        if l:yield l
                        else:break
                        p+=1
        return list(threads_list_iter())
def get_wap_ba_page(ba_name,page):
        url="http://tieba.baidu.com/mo/m?kw=%s&pn=%d"%(urllib.quote(ba_name.encode("gbk")),page*20)
        pagedata=urlopen(url,sleeping_time=GETTHREADS_SLEEPINGTIME).read()
        soup=BS.BeautifulSoup(pagedata)
        kz_re=re.compile("kz=(\d*)")
        return [ get_web_thread(int(kz_re.search(div.a.get("href")).group(1))) for div in soup.findAll("div",{"class":"i"})]
        
def sign_all_tieba(cj):
        mainsoup=BS.BeautifulSoup(urlopen("http://tieba.baidu.com/mo/q---D911C290B25D3B4777AC40593A557281%3AFG%3D1--1-3-0--2--wapp_1404445098952_929/m?tn=bdFBW",cj).read())
        table=mainsoup.find("table",{"class":"tb"})
        for t in table.findAll("tr"):
                print t.td.a.text,"..."
                url="http://tieba.baidu.com/mo/"+t.td.a.get("href")
                sub_soup=BS.BeautifulSoup(urlopen(url,cj).read())
                td=sub_soup.find("div",{"class":"bc"}).find("td",{"style":"text-align:right;"})
                if td.text==u"已签到":
                        print u"                [已签到.]"
                        i=random.randint(5,10)
                else:
                        urlopen("http://tieba.baidu.com"+td.a.get("href"),cj)
                        i=random.randint(10,15)
                print  u"                等待...",i,u"秒"
                time.sleep(i)
                
def get_web_ba_page(ba_name,page_num=0):
        def get_a_thread_data(li):
                datas=json.loads(li.get("data-field").replace("&quot;",'"'))
                title= li.find("div",{"class":"threadlist_text threadlist_title j_th_tit  notStarList "}).text
                if datas["is_top"]:
                        last_reply_user=summary=""
                else:
                        last_reply_user=li.find("div",{"class":" threadlist_detail clearfix"}).find("span",{"class":"tb_icon_author_rely j_replyer"}).text
                        summary=li.find("div",{"class":" threadlist_detail clearfix"}).find("div",{"class":"threadlist_abs threadlist_abs_onlyline"}).text
                datas.update(
                                        title=title,
                                        last_reply_user=last_reply_user, 
                                        summary=summary,#摘要 
                                )
                return datas
        url="http://tieba.baidu.com/f?kw=%s&pn=%d"%(urllib.quote(ba_name.encode("gbk")),page_num*50)
        soup=BS.BeautifulSoup(urlopen(url).read(),fromEncoding="gbk")
        return map(get_a_thread_data  ,soup.findAll("li",{"class":re.compile("j_thread_list (clearfix thread_1st)? *")})  )
def web_ba_page_to_yaml(page_list,filename):
        import yaml
        yaml.safe_dump(page_list,open(filename,'w'),default_flow_style=False,allow_unicode=True)
if __name__=='__main__':
        #~ print get_username("test.cookie")
        app=QApplication([])
        window=YamlLoginWindow("http://passport.baidu.com","usernames.yaml")
        window.show()
        window.load()
        #~ window.load_and_show()
        app.exec_()

#!/usr/bin/python
import urllib
import urllib2
import os
import time
import sys
from bs4 import BeautifulSoup
from datetime import date, timedelta, datetime
from pytz import timezone

stock_url1 = "http://www.chinesefn.com/ci/vip/Archive.asp?subject=&B1=Submit&Type=2&Day="
stock_url2 = "http://www.chinesefn.com/ci/vip/Archive.asp?subject=&B1=Submit&Type=3&Day="
login_url1= "http://www.chinesefn.com/goldennew/member_loginCheck.asp?username=dongfeiwww&password=8326031"
login_url2= "http://www.chinesefn.com/V2013/DisclaimGolden.chtml"
cookie_append="; TrialRegister=Yes; MemberName=dongfeiwww"
txheaders =  {'User-agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
cookie_file = "cookie.txt"
eastern = timezone('US/Eastern')
local = timezone('US/Pacific')

# format '2/14/2014'
def calc_day(delta_day):
  newday = date.today() - timedelta(delta_day)
  return str(newday.month) + '/' + str(newday.day) + '/' + str(newday.year)

class StockAlert:
  delta_day = 0
  cookie = ""
  html = ""
  
  def __init__(self, delta_day):
    self.delta_day = delta_day
    self.oneday = calc_day(delta_day)
    self.cookie = open(cookie_file).read().strip() 
    oldday = date.today() - timedelta(delta_day)
    self.stock_log = open("/Users/dongfeiwww/Dropbox/stock_log/"+oldday.month +"_" + oldday.day +".log", 'w')

  def download(self, url):
    opener = urllib2.build_opener()
    opener.addheaders.append(('Cookie', self.cookie))
    urllib2.install_opener(opener)
    req = urllib2.Request(url, None, txheaders)
    handle = urllib2.urlopen(req)
    cookie = handle.info().getheader('Set-Cookie') 
    if cookie != None:
      self.cookie = cookie + cookie_append
      f = file(cookie_file, 'w')
      print >>f, cookie
  #  print "cookie_download:", cookie2, url
    self.html = handle.read()

  def parse(self, url):
    self.download(url)
    # login and retry
    if self.html.find("main_login") != -1:
      self.download(login_url1)
      self.download(login_url2)
      self.download(url)

    if self.html.find("main_login") == -1:
      print "login success" 
      return self.clean_html_tag() 
    else:
      print "login fail", url 
      return "fail"

  def clean_html_tag(self):
    soup = BeautifulSoup(self.html)
    txt = soup.get_text()
    txt = os.linesep.join([s for s in txt.splitlines() if s])

    pos1 = txt.find(self.oneday + ' ')
    pos2 = txt.rfind(self.oneday + ' ')
    if pos1 != -1 and pos2 != -1:
      start = txt[0:pos1].rfind('[')
      if start == -1: start = pos1
      end = txt[pos2:].find('[')
      if end == -1: end = 100
      txt = txt[start: pos2 + end]
      return txt
    return ''

  def print_stock(self, stock_url, last_text):
    stock_url += self.oneday
    text = self.parse(stock_url)
    if text != "fail" and  last_text != text:
      if last_text == "":
        pos = len(text)
      else:
        pos = text.find(last_text[0:10])
      stock_txt = text[0:pos].encode('utf8', 'ignore')
      print stock_txt
      print >>self.stock_log, stock_txt
      self.stock_log.flush()
    return text

  def realtime(self, delta_day):
    last_text1 = ""
    last_text2 = ""
    while True:
      east_time = datetime.now(local).astimezone(eastern)
      if east_time.hour < 9 || east_time.hour > 16:
        if east_time.hour == 0:
          self.stock_log.close()
          self.stock_log = open("/Users/dongfeiwww/Dropbox/stock_log/"+east_time.month+"_"+east_time.day+".log", 'w')
        time.sleep(600)
        continue
      self.oneday = calc_day(delta_day)
      last_text1 = self.print_stock(stock_url1, last_text1)
      last_text2 = self.print_stock(stock_url2, last_text2)
      time.sleep(60)

if __name__ == "__main__":
  if len(sys.argv) > 1:
    delta_day = int(sys.argv[1])
    stock_url = "http://www.chinesefn.com/ci/vip/Archive.asp?Type=2&Day=" 
    StockAlert(delta_day).print_stock(stock_url, "")
  else:
    # delta_day 0 means today
    StockAlert(0).realtime(1)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 21:54:26 2019

@author: ayx
"""
import os
from tabulate import tabulate
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import boto3
from botocore.exceptions import ClientError


from datetime import datetime, timedelta
from bs4 import BeautifulSoup as BSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import requests
import time
import pandas as pd
import pickle
import re
import sys

import logging

logging.basicConfig(filename='exchange_flow.log',
                    filemode='w',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)
logger = logging.getLogger('flow')
#import os
#os.chdir(r'/Users/ayx/Documents/Trading/CryptoCoin/chainflow')

class flow_tracker():
    def __init__(self):
        self.PROXIES= self.get_proxy(ind=False)
        logger.info('init')
    
    def loaddata(self, fname):
        with open(fname, 'rb') as handle:
            b = pickle.load(handle)
        return b
    def savedata(self, data, fname):
        with open(fname, 'wb') as handle:
            pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
    def get_exchange_address(self):
        ex_lst=['binance','Bitfinex','Kraken']
        ex_dic={}
        for ex in ex_lst:
            label_add='https://etherscan.io/accounts/label/%s' % ex
            bs_obj = BSoup(requests.get(label_add, proxies=self.PROXIES).content, 'html.parser')
            rows = bs_obj.find_all('table')[0].find('tbody').find_all('tr')
        
            adds = []
        
            for row in rows:
                cells = row.find_all('td')
                block = cells[0].get_text()
                adds=adds+[block]
            ex_dic[ex]=adds
        return ex_dic
    def check_active_exchange(self):
        ex_dic = get_exchange_address()
        ex_dic_valid={}
        
        for key in ex_dic:
            add_lst=ex_dic[key]
            add_valid_lst=[]
            for add in add_lst:
                exchange_add='https://etherscan.io/txs?a=%s&f=3' % add
                df_trans=self.gecht_curr_trans(exchange_add)
                if (((datetime.today()-df_trans['time'][0])<timedelta(hours=12)) & (len(df_trans['from'].unique())>2) & (' Binance Token' not in df_trans['to'].unique())):
                    add_valid_lst=add_valid_lst+[add]
            ex_dic_valid[key]=add_valid_lst
        return ex_dic_valid
    def get_valid_address(self):
        ex_dic_valid= self.check_active_exchange()         
        self.savedata(ex_dic_valid, './data/valid_address.pkl')
                
    def get_freq_trans(self):
        logger.info('get trasfers')
        ex_dic_valid=self.loaddata('./data/valid_address.pkl')
        df_msg=pd.DataFrame()
        for key in ex_dic_valid:
            for add in ex_dic_valid[key]:
                exchange_add='https://etherscan.io/txs?a=%s' % add
                df_trans=self.get_curr_trans(exchange_add)
                time.sleep(2)
                if df_trans['value'].max()>300:
                    df_msg=df_msg.append(df_trans.loc[df_trans['value']>300])
        if len(df_msg)>0:
            self.send_email(df_msg)
                    
    def send_email(self, df_msg):
        logger.info('send email')
        me = 'wintersunrise11@gmail.com'
        password = 'ayldxpayx11!!'
        server = 'smtp.gmail.com:587'
        you = 'wintersunrise11@gmail.com'
    
        html = """
        <html><body>
        <p>Crypto - Large order alert!</p>
        {table}
        </body></html>
        """ 
    
        html = html.format(table=tabulate(df_msg, headers=df_msg.columns.values, tablefmt="html"))
        
        message = MIMEMultipart(
            "alternative", None, [MIMEText(html,'html')])
        
        message['Subject'] = "Crypto auto alert"
        message['From'] = me
        message['To'] = you
        server = smtplib.SMTP(server)
        server.ehlo()
        server.starttls()
        server.login(me, password)
        server.sendmail(me, you, message.as_string())
        server.quit()
    def get_proxy(self, ind=True):
        if not ind:
            return None
        exe_path=r"/usr/local/bin/chromedriver"
        chrome_options = Options()  
        chrome_options.add_argument("--headless")
        driver=webdriver.Chrome(executable_path=exe_path, chrome_options=chrome_options)

        driver.get('https://free-proxy-list.net/')
#        driver.find_element_by_xpath("//*[@class='ui-state-default']//*[text()='US']").click()
        driver.find_element_by_xpath("//*[@class='ui-state-default']//*[text()='anonymous']").click()
        driver.find_element_by_xpath("//*[@class='hx ui-state-default']//*[text()='yes']").click()
        html = driver.page_source
        
        bs_obj = BSoup(html, 'html.parser')
        rows = bs_obj.find_all('table')[0].find('tbody').find_all('tr')
    
        trans = []
        
        for row in rows:
            t=[]
            cells = row.find_all('td')
            for i in range(5):
                t.append(cells[i].get_text())
            trans.append(t)
    
        df_trans=pd.DataFrame(trans)
        PROXIES={}
        PROXIES['http']=PROXIES['https']='http://%s:%s' % (df_trans.iloc[0,0], df_trans.iloc[0,1])
        driver.close()
        print(PROXIES)
        return PROXIES

    def get_curr_trans(self, exchange_add):
        logger.info('get exchange transfers for %s' % exchange_add)
        bs_obj = BSoup(requests.get(exchange_add, proxies=self.PROXIES).content, 'html.parser')
        rows = bs_obj.find_all('table')[0].find('tbody').find_all('tr')
    
        trans = []
    
        for row in rows:
            cells = row.find_all('td')
            block = cells[1].get_text()
            age=cells[2].get_text()
            fromadd=cells[3].get_text()
            toadd=cells[5].get_text()
            val=cells[6].get_text()
    
            trans.append([
                block, age, fromadd, toadd, val
            ])
    
        df_trans=pd.DataFrame(trans)
        df_trans.columns=['block','age','from','to','value']
        df_trans['time']=df_trans['age'].apply(lambda x: datetime.today()- self.get_time(x, timedelay=[0,0,0]))
        df_trans['value']=df_trans['value'].apply(lambda x: x.split(' Ether')[0])
        df_trans['value']=df_trans['value'].apply(pd.to_numeric, errors='coerce')
        return df_trans    
    
    
    def get_time(self, x, timedelay=[0,0,0]):
        res=[int(s) for s in x.split() if s.isdigit()]
        if 'days' not in x:
            res=[0]*(3-len(res))+res
        else:
            res=res+[0]*(3-len(res))
        return timedelta(days=res[0]+timedelay[0], hours=res[1]+timedelay[1], minutes=res[2]+timedelay[2])
        
    def send_email_aws(self, df_msg):
        logger.info('send email')
        me = 'wintersunrise11@gmail.com'
        you = 'wintersunrise11@gmail.com'
        server=smtplib.SMTP()
        server.connect('email-smtp.us-east-1.amazonaws.com',587)
        server.starttls()
        server.login('AKIAQBMHTOYYEHJPSPEY','BNykjiMtn9s9dw66OEcEkFV8FqYc38rvo0dSXLhwoJKO')
    
        html = """
        <html><body>
        <p>Crypto - Large order alert!</p>
        {table}
        </body></html>
        """ 
        html = html.format(table=tabulate(df_msg, headers=df_msg.columns.values, tablefmt="html"))
        
        message = MIMEMultipart(
            "alternative", None, [MIMEText(html,'html')])
        
        message['Subject'] = "Crypto auto alert"
        message['From'] = me
        message['To'] = you

        server.sendmail(me, you, message.as_string())
        server.quit()
        
        
tracker=flow_tracker()
tracker.get_freq_trans()






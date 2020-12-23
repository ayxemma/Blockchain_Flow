#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 17:37:12 2019

@author: ayx
"""
import gatelib
import matplotlib.pyplot as plt
import requests
import time
import pandas as pd
import pickle
import re
import sys
from bs4 import BeautifulSoup as BSoup
def loaddata(fname):
    with open(fname, 'rb') as handle:
        b = pickle.load(handle)
    return b
def savedata(data, fname):
    with open(fname, 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)

def get_price(param):
    param='eth_usdt'
    startdate='2016-1-1'
    ts_period="5Min"
    datafolder='/Users/ayx/Documents/Trading/CryptoCoin/Gate/data/'
    df=gatelib.opendata(datafolder, param, startdate)
    df_grp=gatelib.build_ts(df, ts_period)
    return df_grp

def clean_flow_data():
    transactions=[]
    for i in range(3):
        trans=loaddata('./data/gate_%d' % i)
        transactions=transactions+trans
    df_trans=pd.DataFrame(transactions)
    df_trans.columns=['block','age','from','to','value']
    df_trans['time']=df_trans['age'].apply(lambda x: datetime.today()- get_time(x, timedelay=[0,7,0]))
    df_trans['value']=df_trans['value'].apply(lambda x: x.split(' Ether')[0])
    df_trans['value']=df_trans['value'].apply(pd.to_numeric, errors='coerce')
    savedata(df_trans, './data/gate_transfers.pkl')
def flow_analysis():
    df_trans['value'].hist(bins=10)
    df_trans['value'].plot()
    df_trans['value'].describe()
    df_trans['value'].quantile(0.99)
    
def price_analysis():
    df_trans=loaddata('./data/gate_transfers.pkl')
    df_prc=get_price(param='eth_usdt')
    df_prc=df_prc.loc[:,['close','dirdollaramount_sell','dirdollaramount_buy']]
    df_prc=df_prc.reset_index()
    df_trans['time']=df_trans['time'].dt.tz_localize('US/Eastern', ambiguous=True)
    df_trans=df_trans.sort_values(by=['time'])
    df_trans=pd.merge_asof(df_trans, df_prc, left_on='time', right_on='date', direction='forward')
    df_trans['value_dollar']=df_trans['value']*df_trans['close']
    prc_cols=df_prc.columns
    df_trans=df_trans.loc[df_trans['value_dollar']>df_trans['value_dollar'].quantile(0.99)]
    df_trans_cp=df_trans.copy()
    df_trans=df_trans_cp.copy()
    
    fwdtimes=range(1,24,2)

    
    for tm in fwdtimes:
        df_trans['fwdtm_%d' % tm]=df_trans['time']+timedelta(days=tm)
        df_prc.columns=['%s_%d' % (x, tm) for x in prc_cols]
        df_trans=pd.merge_asof(df_trans, df_prc, left_on='fwdtm_%d' % tm, right_on='date_%d' % tm, direction='forward')
        df_trans['rtn_%d' % tm]=df_trans['close_%d' % tm]/df_trans['close']-1
    df_trans=df_trans.set_index('time')    
    for tm in fwdtimes:
#        fig=plt.figure(figsize=(3,3))
#        df_trans['rtn_%d' % tm].hist(bins=10)
        plt.figure()
        df_trans['rtn_%d' % tm].plot(marker='o',linestyle="None")
        plt.axhline(y=df_trans['rtn_%d' % tm].mean(), color='r', linestyle='-')
        plt.title('rtn_%d' % tm)
def get_transactions(pagenum):
#    exchange_add='https://etherscan.io/txs?a=0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be&f=2&p=%d' # binance
    exchange_add='https://etherscan.io/txs?a=0x1c4b70a3968436b9a0a9cf5205c787eb81bb558c&f=2&p=%d' # gate.io
    bs_obj = BSoup(requests.get(exchange_add % pagenum).content, 'html.parser')
    
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

    return trans


def get_flow_data():
    start = datetime.now()
    transactions=[]
    i=0
    for pagenum in range(1, 731):
        trans = get_transactions(pagenum)
        transactions=transactions+trans
        time.sleep(2)
        if pagenum%300==0:
            savedata(transactions, './data/binance_%d' % i)
            transactions=[]
            i+=1
            time.sleep(30)
    savedata(transactions, './data/binance_%d' % i)

    
    finish = datetime.now() - start
    print(finish)
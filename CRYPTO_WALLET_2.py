# %% Libraries

import bitso
from numpy.core.fromnumeric import sort
import pandas as pd
import numpy as np 
import time 
import datetime
import math

from dateutil.parser import parse 

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import io

import os
import matplotlib.pyplot as plt
plt.switch_backend('agg')

# %% Credentials

BITSO_API_KEY = 'dcMnFPNmsy'
BITSO_API_SECRET = 'b1cb4f3032238459f7397a244223c03f'
api = bitso.Api(BITSO_API_KEY, BITSO_API_SECRET)

# %% Books

books = pd.DataFrame(api.ticker())

books['book'] = books[0].apply(lambda x: x.book)
books['book'] = books['book'].apply(lambda x: x.replace('_mxn',''))
books['ask'] = books[0].apply(lambda x: x.ask)
books['bid'] = books[0].apply(lambda x: x.bid)
books['high'] = books[0].apply(lambda x: x.high)
books['last'] = books[0].apply(lambda x: x.last)
books['low'] = books[0].apply(lambda x: x.low)
books['vwap'] = books[0].apply(lambda x: x.vwap)
books['volume'] = books[0].apply(lambda x: x.volume)
books['created_at'] = int(datetime.datetime.strptime(str(datetime.datetime.today().date()), "%Y-%m-%d").timestamp())
books = books[
                [
                'book', 'ask', 'bid', 
                'high', 'last', 'low', 
                'vwap', 'volume', 'created_at'
                ]
            ]

substring = '_mxn'

books_mx = books[
                    books.book.isin(
                                        [
                                            'btc', 'eth', 'xrp', 'ltc'
                                        ]
                                    )
                ]

books_mx['balance'] = books_mx['book'].apply(lambda x: api.balances().__dict__[x].available)
books_mx = books_mx.sort_values('balance', ascending = False)

# %% Ledger

ledger = api.ledger(limit = 10000000)

# %% Operations

oper = pd.DataFrame(ledger)
oper['operation'] = oper[0].apply(lambda x: x.__dict__['operation'])
oper['from'] = oper[0].apply(lambda x: x.__dict__['balance_updates'][1].currency if x.__dict__['operation'] == 'quoted_order' else '-')
oper['to'] = oper[0].apply(lambda x: x.__dict__['balance_updates'][0].currency)
oper['amount_MXN'] = oper[0].apply(lambda x: x.__dict__['balance_updates'][0].amount if x.__dict__['balance_updates'][0].currency == 'mxn' else 'o.o')

oper = oper[~((oper['from'] == '-') & (oper['to'] != 'mxn'))]

oper['amount_MXN'] = oper[0].apply(lambda x: x.__dict__['balance_updates'][1].amount if x.__dict__['balance_updates'][0].currency != 'mxn' else x.__dict__['balance_updates'][0].amount)
oper['amount_MXN'] = oper['amount_MXN'].astype(float)
oper['operation_date'] = oper[0].apply(lambda x: x.__dict__['created_at'].date())
oper = oper.drop(columns = [0])

# %% Operations resume

ivan = np.sum([3050,3050])
res = books_mx.sort_values('ask',ascending=False)
res = res.drop(columns=['bid','high','last','low','vwap','volume'])
res['Investment'] = res['book'].apply(lambda x: -1*oper[oper['to'] == x]['amount_MXN'].sum()-ivan if x == 'btc' else -1*oper[oper['to'] == x]['amount_MXN'].sum())

# Fix
res['Investment'].iloc[[res['book'] == 'btc']] = res['Investment'][0]-np.sum([500,200,500,1000])
res['Investment'].iloc[[res['book'] == 'eth']] = res['Investment'][2]-np.sum([500])

res['Wallet_Value_MXN'] = res['ask'].astype(float)*res['balance'].astype(float)
res['Earnings_MXN'] = res['Wallet_Value_MXN']-res['Investment'].astype(float)
res['Ratio_earn_inv'] = res['Earnings_MXN']/res['Investment']*100

res = res[['book', 'ask', 'created_at', 'Investment', 'balance',
           'Wallet_Value_MXN', 'Earnings_MXN', 'Ratio_earn_inv']]

res

# %% General resume

print('Total investment:', round(res.Investment.sum(),2))
print('Wallet value:', round(res.Wallet_Value_MXN.sum(),2))
print('Total earnings:', round(res.Earnings_MXN.sum(),2))

# %% Historic data

r = books.reset_index()
r['index'] = r['book'].apply(lambda x: len(x))
r = r[r['index'] <= 4].reset_index(drop=True)
r = r.drop('index',axis=1)
r['balance'] = r['book'].apply(lambda x: api.balances().__dict__[x].available)
r['balance'] = round(r['balance'].astype(float),6) 
r = r[['book','ask','created_at','balance']]
r.columns = ['Crypto', 'Value (MXN)', 'Query date', 'Balance']

hist = pd.read_json(r'/home/carlos/Documents/Python_Scripts/ubuntu_crypto_wallet/crypto_history.json')
hist = hist[hist['Query date'] != int(datetime.datetime.strptime(str(datetime.datetime.today().date()), "%Y-%m-%d").timestamp())]
dat = hist.append(r).reset_index()
dat = dat.reset_index()
dat = dat[['Crypto', 'Value (MXN)',	'Query date', 'Balance']]
dat = dat.sort_values('Query date')
dat.to_json(r'/home/carlos/Documents/Python_Scripts/ubuntu_crypto_wallet/crypto_history.json')
dat['str date'] = dat['Query date'].apply(lambda x: datetime.datetime.fromtimestamp(x).strftime('%Y-%m-%d'))

# %% Plots

# Drop Iván

#quote = oper.reset_index(drop = True)
#quote['operation_date'] = quote['operation_date'].astype(str) 
#quote = quote[quote['amount_MXN'] != -3050]
#quote.columns = ['operation', 'from', 'Crypto', 'amount_MXN', 'str date']
#quote = pd.merge(quote, dat, how="left", on=["Crypto","str date"])
#quote['amount_MXN'] = -1*quote['amount_MXN']
#quote = quote.dropna()

quote = oper.reset_index(drop = True)
quote['operation_date'] = quote['operation_date'].astype(str) 
quote = quote[quote['amount_MXN'] != -3050]
quote = quote.merge(dat, left_on = 'operation_date', right_on = 'str date')
quote['amount_MXN'] = -1*quote['amount_MXN']

n = 0
for i in res['book']:
    size = round(len(dat[dat['Crypto'] == i]['str date'])/10*3,0)
    n += 1
    value = dat[(dat['Query date'] == dat['Query date'].max()) & (dat['Crypto'] == i)]['Value (MXN)'].unique().astype(float)[0]
    
    invest = quote[(quote['operation'] == 'quoted_order') & (quote['to'] == i) & (quote['Crypto'] == i)]   
    invest['Value (MXN)'] = invest['Value (MXN)'].astype(float).round(1)
    invest['cc'] = invest['Value (MXN)'].apply(lambda x: 'r' if x > value else 'g') 
    invest['pos'] = invest['Value (MXN)'].apply(lambda x: 'bottom' if x > value else 'top') 
    invest['amount_MXN'] = invest['amount_MXN'].round(1)
    
    withdr = quote[(quote['operation'] == 'quoted_order') & (quote['from'] == i) & (quote['Crypto'] == i)]
    withdr['Value (MXN)'] = withdr['Value (MXN)'].astype(float).round(1)
    withdr['cc'] = withdr['Value (MXN)'].apply(lambda x: 'r' if x < value else 'g') 
    withdr['pos'] = withdr['Value (MXN)'].apply(lambda x: 'top' if x < value else 'bottom') 
    withdr['amount_MXN'] = -1*withdr['amount_MXN'].round(1)
    
    # Maxima & Minima
    # Empty lists to store points of local maxima and minima 
    mx = [] 
    mn = [] 

    n = len(dat[dat['Crypto'] == i]['Value (MXN)'])
    arr = list(dat[dat['Crypto'] == i]['Value (MXN)'])

    # Checking whether the first point is local maxima or minima or neither 
    if(arr[0] > arr[1]): 
        mx.append(0) 
    elif(arr[0] < arr[1]): 
        mn.append(0) 

    # Iterating over all points to check local maxima and local minima 
    for r in range(1, n-1): 

        # Condition for local minima 
        if(arr[r-1] > arr[r] < arr[r + 1]): 
            mn.append(r) 

        # Condition for local maxima 
        elif(arr[r-1] < arr[r] > arr[r + 1]): 
            mx.append(r) 

    # Checking whether the last point is local maxima or minima or neither 
    if(arr[-1] > arr[-2]): 
        mx.append(n-1) 
    elif(arr[-1] < arr[-2]): 
        mn.append(n-1) 
    
    max_min = dat[dat['Crypto'] == i].reset_index(drop=True)
    max = pd.DataFrame(np.array(max_min)[mx])
    min = pd.DataFrame(np.array(max_min)[mn])
    
    print('\n',i)
    plt.figure(figsize=(size,10))
    plt.plot(dat[dat['Crypto'] == i]['str date'][:],dat[dat['Crypto'] == i]['Value (MXN)'][:],'k',label = i)
    
    for a,b,c,d,e in zip(invest['str date'],invest['Value (MXN)'],invest['amount_MXN'],invest['cc'],invest['pos']):
        plt.plot(invest['str date'],invest['Value (MXN)'],'o',color = '#1EEA62', markersize=20)
        plt.annotate('INV: $'+ str(c) + '\nW/L: $' + str(round(c*value/b,1)),(a,b), color = d, ha='center', va=e)
        plt.vlines(invest['str date'], invest['Value (MXN)'], value, colors = invest['cc'], linestyles='solid', linewidth=1)
    
    for a,b,c,d,e in zip(withdr['str date'],withdr['Value (MXN)'],withdr['amount_MXN'],withdr['cc'],withdr['pos']):
        plt.plot(withdr['str date'],withdr['Value (MXN)'],'o',color = '#EA5858', markersize=20)
        plt.annotate('WDL: $'+ str(c) + '\nW/L: $' + str(round(c*value/b,1)),(a,b), color = d, ha='center', va=e) 
        plt.vlines(withdr['str date'], withdr['Value (MXN)'], value, colors = withdr['cc'], linestyles='solid', linewidth=1)
    
    a = list(dat[dat['Crypto'] == i]['str date'])
    b = list(np.float_(dat[dat['Crypto'] == i]['Value (MXN)']))
    c = dat[(dat['Query date'] == dat['Query date'].max()) & (dat['Crypto'] == i)]['Value (MXN)'].unique().astype(float)[0]
    
    try:
        plt.fill_between(a, b, c, where = (b>c), color='red', alpha=.5, interpolate=True)
        plt.fill_between(a, b, c, where = (b<c), color='green', alpha=.5, interpolate=True)
    except:
        print('skip')
    
    plt.plot(max[4],max[1], ':', color = 'green')
    plt.plot(min[4],min[1], ':', color = 'red')
    
    plt.axhline(value, color = 'b', linestyle = '-')
    
    plt.tight_layout(pad=0.1)
    plt.grid(axis = 'y') 
    plt.xticks(rotation = 45)
#    fd = os.open(i+".png",os.O_WRONLY)
#    os.close(fd)
    plt.savefig(os.path.join("/home/carlos/Documents/Python_Scripts/ubuntu_crypto_wallet",i+'.png'), dpi=150, bbox_inches='tight')
    #plt.show()

# %% Candle PLot

for i in res['book']:
    candle1 = dat[dat['Crypto'] == i]
    vals = list(candle1['Value (MXN)'])
    qdts = list(candle1['Query date'])
    dats = list(candle1['str date'])
    candle2 = pd.DataFrame(
                            {
                            'a': vals[:-1],
                            'b': vals[1:],
                            'qd-a': qdts[:-1],
                            'qd-b': qdts[1:], 
                            'date-a': dats[:-1],
                            'date-b': dats[1:] 
                            }  
                            )
    candle2['a'] = candle2['a'].astype(float)
    candle2['b'] = candle2['b'].astype(float)
    candle2['qd-a'] = candle2['qd-a'].astype(float)
    candle2['qd-b'] = candle2['qd-b'].astype(float)
    
    candle2['m'] = (candle2['b']-candle2['a'])/(candle2['qd-b']-candle2['qd-a'])
    candle2['cc'] = candle2['m'].apply(lambda x: 'green' if x>=0 else 'red')
    print(i)
    
    #fig, ax1 = plt.subplots()
    
    plt.vlines(candle2['date-b'], candle2['a'], candle2['b'], colors = candle2['cc'], linestyles='solid', linewidth=1.5)
    plt.xticks(rotation = 90, fontsize=1)
    
    #ax2 = ax1.twinx()
    
    #a = pd.DataFrame(dat[dat['Crypto'] == i]['Value (MXN)']/1000)
    #a['Value (MXN)'] = a['Value (MXN)'].apply(lambda x: round(x,0))
    #a['dato'] = a['Value (MXN)']

    #b = a.groupby('Value (MXN)').count()
    #b = b.reset_index()

    #c = b.sort_values('dato', ascending=False).head(5)

    #ax2.barh(c['Value (MXN)'],c['dato'], 40,alpha = 0.5)
    
    plt.savefig(os.path.join("/home/carlos/Documents/Python_Scripts/ubuntu_crypto_wallet",i+'_candle.png'), dpi=150)
    #plt.show()

# %%



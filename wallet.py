# %%
# Libs

import requests
import pandas as pd
import time
import hmac
import hashlib
import json
import datetime as dt

# %%
# Functions

def api_stat(value):
    
    status = {
                200:'Everything went okay.',
                301:'The server is redirecting you to a different endpoint.',
                400:'The server thinks you made a bad request.',
                401:'The server thinks you’re not authenticated.',
                403:'The resource you’re trying to access is forbidden.',
                404:'The resource you tried to access wasn’t found on the server.',
                503:'The server is not ready to handle the request.'
             }
    
    return status[value] 

BITSO_API_KEY = 'dcMnFPNmsy'
BITSO_API_SECRET = 'b1cb4f3032238459f7397a244223c03f'

# %%
# Available books

response = requests.get("https://api.bitso.com/v3/available_books/")
print('Available books')
print('Status code:',response.status_code,'-',api_stat(response.status_code))

a = pd.DataFrame(response.json())
a['book'] = a['payload'].apply(lambda x: x['book'])

mx_book = []

for i in a['book']:
    if '_mx' in i:
        mx_book.append(i)
print('Available books:', ' | '.join(mx_book))

# %%
# Ticker

response = requests.get("https://api.bitso.com/v3/ticker/")
print('Ticker')
print('Status code:',response.status_code,'-',api_stat(response.status_code))

a = pd.DataFrame(response.json())
a['book'] = a['payload'].apply(lambda x: x['book'])
a['last'] = a['payload'].apply(lambda x: x['last'])
a['low'] = a['payload'].apply(lambda x: x['low'])
a['high'] = a['payload'].apply(lambda x: x['high'])
a['ask'] = a['payload'].apply(lambda x: x['ask'])
a['bid'] = a['payload'].apply(lambda x: x['bid'])
a['created_at'] = a['payload'].apply(lambda x: x['created_at'].split('T')[0])

a = a[a['book'].isin(mx_book)]

ticker = a[['book','last','low','high','ask','bid','created_at']]

# %%
# Trades

response = requests.get("https://api.bitso.com/v3/ledger/", params={})
print('Ticker')
print('Status code:',response.status_code,'-',api_stat(response.status_code))

# %%

import time
import hmac
import hashlib
import requests
import json


bitso_key = 'dcMnFPNmsy'
bitso_secret = 'b1cb4f3032238459f7397a244223c03f'
http_method = "GET" # Change to POST if endpoint requires data
request_path = "/v3/ledger/"
parameters = {}     # Needed for POST endpoints requiring data

# Create signature
nonce =  str(int(round(time.time() * 1000)))
message = nonce+http_method+request_path
if (http_method == "POST"):
  message += json.dumps(parameters)
signature = hmac.new(bitso_secret.encode('utf-8'),
                                            message.encode('utf-8'),
                                            hashlib.sha256).hexdigest()

# Build the auth header
auth_header = 'Bitso %s:%s:%s' % (bitso_key, nonce, signature)

# Send request
if (http_method == "GET"):
  response = requests.get("https://api.bitso.com" + request_path, headers={"Authorization": auth_header})
elif (http_method == "POST"):
  response = requests.post("https://api.bitso.com" + request_path, json = parameters, headers={"Authorization": auth_header})

print(response.content)

# %%

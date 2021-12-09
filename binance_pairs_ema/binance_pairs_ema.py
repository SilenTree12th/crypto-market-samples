import requests
import json
import os
import time
from threading import Thread
from bfxhfindicators import EMA

BASE_URL = 'https://api.binance.com'

TIMEFRAME = '15m'
EMA_PERIODS = [96, 288]

symbols = []
candles = {}
prices = {}
ema_values = {}

def load_candles(sym):
    global candles, prices, BASE_URL
    payload = {
            'symbol': sym,
            'interval': '15m',
            'limit': 250
    }
    resp = requests.get(BASE_URL + '/api/v1/klines', params=payload)
    klines = json.loads(resp.content)
    # parse klines and store open, high, low, close and vol only
    parsed_klines = []
    for k in klines:
        k_candle = {
            'open': float(k[1]),
            'high': float(k[2]),
            'low': float(k[3]),
            'close': float(k[4]),
            'vol': float(k[5])
        }
        parsed_klines.append(k_candle)
    candles[sym] = parsed_klines
    index = len(parsed_klines) - 1 # get index of latest candle
    prices[sym] = parsed_klines[index]['close'] # save current price

# create results folder if it doesn't exist
if not os.path.exists('results/'):
    os.makedirs('results/')
# start with blank files
open('results/good.txt', 'w').close()
open('results/bad.txt', 'w').close()

# load symbols information
print('Getting list of BTC trade pairs...')
resp = requests.get(BASE_URL + '/api/v1/ticker/allBookTickers')
tickers_list = json.loads(resp.content)
for ticker in tickers_list:
    if str(ticker['symbol'])[-4:] == 'USDT':
        symbols.append(ticker['symbol'])

# get 15m candles for symbols
print('Loading candle data for symbols...')
for sym in symbols:
    Thread(target=load_candles, args=(sym,)).start()
while len(candles) < len(symbols):
    print('%s/%s loaded' %(len(candles), len(symbols)), end='\r', flush=True)
    time.sleep(0.1)

# calculate EMAs for each symbol
print('Calculating EMAs...')
for sym in candles:
    for period in EMA_PERIODS:
        iEMA = EMA([period])
        lst_candles = candles[sym][:]
        for c in lst_candles:
            iEMA.add(c['close'])
        if sym not in ema_values:
            ema_values[sym] = {}
        ema_values[sym][period] = iEMA.v()

# save filtered EMA results in txt files
print('Saving filtered EMA results to txt files...')
for sym in ema_values:
    ema_96 = ema_values[sym][96]
    ema_288 = ema_values[sym][288]
    price = prices[sym]
    entry = ''
    if price < ema_288 and price > ema_96 or price > ema_288:
    # save good symbols
        f = open('results/good.txt', 'a')
        #entry = '%s: $%s\n' %(sym, round(price,3))
        entry = '%s: $%s\n' %(sym)
        f.write(entry)
    elif price < ema_96 and price < ema_288:
    # save bad symbols
        f = open('results/bad.txt', 'a')
        entry = '%s: $%s\n' %(sym)
        f.write(entry)
    f.close()
    del f # cleanup

print('All done! Results saved in results folder.')


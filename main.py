import os
import re
import time

from tika import parser
from os import listdir
from os.path import isfile, join
from collections import defaultdict
from datetime import date, datetime
from pandas_datareader import data
from datetime import timedelta
from pandas import DataFrame
from tkinter import *
from tkinter import ttk

import matplotlib.pyplot as plt
import pandas as pd
import matplotlib
import tkinter.scrolledtext as tkst
import numpy as np
import tkinter as tk
import PIL.Image
import PIL.ImageTk


path = "process-pdf/"
SNP = {'^GSPC': 0}
shares = {0:1200, 3: 200, 4: 400, 5: 800}

def retriveFiles(path):
    return [join(path, f) for f in listdir(path) if isfile(join(path, f))]

files = retriveFiles(path)

def generateDates(files):
    root = len(path)
    res = []
    for file in files:
        dstr = file[root:root+8]
        d = date(int(dstr[0:4]),int(dstr[4:6]),int(dstr[6:8]))
        res.append(d)

    res.sort()
    return res

def retrieveRatings(files, day):
    for file in files:
        if day in file:
            break
    raw = parser.from_file(file)
    pattern = '\(.+\) Q+'
    data_pairs = re.findall(pattern, raw['content'])
    res = defaultdict(int)
    for data in data_pairs:
        pair = data.split(' ');
        res[pair[0][1:-1]] = len(pair[1])

    return res

#get open and close prices from yahoo api
#return dic {ticker: [rating, [price1, price2, ...]], ...}
def getTickerPrices(report_date, end_date, ticker_rating_pair):
    res = defaultdict(list)
    for ticker, rating in ticker_rating_pair.items():
        try:
            price_info = data.DataReader(ticker, 'yahoo', report_date, end_date)
            prices = []
            for i in range (price_info.shape[0]):
                prices.append(price_info.iloc[i]['Close'])
            res[ticker] = [rating, prices]
        except:
            print(ticker, " is not public traded in North America stock market, ignored...", sep = "")
    return res

def calculateBalance(ticker_prices, shares):
    balance  = [0] * len(next(iter(ticker_prices.values()))[1])

    for ticker, ops in ticker_prices.items():
        rating = ops[0]
        prices = ops[1]
        for i in range(len(balance)):
            if (rating == 0 or rating >= 3 or rating <= 5):
                balance[i] = balance[i] + prices[i]*shares[rating]
    return balance

def calculateProfits(balance, shares):
    profits_percentage = [0] * len(balance)
    for i in range(len(balance)):
        profits_percentage[i] = (balance[i] - balance[0]) / balance[0]
    return profits_percentage

def getFormatedTickerPrice(ticker_prices, shares):
    s = "Ticker  Quantity   Buy($)  Sell($)\n"
    for ticker, ops in ticker_prices.items():
        ticker = "{:<7}".format(ticker)
        rating = ops[0]
        rating = "{:<10}".format(str(shares[rating]))
        s = s + ticker + ' ' + rating
        prices = ops[1]
        open_price = "{:<8}".format( str(round(prices[0],2)) )
        close_price = "{:<7}".format( str(round(prices[-1],2)) )
        s = s + ' '+  open_price +' '+ close_price
        s = s+'\n'
    return s

# purchaseDate = 'YYYYMMDD'
# threeStarVolume, fourStarVolume, fiveStarVolume
# trailingTime

root = Tk()
root.geometry('1000x610')
root.title("Morningstar Strategy Simulator")
root.resizable(False, False)

lf_dataRange = LabelFrame(root, text = "Data Range")
lf_dataRange.grid(row = 0, column = 0, columnspan = 2, padx = 5, pady = 5)

# awaiting filename data
# generateDates(files)
dataRange = generateDates(files)
dataRangeSelect = ttk.Combobox(lf_dataRange, state="readonly", values = dataRange)
dataRangeSelect.pack()
dataRangeSelect.current(1)

day = ''

def callbackFunc(event):
    print("New Element Selected", dataRangeSelect.get())
    day = ''.join(str(dataRangeSelect.get()).split('-'))
    if (day == ''):
        day = '20180223'
    report_date = date(int(day[0:4]),int(day[4:6]),int(day[6:8]))
    ticker_rating_pair = retrieveRatings(files, day)

dataRangeSelect.bind("<<ComboboxSelected>>", callbackFunc)

# lf_purchaseDate = LabelFrame(root, text = "Purchase Date (YYYYMMDD)")
# lf_purchaseDate.grid(row = 1, column = 0, columnspan = 2, padx = 5, pady = 5)
# entry_purchaseDate = Entry(lf_purchaseDate, bd = 2)
# entry_purchaseDate.pack()
# day = str(entry_purchaseDate.get())
# if (day == ''):
#     day = '20180808'
# report_date = date(int(day[0:4]),int(day[4:6]),int(day[6:8]))

lf_threeStarVolume = LabelFrame(root, text = "3-star Quantity")
lf_threeStarVolume.grid(row = 0, column = 2, columnspan = 2, padx = 5, pady = 5)
entry_threeStarVolume = Entry(lf_threeStarVolume, bd = 2)
entry_threeStarVolume.pack()

lf_fourStarVolume = LabelFrame(root, text = "4-star Quantity")
lf_fourStarVolume.grid(row = 1, column = 2, columnspan = 2, padx = 5, pady = 5)
entry_fourStarVolume = Entry(lf_fourStarVolume, bd = 2)
entry_fourStarVolume.pack()

lf_fiveStarVolume = LabelFrame(root, text = "5-star Quantity")
lf_fiveStarVolume.grid(row = 2, column = 2, columnspan = 2, padx = 5, pady = 5)
entry_fiveStarVolume = Entry(lf_fiveStarVolume, bd = 2)
entry_fiveStarVolume.pack()

lf_TrailingTime = LabelFrame(root, text = "Trailing Return Days")
lf_TrailingTime.grid(row = 0, rowspan = 2, column = 4, columnspan = 2, padx = 5, pady = 5, sticky = "N" + "S")
MODES = [
    ("5 Days", 5),
    ("30 Days", 30),
    ("91 Days", 91),
    ("180 Days", 180),
]

v = StringVar()
v.set(5)

for text, mode in MODES:
    b = Radiobutton(lf_TrailingTime, text = text, variable = v, value = mode)
    b.pack(anchor = W)

tickerInfo = tkst.ScrolledText(
    master = root,
    wrap   = WORD,
    width  = 20,
    height = 10
)

tickerInfo.grid(row = 3, rowspan = 7, column = 0, columnspan = 3, sticky = "N" + "S" + "E" + "W")

# replace text with a func callback
tickerInfo.insert(INSERT, '')

def getDealDays(report_date, end_date, ticker):
    panel_data = data.DataReader(ticker, 'yahoo', report_date, end_date)
    return [pd.to_datetime(d).strftime("%m/%d") for d in list(panel_data.index.values)]

def submitCallback():

    day = ''.join(str(dataRangeSelect.get()).split('-'))
    if (day == ''):
        day = '20180223'
    report_date = date(int(day[0:4]),int(day[4:6]),int(day[6:8]))

    threeStarVolume = int(entry_threeStarVolume.get())
    fourStarVolume = int(entry_fourStarVolume.get())
    fiveStarVolume = int(entry_fiveStarVolume.get())
    shares = {0:1200, 3: threeStarVolume, 4: fourStarVolume, 5: fiveStarVolume}
    trailingTime = int(v.get())
    end_date = report_date + timedelta(days=trailingTime)

    ticker_prices = getTickerPrices(report_date, end_date, retrieveRatings(files, day))
    snp_prices = getTickerPrices(report_date, end_date, SNP)

    balance = calculateBalance(ticker_prices, shares)
    profits = calculateProfits(balance, shares)
    snpBalance = calculateBalance(snp_prices, shares)
    profits_snp = calculateProfits(snpBalance, shares)

    balanceLabel = Label(root, text = "Cost: $" + str(round(balance[0], 2)) + "\n EOP Balance: $" + str(round(balance[len(balance) - 1], 2)))
    balanceLabel.grid(row = 2, column = 6, columnspan = 2, padx = 5, pady = 5, sticky = "N" + "S" + "E" + "W")

    deal_days =  getDealDays(report_date, end_date, '^GSPC')

    tickerInfo.delete(1.0, END)
    tickerInfo.insert(INSERT, getFormatedTickerPrice(ticker_prices, shares))
    tickerInfo.config(state = DISABLED)

    l1, = plt.plot(deal_days,profits, label='Morningstar')
    l2, = plt.plot(deal_days,profits_snp, label='S&P')
    plt.legend(loc='upper right')
    plt.title('Morningstar Recommendations Performance vs. S&P 500')
    plt.xlabel('Date')
    plt.ylabel('Return')
    plt.xticks(rotation=90)
    plt.savefig('myfig.png', dpi = 90, pad_inches = 0)
    plt.close()

    img = PIL.Image.open("myfig.png")
    photo = PIL.ImageTk.PhotoImage(img)

    labelPhoto = Label(image = photo)
    labelPhoto.image = photo
    labelPhoto.grid(row = 3, rowspan = 4, column = 4, columnspan = 4, padx = 5, pady = 5, sticky = "N" + "S" + "E" + "W")

#     canvas = Canvas(root, width=250, height=250)
#     canvas.grid(row = 3, rowspan = 4, column = 4, columnspan = 4, padx = 5, pady = 5, sticky = "N" + "S" + "E" + "W")
#     canvas.create_image(0, 0, anchor="nw", image=photo)

    print("Submitted")


btn_Submit = Button(root, text = "Submit", command = submitCallback)
btn_Submit.grid(row = 1, column = 6, columnspan = 2, padx = 5, pady = 5, sticky = "N" + "S" + "E" + "W")

for col in range(10):
    root.grid_columnconfigure(col, minsize = 100, pad = 2)

for row in range(10):
    root.grid_rowconfigure(row, minsize = 60, pad = 2)


while True:
    try:
        root.mainloop()
        break
    except UnicodeDecodeError:
        pass

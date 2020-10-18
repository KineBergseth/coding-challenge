import requests
from datetime import datetime
from pycoingecko import CoinGeckoAPI
from datetime import datetime


cg = CoinGeckoAPI()


# get data about a crypto currency for a specific date
def get_price_date(id, date):
    data = cg.get_coin_history_by_id(id, date)
    return data
#find price here
#print(get_price_date("bitcoin", "17-10-2016"))


# get history of a crypto currency's price
# 1 day will show data-points for each minute, 1 or more days will show hourly datapoints
# intervals higher than 90 days will show daily data
def get_price_history(coin, currency, days):
    # get market_chart data
    response = cg.get_coin_market_chart_by_id(coin, currency, days)

    # rewrite this
    timestamps = [price[0] / 1000 for price in response['prices']]
    dates = [datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') for timestamp in timestamps]
    prices = [price[1] for price in response['prices']]

    # get lowest and highest price during the time interval
    historic_low = min([price[1] for price in response['prices']])
    historic_high = max([price[1] for price in response['prices']])
    # return coin, date-interval, prices, and historic low and high price
    return coin, dates, prices, historic_low, historic_high

print(get_price_history("bitcoin", "usd", "14"))  # remove

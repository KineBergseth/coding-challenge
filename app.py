import requests
from datetime import date
from pycoingecko import CoinGeckoAPI  # https://github.com/man-c/pycoingecko
from datetime import datetime
import pandas as pd
import numpy as np
from dash import Dash
import dash_core_components as dcc
import dash_html_components as html
from dash_table import DataTable
from dash.dependencies import Input, Output, State

cg = CoinGeckoAPI()


# gets name of cryptos
def get_names():
    coins = cg.get_coins_markets("usd")

    symbols = {}
    for coin in coins:
        symbols[coin['symbol'].upper()] = coin['id']

    return symbols


def getIds():
    coins = cg.get_coins_markets("usd")
    ids = {}
    for coin in coins:
        ids[coin['id']] = coin['symbol'].upper()
    return ids


def get_accounts():
    token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik0wTXhNVEEzTVVFeU5rRkZSREZGTnpSRE1VUXdPVVU0TXpBNFF6QkdRVVF6UkVSRE1VSTNSUSJ9.eyJpc3MiOiJodHRwczovL3N0YWNjeC5ldS5hdXRoMC5jb20vIiwic3ViIjoiejQ0RGdzWVFKREtyNTRCcmZvU0x3c2pLWWRtUDRLdWtAY2xpZW50cyIsImF1ZCI6Imh0dHBzOi8vc3RhY2MuZmludGVjaCIsImlhdCI6MTYwMTIwNTAwNywiZXhwIjoxNjAzNzk3MDA3LCJhenAiOiJ6NDREZ3NZUUpES3I1NEJyZm9TTHdzaktZZG1QNEt1ayIsImd0eSI6ImNsaWVudC1jcmVkZW50aWFscyJ9.fBvgUGcc1zS3eStbdGo19mLC6KqOdMeBdo_xuZEBz9jCzllRfrgqIhPbys5Se2XreGxu5_6oKWlXbqDOvnbuvjTJKnhoO9Aom1meUjqbQgaROeN0hbmPxVDKF-JDtOdZbAWtZv1ds9bWF0zqo9Z7ogicZ0eUi8FnEA2h2I6peVQPL9cJJwSfhjXPW73Ws4e6c0vynnhXLc5BcQgst0iaMZd4n3tdruzP_bgEY5GqbKvJxHjL2KNHh933VZSZdx_7mf4imsgsed2AL1QkIkqj5lvf_niyzrEmOLs_K_rSOZqRzO0c1u9wxrCK7qlryzpv8nz3C3zXfNdnMQHOejOFpQ"
    url = "https://fintech-webinar-2020-api.vercel.app/api/accounts"
    header = {'Authorization': 'Bearer {}'.format(token)}
    response = requests.get(url, headers=header)  # Get request
    df = pd.DataFrame(response.json())

    df.insert(2, 'amount', [balance['amount'] for balance in df['balance']])
    df.insert(3, 'currency', [balance['currency'] for balance in df['balance']])
    df.drop(['balance', 'resource', 'resource_path'], axis=1, inplace=True)
    df.columns = df.columns.str.title()

    # use symbol to get name of coins and put data in df
    namelist = get_names()
    df['Coin'] = df['Currency'].map(namelist)

    coins = ",".join([get_names()[currency] for currency in df['Currency']])
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coins}&vs_currencies=USD&include_market_cap=true"
    response = requests.get(url)

    prices = {getIds()[key]: val for key, val in response.json().items()}
    rates = [prices[currency]['usd'] for currency in df['Currency']]

    # print(coinlist)
    # pricing = cg.get_price(coinlist, "usd")
    # print(pricing)
    # rates = pricing['symbol']
    # print(rates)
    # df['Price'] = df['Coin'].map(pricing)

    # prices = {df['Coin']: val for key, val in response.json().items()}
    # print(prices)
    # rates = [pricing['usd'] for currency in df['Currency']]
    # print(rates)

    df.insert(4, 'tot_value', np.round([float(amount) * float(rate) for amount, rate in zip(df['Amount'], rates)], 2))
    df.insert(5, 'Market Cap', np.round([prices[currency]['usd_market_cap'] for currency in df['Currency']], 2))
    # legg in sortering på total verdi
    df.sort_values(by=['tot_value'], ascending=False, inplace=True)
    df.to_csv(r'acc.csv')
    return df


print(get_accounts())


# get data about a crypto currency for a specific date
def get_price_date(id, date):
    data = cg.get_coin_history_by_id(id, date)
    price = data['market_data']['current_price']['usd']  # kanskje ikke verdens beste løsning, men funker :P
    return price


# get history of a crypto currency's price
# 1 day will show data-points for each minute, 1 or more days will show hourly datapoints
# intervals higher than 90 days will show daily data
def get_price_history(coin, days):
    # get market_chart data from last x number of days
    price_history = cg.get_coin_market_chart_by_id(coin, "usd", days)

    # convert time from UNIX
    timestamps = [price[0] / 1000 for price in price_history['prices']]
    dates = [datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') for timestamp in timestamps]
    prices = [price[1] for price in price_history['prices']]

    # get lowest and highest price during the time interval
    historic_low = min([price[1] for price in price_history['prices']])
    historic_high = max([price[1] for price in price_history['prices']])
    # return coin, date-interval, prices, and historic low and high price
    return coin, dates, prices, historic_low, historic_high


# Dash App med plotly
# bruker extern CSS fil, har ikke skrevet den selv btw
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

# prepare account data for table,
account_data = get_accounts().to_dict('records')


# create table and populate with account data
def generate_table():
    return DataTable(
        id='table',
        columns=[{"name": i, "id": i} for i in get_accounts().columns],
        data=account_data,
        sort_action="native",
    )


# create dropdownlist med alle coins i wallet
def generate_ddl_coin():
    return dcc.Dropdown(
        id='input-ddl',
        options=[{'label': i, 'value': i} for i in get_accounts()['Coin']],
        value='bitcoin',
        style=dict(
            width='40%',
        )
    )


# generate calendar where user can select input
def generate_calendar():
    return dcc.DatePickerSingle(
        id='date-picker',
        min_date_allowed=date(1995, 8, 5),
        max_date_allowed=date(2020, 9, 19),
        initial_visible_month=date(2019, 10, 5),
        date=date(2019, 10, 28)
    )


app.layout = html.Div(children=[

    html.H1("Stacc code challenge"),
    html.H2("Table"),
    html.P("du kan sortere data i tabellen ved å klikke på pilene i headeren"),
    generate_table(),
    html.Br(),
    html.Br(),
    html.H2("Graph"),
    html.Label('Select a coin to display data about'),
    generate_ddl_coin(),
    html.Div(id='graph'),
    html.Div(dcc.Slider(
        id='slider',
        min=1,
        max=360,
        value=30),
        style={'width': '50%', 'padding': '20px 10px 10px 20px'}),
    html.Br(),
    html.H2("See data from the past"),
    html.P("select a date from the calender please, and it will show data about the cpin you selected"),
    generate_calendar(),
    html.Div(id='output-date-picker')

])


# find data for specific date
@app.callback(
    Output('output-date-picker', 'children'),
    [Input('input-ddl', 'value'),
     Input('date-picker', 'date')])
def update_calender_output(coin, date_value):
    string_prefix = 'You have selected the date '
    if date_value is not None:
        date_object = date.fromisoformat(date_value)
        date_string = date_object.strftime('%d-%m-%Y')
        price = get_price_date(coin, date_string)
        return string_prefix + date_string + ", where the following was the price for " + coin + " was USD : " + str(price)


# find data for graph
@app.callback(
    Output('graph', 'children'),
    # Output('low', 'string'),
    # Output('high', 'string'),
    [Input('input-ddl', 'value'),
     Input('slider', 'value')])
def update_graph(coin, days):
    if not coin:
        return None
    else:
        coin, dates, prices, historic_low, historic_high = get_price_history(coin, days)

    return html.Div(dcc.Graph(
        id='figure',
        figure={
            'data': [{
                'x': dates,
                'y': prices,
                'type': 'scatter',
                'name': coin + 'price'
            }
            ],
            'layout': {
                'title': coin + ' Last ' + str(days) + ' Days',
                'xaxis': {
                    'title': 'Date',
                    'showgrid': True,
                },
                'yaxis': {
                    'title': 'Price USD',
                    'showgrid': True,
                }
            }
        },
        config={
            'displayModeBar': False
        }
    ),
        # html.P("Historic low in this period is USD : " + str(historic_low)),
        # html.P("Historic high in this period is USD : " + str(historic_high))
    )


if __name__ == '__main__':
    app.run_server(debug=True)  # dev tool and hot-reloading hihi

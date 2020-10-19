import requests
from datetime import date
from pycoingecko import CoinGeckoAPI  # https://github.com/man-c/pycoingecko
from datetime import datetime
import pandas as pd
from dash import Dash
import dash_core_components as dcc
import dash_html_components as html
from dash_table import DataTable
from dash.dependencies import Input, Output, State

# Python3 wrapper around the CoinGecko API
cg = CoinGeckoAPI()


# gets name of cryptos
def get_names():
    coins = cg.get_coins_markets("usd")

    name = {}
    for coin in coins:
        name[coin['symbol'].upper()] = coin['id']

    return name


# gets price changes of cryptos
def get_info():
    coins = cg.get_coins_markets(vs_currency='usd', include_24hr_change='true')

    info = {}
    for coin in coins:
        info[coin['symbol'].upper()] = coin['price_change_percentage_24h']

    return info


# get account information
def get_accounts():
    token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik0wTXhNVEEzTVVFeU5rRkZSREZGTnpSRE1VUXdPVVU0TXpBNFF6QkdRVVF6UkVSRE1VSTNSUSJ9.eyJpc3MiOiJodHRwczovL3N0YWNjeC5ldS5hdXRoMC5jb20vIiwic3ViIjoiejQ0RGdzWVFKREtyNTRCcmZvU0x3c2pLWWRtUDRLdWtAY2xpZW50cyIsImF1ZCI6Imh0dHBzOi8vc3RhY2MuZmludGVjaCIsImlhdCI6MTYwMTIwNTAwNywiZXhwIjoxNjAzNzk3MDA3LCJhenAiOiJ6NDREZ3NZUUpES3I1NEJyZm9TTHdzaktZZG1QNEt1ayIsImd0eSI6ImNsaWVudC1jcmVkZW50aWFscyJ9.fBvgUGcc1zS3eStbdGo19mLC6KqOdMeBdo_xuZEBz9jCzllRfrgqIhPbys5Se2XreGxu5_6oKWlXbqDOvnbuvjTJKnhoO9Aom1meUjqbQgaROeN0hbmPxVDKF-JDtOdZbAWtZv1ds9bWF0zqo9Z7ogicZ0eUi8FnEA2h2I6peVQPL9cJJwSfhjXPW73Ws4e6c0vynnhXLc5BcQgst0iaMZd4n3tdruzP_bgEY5GqbKvJxHjL2KNHh933VZSZdx_7mf4imsgsed2AL1QkIkqj5lvf_niyzrEmOLs_K_rSOZqRzO0c1u9wxrCK7qlryzpv8nz3C3zXfNdnMQHOejOFpQ"
    url = "https://fintech-webinar-2020-api.vercel.app/api/accounts"
    header = {'Authorization': 'Bearer {}'.format(token)}
    response = requests.get(url, headers=header)  # Get request
    df = pd.DataFrame(response.json())

    # take data out of nested balance
    df.insert(3, 'amount', [balance['amount'] for balance in df['balance']])
    df.insert(4, 'currency', [balance['currency'] for balance in df['balance']])
    # drop some columns
    df.drop(['balance', 'resource', 'resource_path'], axis=1, inplace=True)
    df.columns = df.columns.str.title()

    # use symbol to get name of coins and put data in df
    df['Coin'] = df['Currency'].map(get_names())
    # endre på rekkefølgen på kolonnen lel
    coin_name = df.pop('Coin')
    df.insert(2, 'Coin', coin_name)
    # use symbol to get price change for the last 24h and put data in df
    df['price_change24h'] = df['Currency'].map(get_info())
    # endre på rekkefølgen på kolonnen lel
    coin_pc = df.pop('price_change24h')
    df.insert(5, 'price_change24h', coin_pc)

    # create list of the names of all the coinz
    coinlist = df['Coin'].astype(str).values.flatten().tolist()
    # get prices in usd
    pricing = cg.get_price(coinlist, "usd", include_market_cap='true')
    # putt økonomi ting inn i df - pris for 1 coin, sum for wallets og market_cap
    df.insert(6, 'USD', [pricing[currency]['usd'] for currency in df['Coin']])
    # regn ut totalverdi for wallets
    wallet_value = [float(amount) * float(usd) for amount, usd in zip(df['Amount'], df['USD'])]
    market_cap = [pricing[currency]['usd_market_cap'] for currency in df['Coin']]
    df.insert(7, 'wallet_value', wallet_value)
    df.insert(8, 'Market Cap', market_cap)

    # legg in sortering på total verdi
    df.sort_values(by=['wallet_value'], ascending=False, inplace=True)
    return df


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
    # legger til alle timestamps i liste
    timestamps = [price[0] for price in price_history['prices']]
    dates = [datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S') for timestamp in timestamps]
    prices = [price[1] for price in price_history['prices']]
    # get lowest and highest price during the time interval
    historic_low = min([price[1] for price in price_history['prices']])
    historic_high = max([price[1] for price in price_history['prices']])
    # return coin, date-interval, prices, and historic low and high price
    return dates, prices, historic_low, historic_high


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
        style_data_conditional=[
            {
                'if': {
                    'filter_query': '{price_change24h} < 0',
                    'column_id': 'price_change24h',
                },
                'color': 'red'
            },
            {
                'if': {
                    'filter_query': '{price_change24h} > 0',
                    'column_id': 'price_change24h',
                },
                'color': 'green'
            }
        ]
    )


# create dropdownlist med alle coins i wallet
def generate_ddl_coin():
    return dcc.Dropdown(
        id="input-ddl-coin",
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


# generate slider where user can select input
def generate_slider():
    return html.Div(dcc.Slider(
        id='slider',
        min=1,
        max=360,
        value=30,
        step=1,
        marks={
            7: '1 week',
            30: '1 month',
            90: 'Quarter',
            180: '6 months',
            360: '1 year'
        }
    ),
        style={'width': '50%', 'padding': '20px 10px 10px 20px'},
    )


app.layout = html.Div(children=[
    html.Br(),
    html.H1("Stacc code challenge",
            style={'text-align': 'center'}),
    html.H2("Table"),
    html.P("du kan sortere data i tabellen ved å klikke på pilene i headeren"),
    generate_table(),
    html.Br(),
    html.H2("Graph"),
    html.Label('Select a coin to display data about, and use the slider to decide X numbers of past days you want to see'),
    generate_ddl_coin(),
    html.Br(),
    html.Div(id='graph'),
    generate_slider(),
    html.P(id='low_value'),
    html.P(id='high_value'),
    html.Br(),
    html.H2("Historical price"),
    html.P("select a date from the calender please, and it will show data about the coin you selected"),
    generate_calendar(),
    html.Div(id='output-date-picker'),
    html.Br(),
    html.Br()
])


# find data for specific date
@app.callback(
    Output('output-date-picker', 'children'),
    [Input('input-ddl-coin', 'value'),
     Input('date-picker', 'date')])
def update_calender_output(coin, date_value):
    string_prefix = 'You have selected the date '
    if date_value is not None:
        date_object = date.fromisoformat(date_value)
        date_string = date_object.strftime('%d-%m-%Y')
        price = get_price_date(coin, date_string)
        return string_prefix + date_string + ", where the following was the price for " + coin + ", USD : " + str(
            price)


# find data for graph
@app.callback(
    Output('graph', 'children'),
    [Input('input-ddl-coin', 'value'),
     Input('slider', 'value')])
def update_graph(coin, days):
    dates, prices, historic_low, historic_high = get_price_history(coin, days)
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
    )
    )


# find historical high and lowest price for time period
@app.callback(
    [Output('low_value', 'children'),
     Output('high_value', 'children')],
    [Input('input-ddl-coin', 'value'),
     Input('slider', 'value')])
def update_graph(coin, days):
    dates, prices, historic_low, historic_high = get_price_history(coin, days)
    return "Historic low price in this " + str(days) + " day period for " + coin + " is USD " + str(
        historic_low), "Historic high price in this " + str(days) + " day period for " + coin + " is USD " + str(
        historic_high)


if __name__ == '__main__':
    app.run_server(debug=True)  # dev tool and hot-reloading hihi

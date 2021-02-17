#!/usr/bin/env python
'''
Bot Financiero
---------------------------
Autor: Inove Coding School
Version: 1.0

Descripcion:
Se utiliza Flask para crear un bot capaz de analizar
el análisis y tendencia de instrumentos basado en gráficos
y thresholds configurables
'''

__author__ = "Inove Coding School"
__email__ = "INFO@INOVE.COM.AR"
__version__ = "1.0"

import time
import json
import plotly
import traceback
import sqlite3
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import plotly.graph_objs as go

from flask import Flask, request, jsonify, render_template, Response, redirect , url_for, session

from ..models import trading
from ..app import app

def getInstrument(instrument, interval):

    if interval == '1M':
        days = 30
        resample = '1D'
    elif interval == '2M':
        days = 61
        resample = '1D'
    elif interval == '3M':
        days = 91
        resample = '1D'
    elif interval == '6M':
        days = 182
        resample = '1D'
    elif interval == '1Y':
        days = 365
        resample = '1D'

    
    df3, df_alza = trading.extract_transform_data(instrument, days, resample)

    layout = {}
    layout["uirevision"] = "The User is always right"  # Ensures zoom on graph is the same on update
    layout["margin"] = {"t": 50, "l": 50, "b": 50, "r": 25}
    layout["autosize"] = True
    layout["height"] = 800

    layout["xaxis"] = {}
    layout["xaxis"]["rangeslider"] = {}
    layout["xaxis"]["rangeslider"]["visible"] = False
    layout["xaxis"]["tickformat"] = "%H:%M"
    layout["xaxis"]["type"] = "category"

    layout["yaxis"] = {}
    layout["yaxis"]["showgrid"] = True
    layout["yaxis"]["gridcolor"] = "#3E3F40"
    layout["yaxis"]["gridwidth"] = 1
    layout["yaxis"]["domain"] = [0.5, 1.0]
    layout['paper_bgcolor'] = "#21252C"
    layout['plot_bgcolor'] = "#21252C"

    layout["yaxis2"] = {}
    layout["yaxis2"]["showgrid"] = True
    layout["yaxis2"]["gridcolor"] = "#3E3F40"
    layout["yaxis2"]["gridwidth"] = 1
    layout["yaxis2"]["domain"] = [0, 0.25]

    layout["yaxis3"] = {}
    layout["yaxis3"]["showgrid"] = True
    layout["yaxis3"]["gridcolor"] = "#3E3F40"
    layout["yaxis3"]["gridwidth"] = 1
    layout["yaxis3"]["domain"] = [0.25, 0.5]

    graph = dict(
        data = [
            #go.Ohlc(
            go.Candlestick(
            x=df3.index,
            open=df3["open"],
            high=df3["high"],
            low=df3["low"],
            close=df3["close"],
            showlegend=False,
            name="candlestick",
            # Para ver las barras verde y blanco
            #increasing=dict(line=dict(color="#00ff00")),
            #decreasing=dict(line=dict(color="white")),
            ),
            go.Scatter(
            x=df3.index,
            y=df3['rsi'],
            showlegend=False,
            name="RSI",
            yaxis= "y2",
            ),
            go.Bar(
            x=df3.index,
            y=df3['volume'],
            showlegend=False,
            name="volume",
            yaxis= "y3",
            ),
            # go.Scatter(
            # x=df3.index,
            # y=df3['long_avg'],
            # showlegend=False,
            # name="long_avg",
            # ),
            # go.Scatter(
            # x=df3.index,
            # y=df3['short_avg'],
            # showlegend=False,
            # name="short_avg",
            # ),
            go.Scatter(
            x=df_alza.index,
            y=df_alza['short_avg'],
            showlegend=False,
            name="alza",
            mode='markers',
            marker_color='LightSkyBlue'
            )
    ],
        layout=layout
    )
    
    # Convert the figures to JSON
    graphJSONstring = json.dumps(graph, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSONstring


@app.route('/tradingbot')
def tradingbot():
    graphJSONstring = getInstrument('AAPL', '1Y')
    # Render the Template
    return render_template('tradingbot/index.html', graphJSON=graphJSONstring)


@app.route('/tradingbot/graph', methods=['POST'])
def graph():
    inteval = request.form.get('inteval')
    instrument = request.form.get('instrument')

    if inteval is None:
        inteval = '1Y'
    else:
        inteval = str(inteval)

    if instrument is None:
        instrument = 'AAPL'
    
    graphJSONstring = getInstrument(instrument, inteval)
    graphJSON = json.loads(graphJSONstring)

    # Render the Template
    return jsonify(graphJSON)

# @app.route('/tradingbot/download', methods=['POST'])
# def download():
#     try:
#         instrument = request.form.get('instrument')
#         from_date = request.form.get('from_date')

#         if(instrument is None or from_date is None):
#             # Datos ingresados incorrectos
#             return Response(status=400)

#         thread = Thread(target=download_task, args=(str(instrument), str(from_date)))
#         thread.daemon = True
#         thread.start()
#         return Response(status=200)
#     except Exception as e:
#         print(e)
#         print(traceback.format_exc())
#         return jsonify({'trace': traceback.format_exc()})


@app.route('/tradingbot/download')
def thread():
    try:

        is_running = trading.checkDownloadFlag()
        if is_running == True:
            return Response(status=200)

        trading.backgorund_process()
        trading.clearDownloadFlag()

        return Response(status=200)
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        return jsonify({'trace': traceback.format_exc()})


@app.route('/tradingbot/create_alert', methods=['POST'])
def create_alert():
    try:

        alert_date_str = str(request.form.get('inteval'))
        instrument = str(request.form.get('instrument'))
        current_rsi = float(request.form.get('current_rsi'))
        last_rsi = float(request.form.get('last_rsi'))

        alert_date = datetime.strptime(alert_date_str, "%Y-%m-%d")

        trading.persistAlert(alert_date, instrument, current_rsi, last_rsi)

        return Response(status=200)
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        return jsonify({'trace': traceback.format_exc()})


def download_task(instrument, from_date):
    print('-----------Thread start---------')
    print(f'Download {instrument} from {from_date}')
    i = 0
    while True:
        print(f'Working... {i}')
        i += 1
        time.sleep(1)


@app.route('/')
def index():
    return redirect(url_for('tradingbot'))
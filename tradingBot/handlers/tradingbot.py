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

from threading import Thread
#from uwsgidecorators import thread

import finta

from ..models import trading

from ..app import app

thread_is_running = False

def getDayRecords(instrument):
    # Crear el cursor para poder ejecutar las querys
    conn = sqlite3.connect('instrumentos.db')
    c = conn.cursor()

    dates = c.execute(f"SELECT date FROM {instrument} ORDER BY date DESC").fetchall()
    return dates


def getLastDayRecord(instrument):
    
    try:
        # Crear el cursor para poder ejecutar las querys
        conn = sqlite3.connect('instrumentos.db')
        c = conn.cursor()

        date = c.execute(f"SELECT date FROM {instrument} ORDER BY date DESC").fetchone()[0].split(' ')[0]
        return datetime.strptime(date, '%Y-%m-%d')
    except:
        return datetime.now()


def getInstrument(instrument, interval):

    if interval == '1d':
        days = 1
        resample = '2Min'
    elif interval == '5d':
        days = 5
        resample = '10Min'
    elif interval == '1M':
        days = 30
        resample = '30Min'

    elif interval == '3M':
        days = 90
        resample = '200Min'

    elif interval == '6M':
        days = 180
        resample = '720Min'
    elif interval == '1Y':
        days = 365
        resample = '1D'

    
    last_day_record = getLastDayRecord(instrument)
    #getDayRecords(instrument)

    #from_datetime = datetime.now() - timedelta(days=days)

    from_datetime = last_day_record - timedelta(days=days)
    

    query = f'SELECT * FROM {instrument} WHERE date >= "{from_datetime}"'
    print(query)

    df = pd.read_sql(query, 'sqlite:///instrumentos.db')
    df2 = df.copy()
    df2 = df2.dropna()
    df2['date'] = pd.to_datetime(df2['date'], format="%Y-%m-%d %H:%M:%S")
    df2 = df2.set_index('date')

    #print(df2.head())

    df3 = df2.resample(resample).agg({
        'open':'first',
        'high':'max',
        'low':'min',
        'close':'last',
        'volume':'mean'
    })

    df3 = df3.dropna()
    #print(df3.head(20))

    df3['rsi'] = finta.TA.RSI(df3, 14, 'close')

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
            )
    ],
        layout=layout
    )
    
    # Convert the figures to JSON
    graphJSONstring = json.dumps(graph, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSONstring


@app.route('/tradingbot')
def tradingbot():
    graphJSONstring = getInstrument('endpoints', '1M')
    # Render the Template
    return render_template('tradingbot/index.html', graphJSON=graphJSONstring)


@app.route('/tradingbot/graph', methods=['POST'])
def graph():
    inteval = request.form.get('inteval')

    if inteval is None:
        inteval = '5d'
    else:
        inteval = str(inteval)
    
    graphJSONstring = getInstrument('endpoints', inteval)
    graphJSON = json.loads(graphJSONstring)

    # Render the Template
    return jsonify(graphJSON)

@app.route('/tradingbot/download', methods=['POST'])
def download():
    try:
        instrument = request.form.get('instrument')
        from_date = request.form.get('from_date')

        if(instrument is None or from_date is None):
            # Datos ingresados incorrectos
            return Response(status=400)

        thread = Thread(target=download_task, args=(str(instrument), str(from_date)))
        thread.daemon = True
        thread.start()
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
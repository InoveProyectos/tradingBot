__author__ = "Inove Coding School"
__email__ = "INFO@INOVE.COM.AR"
__version__ = "1.0"

import sys
from datetime import datetime, timedelta
import requests
import pandas as pd
import numpy as np
import sqlalchemy
import sqlite3
import io
import time


class Iex():

    token = 'pk_412392ba96014205a63618a6408a4f14'   # Token created for account at IEXCloud
    def __init__(self, instrument):
        self.instrument = instrument

    def create(self):
        conn = sqlite3.connect('instrumentos.db')

        # Crear el cursor para poder ejecutar las querys
        c = conn.cursor()

        # Crar esquema desde archivo
        c.executescript(open('schema.sql', "r").read())

        # Para salvar los cambios realizados en la DB debemos
        # ejecutar el commit, NO olvidarse de este paso!
        conn.commit()
        # Cerrar la conexión con la base de datos
        conn.close()

    def get(self, date):
        date_str = date.strftime("%Y%m%d")

        
        url = f'https://cloud.iexapis.com/stable/stock/{self.instrument}/chart/date/{date_str}/?token={self.token}&format=csv'
        r = requests.get(url, allow_redirects=True)

        # For each row persist data on database
        # I am sure that it is a way to INSERT all content from an array in one query, I need more
        # expertise on sqlalchemy
        # In case that the csv doesnt contain information I need to catch the excepction
        try:
            df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
        except:
            # Do nothing
            print("No data at " + date_str)
            return None

        # Crear el cursor para poder ejecutar las querys
        conn = sqlite3.connect('instrumentos.db')
        c = conn.cursor()

        for index, row in df.iterrows():
            try:
                date = row['date']
                minute = row['minute']
                open_price = float(row['open'])
                close_price = float(row['close'])
                high_price = float(row['high'])
                low_price = float(row['low'])
                volume = int(row['volume'])

                if volume == 0:
                    continue

                datetime_format = datetime.strptime(date + ' ' + minute, "%Y-%m-%d %H:%M")
                datetime_sql_format = datetime_format.strftime("%Y-%m-%d %H:%M:%S")

                

                result_set = c.execute(f'INSERT INTO {self.instrument}(date,open,close,high,low,volume) VALUES (?,?,?,?,?,?);',
                            (datetime_sql_format, open_price, close_price, high_price, low_price, volume))

                
                        
            except Exception as e:
                print(e)

        c.commit()
        c.close()

        return None



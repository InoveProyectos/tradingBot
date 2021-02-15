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
from datetime import datetime, timedelta

import numpy as np
import finta
from threading import Thread

#pip3 install python-telegram-bot
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

token = None
telegram_token = None

if token is None or telegram_token is None:
    print('Error, create account for IeX and Telegram and replace with your tokens')
    exit(1)

#https://cloud.iexapis.com/stable/stock/AAPL/chart/date/20210209/?token=pk_943d487922124725931c4ce2488e7d02

instruments = ['AAPL', 'FB', 'YPF']

interval_days = 365

def create_table(instrument):
    conn = sqlite3.connect('instrumentos.db')
    c = conn.cursor()

    c.execute(f"DROP TABLE IF EXISTS {instrument};")
    c.execute(f"""
        CREATE TABLE {instrument}(
            date TIMESTAMP WITHOUT TIME ZONE PRIMARY KEY NOT NULL,
            open FLOAT,
            close FLOAT,
            high FLOAT,
            low FLOAT,
            volume INTEGER
        );
                """)

    conn.commit()
    conn.close()


def create_schema():
    conn = sqlite3.connect('instrumentos.db')
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS alert;")
    c.execute("""
                CREATE TABLE alert(
                    date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                    instrument STRING,
                    current_rsi FLOAT,
                    last_rsi FLOAT
                );
                """)

    c.execute("DROP TABLE IF EXISTS config;")
    c.execute("""
                CREATE TABLE config(
                    threadRunning INTEGER,
                    botRunning INTEGER
                );
                """)

    c.execute("DROP TABLE IF EXISTS followers;")
    c.execute("""
                CREATE TABLE followers(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER
                );
                """)

    c.execute("INSERT INTO config (threadRunning, botRunning) VALUES (0,0)")

    conn.commit()
    conn.close()

    # for instrument in instruments:
    #     create_table(instrument)


def tradingbot_callback(update: Update, context: CallbackContext) -> None:
    #update.message.reply_text(f'Hola {update.effective_user.first_name}')
    chat_id = update.message.chat_id
    persistFollower(chat_id)
    update.message.reply_text(f'Suscripción exitosa')


def tradingbot_baja_callback(update: Update, context: CallbackContext) -> None:
    #update.message.reply_text(f'Hola {update.effective_user.first_name}')
    chat_id = update.message.chat_id
    deleteFollower(chat_id)
    update.message.reply_text(f'Esperamos su regreso!')


def tradingbot_historico_callback(update: Update, context: CallbackContext) -> None:
    #update.message.reply_text(f'Hola {update.effective_user.first_name}')
    alerts = getAlerts()
    chat_id = update.message.chat_id
    if len(alerts) > 0:
        update.message.reply_text(f'Últimas {len(alerts)} alertas')
        for alert in alerts:
            alert_date_str, instrument, current_rsi, last_rsi = alert
            alert_date = datetime.strptime(alert_date_str, '%Y-%m-%d %H:%M:%S')
            sendAlert(chat_id, alert_date, instrument, current_rsi, last_rsi)
    else:
        update.message.reply_text(f'No hay alertas registradas, intenta más tarde!')


def getAlerts(limit=10):
    conn = sqlite3.connect('instrumentos.db')
    c = conn.cursor()

    alerts = c.execute(f"SELECT * FROM alert ORDER BY date DESC LIMIT {limit}").fetchall()
    conn.close()
    return alerts


def persistAlert(alert_date, instrument, current_rsi, last_rsi):
    conn = sqlite3.connect('instrumentos.db')
    c = conn.cursor()

    datetime_sql_format = alert_date.strftime("%Y-%m-%d %H:%M:%S")

    values = [datetime_sql_format, instrument, current_rsi, last_rsi]

    c.execute("INSERT INTO alert (date,instrument,current_rsi,last_rsi) VALUES (?,?,?,?)", values)

    conn.commit()
    conn.close()


def getFollowers():
    conn = sqlite3.connect('instrumentos.db')
    c = conn.cursor()

    followers = c.execute(f"SELECT chat_id FROM followers").fetchall()
    conn.close()
    return followers

def persistFollower(chat_id):
    conn = sqlite3.connect('instrumentos.db')
    c = conn.cursor()

    c.execute("INSERT INTO followers (chat_id) VALUES (?)", (chat_id,))

    conn.commit()
    conn.close()


def deleteFollower(chat_id):
    conn = sqlite3.connect('instrumentos.db')
    c = conn.cursor()

    c.execute("DELETE FROM followers WHERE chat_id =?;", (chat_id,))

    conn.commit()
    conn.close()


def sendAlert(chat_id, alert_date, instrument, current_rsi, last_rsi):

    date_str = alert_date.strftime("%Y-%m-%d")
    message = f'{date_str}: {instrument} RSI cambió de {last_rsi} a {current_rsi}'

    try:
        bot_sender = Updater(telegram_token)        
        bot_sender.bot.send_message(chat_id, message)
    except Exception as e:
        e_str = str(e)
        #print(e)


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
        return None


def featch_instrument_csv(instrument, date):
    date_str = date.strftime("%Y%m%d")

    
    url = f'https://cloud.iexapis.com/stable/stock/{instrument}/chart/date/{date_str}/?token={token}&format=csv'
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

            result_set = c.execute(f'INSERT INTO {instrument} (date,open,close,high,low,volume) VALUES (?,?,?,?,?,?);',
                        (datetime_sql_format, open_price, close_price, high_price, low_price, volume))
    
        except Exception as e:
            print(e)

    conn.commit()
    conn.close()

    return None

def analysis_instrument(instrument):
    # Extraer información del insturmento de los
    # últimos 365 días agrupados por días.
    df3, _ = extract_transform_data(instrument)

    print(df3.tail())

    current_rsi = df3['rsi'][-1]
    last_rsi = df3['rsi'][-2]

    create_alert = False

    if last_rsi >= 60 and current_rsi < 60:
        create_alert = True
    elif last_rsi <= 40 and current_rsi > 40:
        create_alert = True
    elif (last_rsi > 50 and current_rsi <= 50) or (last_rsi < 50 and current_rsi >= 50):
        create_alert = True
    else:
        pass

    if create_alert == True:
        alert_date = datetime.now()
        persistAlert(alert_date, instrument, current_rsi, last_rsi)

        followers = getFollowers()
        for follower in followers:
            chat_id = follower[0]
            sendAlert(chat_id, alert_date, instrument, current_rsi, last_rsi)



def featch_instrument(instrument, date):
    date_str = date.strftime("%Y%m%d")
    updated = False

    try:
        url = f'https://cloud.iexapis.com/stable/stock/{instrument}/chart/date/{date_str}/?token={token}'
        r = requests.get(url, allow_redirects=True)
        
        json = r.json()
        if len(json) == 0:
            #print("No data at " + date_str)
            return updated
    except Exception as e:
        e_str = str(e)
        # Do nothing
        #print("No data at " + date_str)
        return updated

    # Crear el cursor para poder ejecutar las querys
    conn = sqlite3.connect('instrumentos.db')
    c = conn.cursor()

    for row in json:
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

            result_set = c.execute(f'INSERT INTO {instrument} (date,open,close,high,low,volume) VALUES (?,?,?,?,?,?);',
                        (datetime_sql_format, open_price, close_price, high_price, low_price, volume))

            updated = True
    
        except Exception as e:
            #print(datetime_sql_format, instrument, e)
            pass
    
    if updated == True:
        print(date_str, instrument, 'downloaded')
    conn.commit()
    conn.close()

    return updated


def download_process():
    instruments_updated = []
    # Evaluar si hay que descargar nueva data de algún instrumento
    try:
        for instrument in instruments:
            last_day_record = getLastDayRecord(instrument)

            if last_day_record is not None:
                elapsed_time = datetime.now() - last_day_record
                if elapsed_time.days > 1:
                    from_datetime = datetime.now() - timedelta(days=elapsed_time.days)
                else:
                    #print(f"Aún no es momento de descargar {instrument}, la información está al día")
                    continue
            else:
                from_datetime = datetime.now() - timedelta(days=interval_days)

            print(f'Downloading {instrument} start from {from_datetime.strftime("%Y-%m-%d %H:%M:%S")}')

            while True:
                updated = featch_instrument(instrument, from_datetime)
                from_datetime = from_datetime + timedelta(days=1)
                
                if updated == True and instrument not in instruments_updated:
                    instruments_updated.append(instrument)

                elapsed_time = datetime.now() - from_datetime
                if elapsed_time.days < 1:
                    break

            print(f'Finish downloading {instrument}')

    except Exception as e:
        print(e)

    return instruments_updated

    
def backgorund_process():

    checkBotFlag()

    instruments_updated = []
    instruments_updated = download_process()
    # Aquellos instrumentos actualizados se someterán a análisis
    try:
        for instrument in instruments_updated:
            print(f'Instrument analysis {instrument}')
            analysis_instrument(instrument)
    except Exception as e:
        print(e)

    # try:
    #     bot_sender = Updater(telegram_token)
    #     followers = getFollowers()
    #     for follower in followers:
    #         bot_sender.bot.send_message(follower[0], 'Probando')
    # except Exception as e:
    #     print(e)


def checkDownloadFlag():
    conn = sqlite3.connect('instrumentos.db')
    c = conn.cursor()

    query = c.execute('SELECT * FROM config').fetchall()

    threadRunning = c.execute('SELECT threadRunning FROM config').fetchone()[0]

    if threadRunning == True:
        #print(f'Thread already running')
        return True

    c.execute("UPDATE config SET threadRunning=1")
    conn.commit()
    conn.close()
    return False


def checkBotFlag():
    conn = sqlite3.connect('instrumentos.db')
    c = conn.cursor()

    botRunning = c.execute('SELECT botRunning FROM config').fetchone()[0]

    if botRunning == True:
        #print(f'Bot already running')
        return True

    updater = Updater(telegram_token)
    updater.dispatcher.add_handler(CommandHandler('tradingbot', tradingbot_callback))
    updater.dispatcher.add_handler(CommandHandler('tradingbot_baja', tradingbot_baja_callback))
    updater.dispatcher.add_handler(CommandHandler('tradingbot_historico', tradingbot_historico_callback))
    updater.start_polling()

    c.execute("UPDATE config SET botRunning=1")
    conn.commit()
    conn.close()
    return False


def clearDownloadFlag():
    conn = sqlite3.connect('instrumentos.db')
    c = conn.cursor()

    c.execute("UPDATE config SET threadRunning=0")
    conn.commit()
    conn.close()

def clearBotFlag():
    conn = sqlite3.connect('instrumentos.db')
    c = conn.cursor()

    c.execute("UPDATE config SET botRunning=0")
    conn.commit()
    conn.close()


def background_task():
    print('-----------Thread start---------')
    i = 0

    while True:
        #print(f'Working... {i}')
        #i += 1
        try:
            requests.get('http://127.0.0.1:5000/tradingbot/download')
        except:
            pass
        time.sleep(3600)


def extract_transform_data(instrument, days=365, resample='1D', rsi_samples=21):
    
    last_day_record = getLastDayRecord(instrument)
    if last_day_record == None:
        last_day_record = datetime.now()

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

    df3['rsi'] = finta.TA.RSI(df3, rsi_samples, 'close')

    # Exponential moving averages using the closing data
    df3['short_avg'] = df3['close'].ewm(span=7, adjust=False).mean()
    df3['long_avg'] = df3['close'].ewm(span=21, adjust=False).mean()

    df3['alza'] = df3.apply(lambda x: x['short_avg'] if x['short_avg'] > x['long_avg'] else -1, axis=1)
    df_alza = df3[df3['alza'] > 0]

    return df3, df_alza


def start():

    conn = sqlite3.connect('instrumentos.db')

    # Crear el cursor para poder ejecutar las querys
    c = conn.cursor()

    try:
        c.execute('SELECT * FROM config')
        conn.close()
    except:
        conn.close()
        create_schema()

    clearDownloadFlag()
    clearBotFlag()

    thread = Thread(target=background_task)
    thread.daemon = True
    thread.start()

start()
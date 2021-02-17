#!/usr/bin/env python
'''
---------------------------
Autor: Inove Coding School
Version: 1.0
 
Descripcion:
Se utiliza request para generar un HTTP post al servidor Flask
'''

__author__ = "Inove Coding School"
__email__ = "INFO@INOVE.COM.AR"
__version__ = "1.0"

import os
import requests

ip = '127.0.0.1'
port = 5000
endpoint = 'tradingbot/create_alert'

url = f'http://{ip}:{port}/{endpoint}'

if __name__ == "__main__":
    try:
        inteval = str(input('Ingrese la fecha en formato %Y-%m-%d:'))
        instrument = str(input('Ingrese el instrumento:'))
        current_rsi = str(input('Ingrese el current RSI:'))
        last_rsi = str(input('Ingrese el last RSI:'))

        post_data = {"inteval": inteval, "instrument": instrument, "current_rsi": current_rsi, "last_rsi": last_rsi}        
        x = requests.post(url, data = post_data)
        print('POST enviado a:',url)
        print('Datos:')
        print(post_data)
    except:
        print('Error, POST no efectuado')
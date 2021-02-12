#!/usr/bin/env python
'''
Monitor cardíaco
---------------------------
Autor: Inove Coding School
Version: 1.0

Descripcion:
Se utiliza Flask para crear un WebServer que levanta los datos de
las personas que registran su ritmo cardíaco.

Ejecución: Lanzar el programa y abrir en un navegador la siguiente dirección URL
NOTA: Si es la primera vez que se lanza este programa crear la base de datos
entrando a la siguiente URL
http://127.0.0.1:5000/monitor/reset

Ingresar a la siguiente URL
http://127.0.0.1:5000/monitor

Nos deberá aparecer el una tabla con todas las personas que registraron
su ritmo cardíaco en el sistema, de cada una podremos ver el historial
cargador.

- Podremos también generar nuevos registros en el sistema ingresando a:
http://127.0.0.1:5000/monitor/registro

Requisitos de instalacion:

- Python 3.x
- Libreriras (incluye los comandos de instalacion)
    pip install numpy
    pip install matplotlib
    pip install pandas
    pip install -U Flask
    pip install paho.mqtt
'''

__author__ = "Inove Coding School"
__email__ = "INFO@INOVE.COM.AR"
__version__ = "1.0"

# Debug
print('__file__={0:<35} | __name__={1:<25} | __package__={2:<25}'.format(__file__,__name__,str(__package__)))

from .app import app


def main():
    try:
        port = int(sys.argv[1]) # This is for a command-line argument
    except:
        port = 5000 # Puerto default

    # bajar el flag
    # lanzar thread
    #    ---> thread levanta el flag


    app.run(host='0.0.0.0', port=port, debug=True)

    # lanza el thread pero se muere solo


if __name__ == '__main__':
    main()
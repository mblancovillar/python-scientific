"""
==================
Final Assignment
==================

Todos los archivos están subidos a campus.
El largo de los registros es entre 10 y 11 minutos
Fs = 512

FECHA DE ENTREGA: 31/05/2026 23:59.59 GMT-3 (7/06/2026 23:59.59 GMT)
x campus
FORMATO DE LA ENTREGA DE ARXIV: https://arxiv.org/help/submit#submissions


|---- BASELINE --------|
|---- PESTANEO ------|
|---- OJOS CERRADOS ----|
|---- MIRAR C/ANTEOJOS ------|
|---- MIRAR S/ANTEOJOS ------|
|---- ESCUCHANDO ESPAÑOL ----|
|---- ESCUCHANDO INGLES ------|

* Baseline: esta parte la pueden utilizar para tener ejemplos negativos de cualquier cosa que deseen detectar.  Por 
ejemplo si quieren detectar que algo cambia cuando hay "imaginación en colores violeta", extraen features de ese momento y de
este e intentan armar un clasificador.
* Pestaneos: los pestaneos son eventos temporales que pueden ser detectados directamente en la señal.
* Ojos cerrados: puede aparecer un aumento de la señal en la banda alfa, la potencia de 10 Hz.
* Mirar s/anteojos o escuchando ingles: puede aparecer un aumento en señales de alta frecuencia (30,40,50 Hz).  Puede aparecer también
un aumento en la potencia de la banda alfa (x aburrimiento).

Objetivo:
El objetivo es dado este registro implementar un análisis de estos datos, exploratorio, superviado 
o no supervisado, para intentar identificar que es lo que el sujeto está haciendo en cada bloque.  Pueden 
intentar separar dos bloques entre sí, un bloque particular frente al BASELINE (esto es el momento cuando el sujeto
no hace nada particular).  Pueden usar una parte de dos bloques para entrenar y luego intentar predecir las otras partes.
Tienen que producir un PDF informe con gráficos/tablas breve y resumido (no más de 4 páginas)

"""

print(__doc__)
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from io import StringIO

# El protocolo experimental que implementamos tiene 2 datasets:
# 1- Dataset de las señales de EEG
# 2- El video de las imágenes (de la grabación de la clase)
#
#
# La idea es tomar estos datasets y derivar de forma automática las diferentes secciones.  Esto se puede hacer en base self-supervised, es
# decir tomar los datos de algún dataset, derivar los labels para cada secciones y luego intentar implementar un clasificador multiclase.
#
# Tienen que entregar un PDF, tipo Markdown con código, gráficos y cualquier insight obtenido del dataset.

signals = pd.read_csv('data/blinking.dat', delimiter=' ', names = ['timestamp','counter','eeg','attention','meditation','blinking'])

print('Estructura de la informacion:')
print(signals.head())

data = signals.values
eeg = data[:,2]

print(eeg)

plt.plot(eeg,'r', label='EEG')
plt.xlabel('t');
plt.ylabel('eeg(t)');
plt.title(r'EEG Signal')     # r'' representa un raw string que no tiene caracteres especiales
plt.ylim([-2000, 2000]);
plt.xlim([0,len(eeg)])
plt.show()
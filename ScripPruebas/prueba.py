# In[1]
import numpy as np
import os
# In[2] Verificar el tamaño del archivo y su formato
archivo = r"C:/ITBA/anal_dat_cien_geo_TP/python-scientific/data/trabajo/baselinecerradosos.dat"

# 1. Verificar tamaño físico del archivo
if os.path.exists(archivo):
    tamano_bytes = os.path.getsize(archivo)
    print(f"Tamaño del archivo: {tamano_bytes / (1024**2):.2f} MB")
else:
    print(f"No se encuentra el archivo {archivo} en el directorio actual.")
# In[3]
# 2. Intentar cargar asumiendo que es una matriz de texto (CSV/TXT común)
try:
    # Probamos leer solo las primeras 5 líneas para ver la estructura
    with open(archivo, 'r') as f:
        print("\n--- Primeras líneas del archivo (si es texto) ---")
        for _ in range(5):
            linea = f.readline()
            if not linea: break
            print(linea.strip())
except Exception as e:
    print(f"\nNo se pudo leer como texto plano: {e}")
# In[4]
# 3. Intentar cargar asumiendo que es un binario de NumPy (.npy o raw float)
try:
    # Intentamos cargar asumiendo floats de 32 bits (muy común en señales)
    data_binaria = np.fromfile(archivo, dtype=np.float32)
    print(f"\n--- Si es binario (float32) ---")
    print(f"Cantidad total de elementos: {len(data_binaria)}")
    # Como Fs = 512 y son 3 bloques de 3 min (9 min totales = 276480 muestras por canal)
    # Podemos deducir canales estimando: len(data_binaria) / (9 * 60 * 512)
    muestras_estimadas = 9 * 60 * 512
    canales_estimados = len(data_binaria) / muestras_estimadas
    print(f"Canales estimados basados en tiempo: {canales_estimados}")
except Exception as e:
    print(f"No se pudo analizar como binario float32: {e}")

#--------------------------------------------------------------------

# In[5]

import numpy as np

archivo = r"C:/ITBA/anal_dat_cien_geo_TP/python-scientific/data/trabajo/baselinecerradosos.dat"

try:
    # Cargamos el archivo completo en una matriz de NumPy
    data = np.loadtxt(archivo)
    
    # Vemos las dimensiones (Filas, Columnas)
    filas, columnas = data.shape
    print(f"Dimensiones de la matriz: {filas} filas por {columnas} columnas.")
    
    # Calculamos la duración real registrada basada en las filas y Fs = 512
    Fs = 512
    duracion_segundos = filas / Fs
    duracion_minutos = duracion_segundos / 60
    print(f"Duración estimada del registro: {duracion_segundos:.2f} segundos ({duracion_minutos:.2f} minutos)")
    
    # Verificamos si hay valores distintos de cero en las columnas de datos (de la columna index 2 en adelante)
    print("\nValores máximos por columna para chequear actividad:")
    for i in range(columnas):
        print(f"  Columna {i}: Max = {np.max(data[:, i])}, Min = {np.min(data[:, i])}")

except Exception as e:
    print(f"Error al procesar el archivo completo: {e}")

# In[6]
import numpy as np
import matplotlib.pyplot as plt

# Cargar datos
data = np.loadtxt(r"C:/ITBA/anal_dat_cien_geo_TP/python-scientific/data/trabajo/baselinecerradosos.dat")
eeg = data[:, 2]        # Canal de EEG
marca_1 = data[:, 3]    # Marca columna 3
marca_2 = data[:, 4]    # Marca columna 4
tiempo = (data[:, 0] - data[:, 0][0])  # Tiempo relativo en segundos (empieza en 0)

# Graficar para inspeccionar visualmente
plt.figure(figsize=(12, 6))

plt.subplot(2, 1, 1)
plt.plot(tiempo, eeg, color='blue', alpha=0.7)
plt.title("Canal de EEG Raw (Columna 2)")
plt.ylabel("Amplitud (Digital Counts)")
plt.grid(True)

plt.subplot(2, 1, 2)
plt.plot(tiempo, marca_1, label="Marca Col 3", color='red')
plt.plot(tiempo, marca_2, label="Marca Col 4", color='green')
plt.title("Columnas de Marcas / Triggers")
plt.xlabel("Tiempo (segundos)")
plt.ylabel("Valor de Marca")
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()

# ---------------------------------------------------------------
# In[7]
import numpy as np
import matplotlib.pyplot as plt

# Cargar datos
data = np.loadtxt(r"C:/ITBA/anal_dat_cien_geo_TP/python-scientific/data/trabajo/baselinecerradosos.dat")
eeg = data[:, 2]        # Canal de EEG
marca_1 = data[:, 3]    # Marca columna 3
marca_2 = data[:, 4]    # Marca columna 4
tiempo = (data[:, 0] - data[:, 0][0])  # Tiempo relativo en segundos (empieza en 0)

# Graficar para inspeccionar visualmente
plt.figure(figsize=(12, 6))

plt.subplot(2, 1, 1)
plt.plot(tiempo, eeg, color='blue', alpha=0.7)
plt.title("Canal de EEG Raw (Columna 2)")
plt.ylabel("Amplitud (Digital Counts)")
plt.grid(True)

plt.subplot(2, 1, 2)
plt.plot(tiempo, marca_1, label="Marca Col 3", color='red')
plt.plot(tiempo, marca_2, label="Marca Col 4", color='green')
plt.title("Columnas de Marcas / Triggers")
plt.xlabel("Tiempo (segundos)")
plt.ylabel("Valor de Marca")
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()

# -------------------------------------------------------------------
# In[8]
import pandas as pd
import numpy as np

# 1. Carga de datos con Pandas (como en el helloworld notebook)
nombres_columnas = ['timestamp', 'counter', 'eeg', 'attention', 'meditation', 'vacia']
df = pd.read_csv(r'C:/ITBA/anal_dat_cien_geo_TP/python-scientific/data/trabajo/baselinecerradosos.dat', delimiter=' ', names=nombres_columnas)

# Extraemos los vectores de interés
counter = df['counter'].values
eeg_raw = df['eeg'].values
Fs = 512

print("--- 1. RECONSTRUCCIÓN DEL COUNTER ---")
eeg_reparado = eeg_raw.copy()
saltos = 0
for i in range(1, len(counter)):
    esperado = (counter[i-1] + 1) % 100
    if counter[i] != esperado:
        saltos += 1
        if i < len(counter) - 1:
            eeg_reparado[i] = (eeg_raw[i-1] + eeg_raw[i+1]) / 2
print(f"Muestras perdidas interpoladas: {saltos}")

print("\n--- 2. RECONSTRUCCIÓN DEL TIEMPO REAL ---")
# Fórmula oficial del apunte: t = t0 + n / Fs
muestras_totales = len(df)
tiempo_reconstruido = np.array([i / Fs for i in range(muestras_totales)])
print(f"Base de tiempo generada: de 0.0s a {tiempo_reconstruido[-1]:.2f}s")

print("\n--- 3. SEGMENTACIÓN DE TRÁMEDS (1 MINUTO C/U) ---")
# Cada tramo dura exactamente 1 minuto (60 segundos)
muestras_por_minuto = 60 * Fs  # 30720 muestras

# Cortamos según el protocolo de Alejandro
bloque_sos = eeg_reparado[0 : muestras_por_minuto]
bloque_ojos_cerrados = eeg_reparado[muestras_por_minuto : 2 * muestras_por_minuto]
bloque_baseline = eeg_reparado[2 * muestras_por_minuto : 3 * muestras_por_minuto]

print(f"Tamaño Bloque 1 (S.O.S): {len(bloque_sos)} muestras")
print(f"Tamaño Bloque 2 (Ojos Cerrados): {len(bloque_ojos_cerrados)} muestras")
print(f"Tamaño Bloque 3 (Baseline): {len(bloque_baseline)} muestras")

#----------------------------------------------------------------
# %%
import matplotlib.pyplot as plt
from scipy.signal import welch

# 1. Calcular la densidad espectral de potencia usando el Método de Welch (oficial de clase)
# Usamos ventanas estándar de 512 muestras (1 segundo por ventana)
nperseg = 512
frecuencias_oc, psd_oc = welch(bloque_ojos_cerrados, fs=Fs, nperseg=nperseg)
frecuencias_bl, psd_bl = welch(bloque_baseline, fs=Fs, nperseg=nperseg)

# 2. Graficar la comparación de los espectros
plt.figure(figsize=(10, 5))
plt.plot(frecuencias_bl, psd_bl, label='Baseline (Ojos Abiertos)', color='blue', alpha=0.8)
plt.plot(frecuencias_oc, psd_oc, label='Ojos Cerrados (Ritmo Alfa)', color='red', alpha=0.8)

# Configuraciones del gráfico para el informe tipo arXiv
plt.title("Densidad Espectral de Potencia (PSD) - Método de Welch")
plt.xlabel("Frecuencia (Hz)")
plt.ylabel("Potencia Espectral (V^2 / Hz)")
plt.xlim([1, 40]) # Acotamos hasta 40 Hz para ver claramente las bandas principales (Delta, Theta, Alpha, Beta)
plt.axvspan(8, 13, color='gray', alpha=0.2, label='Banda Alfa (8-13 Hz)') # Resaltamos la banda clave
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()

# 3. Extraer una feature simple (Potencia media en Banda Alfa) para el informe
idx_alfa = (frecuencias_oc >= 8) & (frecuencias_oc <= 13)
potencia_alfa_oc = np.mean(psd_oc[idx_alfa])
potencia_alfa_bl = np.mean(psd_bl[idx_alfa])

print("--- EXTRAECCIÓN DE FEATURES PARA EL INFORME ---")
print(f"Potencia media en Banda Alfa (Ojos Cerrados): {potencia_alfa_oc:.2f}")
print(f"Potencia media en Banda Alfa (Baseline): {potencia_alfa_bl:.2f}")
print(f"Incremento relativo de potencia: {(potencia_alfa_oc / potencia_alfa_bl):.2f} veces mayor en ojos cerrados.")

# In[9]:
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import welch

# ==========================================
# 1. CARGA DE DATOS (Pipeline Oficial)
# ==========================================
nombres_columnas = ['timestamp', 'counter', 'eeg', 'attention', 'meditation', 'vacia']
# Usamos tu ruta absoluta corregida
df = pd.read_csv(r'C:/ITBA/anal_dat_cien_geo_TP/python-scientific/data/trabajo/baselinecerradosos.dat', delimiter=' ', names=nombres_columnas)

counter = df['counter'].values
eeg_raw = df['eeg'].values
Fs = 512

# ==========================================
# 2. SANEAMIENTO (Counter e Interpolación)
# ==========================================
eeg_reparado = eeg_raw.copy()
saltos = 0
for i in range(1, len(counter)):
    if counter[i] != (counter[i-1] + 1) % 100:
        saltos += 1
        if i < len(counter) - 1:
            eeg_reparado[i] = (eeg_raw[i-1] + eeg_raw[i+1]) / 2

# ==========================================
# 3. SEGMENTACIÓN QUIRÚRGICA (Protocolo Alejandro)
# ==========================================
muestras_por_minuto = 60 * Fs  # 30720 muestras por tramo de 1 minuto
bloque_oc = eeg_reparado[muestras_por_minuto : 2 * muestras_por_minuto]
bloque_bl = eeg_reparado[2 * muestras_por_minuto : 3 * muestras_por_minuto]

# ==========================================
# 4. ANÁLISIS ESPECTRAL (Método de Welch)
# ==========================================
nperseg = 512
f, psd_oc = welch(bloque_oc, fs=Fs, nperseg=nperseg)
f, psd_bl = welch(bloque_bl, fs=Fs, nperseg=nperseg)

# ==========================================
# 5. NUEVA MÉTRICA: POTENCIA RELATIVA (RBP)
# ==========================================
# Definimos los índices de la banda Alfa (8-13 Hz) y de la Banda Total Útil (1-40 Hz)
idx_alfa = (f >= 8) & (f <= 13)
idx_total = (f >= 1) & (f <= 40)

# Calculamos la proporción de energía (Área bajo la curva de Alfa / Área Total)
rbp_oc = np.sum(psd_oc[idx_alfa]) / np.sum(psd_oc[idx_total])
rbp_bl = np.sum(psd_bl[idx_alfa]) / np.sum(psd_bl[idx_total])

print("--- NUEVOS RESULTADOS PARA EL INFORME MEJORADO ---")
print(f"Potencia Relativa (RBP) en Ojos Cerrados: {rbp_oc:.4f} ({rbp_oc*100:.2f}% de la energía total)")
print(f"Potencia Relativa (RBP) en Baseline: {rbp_bl:.4f} ({rbp_bl*100:.2f}% de la energía total)")
print(f"Relación de mejora normalizada: {rbp_oc / rbp_bl:.2f} veces a favor de Ojos Cerrados.")
# %%
import pandas as pd
import numpy as np
from scipy.signal import welch
from sklearn.linear_model import LogisticRegression

# -----------------------------------------------------------------
# PASO 1: Carga y preprocesamiento del Dataset de Validación
# -----------------------------------------------------------------
nombres_col = ['timestamp', 'counter', 'eeg', 'attention', 'meditation', 'vacia']
Fs = 512
muestras_por_minuto = 60 * Fs

def procesar_archivo_dat(ruta_archivo):
    df = pd.read_csv(ruta_archivo, delimiter=' ', names=nombres_col)
    counter = df['counter'].values
    eeg_raw = df['eeg'].values
    
    # Saneamiento del canal por interpolación vecinal
    eeg_reparado = eeg_raw.copy()
    for i in range(1, len(counter)):
        if counter[i] != (counter[i-1] + 1) % 100:
            if i < len(counter) - 1:
                eeg_reparado[i] = (eeg_raw[i-1] + eeg_raw[i+1]) / 2
                
    # Segmentación en 3 bloques de 1 minuto cada uno
    bloque_1 = eeg_reparado[0 : muestras_por_minuto]
    bloque_2 = eeg_reparado[muestras_por_minuto : 2 * muestras_por_minuto]
    bloque_3 = eeg_reparado[2 * muestras_por_minuto : 3 * muestras_por_minuto]
    return bloque_1, bloque_2, bloque_3

# Procesamos los archivos requeridos
_, bloque_oc, bloque_bl = procesar_archivo_dat(r'C:/ITBA/anal_dat_cien_geo_TP/python-scientific/data/trabajo/baselinecerradosos.dat')
b_gusta, b_nogusta, b_query = procesar_archivo_dat(r'C:/ITBA/anal_dat_cien_geo_TP/python-scientific/data/trabajo/gustanogustaquery.dat')

# -----------------------------------------------------------------
# PASO 2: Extracción de Características Espectrales (Feature Engineering)
# -----------------------------------------------------------------
def extraer_features_ventanas(eeg_bloque, tam_ventana=512):
    features = []
    # Segmentación en ventanas continuas (1 segundo de duración)
    for i in range(0, len(eeg_bloque), tam_ventana):
        ventana = eeg_bloque[i:i+tam_ventana]
        if len(ventana) < tam_ventana: break
        
        f, psd = welch(ventana, fs=Fs, nperseg=256)
        idx_alfa = (f >= 8) & (f <= 13)
        idx_gamma = (f >= 30) & (f <= 50)
        idx_total = (f >= 1) & (f <= 40)
        
        # Computamos Potencias Relativas en Banda (RBP)
        rbp_alfa = np.sum(psd[idx_alfa]) / np.sum(psd[idx_total])
        rbp_gamma = np.sum(psd[idx_gamma]) / np.sum(psd[idx_total])
        features.append([rbp_alfa, rbp_gamma])
        
    return np.array(features)

X_gusta = extraer_features_ventanas(b_gusta)
X_nogusta = extraer_features_ventanas(b_nogusta)
X_query = extraer_features_ventanas(b_query)

# -----------------------------------------------------------------
# PASO 3: Entrenamiento del Clasificador BCI y Predicción de Query
# -----------------------------------------------------------------
# Construcción del set de entrenamiento supervisado
X_train = np.vstack((X_gusta, X_nogusta))
y_train = np.concatenate((np.ones(len(X_gusta)), np.zeros(len(X_nogusta)))) # 1 = GUSTA, 0 = NO GUSTA

# Clasificador lineal robusto (Regresión Logística)
clf = LogisticRegression(solver='lbfgs')
clf.fit(X_train, y_train)

# Predicción sobre las ventanas de la canción query
y_pred_query = clf.predict(X_query)
porcentaje_nogusta = (np.sum(y_pred_query == 0) / len(y_pred_query)) * 100

print("\n--- RESULTADOS DEL CLASIFICADOR DE PREFERENCIA MUSICAL ---")
print(f"Total de ventanas evaluadas en la canción QUERY: {len(X_query)}")
print(f"Ventanas clasificadas como NO GUSTA: {np.sum(y_pred_query == 0)} ({porcentaje_nogusta:.2f}%)")
print(f"Ventanas clasificadas como GUSTA: {np.sum(y_pred_query == 1)} ({100 - porcentaje_nogusta:.2f}%)")

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, welch
from sklearn.linear_model import LogisticRegression

# -----------------------------------------------------------------
# 1. CARGA DE DATOS Y SANEAMIENTO (Pipeline Oficial)
# -----------------------------------------------------------------
nombres_col = ['timestamp', 'counter', 'eeg', 'attention', 'meditation', 'vacia']
Fs = 512

# Cargamos el archivo de música
df_musica = pd.read_csv(r'C:/ITBA/anal_dat_cien_geo_TP/python-scientific/data/trabajo/gustanogustaquery.dat', delimiter=' ', names=nombres_col)
counter = df_musica['counter'].values
eeg_raw = df_musica['eeg'].values

# Saneamiento del canal por interpolación vecinal (Muestras perdidas)
eeg_reparado = eeg_raw.copy()
saltos = 0
for i in range(1, len(counter)):
    if counter[i] != (counter[i-1] + 1) % 100:
        saltos += 1
        if i < len(counter) - 1:
            eeg_reparado[i] = (eeg_raw[i-1] + eeg_raw[i+1]) / 2

# Base de tiempo real reconstructiva
tiempo = np.array([i / Fs for i in range(len(df_musica))])

# -----------------------------------------------------------------
# 2. DETECCIÓN DE PARPADEOS DE MARCA (Segmentación Precisa)
# -----------------------------------------------------------------
# Criterio estadístico dictado en clase: media + 3 desvíos estándar
media = np.mean(eeg_reparado)
desvio = np.std(eeg_reparado)
umbral_marcas = media + 3 * desvio

# Detectamos los picos de los parpadeos voluntarios (marcas de transición)
picos_indices, _ = find_peaks(eeg_reparado, height=umbral_marcas, distance=Fs*10)

print("--- 1. PREPROCESAMIENTO Y SEGMENTACIÓN ---")
print(f"Muestras perdidas corregidas en el counter: {saltos}")
print(f"Índices temporales de marcas detectadas (segundos): {tiempo[picos_indices]}")

# Segmentación dinámica basada en los parpadeos reales detectados
# El protocolo consistía en: Bloque 1 (Gusta) -> Marca 1 -> Bloque 2 (No Gusta) -> Marca 2 -> Bloque 3 (Query)
b_gusta = eeg_reparado[0 : picos_indices[0]]
b_nogusta = eeg_reparado[picos_indices[0] : picos_indices[1]]
b_query = eeg_reparado[picos_indices[1] : : ]

# -----------------------------------------------------------------
# 3. EXTRAECCIÓN DE FEATURES ESPECTRALES (Welch)
# -----------------------------------------------------------------
def extraer_features_ventanas(eeg_bloque, tam_ventana=512):
    features = []
    for i in range(0, len(eeg_bloque), tam_ventana):
        ventana = eeg_bloque[i:i+tam_ventana]
        if len(ventana) < tam_ventana: break
        
        # Método de Welch para estimar la densidad espectral de potencia (PSD)
        f, psd = welch(ventana, fs=Fs, nperseg=256)
        idx_alfa = (f >= 8) & (f <= 13)
        idx_gamma = (f >= 30) & (f <= 50)
        idx_total = (f >= 1) & (f <= 40)
        
        # Métrica de ingeniería: Potencia Espectral Relativa (RBP)
        rbp_alfa = np.sum(psd[idx_alfa]) / np.sum(psd[idx_total])
        rbp_gamma = np.sum(psd[idx_gamma]) / np.sum(psd[idx_total])
        features.append([rbp_alfa, rbp_gamma])
    return np.array(features)

X_gusta = extraer_features_ventanas(b_gusta)
X_nogusta = extraer_features_ventanas(b_nogusta)
X_query = extraer_features_ventanas(b_query)

# -----------------------------------------------------------------
# 4. ENTRENAMIENTO DEL CLASIFICADOR Y PREDICCIÓN DE CANCIÓN QUERY
# -----------------------------------------------------------------
X_train = np.vstack((X_gusta, X_nogusta))
y_train = np.concatenate((np.ones(len(X_gusta)), np.zeros(len(X_nogusta)))) # 1 = GUSTA, 0 = NO GUSTA

clf = LogisticRegression(solver='lbfgs')
clf.fit(X_train, y_train)

y_pred_query = clf.predict(X_query)
porcentaje_nogusta = (np.sum(y_pred_query == 0) / len(y_pred_query)) * 100

print("\n--- 2. CLASIFICADOR DE PREFERENCIA MUSICAL (QUERY) ---")
print(f"Ventanas evaluadas en QUERY: {len(X_query)}")
print(f"Predicción final: {porcentaje_nogusta:.2f}% NO GUSTA | {100 - porcentaje_nogusta:.2f}% GUSTA")

# -----------------------------------------------------------------
# 5. GENERACIÓN DE LA FIGURA DE LA SEÑAL TEMPORAL CRUDA
# -----------------------------------------------------------------
plt.figure(figsize=(12, 5))
plt.plot(tiempo, eeg_reparado, color='blue', alpha=0.7, label='EEG Saneado')
plt.axhline(umbral_marcas, color='red', linestyle='--', label=f'Umbral Adaptativo ({umbral_marcas:.1f} uV)')
plt.scatter(tiempo[picos_indices], eeg_reparado[picos_indices], color='black', marker='x', s=100, zorder=5, label='Marcas de Parpadeo Detectadas')

# Líneas divisorias de los bloques experimentales
for idx in picos_indices:
    plt.axvline(tiempo[idx], color='green', linestyle=':', alpha=0.8)

plt.title("Señal Temporal de EEG Cruda - Registro de Preferencia Musical")
plt.xlabel("Tiempo (segundos)")
plt.ylabel("Amplitud (uV)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('grafico_senal_temporal.png') # Guardamos para subir a Overleaf
plt.show()
# %%
import matplotlib.pyplot as plt

plt.figure(figsize=(7, 5))
plt.scatter(X_gusta[:, 0], X_gusta[:, 1], color='blue', marker='o', alpha=0.7, label='Gusta (Control +)')
plt.scatter(X_nogusta[:, 0], X_nogusta[:, 1], color='red', marker='x', alpha=0.7, label='No Gusta (Control -)')
plt.scatter(X_query[:, 0], X_query[:, 1], color='orange', marker='^', alpha=0.8, label='Query (Incógnita)')
plt.xlabel('RBP Alfa (8-13 Hz)')
plt.ylabel('RBP Gamma (30-50 Hz)')
plt.title('Distribución de Características Espectrales (Separabilidad BCI)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('grafico_scatterplot.png')
plt.show()
# %%
import pandas as pd
import numpy as np
from scipy.signal import find_peaks, welch
from sklearn.linear_model import LogisticRegression

# Saneamiento de tramas de red e interpolacion lineal vecinal
def procesar_eeg(ruta):
    df = pd.read_csv(ruta, delimiter=' ', names=['timestamp', 'counter', 'eeg', 'att', 'med', 'v'])
    counter, eeg_raw, Fs = df['counter'].values, df['eeg'].values, 512
    eeg_rep = eeg_raw.copy()
    for i in range(1, len(counter)):
        if counter[i] != (counter[i-1] + 1) % 100 and i < len(counter) - 1:
            eeg_rep[i] = (eeg_raw[i-1] + eeg_raw[i+1]) / 2
    return eeg_rep

eeg_musica = eeg_musica = procesar_eeg(r"C:\Users\maxim\OneDrive\Documentos\ITBA\CURSADA\Análisis de Datos Científicos y Geográficos\TP\Trabajo Individual señales\gustanogustaquery.dat")
Fs = 512

# Segmentacion automatizada por umbral adaptativo (Media + 3 Sigma)
picos, _ = find_peaks(eeg_musica, height=np.mean(eeg_musica)+3*np.std(eeg_musica), distance=Fs*10)
b_gusta = eeg_musica[0 : picos[0]]
b_nogusta = eeg_musica[picos[0] : picos[1]]
b_query = eeg_musica[picos[1] : : ]

# Extraccion de Caracteristicas Espectrales de Potencia Relativa (RBP)
def extraer_features(bloque, Fs=512):
    feat = []
    for i in range(0, len(bloque), Fs):
        ventana = bloque[i:i+Fs]
        if len(ventana) < Fs: break
        f, psd = welch(ventana, fs=Fs, nperseg=256)
        tot = np.sum(psd[(f >= 1) & (f <= 40)])
        rbp_alfa = np.sum(psd[(f >= 8) & (f <= 13)]) / tot
        rbp_gamma = np.sum(psd[(f >= 30) & (f <= 50)]) / tot
        feat.append([rbp_alfa, rbp_gamma])
    return np.array(feat)

X_gusta, X_nogusta, X_query = extraer_features(b_gusta), extraer_features(b_nogusta), extraer_features(b_query)

# Modelado de clasificacion supervisada BCI
X_train = np.vstack((X_gusta, X_nogusta))
y_train = np.concatenate((np.ones(len(X_gusta)), np.zeros(len(X_nogusta))))

clf = LogisticRegression(solver='lbfgs')
clf.fit(X_train, y_train)
y_pred = clf.predict(X_query)
print(f"Prediccion QUERY: {np.sum(y_pred == 0)/len(y_pred)*100:.2f}% NO GUSTA")
# %%

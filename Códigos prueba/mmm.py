import numpy as np
from scipy.signal import find_peaks
import serial
import time

# Configura el puerto serie
ser = serial.Serial('COM4', 115200)  # Asegúrate de seleccionar el puerto COM correcto

def calculate_bpm(values, fs):
    # Aplica la transformada de Fourier
    fft = np.fft.rfft(values)
    
    # Encuentra las frecuencias
    frequencies = np.fft.rfftfreq(len(values), 1/fs)
    
    # Encuentra los picos en el espectro de frecuencias
    peaks, _ = find_peaks(np.abs(fft))
    
    # Encuentra la frecuencia del pico más grande (excluyendo la frecuencia cero)
    peak_frequency = frequencies[peaks[1]]
    
    # Convierte la frecuencia a BPM
    bpm = peak_frequency * 60
    
    return bpm

# Configura la ventana deslizante
window_size = 1000  # Tamaño de la ventana en muestras
window = []

while True:
    try:
        # Lee una línea del puerto serie
        line = ser.readline().decode('utf-8').strip()
        
        # Convierte la línea a un número entero
        value = int(line)
        
        # Añade el valor a la ventana
        window.append(value)
        
        # Si la ventana es demasiado grande, quita el valor más antiguo
        if len(window) > window_size:
            window.pop(0)
        
        # Si la ventana está llena, calcula el BPM
        if len(window) == window_size:
            bpm = calculate_bpm(window, fs=1000)  # Asegúrate de usar la frecuencia de muestreo correcta
            print('BPM:', bpm)
        
        # Espera un poco antes de la próxima muestra
        time.sleep(0.001)
        
    except Exception as e:
        print(e)

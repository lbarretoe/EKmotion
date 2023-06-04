import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from collections import deque
import serial

class ECGApp:
    def __init__(self, master):
        self.master = master
        self.master.title("ECG Monitor")
        
        # Deques para almacenar los valores y tiempos
        self.ecg_values = deque(maxlen=100)
        self.times = deque(maxlen=100)

        # Frame para el plot
        self.plot_frame = tk.Frame(master)
        self.plot_frame.grid(row=0, column=0)

        # Frame para los botones
        self.button_frame = tk.Frame(master)
        self.button_frame.grid(row=0, column=1)

        # Configurando plot
        self.fig = Figure(figsize=(5, 5), dpi=100)
        self.ecg_plot = self.fig.add_subplot(111)
        self.line, = self.ecg_plot.plot([], [])
        self.canvas = FigureCanvasTkAgg(self.fig, self.plot_frame) 
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Botones
        self.start_button = tk.Button(self.button_frame, text="Iniciar grabación", command=self.start_recording)
        self.start_button.pack(side=tk.TOP)

        self.stop_button = tk.Button(self.button_frame, text="Parar grabación", command=self.stop_recording)
        self.stop_button.pack(side=tk.TOP)
        
        # Inicialización del tiempo
        self.t = 0

        # Configuración de la comunicación serial
        self.port = 'COM13'   # '/dev/ttyS0'  # puerto serial del ESP32 conectado al Raspberry Pi
        self.baud_rate = 9600
        self.data_bits = serial.EIGHTBITS  # número de bits de datos
        self.parity = serial.PARITY_NONE  # tipo de paridad
        self.stop_bits = serial.STOPBITS_ONE  # número de bits de parada

        # Abre el puerto serial. 
        self.ser = serial.Serial(self.port, self.baud_rate, self.data_bits, self.parity, self.stop_bits)

    def start_recording(self):
        self.recording = True
        self.update_plot()

    def stop_recording(self):
        self.recording = False
        # Cierra el puerto serial cuando se interrum> pe el programa.
        print("\nPrograma interrumpido. Cerrando el puerto serial...")
        self.ser.close()

    def update_plot(self):
        if self.recording:
            # Si hay datos disponibles para leer, entonces léelos.
            if self.ser.in_waiting > 0:
                data = self.ser.readline()
                value = float(data.decode('utf-8').strip())  # Decodifica los datos y elimina espacios en blanco al final.
                
                # Agrega el valor y el tiempo a las listas
                self.ecg_values.append(value)
                self.times.append(self.t)
                
                # Incrementa el tiempo
                self.t += 0.01
                
                # Actualiza los datos del gráfico
                self.line.set_data(self.times, self.ecg_values)
                
                # Ajusta los límites del gráfico si hay más de un punto
                if len(self.times) > 1 and len(self.ecg_values) > 1:
                    self.ecg_plot.set_xlim(min(self.times), max(self.times))
                    self.ecg_plot.set_ylim(min(self.ecg_values), max(self.ecg_values))
                
                # Actualiza el canvas
                self.canvas.draw()

            # Programa la próxima actualización
            self.master.after(50, self.update_plot)  # Actualiza cada 50 ms

root = tk.Tk()
app = ECGApp(root)
root.mainloop()

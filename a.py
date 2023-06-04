import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from collections import deque

class ECGApp:
    def __init__(self, master):
        self.master = master
        self.master.title("ECG Monitor")
        
        # Deques para almacenar los valores y tiempos
        self.ecg_values = deque(maxlen=100)
        self.times = deque(maxlen=100)

        # Frame para el plot
        self.plot_frame = tk.Frame(master)
        self.plot_frame.pack(side=tk.TOP)

        # Frame para los botones
        self.button_frame = tk.Frame(master)
        self.button_frame.pack(side=tk.BOTTOM)

        # Configurando plot
        self.fig = Figure(figsize=(5, 5), dpi=100)
        self.ecg_plot = self.fig.add_subplot(111)
        self.line, = self.ecg_plot.plot([], [])
        self.canvas = FigureCanvasTkAgg(self.fig, self.plot_frame) 
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Botones
        self.start_button = tk.Button(self.button_frame, text="Iniciar grabación", command=self.start_recording)
        self.start_button.pack(side=tk.LEFT)

        self.stop_button = tk.Button(self.button_frame, text="Parar grabación", command=self.stop_recording)
        self.stop_button.pack(side=tk.LEFT)
        
        # Inicialización del tiempo
        self.t = 0

    def start_recording(self):
        self.recording = True
        self.update_plot()

    def stop_recording(self):
        self.recording = False

    def update_plot(self):
        if self.recording:
            # Genera el valor de la onda sinusoidal
            value = np.sin(2 * np.pi * 5 * self.t)
            
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

import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import time
import scipy
import os
import serial


# tiempo manual
# ejes, grid, 

class EKmotionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ECG Monitor")
        self.width = 800
        self.height = 400
        self.geometry(f"{self.width}x{self.height}")
        self.b_bg = "#FFFFFF"
        self.configure(bg=self.b_bg)
        self.sv_file_prefix = "./saves/"
        # Inicialización del tiempo
        self.t = 0
        
        # tiempo 
        self.max_time = self.t
        self.view_width = 5;
        # vars
        self.scale_time = tk.IntVar()
        self.scale_time.set(0)
        self.bpm_var = tk.StringVar()
        self.bpm_var.set("--")
        self.patient_entries_lst = ["Nombre", "ID", "Edad", "Sexo", "BP_num", "BP_den", "Altura", "Peso", "Condicion", "Medicacion"]
        self.patient_data = {k:tk.StringVar() for k in self.patient_entries_lst}
        for key in self.patient_data:
            self.patient_data[key].set("--")
        self.patient_data["Nombre"].set("Paciente")
        self.patient_data["ID"].set("001")
        self.ecg_values = []
        self.times = []
        # pantalla inicio
        self.frame = tk.Frame(self,bg=self.b_bg, width=self.width, height=self.height)
        self.frame.pack(ipady=0)
        self.port = 'COM13'   # '/dev/ttyS0'  # puerto serial del ESP32 conectado al Raspberry Pi
        self.baud_rate = 115200
        self.data_bits = serial.EIGHTBITS  # número de bits de datos
        self.parity = serial.PARITY_NONE  # tipo de paridad
        self.stop_bits = serial.STOPBITS_ONE  # número de bits de parada

        # Abre el puerto serial. 
        self.ser = serial.Serial(self.port, self.baud_rate, self.data_bits, self.parity, self.stop_bits)

        self.main_window()
        

    def main_window(self):
        self.frame.destroy()
        self.frame = tk.Frame(self,bg=self.b_bg, width=self.width, height=self.height)
        self.frame.pack(ipady=0)
        # Frame para el plot
        self.plot_frame = tk.Frame(self.frame, bg=self.b_bg)
        self.plot_frame.grid(row=0, column=0, rowspan=4, columnspan=8)  

        # Frame para los botones
        self.button_frame = tk.Frame(self.frame, bg=self.b_bg)
        self.button_frame.grid(row=0, column=8, rowspan=3) 
        # frame para labels
        self.label_frame = tk.Frame(self.frame, bg=self.b_bg)
        self.label_frame.grid(row=3, column=8, rowspan=2)

        # Configurando plot
        
        self.fig = Figure(figsize=(6, 3), dpi=100, facecolor=self.b_bg)
        self.ecg_plot = self.fig.add_subplot(111)
        self.line, = self.ecg_plot.plot([], [])
        
        self.canvas = FigureCanvasTkAgg(self.fig, self.plot_frame) 
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        if len(self.times) > 0:
            self.line.set_data(self.times, self.ecg_values)
            xllim = max(self.times) - self.view_width 
            xllim = 0 if xllim < 0 else xllim
            self.ecg_plot.set_xlim(xllim, max(self.times))
            self.ecg_plot.set_ylim(min(self.ecg_values), max(self.ecg_values))
            self.canvas.draw()

        # Botones
        # frame grabacion
        self.rec_f = tk.Frame(self.button_frame, bg=self.b_bg)
        # botones ahora si
        self.start_button = tk.Button(self.rec_f, text="▶", command=self.start_recording, font=("Arial", 15))
        self.start_button.pack(side=tk.LEFT, padx=10)  # 

        self.stop_button = tk.Button(self.rec_f, text="⏸", command=self.stop_recording, font=("Arial", 15))
        self.stop_button.pack(side=tk.RIGHT, padx=10)  # 
        self.rec_f.pack(side=tk.TOP)
        
        self.ac_b = tk.Button(self.button_frame, text="Iniciar adquisición", command=self.start_acquisition, width=15)
        self.ac_b.pack(side=tk.TOP, pady=6)  # 

        self.s_ac_b = tk.Button(self.button_frame, text="Pausar adquisición", command=self.stop_acquisition, width=15)
        self.s_ac_b.pack(side=tk.TOP, pady=6)  # 
        self.data_b = tk.Button(self.button_frame, text="Ingresar datos", command=self.pat_data_window, width=15)
        self.data_b.pack(side=tk.TOP, pady=6)  # 
        self.save_b = tk.Button(self.button_frame, text="Guardar", command=self.save_win, width=15)
        self.save_b.pack(side=tk.TOP, pady=6)  # 
        self.load_b = tk.Button(self.button_frame, text="Cargar", command=self.load_win, width=15)
        self.load_b.pack(side=tk.TOP, pady=6)
        self.send_mail_b = tk.Button(self.button_frame, text="Enviar mail", command=self.handle_mail, width=15)
        self.send_mail_b.pack(side=tk.TOP, pady=6)  # 
        # labels
        self.bpm_l = tk.Label(self.label_frame, bg=self.b_bg, textvariable=self.bpm_var, font=("Arial", 15))
        self.bpmt_l = tk.Label(self.label_frame, bg=self.b_bg, text="BPM", font=("Arial", 15))
        self.user_name = tk.Label(self.label_frame, bg=self.b_bg, textvariable=self.patient_data["Nombre"])
        self.user_id = tk.Label(self.label_frame, bg=self.b_bg, textvariable=self.patient_data["ID"])
        self.bpm_l.pack(side=tk.TOP)
        self.bpmt_l.pack(side=tk.TOP)
        self.user_name.pack(side=tk.TOP)
        self.user_id.pack(side=tk.TOP)
        
        self.time_sc = tk.Scale(self.frame, from_=0, to=0, orient=tk.HORIZONTAL,bg=self.b_bg ,length=400, variable=self.scale_time, command=self.update_scale)
        self.time_sc.grid(row=4, column=0, columnspan=8)
        self.time_sc.config(state=tk.DISABLED)


    
    def handle_mail(self):
        pass
        


    def pat_data_window(self):
        self.frame.destroy()
        self.frame = tk.Frame(self,bg=self.b_bg, width=self.width, height=self.height)
        self.frame.pack(fill="both", ipady=0)
        self.patient_data_el = {}
        f = ("Arial", 12)
        yp = 25
        xp = 18
        count = 0;
        for key in self.patient_data.keys():
            if count == 4:
                self.bpframe1 = tk.Frame(self.frame,bg=self.b_bg)
                self.bpframe1.grid(row = 4, column = 0,pady=yp, padx=xp)
                label = tk.Label(self.bpframe1, bg=self.b_bg, text="B.P. (mmHg)", font=f)
                entry = tk.Entry(self.bpframe1, font=f, width=5)
                label.pack(side=tk.LEFT)
                entry.pack(side=tk.RIGHT)
                
            elif count == 5:
                self.bpframe2 = tk.Frame(self.frame,bg=self.b_bg)
                self.bpframe2.grid(row = 4, column = 1, pady=yp, padx=xp)
                label = tk.Label(self.bpframe2, bg=self.b_bg, text="/", font=f)
                entry = tk.Entry(self.bpframe2, font=f, width=5)
                label.pack(side=tk.LEFT)
                entry.pack(side=tk.RIGHT)
            else:
                label = tk.Label(self.frame, bg=self.b_bg, text=key, font=f)
                entry = tk.Entry(self.frame, font=f)
                label.grid(row = count%6, column = 0 + 2*int(count>5), pady=yp, padx=xp)
                entry.grid(row = count%6, column = 1 + 2*int(count>5), pady=yp, padx=xp)
            self.patient_data_el[key] = (label, entry)
            count+=1
        
        self.save_patient_b = tk.Button(self.frame, text="Guardar", command=self.save_patient, width=40)
        self.return_b = tk.Button(self.frame, text="Volver", command=self.main_window, width=40)
        self.save_patient_b.grid(row=5, column=0, columnspan=2)
        self.return_b.grid(row=5, column=2, columnspan=2)
    
    def save_patient(self):
        for key, value in self.patient_data_el.items():
            if value[1].get() != "":
                self.patient_data[key].set(value[1].get())
    
    def save_win(self):
        self.top = tk.Toplevel(self)
        self.top.geometry("300x200")
        t_name = tk.Label(self.top, width=25, text="Nombre de archivo:")
        t_name.pack(side=tk.TOP, pady=20)
        self.t_entry = tk.Entry(self.top, width=25)
        self.t_entry.pack(side=tk.TOP, pady=20)
        t_conf_b = tk.Button(self.top, width=25,text="Confirmar", command=self.handle_save)
        t_conf_b.pack(side=tk.TOP, pady=20)
        

    def handle_save(self):
        if self.t_entry.get() == "":
            return
        
        self.patient_dict = {
            "patient_data": {k:v.get() for (k, v) in self.patient_data.items()},
            "data": np.array(self.ecg_values),
            "time": np.array(self.times)
        }
        file_path = os.path.join(self.sv_file_prefix, self.t_entry.get() + ".mat")
        os.makedirs(self.sv_file_prefix, exist_ok=True)
        encoded_data = {key: value.encode('utf-8') if isinstance(value, str) else value for key, value in self.patient_dict.items()}
        scipy.io.savemat(file_path, encoded_data)
        self.top.destroy()



    def load_win(self):
        # Obtener la carpeta seleccionada
        folder_path = self.sv_file_prefix

        # Crear una ventana emergente
        popup = tk.Toplevel(self)
        popup.title("Seleccionar Archivo")

        # Crear el Listbox
        file_listbox = tk.Listbox(popup, selectmode="single")
        file_listbox.pack()

        # Obtener los nombres de los archivos de la carpeta
        file_names = os.listdir(folder_path)

        # Agregar los nombres de los archivos al Listbox
        for file_name in file_names:
            file_listbox.insert("end", file_name)


        # Botón para cargar el archivo seleccionado
        load_button = tk.Button(popup, text="Cargar", command=lambda: self.handle_load(file_listbox))
        load_button.pack()
    
    def handle_load(self, file_listbox):
        selected_index = file_listbox.curselection()
        if selected_index:
            selected_file = file_listbox.get(selected_index)
            file_path = os.path.join(self.sv_file_prefix, selected_file)
            data = scipy.io.loadmat(file_path)
            print(f"Archivo cargado: {selected_file}")
            print(data)

    
    def start_acquisition(self):
        pass

    def stop_acquisition(self):
        pass

    def update_scale(self, val):
        self.current_disp_secs = float(val)
        if self.current_disp_secs < self.curr_xlim:
            self.curr_xlim = self.current_disp_secs
            self.curr_ylim = self.curr_xlim + self.view_width
        elif self.current_disp_secs > self.curr_ylim:
            self.curr_ylim = self.current_disp_secs
            self.curr_xlim = self.curr_ylim - self.view_width
        else:
            return
        self.ecg_plot.set_xlim(self.curr_xlim, self.curr_ylim)
        self.canvas.draw()

    def start_recording(self):
        self.recording = True
        self.scale_time.set(int(self.max_time))
        self.time_sc.config(state=tk.DISABLED)
        
        self.start_time = time.time() - self.max_time
        if self.max_time > 0:
            xllim = max(self.times) - self.view_width 
            xllim = 0 if xllim < 0 else xllim
            self.ecg_plot.set_xlim(xllim, max(self.times))
            self.canvas.draw()
        self.update_plot()

    def stop_recording(self):
        # for scale
        xllim = max(self.times) - self.view_width 
        xllim = 0 if xllim < 0 else xllim
        self.curr_xlim = xllim
        self.curr_ylim = max(self.times)
        self.time_sc.config(state=tk.NORMAL)
        self.recording = False

    def update_plot(self):
        
        if self.recording:
            if self.ser.in_waiting > 0:
                data = self.ser.readline()
                value = float(data.decode('utf-8').strip())
                self.t = time.time() - self.start_time
                
                if self.t > self.max_time:
                    self.max_time = self.t
                    self.time_sc.config(to=self.max_time)
                self.scale_time.set(int(self.t))
                
                # Agrega el valor y el tiempo a las listas
                self.ecg_values.append(value)
                self.times.append(self.t)

                
            
                # Actualiza los datos del gráfico
                self.line.set_data(self.times, self.ecg_values)
                
                # Ajusta los límites del gráfico si hay más de un punto
                if len(self.times) > 1 and len(self.ecg_values) > 1:
                    xllim = max(self.times) - self.view_width 

                    xllim = 0 if xllim < 0 else xllim
                    self.ecg_plot.set_xlim(xllim, max(self.times))
                    if len(self.ecg_values) > 50:
                        self.ecg_plot.set_ylim(min(self.ecg_values[:-50]), max(self.ecg_values[:-50]))
                    else:
                        self.ecg_plot.set_ylim(min(self.ecg_values), max(self.ecg_values))
                
                # Actualiza el canvas
                self.canvas.draw()

                # Programa la próxima actualización
                self.after(1, self.update_plot) 
if __name__ == "__main__":
    app = EKmotionApp()
    app.mainloop()
import tkinter as tk
import numpy as np
import time
import os
import serial
import threading
import queue
import json

class SerialThread(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        s = serial.Serial('/dev/ttyS0', 115200)
        s.reset_input_buffer()

        last_value = 0
        last_value2 = 60
        last_value3 = 0
        while True:
            data = s.readline().decode().strip()
            if data:
                try:
                    data_lst = data.split(",")
                    last_value = float(data_lst[0])
                    last_value2 = float(data_lst[1])
                    last_value3 = float(data_lst[2])
                    self.queue.put((last_value, last_value2, last_value3))
                except:
                    # If we cannot convert data to float, put the last valid value instead
                    self.queue.put((last_value, last_value2, last_value3))
# tiempo manual
# ejes, grid, 

class EKmotionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.queue = queue.Queue()
        self.grid_spacing = 5
        self.grid_color = "#C0C0C0"
        self.title("ECG Monitor")
        self.current_mail_file = ""
        self.width = 800
        self.height = 400
        self.plot_height = 250
        self.plot_width = 500
        self.geometry(f"{self.width}x{self.height}")
        self.b_bg = "#FFFFFF"
        self.configure(bg=self.b_bg)
        self.sv_file_prefix = "./"
        # Inicialización del tiempo
        self.t = 0
        
        # tiempo 
        self.max_time = self.t
        self.view_width = 5
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

        # Abre el puerto serial. 
        self.recording = False
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
        #????
        self.margin_top = 10
        self.margin_bottom = 20

        # El alto efectivo de tu canvas sería:
        self.effective_canvas_height = self.plot_height - self.margin_top - self.margin_bottom

        # Configurando plot
        self.plot_canvas = tk.Canvas(self.plot_frame,bg=self.b_bg, height=self.plot_height, width=self.plot_width)
        self.plot_canvas.pack()
        # Draw grid lines
        for i in range(0, self.plot_width, self.grid_spacing):
            self.plot_canvas.create_line(i, self.margin_top, i, self.plot_height - self.margin_bottom, fill=self.grid_color)
        for i in range(0, self.plot_height, self.grid_spacing):
            self.plot_canvas.create_line(0, i + self.margin_top, self.plot_width, i + self.margin_top, fill=self.grid_color)

        self.thread = SerialThread(self.queue)
        self.thread.start()

        self.data_points = myQueue()
        self.all_data = LinkedList()
        self.data_file = open("data.txt", "w")
        self.lines = []
        self.min_val = float('inf')
        self.max_val = float('-inf')
        self.min_val = 0     # Set y-range min
        self.max_val = 4100  # Set y-range max
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
        #self.time_sc.grid(row=4, column=0, columnspan=8)
        self.time_sc.config(state=tk.DISABLED)
        self.after(100, self.update_plot) 

    def handle_mail(self):
        self.top = tk.Toplevel(self)
        self.top.geometry("300x200")
        t_name = tk.Label(self.top, width=25, text="Email:")
        t_name.pack(side=tk.TOP, pady=20)
        self.t_entry = tk.Entry(self.top, width=25)
        self.t_entry.pack(side=tk.TOP, pady=20)
        
        t_conf_b = tk.Button(self.top, width=25,text="Confirmar", command=self.handle_save)
        t_conf_b.pack(side=tk.TOP, pady=20)
        
    def pat_data_window(self):
        self.frame.destroy()
        self.frame = tk.Frame(self,bg=self.b_bg, width=self.width, height=self.height)
        self.frame.pack(fill="both", ipady=0)
        self.patient_data_el = {}
        f = ("Arial", 12)
        yp = 25
        xp = 18
        count = 0
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
        list_data = self.all_data.to_list()
        self.patient_dict = {
            "patient_data": {k:v.get() for (k, v) in self.patient_data.items()},
            "data": list_data,
            "time": list(np.arange(len(list_data))/100)
        }
        
        json_data = json.dumps(self.patient_dict)
        with open(self.t_entry.get() + ".json", "w") as outfile:
            outfile.write(json_data)
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
        file_names = []
        # Obtener los nombres de los archivos de la carpeta
        for filename in os.listdir(folder_path):
            if filename.endswith('.json'):
                file_names.append(filename)
        # Agregar los nombres de los archivos al Listbox
        for file_name in file_names:
            file_listbox.insert("end", file_name)


        # Botón para cargar el archivo seleccionado

        load_button = tk.Button(popup, text="Cargar", command=lambda: self.handle_load(file_listbox))
        load_button.pack()
    
    def load_formail(self):
        # Obtener la carpeta seleccionada
        folder_path = self.sv_file_prefix

        # Crear una ventana emergente
        popup = tk.Toplevel(self)
        popup.title("Seleccionar Archivo")

        # Crear el Listbox
        file_listbox = tk.Listbox(popup, selectmode="single")
        file_listbox.pack() 
        file_names = []
        # Obtener los nombres de los archivos de la carpeta
        for filename in os.listdir(folder_path):
            if filename.endswith('.json'):
                file_names.append(filename)
        # Agregar los nombres de los archivos al Listbox
        for file_name in file_names:
            file_listbox.insert("end", file_name)


        # Botón para cargar el archivo seleccionado
        
        load_button = tk.Button(popup, text="Cargar", command=lambda: self.handle_load2(file_listbox))
        load_button.pack()
    
    def handle_load2(self, file_listbox):
        selected_index = file_listbox.curselection()
        if selected_index:
            selected_file = file_listbox.get(selected_index)
            self.current_mail_file = selected_file
    
    def handle_load(self, file_listbox):
        selected_index = file_listbox.curselection()
        if selected_index:
            selected_file = file_listbox.get(selected_index)
            file_path = os.path.join(self.sv_file_prefix, selected_file)
            print(f"Archivo cargado: {selected_file}")
    
    def start_acquisition(self):
        pass

    def stop_acquisition(self):
        pass

    def update_scale(self, val):
        self.current_disp_secs = float(val)
        self.plot_canvas.delete('data_line')  # Remove the old line
        y_range = self.max_val - self.min_val  # Compute y range based on constant min and max values

        
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
        if not self.recording:
            self.recording = True
            self.it_count = 0
            self.scale_time.set(int(self.max_time))
            self.time_sc.config(state=tk.DISABLED)
            
            self.start_time = time.time() - self.max_time

    def stop_recording(self):
        # for scale
        self.time_sc.config(state=tk.NORMAL)
        self.recording = False
        self.data_points = myQueue()

    def update_plot(self):
        if self.recording:
            while not self.queue.empty():
                data_str = self.queue.get()
                val = data_str[0]
                bpm = data_str[1]
                mpu = data_str[2]
                color = "red" if mpu else "black"
                self.data_points.EnQueue(val)
                self.bpm_var.set(str(bpm))

                if self.data_points.size > self.plot_width:
                    self.data_points.DeQueue()
                
                self.plot_canvas.delete('data_line')  # Remove the old line

                # Compute y range based on constant min and max values
                y_range = self.max_val - self.min_val

                # Now we iterate over data_points instead of all_data
                current_node = self.data_points.front
                i = 0
                previous_y = self.margin_top + self.effective_canvas_height - ((current_node.data - self.min_val) / y_range * self.effective_canvas_height) if y_range != 0 else self.plot_height / 2
                while current_node != None:
                    current_y = self.margin_top + self.effective_canvas_height - ((current_node.data - self.min_val) / y_range * self.effective_canvas_height) if y_range != 0 else self.plot_height / 2
                    self.plot_canvas.create_line(i - 1, previous_y, i, current_y, fill=color, tags='data_line', width=3) 
                    previous_y = current_y
                    current_node = current_node.next
                    i += 1

                self.t = time.time() - self.start_time
                if self.t > self.max_time:
                    self.max_time = self.t
                    self.time_sc.config(to=self.max_time)
                self.scale_time.set(int(self.t))
        self.after(100, self.update_plot)

class Node:
    def __init__(self, data=None):
        self.data = data
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None
        self.tail = None

    def append(self, data):
        if not self.head:
            self.head = Node(data)
            self.tail = self.head
        else:
            new_node = Node(data)
            self.tail.next = new_node
            self.tail = new_node

    def pop_head(self):
        if self.head:
            data = self.head.data
            self.head = self.head.next
            if self.head is None:
                self.tail = None
            return data

    def __iter__(self):
        node = self.head
        while node is not None:
            yield node.data
            node = node.next

    def to_list(self):
        return [data for data in self]


class myQueue:
    def __init__(self):
        self.front = self.rear = None
        self.size = 0

    def is_empty(self):
        return self.front == None

    def EnQueue(self, data):
        temp = Node(data)
        self.size += 1

        if self.rear == None:
            self.front = self.rear = temp
            return
        self.rear.next = temp
        self.rear = temp

    def DeQueue(self):
        if self.is_empty():
            return
        self.size -= 1
        temp = self.front
        self.front = temp.next

        if(self.front == None):
            self.rear = None
        return temp.data


if __name__ == "__main__":
    app = EKmotionApp()
    app.mainloop()
import sys
from PyQt5 import QtWidgets
from PyQt5 import QtGui
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
import serial
import numpy as np
from PyQt5 import uic
import time
import json
import os
import glob
import send_mail


class PatientPopUp(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('pat_dialog.ui', self)
        self.show()

class SaveDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('save_dialog.ui', self)
        self.show()

class LoadDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('load_dialog.ui', self)
        self.show()

class PlotDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('plot_dialog.ui', self)
        self.show()

class MailDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('mail_dialog.ui', self)
        self.show()

class SerialPlotter(QtWidgets.QMainWindow):
    def __init__(self, port, baudrate):
        super().__init__()
        uic.loadUi("ekmotion.ui", self)
        self.setWindowTitle("EKMotion 2.0 - by Yaku")
        self.setWindowIcon(QtGui.QIcon("logo.png"))
        self.data_rec = myQueue()
        self.patient_data = {
            "Nombre": "--",
            "ID": "00",
            "Edad": "--",
            "Sexo": "--",
            "BP_num": "--",
            "BP_den": "--",
            "Altura": "--",
            "Peso": "--",
            "Condicion": "--",
            "Medicacion": "--"
        }

        self.mail_message = "Esta es tu señal ECG con los datos del paciente,\n- EKmotion."

        self.ser_fs = 125
        self.plot_length = self.ser_fs*3
        self.serial_port = serial.Serial(port, baudrate)
        self.recording = False
        self.is_saving = False
        pg.setConfigOption('foreground', '#000000')
        self.plot_widget = pg.PlotWidget()
        self.plot_lay.addWidget(self.plot_widget)
        self.data = np.zeros(self.plot_length)
        self.time = np.linspace(0, 3, self.plot_length)
        self.pen = pg.mkPen(color=(0, 0, 255))
        self.curve = self.plot_widget.plot(self.time, self.data, pen=self.pen)
        
        self.plot_widget.setBackground((240,240,240))
        self.plot_widget.setLabel('left', 'Amplitud (mV)')
        self.plot_widget.setLabel('bottom', 'Tiempo (s)')
        self.plot_widget.showGrid(x=True, y=True)
        self.timer = QtCore.QTimer()
        
        self.prev_mpu = 0

        self.play_b.clicked.connect(self.play)
        self.pause_b.clicked.connect(self.pause)
        self.data_b.clicked.connect(self.edit_patient)
        self.save_b.clicked.connect(self.start_aq)
        self.save_b.setEnabled(False)
        self.load_b.clicked.connect(self.load_file)
        self.mail_b.clicked.connect(self.mail_dialog)
        self.timer.timeout.connect(self.update)
        self.selected_file = ""
        self.timer.start(5)

    def mail_dialog(self):
        self.mail_d = MailDialog()
        self.mail_d.setWindowTitle("Enviar mail")
        directory_path = './'
        os.chdir(directory_path)
        for file in glob.glob("*.json"):
            self.mail_d.mail_list.addItem(file)
        self.mail_d.mail_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.mail_d.mail_list.itemSelectionChanged.connect(self.on_selection_change_mail)
        self.mail_d.bb_mail.accepted.connect(self.mail_accept)
        self.mail_d.bb_mail.rejected.connect(self.mail_d.close)
    
    def on_selection_change_mail(self):
        self.selected_file = self.mail_d.mail_list.selectedItems()[0].text()

    def mail_accept(self):
        if self.mail_d.mail_ed.text() != "" and self.selected_file != "":
            email = self.mail_d.mail_ed.text()
            send_mail.emailverify(email, self.mail_message, self.selected_file)
            self.mail_d.close()

    def play(self):
        if not self.recording:
            self.recording = True
            self.save_b.setEnabled(True)
            self.load_b.setEnabled(False)

    def pause(self):
        if self.recording:
            self.recording = False
            self.save_b.setEnabled(False)
            self.load_b.setEnabled(True)


    def edit_patient(self):
        self.popup = PatientPopUp()
        self.popup.setWindowTitle("Editar paciente")
        
        self.popup.BP_den_ed.setText(self.patient_data["BP_den"])
        self.popup.BP_num_ed.setText(self.patient_data["BP_num"])
        self.popup.age_ed.setText(self.patient_data["Edad"])
        self.popup.cond_ed.setText(self.patient_data["Condicion"])
        self.popup.height_ed.setText(self.patient_data["Altura"])
        self.popup.id_ed.setText(self.patient_data["ID"])
        self.popup.med_ed.setText(self.patient_data["Medicacion"])
        self.popup.name_ed.setText(self.patient_data["Nombre"])
        self.popup.sex_ed.setText(self.patient_data["Sexo"])
        self.popup.weight_ed.setText(self.patient_data["Peso"])
        self.popup.save_pat_b.clicked.connect(self.save_patient)
    
    def save_patient(self):
        self.patient_data["BP_den"] = self.popup.BP_den_ed.text()
        self.patient_data["BP_num"] = self.popup.BP_num_ed.text()
        self.patient_data["Edad"] = self.popup.age_ed.text()
        self.patient_data["Condicion"] = self.popup.cond_ed.text()
        self.patient_data["Altura"] = self.popup.height_ed.text()
        self.patient_data["ID"] = self.popup.id_ed.text()
        self.patient_data["Medicacion"] = self.popup.med_ed.text()
        self.patient_data["Nombre"] = self.popup.name_ed.text()
        self.patient_data["Sexo"] = self.popup.sex_ed.text()
        self.patient_data["Peso"] = self.popup.weight_ed.text()
        self.pat_lab.setText(f"Paciente: {self.patient_data['ID']}\n{self.patient_data['Nombre']}")

    def start_aq(self):
        
        if not self.is_saving:
            self.pause_b.setEnabled(False)
            self.data_rec = myQueue()
            self.is_saving = True
            self.save_b.setText("Detener Adquisición 🛑")
        else:
            self.pause_b.setEnabled(True)
            self.is_saving = False
            total_data = self.data_rec.to_list() + list(self.data)
            self.save_b.setText("Iniciar adquisición ▶")
            self.init_saving(total_data)
            

    def init_saving(self, data):
        self.save_d = SaveDialog()
        self.save_d.setWindowTitle("Guardar señal")
        self.save_d.save_ed.setText(f"Patient_{self.patient_data['ID']}_{time.strftime('%y-%m-%d_%H-%M')}")
        self.save_d.bb_save.accepted.connect(lambda: self.save_accept(data))
        self.save_d.bb_save.rejected.connect(self.save_d.close)

    def save_accept(self, data):
        filename = self.save_d.save_ed.text() + ".json"
        final_dict = {"data": data,"fs":str(self.ser_fs) ,"patient_data":self.patient_data}
        if filename != ".json":
            with open(filename, "w") as outfile:
                json.dump(final_dict, outfile)
        self.save_d.close()
    
    def load_file(self):
        self.load_d = LoadDialog()
        self.load_d.setWindowTitle("Cargar señal")

        directory_path = './'
        os.chdir(directory_path)
        for file in glob.glob("*.json"):
            self.load_d.load_list.addItem(file)
        self.load_d.load_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.load_d.load_list.itemSelectionChanged.connect(self.on_selection_change)
        self.load_d.bb_load.accepted.connect(self.load_accept)
        self.load_d.bb_load.rejected.connect(self.load_d.close)
    
    def load_accept(self):
        if self.selected_file != "":
            with open(self.selected_file, "r") as file:
                data_dict = json.load(file)
            self.open_plot(data_dict)
        else:
            self.load_d.close()

    def open_plot(self, data):
        self.pd = PlotDialog()
        self.pd.setWindowTitle("Ploteo de señal")
        self.load_vals = list(data["data"])
        self.load_fs = int(data["fs"])
        self.load_plot = pg.PlotWidget()
        self.pd.load_plot_lay.addWidget(self.load_plot)

        #plot things
        self.load_plot.setBackground((240,240,240))
        self.load_plot.setLabel('left', 'Amplitud (mV)')
        self.load_plot.setLabel('bottom', 'Tiempo (s)')
        self.load_plot.showGrid(x=True, y=True)


        self.load_time = np.arange(len(self.load_vals)) / self.load_fs
        
        self.pd.plot_slider.setMinimum(0)
        self.pd.plot_slider.setMaximum(len(self.data) - 1)
        self.pd.plot_slider.setValue(0)

        self.pd.plot_slider.valueChanged.connect(self.update_graph)

        self.update_graph(self.pd.plot_slider.value())

    def update_graph(self, value):
        start_index = value
        end_index = start_index + int(self.load_fs * 3)  # Mostrar 3 segundos de señal.

        self.load_plot.clear()
        self.load_plot.plot(self.load_time[start_index:end_index], self.load_vals[start_index:end_index], pen='b')


    def on_selection_change(self):
        self.selected_file = self.load_d.load_list.selectedItems()[0].text()


    def update(self):
        line = self.serial_port.readline().decode()
        if self.recording:
            try:
                vals = line.split(",")
                number = float(vals[0])
                if self.is_saving:
                    self.data_rec.EnQueue(self.data[0])
                    if self.data_rec.size > 10000:
                        self.data_rec.DeQueue()
                    
                self.data[:-1] = self.data[1:]
                self.data[-1] = number
                
                if self.prev_mpu == 0 and int(vals[2]) == 1:
                    self.pen = pg.mkPen(color=(255, 0, 0))
                if self.prev_mpu == 1 and int(vals[2]) == 0:
                    self.pen = pg.mkPen(color=(0, 0, 255))
                self.curve.setData(self.time, self.data, pen=self.pen)
                self.bpm_edit.setText(vals[1])
                self.prev_mpu = int(vals[2])
            except ValueError:
                pass

class Node:
    def __init__(self, data=None):
        self.data = data
        self.next = None

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
    
    def to_list(self):
        list_ = []
        temp = self.front
        while temp:
            list_.append(temp.data)
            temp = temp.next
        return list_


def main():
    app = QtWidgets.QApplication(sys.argv)
    #plotter = SerialPlotter(port='COM14', baudrate=115200)
    plotter = SerialPlotter(port='/dev/ttyS0', baudrate=115200)
    plotter.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

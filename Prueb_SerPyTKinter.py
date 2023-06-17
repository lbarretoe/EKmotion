import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from queue import Queue
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from threading import Thread
import serial
import time
import collections
import struct

PORT = 'COM15'
BAUDIOS = 9600
maxPlotLength = 100


class serialPlot:
    def __init__(self, queue, serialPort=PORT, serialBaud=BAUDIOS, plotLength=100, dataNumBytes=2):
        self.queue = queue
        self.port = serialPort
        self.baud = serialBaud
        self.plotMaxLength = plotLength
        self.dataNumBytes = dataNumBytes
        self.rawData = bytearray(dataNumBytes)
        self.data = collections.deque([0] * plotLength, maxlen=plotLength)
        self.isRun = True
        self.isReceiving = False
        self.thread = None
        self.plotTimer = 0
        self.previousTimer = 0

        try:
            self.serialConnection = serial.Serial(serialPort, serialBaud, timeout=4)
        except:
            print("Failed to connect with " + str(serialPort) + ' at ' + str(serialBaud) + ' BAUD.')

    def readSerialStart(self):
        if self.thread == None:
            self.thread = Thread(target=self.backgroundThread)
            self.thread.start()

    def backgroundThread(self):    # retrieve data
        time.sleep(1.0)
        self.serialConnection.reset_input_buffer()
        while (self.isRun):
            self.serialConnection.readinto(self.rawData)
            self.isReceiving = True
            value,  = struct.unpack('f', self.rawData)
            self.queue.put(value)

    def close(self):
        self.isRun = False
        self.thread.join()
        self.serialConnection.close()
        print('Disconnected...')


def serial_read(queue):
    portName = PORT
    baudRate = BAUDIOS
    maxPlotLength = 100
    dataNumBytes = 4
    s = serialPlot(queue, portName, baudRate, maxPlotLength, dataNumBytes)
    s.readSerialStart()


def getSerialData(frame, queue, lines, lineValueText, lineLabel, timeText):
    if not queue.empty():
        value = queue.get()
        lines.set_ydata(value)
        lineValueText.set_text('[' + lineLabel + '] = ' + str(value))


def main():
    root = tk.Tk()

    queue = Queue()
    serial_thread = Thread(target=serial_read, args=(queue,))
    serial_thread.start()

    pltInterval = 50
    xmin = 0
    xmax = 100
    ymin = -(200)
    ymax = 200
    fig = plt.figure(figsize=(10, 5))
    ax = plt.axes(xlim=(xmin, xmax), ylim=(float(ymin - (ymax - ymin) / 10), float(ymax + (ymax - ymin) / 10)))
    ax.set_title('Arduino Analog Read')
    ax.set_xlabel("time")
    ax.set_ylabel("AnalogRead Value")

    lineLabel = 'Potentiometer Value'
    timeText = ax.text(0.50, 0.95, '', transform=ax.transAxes)
    lines = ax.plot([], [], label=lineLabel)[0]
    lineValueText = ax.text(0.50, 0.90, '', transform=ax.transAxes)
    anim = animation.FuncAnimation(fig, getSerialData, fargs=(queue, lines, lineValueText, lineLabel, timeText),
                                   interval=pltInterval)

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()
    canvas.get_tk_widget().pack(side=tk.TOP)

    tk.mainloop()

    serial_thread.join()


if __name__ == '__main__':
    main()

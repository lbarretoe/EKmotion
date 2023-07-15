import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import serial
import threading
import queue

class SerialThread(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        s = serial.Serial('COM14', 115200)
        s.reset_input_buffer()

        last_value = 0
        while True:
            data = s.readline().decode().strip()
            if data:
                try:
                    last_value = float(data)
                    self.queue.put(last_value)
                except ValueError:
                    # If we cannot convert data to float, put the last valid value instead
                    self.queue.put(last_value)



class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.queue = queue.Queue()
        self.fig = Figure(figsize=(5, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.graph = FigureCanvasTkAgg(self.fig, master=self)
        self.graph.get_tk_widget().pack(side="top", fill='both', expand=True)

        self.thread = SerialThread(self.queue)
        self.thread.start()

        self.data = []
        self.ani = animation.FuncAnimation(self.fig, self.animate, interval=10)

    def animate(self, i):
        while self.queue.qsize():
            try:
                data_str = self.queue.get()
                try:
                    self.data.append(float(data_str))
                    if len(self.data) > 200:  # Limit data array length
                        self.data.pop(0)
                except ValueError:
                    pass  # Ignore values that cannot be converted to float
            except queue.Empty:
                pass
        self.ax.clear()
        self.ax.plot(self.data)



if __name__ == '__main__':
    app = App()
    app.mainloop()

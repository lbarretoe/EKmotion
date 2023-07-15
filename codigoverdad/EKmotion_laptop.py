import tkinter as tk
import threading
import queue
import serial

class SerialThread(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        s = serial.Serial('COM14', 115200)
        s.reset_input_buffer()

        while True:
            data = s.readline().decode().strip()
            if data:
                try:
                    value = float(data)
                    self.queue.put(value)
                except ValueError:
                    pass

class EKmotionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.queue = queue.Queue()
        self.canvas_width = 200
        self.canvas_height = 400
        self.grid_spacing = 10
        self.title("ECG Monitor")
        self.geometry(f"{self.canvas_width}x{self.canvas_height}")
        self.grid_color = "#C0C0C0"
        self.b_bg = "#FFFFFF"
        self.configure(bg=self.b_bg)
        # En tu método __init__, define tus márgenes (en píxeles):
        self.margin_top = 10
        self.margin_bottom = 20

        # El alto efectivo de tu canvas sería:
        self.effective_canvas_height = self.canvas_height - self.margin_top - self.margin_bottom

        self.plot_canvas = tk.Canvas(self, width=self.canvas_width, height=self.canvas_height, bg=self.b_bg)
        self.plot_canvas.pack()

        # Draw grid lines
        for i in range(0, self.canvas_width, self.grid_spacing):
            self.plot_canvas.create_line(i, self.margin_top, i, self.canvas_height - self.margin_bottom, fill=self.grid_color)
        for i in range(0, self.effective_canvas_height, self.grid_spacing):
            self.plot_canvas.create_line(0, i + self.margin_top, self.canvas_width, i + self.margin_top, fill=self.grid_color)

        self.thread = SerialThread(self.queue)
        self.thread.start()

        self.data_points = []
        self.data_file = open("data.txt", "w")  # File where the data will be stored

        self.min_val = 0     # Set y-range min
        self.max_val = 1200  # Set y-range max
        self.after(100, self.update_plot)  # Refresh rate is 0.1 second

    def update_plot(self):
        while not self.queue.empty():
            val = self.queue.get()
            self.data_points.append(val)  # Store raw data point

        # Empty the data_points list if it's too long, to avoid slowing down.
        if len(self.data_points) > self.canvas_width:
            self.data_points = self.data_points[-self.canvas_width:]

        if len(self.data_points) > 1:
            self.plot_canvas.delete('data_line')  # Remove the old line

            y_range = self.max_val - self.min_val  # Compute y range based on constant min and max values

            for i in range(1, len(self.data_points)):
                # Map the data point value onto the pixel range (height of the canvas minus margins)
                y1 = self.margin_top + self.effective_canvas_height - ((self.data_points[i - 1] - self.min_val) / y_range * self.effective_canvas_height) if y_range != 0 else self.canvas_height / 2
                y2 = self.margin_top + self.effective_canvas_height - ((self.data_points[i] - self.min_val) / y_range * self.effective_canvas_height) if y_range != 0 else self.canvas_height / 2
                self.plot_canvas.create_line(i - 1, y1, i, y2, fill="black", tags='data_line') 
        if len(self.data_points) > 10000:  # Adjust this value as needed
                for point in self.data_points:
                    self.data_file.write(f"{point}\n")
                self.data_points = []
        self.after(100, self.update_plot)
    
    def __del__(self):  # Destructor to properly close the file
        self.data_file.close()


if __name__ == "__main__":
    app = EKmotionApp()
    app.mainloop()

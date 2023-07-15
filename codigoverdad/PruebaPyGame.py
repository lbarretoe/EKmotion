import pygame
import sys
import numpy as np
import serial
import threading
import queue

# Configuración de Pygame
pygame.init()
window_size = (800, 600)
screen = pygame.display.set_mode(window_size)
clock = pygame.time.Clock()

# Configuración de la simulación
frequency = 1.5
amplitude = 100
time = 0
dt = 1.0 / 60.0  # 60 FPS

# Configuración de la cola y el hilo
data_queue = queue.Queue()

def serial_thread(queue):
    s = serial.Serial('/dev/ttyUSB0', 115200)
    s.reset_input_buffer()

    while True:
        data = s.readline().decode().strip()
        if data:
            try:
                data_lst = data.split(",")
                values = [float(x) for x in data_lst]
                queue.put(values)
            except ValueError:
                pass

thread = threading.Thread(target=serial_thread, args=(data_queue,))
thread.start()

# Bucle principal
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Llenar la pantalla de blanco
    screen.fill((255, 255, 255))

    # Dibujar la onda sinusoidal
    for i in range(1, window_size[0]):
        y1 = int(amplitude * np.sin(2 * np.pi * frequency * (i - 1) * dt) + window_size[1] / 2)
        y2 = int(amplitude * np.sin(2 * np.pi * frequency * i * dt) + window_size[1] / 2)
        pygame.draw.line(screen, (0, 0, 0), (i - 1, y1), (i, y2))

    # Actualizar la pantalla
    pygame.display.flip()

    # Limitar a 60 FPS
    clock.tick(60)

    # Actualizar el tiempo
    time += dt

# Limpiar
pygame.quit()
sys.exit()
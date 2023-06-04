import serial

# Parámetros de la conexión serial
port = '/dev/ttyS0'  # puerto serial del ESP32 conectado al Raspberry Pi
baud_rate = 9600
data_bits = serial.EIGHTBITS  # número de bits de datos
parity = serial.PARITY_NONE  # tipo de paridad
stop_bits = serial.STOPBITS_ONE  # número de bits de parada

# Abre el puerto serial. 
ser = serial.Serial(port, baud_rate, data_bits, parity, stop_bits)

try:
    while True:
        # Si hay datos disponibles para leer, entonces léelos e imprímelos.
        if ser.in_waiting > 0:
            data = ser.readline()
            print('Received: ', data.decode('utf-8').strip())  # Decodifica los datos y elimina espacios en blanco al final.

except KeyboardInterrupt:
    # Cierra el puerto serial cuando se interrumpe el programa.
    print("\nPrograma interrumpido. Cerrando el puerto serial...")
    ser.close()

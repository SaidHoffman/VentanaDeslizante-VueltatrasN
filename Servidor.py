import socket
import os
import random

# Crear un socket UDP
servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
servidor.bind(('localhost', 5000))
print('Servidor iniciado...')

# Obtener el tamaño de la ventana y el búfer del cliente
print('Esperando tamaños del cliente...')
ventana_size, addr = servidor.recvfrom(1024)
ventana_size = int(ventana_size)
print(f'Tamaño de ventana recibido: {ventana_size}')
buffer_size, addr = servidor.recvfrom(1024)
buffer_size = int(buffer_size)
print(f'Tamaño de búfer recibido: {buffer_size}')

# Obtener el nombre del archivo de entrada del cliente
print('Esperando nombre de archivo de entrada...')
archivo_entrada_nombre, addr = servidor.recvfrom(1024)
archivo_entrada_nombre = archivo_entrada_nombre.decode()
print(f'Nombre de archivo de entrada recibido: {archivo_entrada_nombre}')

# Nombre del archivo de salida
archivo_salida_nombre = "archivo_salida.pdf"

# Crear el archivo de salida si no existe
if not os.path.exists(archivo_salida_nombre):
    archivo_salida = open(archivo_salida_nombre, 'wb')
else:
    print(f"El archivo {archivo_salida_nombre} ya existe. Se sobreescribirá.")
    archivo_salida = open(archivo_salida_nombre, 'wb')

# Función para simular la pérdida de paquetes
def simular_perdida_paquetes(paquete, tasa_perdida):
    if random.random() < tasa_perdida:
        return None  # Simular la pérdida del paquete
    else:
        return paquete

tasa_perdida = 0.1

# Búferes para los datos y ACKs
datos_buffer = []
ack_buffer = []

# Punteros para la ventana deslizante
ptr_datos = 0
ptr_ack = 0

# Contador para paquetes y ACKs
paquete_esperado = 1
ack_count = 0

while True:
    paquete, addr = servidor.recvfrom(buffer_size + 4)
    paquete_numero = int.from_bytes(paquete[:4], byteorder='big')
    datos = paquete[4:]

    paquete_simulado = simular_perdida_paquetes(datos, tasa_perdida)
    #paquete_simulado = datos

    if paquete_simulado is None:
        print(f'Paquete #{paquete_numero} perdido')
        continue
    print(f'Paquete #{paquete_numero} recibido: {len(datos)} bytes')

    # Verificar si el paquete recibido es el esperado
    if paquete_esperado == paquete_numero:
        # Si es el paquete esperado, añadirlo al búfer de datos
        datos_buffer.append(paquete_simulado)
        paquete_esperado += 1

        # Enviar ACK solo si se recibe el paquete esperado
        ack = b'ACK'
        servidor.sendto(ack, addr)
        ack_buffer.append(ack)
        print(f'ACK #{ack_count + 1} enviado para el paquete #{paquete_numero}')
        ack_count += 1

        # Si se llenó la ventana o es el último paquete
        if len(datos_buffer) == ventana_size or len(datos) < buffer_size:
            # Escribir los datos recibidos en el archivo
            for dato in datos_buffer:
                archivo_salida.write(dato)

            # Limpiar los búferes
            datos_buffer = []
            ack_buffer = []

    # Verificar si se recibieron todos los datos
    if len(datos) < buffer_size:
        break

# Cerrar el archivo de salida
archivo_salida.close()
print('Transferencia completa')

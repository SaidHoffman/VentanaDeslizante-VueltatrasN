import socket
import threading
import time

# CREACION DEL SOCKET DEL CLIENTE
cliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# PETICION DE DATOS AL CLIENTE
servidor_addr = ('localhost', 5000)

# Obtener el tamaño de la ventana y el búfer del usuario
ventana_size = int(input("Ingrese el tamaño de la ventana: "))
cliente.sendto(str(ventana_size).encode(), servidor_addr)
buffer_size = int(input("Ingrese el tamaño del búfer de envío (en bytes): "))

cliente.sendto(str(buffer_size).encode(), servidor_addr)

# Archivo a enviar
archivo_entrada_nombre = input("Ingrese el nombre del archivo a enviar: ")
cliente.sendto(archivo_entrada_nombre.encode(), servidor_addr)
archivo_entrada = open(archivo_entrada_nombre, 'rb')
datos = archivo_entrada.read()
archivo_entrada.close()

# DIVISION DE LOS DATOS EN PAQUETES
paquetes = [datos[i:i+buffer_size] for i in range(0, len(datos), buffer_size)]
num_paquetes = len(paquetes)
print(f"El archivo se dividió en {num_paquetes} paquetes.")

# Punteros para la ventana deslizante
ptr_envio = 0
ptr_recepcion = 0
debe_parar = [threading.Event() for _ in range(num_paquetes)]

# Función que maneja el temporizador para reenviar paquetes
def temporizador(paquete, paquete_numero, cliente, servidor_addr, debe_parar):
    while not debe_parar.is_set():
        time.sleep(1)
        print(f'Reenviando paquete #{int.from_bytes(paquete_numero, byteorder="big")}')
        cliente.sendto(paquete_numero + paquete, servidor_addr)

# Enviar paquetes y esperar ACKs
while ptr_envio < num_paquetes:
    # Lista para almacenar los hilos
    threads = []

    # Enviar paquetes dentro de la ventana
    for i in range(ptr_envio, min(ptr_envio + ventana_size, num_paquetes)):
        paquete_numero = (i + 1).to_bytes(4, byteorder='big')
        cliente.sendto(paquete_numero + paquetes[i], servidor_addr)
        print(f'Paquete #{i + 1} enviado: {len(paquetes[i])} bytes')
        t = threading.Thread(target=temporizador, args=(paquetes[i], paquete_numero, cliente, servidor_addr, debe_parar[i])) 
        t.start()
        threads.append(t)

    # Esperar los ACKs
    ack_count = 0
    acks_esperados = min(ventana_size, num_paquetes - ptr_envio)
    while ack_count < acks_esperados: 
        ack, _ = cliente.recvfrom(1024)
        if ack == b'ACK':
            print(f'ACK #{ack_count + ptr_recepcion + 1} recibido')
            ack_count += 1

    if ack_count > 0:
        ptr_recepcion += ack_count

        # Indicar a los hilos correspondientes que deben parar
        for i in range(ptr_recepcion - ack_count, ptr_recepcion):
            debe_parar[i].set()

        # Mover el puntero de envío
    ptr_envio += ack_count

    # Esperar a que todos los hilos terminen antes de continuar
    for t in threads:
        t.join() 

print('Transferencia completa')

# Cerrar el socket del cliente
cliente.close()

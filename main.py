import datetime
import time

import serial
from serial import Serial
from serial.tools.list_ports import comports
import src.pyMultiSerial as p

BAUDRATE = 9600
TIMEOUT = 2

ports = []

# creo i callbacks per il thread:
'''
List of Events for callback:
1. On detecting a port connection
2. On reading data from port
3. On port disconection
4. On Keyboard Interrupt (Ctrl+C)
5. Continuous loop execution
'''
# Callback function on detecting a port connection.
# Parameters: Port Number, Serial Port Object
def port_connection_found_callback(portno, serial):
    if portno not in ports:
        ms.ignore_port(serial)
        print("Port " + portno + " rejected.")
    else:
        datafile = open(workingDir + "/" + portno + "_" + formatted_date + ".ubx", 'x')

# Callback on receiving port data
# Parameters: Port Number, Serial Port Object, Text read from port
def port_read_callback(portno, serial, text):
    # BUFFER[portno] += text
    print("Received '"+len(text)+"' bytes from port "+portno)
    # if len(BUFFER[portno]) > MAX_BUFFER_SIZE:
    with open(workingDir + "/" + portno + "_" + formatted_date + ".ubx", 'a') as file:
        file.write(text)
    pass

# Callback on port disconnection. Triggered when a device is disconnected from port.
# Parameters: Port No
def port_disconnection_callback(portno):
    print("Port " + portno + " disconnected.")
    pass

# Callback on interrupt. Triggered when python script execution is interrupted.
# Parameters: -
def interrupt_callback():
    print("Stopped Monitoring")
    pass

## ------------------- MAIN CODE ------------------- ##
while len(ports) == 0:
    mode = int(input("Digitare 0 per scansione automatica degli u-blox, 1 per l'inserimento manuale: "))
    if mode == 0:
        # scansione porte
        availablePorts = comports()
        for p in range(len(availablePorts)):
            try:
                # creo l'oggetto
                s = Serial(availablePorts[p].device, BAUDRATE)
                # se la connessione non è aperta, la apro
                if not s.isOpen():
                    s.open()
                # leggo tutti i bytes
                s.read(s.inWaiting())
                # invio la richiesta di poll
                s.write(b"\xb5\x62\x02\x15\x00\x00\x17\x47")
                # aspetto
                b1 = 0
                b2 = 0
                # leggo in due variabili diverse fino a che non c'è un momento in cui leggo la stessa cosa
                while (b1 != b2 or b1 == 0):
                    b1 = s.inWaiting()
                    time.sleep(0.5)
                    b2 = s.inWaiting()
                # definisco i bytes da ricercare nel contenuto che la periferica mi manda
                searchBytes = b"\xb5\x62\x02\x15"
                # se c'è l'intestazione di un pacchetto UBX, lo considero ricevitore, sennò no
                if s.read(b1).find(searchBytes) > 0:
                    ports.append(availablePorts[p].device)
                s.close()
                del s
            except serial.SerialException as e:
                print(e)
                break
    elif mode == 1:
        # inserimento manuale
        listPorts = input("Inserire il nome della porta di ciascun ricevitore (separato da ','): ")
        for p in range(len(listPorts.split(","))):
            ports.append(listPorts.split(",")[p].strip())
    else:
        # comando non valido
        print("Comando non valido.")

confirm = int(input("Le porte inserite/riconosciute sono queste: ", ports, ", procedo? (1: sì, 0: no) "))
if confirm == 1:
    # creo l'oggetto per la classe pyMultiSerial
    ms = p.MultiSerial()
    ms.baudrate = BAUDRATE
    ms.timeout = TIMEOUT

    workingDir = input("Inserire il percorso assoluto in cui salvare i files: ")

    # prendo la data/ora di adesso (per i nomi dei files)
    current_date = datetime.now()
    formatted_date = current_date.strftime("%Y_%m_%d_%H_%M_%S")

    # avvio il thread dopo aver registrato le funzioni di callback
    ms.port_connection_found_callback = port_connection_found_callback
    ms.port_read_callback = port_read_callback
    ms.port_disconnection_callback = port_disconnection_callback
    ms.interrupt_callback = interrupt_callback

    start = int(input("Avviare la raccolta dati? (1: sì, 0: no) "))
    if start == 1:
        print("Raccolta dati avviata! Per fermare il monitoraggio, premere CTRL+C.")
        time.sleep(5)
        ms.Start()

## To stop monitoring, press Ctrl+C in the console or command line.
# Caution: Any code written below ms.Start() will be executed only after monitoring is stopped.
# Make use of callback functions to execute your code.
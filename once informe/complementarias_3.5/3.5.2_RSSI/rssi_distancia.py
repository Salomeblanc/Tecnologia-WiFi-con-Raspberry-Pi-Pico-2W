# Comunicaciones Digitales - UMNG
# Practica WiFi, 3.5.2: RSSI vs distancia. Pico W / Pico 2 W, MicroPython.
# Mide el RSSI de un AP (por ejemplo el hotspot del celular) en cada punto,
# promedia SAMPLES medidas y guarda dos CSV dentro de la Pico:
#   rssi_distancia.csv -> resumen, una fila por distancia
#   rssi_muestras.csv  -> todas las medidas individuales
# Si lo ejecutas de nuevo, los datos se agregan al final de los CSV.
import network
import time
import os
import math
from machine import Pin

TARGET_SSID = 'MI_CELULAR'  # <- nombre EXACTO del AP a medir (hotspot del celular)
SAMPLES = 10                # medidas por punto (minimo 10)
START_M = 1                 # primera distancia (m)
STEP_M = 1                  # paso entre puntos (m)
MAX_TRIES = 40              # barridos maximos por punto antes de darlo por "sin senal"
BUTTON_PIN = None           # None: pulsar Enter en Thonny. Ej. 10: pulsador entre GP10 y GND
CSV_SUMMARY = 'rssi_distancia.csv'
CSV_RAW = 'rssi_muestras.csv'

HEADER_SUMMARY = 'distancia_m,n,rssi_prom_dbm,desv_dbm,rssi_min_dbm,rssi_max_dbm,barridos'
HEADER_RAW = 'distancia_m,muestra,rssi_dbm'

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
led = Pin('LED', Pin.OUT)
target = TARGET_SSID.encode()
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP) if BUTTON_PIN is not None else None


def read_rssi():
    # Un barrido; devuelve el RSSI (dBm) del AP objetivo o None si no aparece.
    try:
        networks = wlan.scan()  # (ssid, bssid, canal, rssi, seguridad, oculta)
    except OSError:
        return None
    best = None
    for net in networks:
        if net[0] == target and (best is None or net[3] > best):
            best = net[3]
    return best


def wait_start(dist):
    if button is None:
        input('Colocate a {} m y pulsa Enter (Ctrl+C para terminar): '.format(dist))
    else:
        print('Colocate a {} m y pulsa el boton (Ctrl+C para terminar)'.format(dist))
        while button.value():        # espera a que se pulse (0 = pulsado)
            time.sleep_ms(20)
        while not button.value():    # espera a que se suelte
            time.sleep_ms(20)
        time.sleep_ms(100)


def append_lines(name, header, lines):
    is_new = name not in os.listdir()
    with open(name, 'a') as f:
        if is_new:
            f.write(header + '\n')
        for line in lines:
            f.write(line + '\n')


def mean_std(values):
    n = len(values)
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / (n - 1) if n > 1 else 0
    return mean, math.sqrt(var)


def main():
    print('Midiendo RSSI de "{}"  ({} medidas por punto)'.format(TARGET_SSID, SAMPLES))
    dist = START_M
    last_ok = None
    try:
        while True:
            wait_start(dist)
            values = []
            tries = 0
            led.on()
            while len(values) < SAMPLES and tries < MAX_TRIES:
                tries += 1
                rssi = read_rssi()
                if rssi is not None:
                    values.append(rssi)
                print('  {} m, barrido {}: {}'.format(dist, tries, rssi if rssi is not None else 'sin senal'))
            led.off()
            if values:
                mean, std = mean_std(values)
                row = '{},{},{:.2f},{:.2f},{},{},{}'.format(
                    dist, len(values), mean, std, min(values), max(values), tries)
                last_ok = dist
                print('>>> {} m: promedio {:.1f} dBm, desv {:.1f}, n={}'.format(dist, mean, std, len(values)))
            else:
                row = '{},0,,,,,{}'.format(dist, tries)
                print('>>> {} m: AP no detectado'.format(dist))
            append_lines(CSV_SUMMARY, HEADER_SUMMARY, [row])
            append_lines(CSV_RAW, HEADER_RAW,
                         ['{},{},{}'.format(dist, i + 1, v) for i, v in enumerate(values)])
            dist += STEP_M
    except KeyboardInterrupt:
        led.off()
        print('\nMedicion terminada.')
        if last_ok is not None:
            print('Alcance maximo con deteccion: {} m'.format(last_ok))
        print('Archivos en la Pico: {}, {}'.format(CSV_SUMMARY, CSV_RAW))


main()

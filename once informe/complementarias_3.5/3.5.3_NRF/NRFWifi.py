# Comunicaciones Digitales - UMNG
# Practica WiFi, 3.5.3: Pico W / Pico 2 W + NRF24L01 controlado por WiFi.
# La Pico crea un AP WiFi; desde la pagina web (nrf.html) se cambia el canal y la
# potencia del NRF24L01 y se envian/reciben mensajes por el radio NRF.
# Copiar a la Pico: NRFWifi.py, nrf.html y el driver nrf24l01.py (el del laboratorio del NRF).
# Se usa el MISMO programa en los dos nodos; solo cambia ROLE ('A' en uno, 'B' en el otro).
import network
import socket
import time
import gc
import json
from machine import Pin, SPI
from nrf24l01 import NRF24L01

ROLE = 'A'                       # 'A' en un nodo, 'B' en el otro

# --- WiFi (punto de acceso) ---
SSID = 'PicoW-NRF-Grupo_1'       # usa un nombre distinto en cada nodo (ej. ..._A y ..._B)
PASSWORD = '12345678'
WIFI_CHANNEL = 1                 # canal WiFi 1..11
IP = '192.168.4.1'
MASK = '255.255.255.0'
HTML_FILE = 'nrf.html'

# --- NRF24L01 (pines del laboratorio) ---
NRF_CHANNEL = 43                 # 0..125 -> frecuencia = 2400 + canal (MHz)
NRF_POWER = 3                    # 0..3 -> -18, -12, -6, 0 dBm
PAYLOAD = 32                     # bytes por paquete (maximo 32); igual en los dos nodos
SPI_ID, SCK, MOSI, MISO = 0, 18, 19, 16
CSN, CE = 17, 20
PIPES = (b'\xe1\xf0\xf0\xf0\xf0', b'\xd2\xf0\xf0\xf0\xf0')   # direcciones del driver estandar

POWER_BITS = (0x00, 0x02, 0x04, 0x06)   # RF_SETUP[2:1]: -18, -12, -6, 0 dBm
REG_RF_CH = 0x05
REG_RF_SETUP = 0x06

msgs = []       # [numero, tipo, texto]; tipo: tx, rx, err, sys
seq = 0
cfg = {'ch': NRF_CHANNEL, 'pwr': NRF_POWER}
led = Pin('LED', Pin.OUT)


def add_msg(kind, text):
    global seq
    seq += 1
    msgs.append([seq, kind, text])
    if len(msgs) > 15:
        msgs.pop(0)


# ---------------- NRF24L01 ----------------
spi = SPI(SPI_ID, baudrate=4000000, polarity=0, phase=0,
          sck=Pin(SCK), mosi=Pin(MOSI), miso=Pin(MISO))
nrf = NRF24L01(spi, Pin(CSN, Pin.OUT), Pin(CE, Pin.OUT),
               channel=NRF_CHANNEL, payload_size=PAYLOAD)
if ROLE == 'A':
    nrf.open_tx_pipe(PIPES[0])
    nrf.open_rx_pipe(1, PIPES[1])
else:
    nrf.open_tx_pipe(PIPES[1])
    nrf.open_rx_pipe(1, PIPES[0])


def apply_cfg(ch, pwr):
    nrf.stop_listening()
    nrf.reg_write(REG_RF_CH, ch)
    nrf.reg_write(REG_RF_SETUP, (nrf.reg_read(REG_RF_SETUP) & 0xF9) | POWER_BITS[pwr])
    nrf.start_listening()
    cfg['ch'], cfg['pwr'] = ch, pwr
    add_msg('sys', 'NRF: canal {} ({} MHz), potencia {} dBm'.format(
        ch, 2400 + ch, (-18, -12, -6, 0)[pwr]))


def send_msg(text):
    while len(text.encode()) > PAYLOAD:      # recorta para que quepa en un paquete
        text = text[:-1]
    data = text.encode()
    buf = data + b'\x00' * (PAYLOAD - len(data))   # relleno: el paquete es de tamano fijo
    nrf.stop_listening()
    nrf.send_start(buf)
    start = time.ticks_ms()
    result = None
    while result is None and time.ticks_diff(time.ticks_ms(), start) < 500:
        result = nrf.send_done()             # 1 = entregado (ACK), 2 = sin ACK
    nrf.start_listening()
    if result == 1:
        add_msg('tx', text)
        return True, 'Entregado (ACK recibido)'
    add_msg('err', text)
    return False, 'Sin ACK: el otro nodo no respondio (revisa canal y potencia)'


def poll_nrf():
    while nrf.any():
        raw = bytes(nrf.recv()).rstrip(b'\x00')
        try:
            text = raw.decode()
        except Exception:
            text = str(raw)
        add_msg('rx', text)
        led.toggle()


# ---------------- Servidor HTTP ----------------
def unquote(s):
    s = s.replace('+', ' ')
    parts = s.split('%')
    out = bytearray(parts[0].encode())
    for p in parts[1:]:
        out.append(int(p[:2], 16))
        out.extend(p[2:].encode())
    return out.decode()


def read_request(conn):
    conn.settimeout(3)
    data = b''
    while b'\r\n\r\n' not in data:
        chunk = conn.recv(512)
        if not chunk:
            raise ValueError('peticion vacia')
        data += chunk
        if len(data) > 2048:
            raise ValueError('peticion muy grande')
    line = data.split(b'\r\n', 1)[0].decode()
    method, target, _ = line.split()
    path, _, query = target.partition('?')
    params = {}
    for pair in query.split('&'):
        if '=' in pair:
            key, value = pair.split('=', 1)
            params[key] = unquote(value)
    return method, path, params


def respond(conn, body, ctype='application/json', status='200 OK'):
    if isinstance(body, str):
        body = body.encode()
    head = ('HTTP/1.1 {}\r\nContent-Type: {}\r\nContent-Length: {}\r\n'
            'Connection: close\r\nCache-Control: no-store\r\n\r\n').format(status, ctype, len(body))
    conn.sendall(head.encode())
    if body:
        conn.sendall(body)


def status_json():
    return json.dumps({'role': ROLE, 'ch': cfg['ch'], 'freq': 2400 + cfg['ch'],
                       'pwr': cfg['pwr'], 'wifi_ch': WIFI_CHANNEL, 'msgs': msgs})


def handle(conn, html):
    method, path, p = read_request(conn)
    if path == '/' and method == 'GET':
        respond(conn, html, 'text/html; charset=utf-8')
    elif path == '/status' and method == 'GET':
        respond(conn, status_json())
    elif path == '/cfg' and method == 'POST':
        ch = int(p.get('ch', cfg['ch']))
        pwr = int(p.get('pwr', cfg['pwr']))
        if 0 <= ch <= 125 and 0 <= pwr <= 3:
            apply_cfg(ch, pwr)
            respond(conn, status_json())
        else:
            respond(conn, '{"ok":false,"info":"Canal 0..125, potencia 0..3"}', status='400 Bad Request')
    elif path == '/send' and method == 'POST':
        text = p.get('m', '')
        if text:
            ok, info = send_msg(text)
            respond(conn, json.dumps({'ok': ok, 'info': info}))
        else:
            respond(conn, '{"ok":false,"info":"Mensaje vacio"}', status='400 Bad Request')
    elif path == '/favicon.ico':
        respond(conn, b'', status='204 No Content')
    else:
        respond(conn, 'Ruta no encontrada', 'text/plain', '404 Not Found')


def start_ap(ap):
    ap.active(False)
    time.sleep_ms(100)
    try:
        ap.config(ssid=SSID, password=PASSWORD, channel=WIFI_CHANNEL)
    except TypeError:
        ap.config(essid=SSID, password=PASSWORD, channel=WIFI_CHANNEL)
    ap.ifconfig((IP, MASK, IP, IP))
    ap.active(True)
    started = time.ticks_ms()
    while not ap.active():
        if time.ticks_diff(time.ticks_ms(), started) >= 10000:
            raise RuntimeError('El AP no se activo a tiempo')
        time.sleep_ms(50)
    print('AP:', SSID, '| IP:', ap.ifconfig()[0], '| Canal WiFi:', WIFI_CHANNEL)


def main():
    ap = network.WLAN(network.AP_IF)
    srv = None
    try:
        start_ap(ap)
        with open(HTML_FILE, 'rb') as f:
            html = f.read()
        apply_cfg(NRF_CHANNEL, NRF_POWER)
        srv = socket.socket()
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', 80))
        srv.listen(3)
        srv.settimeout(0.05)   # accept() con limite de tiempo para poder revisar el NRF
        print('Nodo {} listo. Abrir http://{}/  (Ctrl+C para detener)'.format(ROLE, IP))
        while True:
            try:
                conn, remote = srv.accept()
            except OSError:
                conn = None
            if conn:
                try:
                    handle(conn, html)
                except Exception as error:
                    print('Error atendiendo', remote, ':', error)
                    try:
                        respond(conn, 'Error', 'text/plain', '400 Bad Request')
                    except OSError:
                        pass
                finally:
                    conn.close()
                    gc.collect()
            poll_nrf()
    except KeyboardInterrupt:
        print('\nDetenido.')
    finally:
        if srv is not None:
            srv.close()
        led.value(0)
        ap.active(False)


main()

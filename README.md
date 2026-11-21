# Tecnología WiFi con Raspberry Pi Pico 2W

Comunicaciones Digitales · Ingeniería en Telecomunicaciones · Universidad Militar Nueva Granada · Periodo 2026-2

- **Docente:** Ing. José de Jesús Rugeles Uribe
- **Autores:** Harol Felipe Riveros Sierra y Salome Bohórquez Blanco




## Estructura de la carpeta

```
README.md
test_1/                    3.1 y 3.2 (código de la guía)
  wifi_mac.py
  scanner_wifi.py
test_2/                    3.3 (código de la guía)
  APWifipico.py
  index.html
test_3/                    3.4 (código de la guía)
  TrafficWifi.py
  index.html
complementarias_3.5/       3.5 (código desarrollado en esta práctica)
  3.5.1_ADC/               APWifipico.py + index.html con lectura del ADC 0
  3.5.2_RSSI/              rssi_distancia.py (en la Pico) + analisis_rssi.py (en el PC)
  3.5.3_NRF/               NRFWifi.py + nrf.html + nrf24l01.py
imagenes/                  capturas y fotos del informe, por sección
```




## Cómo ejecutar cada parte

En todos los casos se suben los archivos a la **raíz** de la Pico (Thonny, Guardar como, Raspberry Pi Pico). Antes de cambiar de parte conviene borrar los archivos de la anterior, y revisar que no quede un `main.py` viejo que arranque solo.

### 3.1 Dirección MAC
1. Ejecutar `test_1/wifi_mac.py`.
2. Reiniciar la placa varias veces y anotar la MAC en cada una.

### 3.2 Escaneo de redes
1. Ejecutar `test_1/scanner_wifi.py` durante más de 60 s.
2. El filtro `MIN_RSSI = -80` oculta las redes débiles. Para verlas todas, ponerlo en `None`.
3. La pantalla OLED es opcional. Sin ella el programa sigue por consola.

### 3.3 Punto de acceso y control del LED
1. En `test_2/APWifipico.py` cambiar `SSID` a `PicoW-AP-<GRUPO>` y `CHANNEL` a un canal distinto al de los demás grupos.
2. Ejecutar, conectarse a esa red (clave `12345678`) y abrir `http://192.168.4.1` con `http://` completo.
3. Probar los botones LED ON y LED OFF.

### 3.4 Medida del espectro
1. Subir `test_3/TrafficWifi.py` y `test_3/index.html`, y configurar `SSID` y `CHANNEL`.
2. Conectarse y abrir `http://192.168.4.1`. Los botones **Intermitente** (2 s de tráfico y 3 s de pausa) y **Sostenido** generan el tráfico.
3. En el analizador: frecuencia central en el canal elegido, span de unos 40 MHz, y marcadores para la frecuencia inferior y la superior de la señal. El ancho de banda es su diferencia.
4. Con el modo espectrograma se captura cada tipo de tráfico.

### 3.5.1 Lectura del ADC 0
1. Subir `complementarias_3.5/3.5.1_ADC/APWifipico.py` y `index.html`.
2. Conectar el potenciómetro: extremos a 3.3 V y GND, centro a **GP26** (pin físico 31). Nunca más de 3.3 V.
3. La página muestra el voltaje, el valor crudo (0 a 65535) y una barra, y se actualiza cada segundo.

### 3.5.2 RSSI contra la distancia
1. En `rssi_distancia.py` poner en `TARGET_SSID` el nombre **exacto** del AP, tal como sale en un escaneo.
2. Si el AP es un celular, debe emitir en **2.4 GHz** (en iPhone, activar "Maximizar compatibilidad") y tener abierta la pantalla del hotspot.
3. Ejecutar en Thonny. En cada punto el programa pide pulsar Enter, toma 10 medidas, y guarda `rssi_distancia.csv` (promedio por distancia) y `rssi_muestras.csv` (todas las medidas) dentro de la Pico.
4. Descargar los CSV (Thonny, View, Files) y, en el PC, ejecutar:
   ```
   pip install numpy matplotlib
   python analisis_rssi.py rssi_distancia.csv
   ```
   Entrega la gráfica `rssi_vs_distancia.png`, el alcance máximo y la ecuación `RSSI(d) = A − 10·n·log10(d)`.

### 3.5.3 NRF24L01 controlado por WiFi
1. Cablear el NRF24L01 a la Pico: CE a GP20, CSN a GP17, SCK a GP18, MOSI a GP19, MISO a GP16, y VCC a 3V3 (pin 36) con GND.
2. Subir a **cada** Pico `NRFWifi.py`, `nrf.html` y `nrf24l01.py` (el driver estándar de MicroPython).
3. En una Pico dejar `ROLE = 'A'` y en la otra `ROLE = 'B'`. Poner un `SSID` distinto en cada una, por ejemplo `PicoW-NRF-Grupo_1_A` y `..._B`. Si no, un mismo PC puede abrir siempre el mismo nodo.
4. Conectar un PC o celular a cada red y abrir `http://192.168.4.1`. Desde la página se cambian el canal NRF (0 a 125) y la potencia (0, −6, −12 y −18 dBm), y se envían mensajes.
5. Los dos nodos deben tener el **mismo canal NRF** para entenderse. Un mensaje se marca "Enviado" cuando el otro radio confirma la recepción, y "No entregado" si no hubo confirmación.

---

## Resultados del informe

| Parte | Resultado |
|---|---|
| 3.1 MAC | `2C:CF:67:DD:68:90` en las cuatro pruebas: no cambia entre reinicios |
| 3.2 Escaneo | 5 barridos de unos 10 s sin filtro de RSSI, con los AP por SSID, BSSID, canal y RSSI. Los cinco más fuertes están en los canales 6 (tres), 1 y 9 |
| 3.3 AP | Red creada y LED controlado desde `http://192.168.4.1` |
| 3.4 Espectro | Canal WiFi 6 (2437 MHz), ancho de banda medido de **17.38 MHz**, entre 2.428418 GHz y 2.445800 GHz |
| 3.5.3 NRF | Canal NRF 37 (2437 MHz), potencias 0, −6, −12 y −18 dBm, distancias de 5, 10 y 15 m. El nodo A recibió en todas las combinaciones y el nodo B registró un mensaje "No entregado" |

Las capturas de cada resultado están en `imagenes/`, con el número de figura del informe en el nombre del archivo.

## Problemas frecuentes

- **El AP no deja conectarse o la página no abre.** Los canales WiFi de 2.4 GHz válidos son del 1 al 13, y en la práctica del 1 al 11. Un número como 43, 72 o 76 es un canal del NRF24L01, no del WiFi. Conectarse a la red de la Pico antes de abrir la página.
- **El celular marca "sin internet".** Es normal: el AP es una red local. Mantener la conexión y apagar los datos móviles.
- **`ImportError: no module named 'nrf24l01'`.** Falta subir `nrf24l01.py` a esa Pico.
- **`OSError: nRF24L01+ Hardware not responding`.** Revisar el cableado del NRF24L01.
- **`sin senal` en el RSSI contra distancia.** El nombre del AP no coincide, o el AP está en 5 GHz. La Pico solo ve 2.4 GHz.
- **Mismo número, distinta frecuencia.** El canal WiFi 6 es 2437 MHz (2407 + 5 × canal). El canal NRF 6 es 2406 MHz (2400 + canal). Para que el NRF quede en 2437 MHz se usa el canal NRF 37.

## Estado del código

- `test_1`, `test_2` y `test_3` son los archivos de la guía, sin modificar salvo el renombrado indicado.
- `scanner_wifi.py` es la versión original. Las tablas de resumen del informe (mínimo, máximo, promedio y desviación por AP) salen de una versión ampliada del escáner que no está en esta carpeta.
- El código de `3.5.3_NRF` se ejecutó en dos Pico con NRF24L01 y es el que produjo los resultados del informe (sección E).
- El código de `3.5.1_ADC` y `3.5.2_RSSI` está incluido pero **el informe no tiene resultados de esas dos actividades**. Se probó su lógica en el computador con datos simulados, no en la placa.

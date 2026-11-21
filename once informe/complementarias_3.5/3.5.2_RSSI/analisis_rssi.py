# Analisis del RSSI vs distancia (se ejecuta en el COMPUTADOR, no en la Pico).
# Uso:  python analisis_rssi.py rssi_distancia.csv
# Requiere: pip install numpy matplotlib
import csv
import sys
import numpy as np
import matplotlib.pyplot as plt

archivo = sys.argv[1] if len(sys.argv) > 1 else 'rssi_distancia.csv'

d, rssi, desv, sin_senal = [], [], [], []
with open(archivo, newline='') as f:
    for fila in csv.DictReader(f):
        dist = float(fila['distancia_m'])
        if int(fila['n']) == 0 or fila['rssi_prom_dbm'] == '':
            sin_senal.append(dist)
            continue
        d.append(dist)
        rssi.append(float(fila['rssi_prom_dbm']))
        desv.append(float(fila['desv_dbm']))

d, rssi, desv = np.array(d), np.array(rssi), np.array(desv)
if len(d) < 2:
    sys.exit('Se necesitan al menos 2 distancias con senal.')

# Modelo de perdidas log-distancia:  RSSI(d) = A - 10*n*log10(d)
#   A = RSSI a 1 m (dBm),  n = exponente de perdidas (2 en espacio libre)
x = np.log10(d)
pendiente, A = np.polyfit(x, rssi, 1)
n = -pendiente / 10
ajuste = pendiente * x + A
r2 = 1 - np.sum((rssi - ajuste) ** 2) / np.sum((rssi - rssi.mean()) ** 2)

# Ajuste lineal, solo como referencia
b, a = np.polyfit(d, rssi, 1)

alcance = d.max()
print('Distancias con senal: {} a {} m'.format(int(d.min()), int(alcance)))
if sin_senal:
    print('Sin senal en: {} m'.format(', '.join(str(int(s)) for s in sorted(sin_senal))))
print('Alcance maximo medido: {:.0f} m (RSSI {:.1f} dBm)'.format(alcance, rssi[np.argmax(d)]))
print('\nModelo log-distancia:')
print('  RSSI(d) = {:.2f} - 10*{:.2f}*log10(d)  [dBm, d en m]   R2 = {:.3f}'.format(A, n, r2))
print('  RSSI a 1 m = {:.1f} dBm,  exponente de perdidas n = {:.2f}'.format(A, n))
print('Ajuste lineal (referencia): RSSI(d) = {:.2f} {:+.2f}*d'.format(a, b))

dd = np.linspace(d.min(), alcance * 1.05, 200)
plt.figure(figsize=(8, 5))
plt.errorbar(d, rssi, yerr=desv, fmt='o', capsize=3, label='Medidas (promedio ± desv.)')
plt.plot(dd, A - 10 * n * np.log10(dd), '-',
         label='RSSI = {:.1f} - {:.1f}·log10(d)   (R² = {:.2f})'.format(A, 10 * n, r2))
plt.axvline(alcance, ls='--', color='gray', label='Alcance máximo: {:.0f} m'.format(alcance))
plt.xlabel('Distancia (m)')
plt.ylabel('RSSI (dBm)')
plt.title('RSSI vs distancia')
plt.grid(alpha=.3)
plt.legend()
plt.tight_layout()
plt.savefig('rssi_vs_distancia.png', dpi=150)
print('\nGrafica guardada en rssi_vs_distancia.png')
plt.show()

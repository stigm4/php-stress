# PHP-Stress v0.01

Herramienta de **Fuzzing Recursivo, Análisis de Latencia y Pruebas de Estrés** escrita en Python. 
Diseñada para auditar servidores web, descubrir archivos `.php`, detectar cuellos de botella y probar la resistencia de scripts específicos.

## 🚀 Características

*   **Fuzzing Multihilo:** Escaneo rápido de directorios y archivos.
*   **Recursividad Inteligente:** Si encuentra un directorio, se mete en él automáticamente.
*   **Filtros Anti-False Positive:** Detección de *Wildcard 403* y *Catch-All 200* para evitar falsos positivos.
*   **Análisis de Latencia:** Mide qué script PHP tarda más en responder.
*   **Modo Estrés:** Se integra con `Apache Benchmark (ab)` para lanzar pruebas de carga controladas al archivo más lento detectado.
*   **Resultados:** Exportación automática de hallazgos con fecha y dominio.

## 📋 Requisitos

*   Python 3.x
*   Apache Benchmark (`ab`)

### Instalación de dependencias (Linux/Kali/Debian)

```bash
# 1. Instalar Apache Benchmark
sudo apt update
sudo apt install apache2-utils

# 2. Instalar librerías de Python
pip3 install -r requirements.txt
```

## 🛠️ Uso
```bash
python3 php-stress.py -u <URL> [opciones]

opciones:
  -h, --help            Mostrar ayuda
  -u, --url URL         URL Objetivo
  -w, --wordlist WORDLIST
                        Diccionario
  -t, --threads THREADS
                        Hilos simultáneos
  --test                Auto-ejecutar estrés al endpoint más lento
  --resultado FILE      Cargar resultados desde un archivo específico (ej: dominio_fecha.txt)

```

### Escaneo básico (Buscar y medir tiempos):
```bash
python3 php-stress.py -u http://192.168.1.50 -w common.txt
```

### Escaneo agresivo + Prueba de estrés al final:
```bash
python3 php-stress.py -u http://site.com -w big.txt -t 50 --test
```
  
### Reutilizar resultados de un escaneo anterior:
```bash
python3 php-stress.py --resultado site.com_2023-10-27.txt --test
```

  
## ⚠️ Disclaimer

Esta herramienta ha sido creada únicamente con fines educativos y para auditorías de seguridad autorizadas. El uso de esta herramienta contra objetivos sin consentimiento previo es ilegal. El autor no se hace responsable del mal uso.

    
---
---

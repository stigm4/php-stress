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


🛠️ Uso

python3 php-stress.py -u <URL> [opciones]

  

Argumentos
Flag	Descripción
-u, --url	URL Objetivo (ej: http://ejemplo.com)
-w, --wordlist	Ruta del diccionario (default: common.txt)
-t, --threads	Número de hilos simultáneos (default: 20)
--test	Activa la prueba de estrés automática con ab
--resultado	Carga un archivo de resultados previo en lugar de escanear
Ejemplos

Escaneo básico (Buscar y medir tiempos):


    
python3 php-stress.py -u http://192.168.1.50 -w common.txt

  

Escaneo agresivo + Prueba de estrés al final:
code Bash

    
python3 php-stress.py -u http://site.com -w big.txt -t 50 --test

  

Reutilizar resultados de un escaneo anterior:
code Bash

    
python3 php-stress.py --resultado site.com_2023-10-27.txt --test

  

⚠️ Disclaimer

Esta herramienta ha sido creada únicamente con fines educativos y para auditorías de seguridad autorizadas. El uso de esta herramienta contra objetivos sin consentimiento previo es ilegal. El autor no se hace responsable del mal uso.
code Code

    
---

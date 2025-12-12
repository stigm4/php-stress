import requests
import time
import argparse
import sys
import os
import subprocess
import shutil
import threading
import random
import string
from queue import Queue
from datetime import datetime
from urllib.parse import urlparse

# --- CONFIGURACIÓN DE COLORES ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    GREY = '\033[90m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    
    UP = '\033[A'        # Subir línea
    CLR = '\033[2K'      # Borrar línea
    RST = '\r'           # Inicio de línea

# --- BANNER ASCII ---
BANNER = f"""{Colors.BOLD}{Colors.RED}
                          +
                                                                     *                           v0.01
    *                                 @@@@@@@=                                             por estigma 
                                     @@@%           :                          +                       
       @@@@@  @+  @=  @@@@@@@@-     @@@@     =@@@@@@@@@@@@@  @@@@@@@@@  +                         +    
    @@@    @@ @@  @= @@@@    @@     @@@      #@@=  *@@      =@@   @@@  @@      -      @@@@@@           
     @@  *@@@ @@  @   @@@    @@     @@@%           *@@      =@@ %%@@  @@@@@ @@@@@@@  @@@= @@@          
     @@@@@@@ @@@  @    @@ #@@@@     @@@@           @@@      =@@@@@+   @@#@@ @@@      @@                
     @@@@    #@@@@@@@  @@@@=     +  +@@@           @@@      =@@@     -@@  @ @@@      @@          #     
     @=      @@@ +@    @@     @@@@#  @@@@@@-       @@@       @@@@@   @@@=@*  @@@      @#         @*@@  
     @@      *@* +@    @@                :@@@.     @@=       @@ @@@  @@@       %@@     @+     @@@@@@@  
     @@      =@@ @@    @%            @       @@    @@@       @@  @@% @@@    @@  @@@     @@   #@   @@.  
     @@      =@@ @@#   @*            @@     @@@    @%#      =@@  = @  @% @  @@ @@@@     *@   @#   @@   
      @@     =@@ @@    @.            :@@@=@@@@@    @#       @@@    @* %@@@  @@@@@@  @@@*@@  +@         
      @@     @@  @@                      ---       @        @@@          -           @@@@   @-         
       @=     @                                                  +                         @@          
       @                         *                                             @@@@@@@@@@@@@     +      
                                                       *              +                         *      
  *               *                                                                                    
{Colors.ENDC}"""

HELP_TEXT = f"""
Modo de uso: python3 php-stress.py -h[help] -u URL [-w WORDLIST] [-t HILOS] --test[hacer prueba de estrés] --resultado [ARCHIVO]

opciones:
  -h, --help            Mostrar ayuda
  -u, --url URL         URL Objetivo
  -w, --wordlist WORDLIST
                        Diccionario
  -t, --threads THREADS
                        Hilos simultáneos
  --test                Auto-ejecutar estrés al endpoint más lento
  --resultado FILE      Cargar resultados desde un archivo específico (ej: dominio_fecha.txt)
"""

# --- VARIABLES GLOBALES ---
print_lock = threading.Lock()
found_urls = []
wordlist_content = [] 
job_queue = Queue()
MAX_DEPTH = 2 

if os.name == 'nt': os.system('color')

# --- FUNCIONES DE UTILIDAD ---
def print_help_and_exit():
    print(BANNER)
    print(HELP_TEXT)
    sys.exit(0)

def generate_filename(url):
    """Genera un nombre de archivo basado en dominio y fecha."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc if parsed.netloc else parsed.path
        # Limpiar caracteres invalidos para archivos
        domain = domain.replace(":", "_").replace("/", "")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return f"{domain}_{timestamp}.txt"
    except:
        return "resultados_scan.txt"

def save_results(urls, filename):
    try:
        with open(filename, 'w') as f:
            for url in urls:
                f.write(f"{url}\n")
        print(f"\n{Colors.BLUE}[i] Resultados guardados en: {Colors.BOLD}{filename}{Colors.ENDC}")
        print(f"{Colors.GREY}    Para reusar: python3 php-stress.py --resultado {filename} --test{Colors.ENDC}")
    except IOError as e:
        print(f"{Colors.RED}[!] Error guardando resultados: {e}{Colors.ENDC}")

def load_results(filename):
    if not os.path.exists(filename):
        print(f"{Colors.RED}[!] No existe el archivo '{filename}'.{Colors.ENDC}")
        sys.exit(1)
    
    urls = []
    try:
        print(f"{Colors.BLUE}[*] Cargando resultados desde {filename}...{Colors.ENDC}")
        with open(filename, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        if not urls:
            print(f"{Colors.RED}[!] El archivo está vacío.{Colors.ENDC}")
            sys.exit(1)
            
        return urls
    except Exception as e:
        print(f"{Colors.RED}[!] Error leyendo el archivo: {e}{Colors.ENDC}")
        sys.exit(1)

def check_ab_installed():
    if shutil.which("ab") is None:
        print(f"{Colors.RED}[!] Error: 'ab' no está instalado.{Colors.ENDC}")
        sys.exit(1)

# --- VALIDACIÓN WILDCARD 403 ---
def is_wildcard_403(url):
    junk_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    test_url = f"{url.rstrip('/')}/{junk_name}"
    try:
        r = requests.head(test_url, timeout=3)
        return r.status_code == 403
    except:
        return True 

# --- GESTOR DE PANTALLA ---
class DisplayManager:
    def __init__(self):
        self.separator = "-" * 70
        print(f"{Colors.GREY}{self.separator}{Colors.ENDC}")
        sys.stdout.write("Iniciando workers...")
        sys.stdout.flush()

    def update_status(self, code, url):
        with print_lock:
            # Mostramos una URL truncada para que quepa
            display_url = (url[-60:]) if len(url) > 60 else url
            color = Colors.RED if code == 404 else Colors.YELLOW
            
            # Borrar linea actual (\033[2K) e imprimir estado encima
            sys.stdout.write(f"{Colors.RST}{Colors.CLR}{color}[{code}]{Colors.ENDC} Escaneando: ...{display_url}")
            sys.stdout.flush()

    def print_found(self, url, type_str="PHP", note=""):
        with print_lock:
            # 1. Borrar la línea de estado actual
            sys.stdout.write(f"{Colors.RST}{Colors.CLR}") 
            # 2. Subir a la línea del separador y borrarla también
            sys.stdout.write(f"{Colors.UP}{Colors.CLR}") 
            
            # 3. Imprimir el hallazgo
            icon = "[DIR]" if type_str == "DIR" else "[200 OK]"
            color = Colors.CYAN if type_str == "DIR" else Colors.GREEN
            
            msg = f"{color}{icon}{Colors.ENDC} {url} {Colors.BOLD}ENCONTRADO{Colors.ENDC}"
            if note:
                msg += f" {Colors.GREY}({note}){Colors.ENDC}"

            print(msg)
            
            # 4. Volver a dibujar el footer para el siguiente estado
            print(f"{Colors.GREY}{self.separator}{Colors.ENDC}")
            
            # Texto dinámico "Scan active..."
            sys.stdout.write(f"{Colors.GREY}Scan active...{Colors.ENDC}")
            sys.stdout.flush()

display = None

# --- LÓGICA DEL WORKER ---
def worker():
    while True:
        try:
            base_url, word, depth = job_queue.get()
            scan_target(base_url, word, depth)
            job_queue.task_done()
        except Exception:
            job_queue.task_done()

def scan_target(base_url, word, depth):
    # PARTE 1: PHP
    url_php = f"{base_url}/{word}.php".replace("//", "/").replace("http:/", "http://").replace("https:/", "https://")
    try:
        res = requests.head(url_php, timeout=3)
        if res.status_code == 200:
            found_urls.append(url_php)
            display.print_found(url_php, "PHP")
        else:
            display.update_status(res.status_code, url_php)
    except requests.RequestException:
        pass

    # PARTE 2: DIRECTORIO (Solo si NO termina en .php)
    if not word.lower().endswith(".php"):
        url_dir = f"{base_url}/{word}/".replace("//", "/").replace("http:/", "http://").replace("https:/", "https://")
        
        if depth < MAX_DEPTH:
            try:
                res_dir = requests.head(url_dir, timeout=3)
                
                if res_dir.status_code == 200:
                    display.print_found(url_dir, "DIR")
                    for w in wordlist_content:
                        job_queue.put((url_dir.rstrip("/"), w, depth + 1))

                elif res_dir.status_code == 403:
                    if is_wildcard_403(url_dir):
                        display.print_found(url_dir, "DIR", note="403 Locked - Sin Escanear")
                    else:
                        display.print_found(url_dir, "DIR", note="403 Protegido")
                        for w in wordlist_content:
                            job_queue.put((url_dir.rstrip("/"), w, depth + 1))
            except requests.RequestException:
                pass

def run_fuzzer(start_url, wordlist_path, threads=30, output_file="resultados.txt"):
    global display, wordlist_content
    
    print(BANNER) # Mostrar banner al inicio del proceso también
    print(f"{Colors.HEADER}[*] INICIANDO FUZZING RECURSIVO ({threads} hilos){Colors.ENDC}")
    print("Los resultados aparecerán arriba. El escaneo activo abajo.")
    print("=" * 70 + "\n")
    
    display = DisplayManager()

    try:
        with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
            wordlist_content = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"\n{Colors.RED}[!] Wordlist no encontrada: {wordlist_path}{Colors.ENDC}")
        sys.exit(1)

    for word in wordlist_content:
        job_queue.put((start_url, word, 0))

    for _ in range(threads):
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()

    try:
        job_queue.join()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}[!] Deteniendo escaneo...{Colors.ENDC}")
        if found_urls:
            save_results(found_urls, output_file)
        sys.exit(0)

    with print_lock:
        sys.stdout.write(f"{Colors.RST}{Colors.CLR}") 
        print(f"{Colors.BLUE}[*] Escaneo finalizado.{Colors.ENDC}")

    return found_urls

# --- LATENCIA Y ESTRÉS ---
def measure_latency(urls):
    if not urls: return None, 0
    
    php_urls = [u for u in urls if u.endswith('.php')]
    if not php_urls: return None, 0

    print(f"\n{Colors.HEADER}[*] Midiendo latencia de {len(php_urls)} archivos PHP...{Colors.ENDC}")
    slowest_url = None
    max_time = 0.0

    for url in php_urls:
        try:
            start = time.time()
            requests.get(url, timeout=5)
            end = time.time()
            total = end - start
            
            bar = "█" * int(total * 20)
            color = Colors.RED if total > 1.0 else Colors.GREEN
            print(f"   {url:<40} | {color}{total:.4f}s {bar}{Colors.ENDC}")

            if total > max_time:
                max_time = total
                slowest_url = url
        except:
            pass
            
    return slowest_url, max_time

def stress_test(url):
    print(f"\n{Colors.HEADER}[*] EJECUTANDO PRUEBA DE ESTRÉS (ab){Colors.ENDC}")
    print(f"Objetivo: {Colors.BOLD}{url}{Colors.ENDC}")
    
    cmd = ["ab", "-n", "500", "-c", "120", "-k", "-l", "-s", "5000", url]
    print(f"{Colors.GREY}Comando: {' '.join(cmd)}{Colors.ENDC}\n")
    print("-" * 70)
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None: break
            if line:
                if any(x in line for x in ["Requests per second", "Time taken", "Failed requests"]):
                    print(f"{Colors.GREEN}>> {line.strip()}{Colors.ENDC}")
                elif "Copyright" not in line and "Benchmarking" not in line:
                    print(f"{Colors.GREY}{line.strip()}{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.RED}[!] Error: {e}{Colors.ENDC}")

# --- MAIN ---
def main():
    # 1. Si se ejecuta sin argumentos, mostrar Help y salir
    if len(sys.argv) == 1:
        print_help_and_exit()

    # 2. Configurar Argumentos
    parser = argparse.ArgumentParser(add_help=False) 
    
    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("-u", "--url", help="URL Objetivo")
    parser.add_argument("-w", "--wordlist", default="common.txt")
    parser.add_argument("-t", "--threads", type=int, default=40)
    parser.add_argument("--test", action="store_true")
    # Cambiado: Ahora espera un string (el nombre del archivo)
    parser.add_argument("--resultado", type=str, metavar="ARCHIVO", help="Ruta del archivo de resultados anterior")
    
    args = parser.parse_args()

    # Gestión de ayuda manual con -h
    if args.help:
        print_help_and_exit()

    if args.test: check_ab_installed()
    
    final_found_urls = []

    # FLUJO 1: Usar resultados anteriores (requiere archivo)
    if args.resultado:
        print(BANNER)
        # El usuario proporciona el nombre exacto del archivo
        final_found_urls = load_results(args.resultado)
        
    # FLUJO 2: Escaneo Nuevo
    elif args.url:
        base_url = args.url.rstrip("/")
        # Generamos el nombre del archivo con Dominio + Fecha
        filename = generate_filename(base_url)
        
        final_found_urls = run_fuzzer(base_url, args.wordlist, args.threads, filename)
        
        # Guardar resultados
        if final_found_urls:
            save_results(final_found_urls, filename)
        else:
            sys.exit(0)
    else:
        # Caso de seguridad
        print(f"{Colors.RED}[!] Debes especificar una URL (-u) o cargar resultados (--resultado ARCHIVO){Colors.ENDC}")
        sys.exit(1)

    # Parte Común: Latencia y Estrés
    slowest, time_taken = measure_latency(final_found_urls)

    if slowest:
        print(f"\n{Colors.YELLOW}" + "="*70)
        print(f"REPORTE: Más lento -> {Colors.RED}{Colors.BOLD}{slowest}{Colors.ENDC}")
        print(f"{Colors.YELLOW}" + "="*70 + f"{Colors.ENDC}")
        
        if args.test:
            stress_test(slowest)
        else:
            print(f"\n{Colors.BLUE}[i] Usa --test para carga.{Colors.ENDC}")

if __name__ == "__main__":
    main()

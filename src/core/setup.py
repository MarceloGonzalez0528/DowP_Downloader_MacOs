import os
import platform
import shutil
import subprocess
import sys
import tarfile
import zipfile
import requests

# --- CONSTANTES DEL PROYECTO ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BIN_DIR = os.path.join(PROJECT_ROOT, "bin")
FFMPEG_VERSION_FILE = os.path.join(BIN_DIR, "ffmpeg_version.txt")


# --- FUNCIÓN 1: VERIFICAR DEPENDENCIAS DE PYTHON ---
def check_and_install_python_dependencies(progress_callback):
    """Verifica e instala dependencias de Python desde requirements.txt."""
    progress_callback("Verificando dependencias de Python...", 5)
    try:
        import customtkinter, PIL, requests, yt_dlp
        progress_callback("Dependencias de Python verificadas.", 15)
        return True
    except ImportError:
        progress_callback("Instalando dependencias necesarias...", 10)
        requirements_path = os.path.join(PROJECT_ROOT, "requirements.txt")
        if not os.path.exists(requirements_path):
            progress_callback("ERROR: No se encontró 'requirements.txt'.", -1)
            return False
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-r", requirements_path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            progress_callback("Dependencias instaladas.", 15)
            return True
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Falló la instalación de dependencias con pip: {e}")
            progress_callback("Error al instalar dependencias.", -1)
            return False

# --- FUNCIÓN 2: OBTENER INFO DE ÚLTIMA VERSIÓN DE FFMPEG ---
def get_latest_ffmpeg_info(progress_callback):
    """Consulta la API de GitHub para la última versión de FFmpeg."""
    progress_callback("Consultando la última versión de FFmpeg...", 5)
    try:
        api_url = "https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/latest"
        response = requests.get(api_url, timeout=15)
        response.raise_for_status()
        latest_release_data = response.json()
        tag_name = latest_release_data["tag_name"]
        
        system = platform.system()
        if system == "Windows": file_identifier = "win64-gpl.zip"
        elif system == "Linux": file_identifier = "linux64-gpl.tar.xz"
        elif system == "Darwin": file_identifier = "osx64-gpl.zip"
        else: return None, None

        for asset in latest_release_data["assets"]:
            if file_identifier in asset["name"] and "shared" not in asset["name"]:
                progress_callback("Información de FFmpeg encontrada.", 10)
                return tag_name, asset["browser_download_url"]
        return tag_name, None
    except requests.RequestException as e:
        progress_callback(f"Error de red al buscar FFmpeg.", -1)
        print(f"DEBUG: Error de red: {e}")
        return None, None

# --- FUNCIÓN 3: DESCARGAR E INSTALAR FFMPEG ---
def download_and_install_ffmpeg(version, url, progress_callback):
    """Descarga, extrae e instala FFmpeg en el directorio bin."""
    if not os.path.exists(BIN_DIR):
        os.makedirs(BIN_DIR)
    
    is_zip = url.endswith(".zip")
    ext = ".zip" if is_zip else ".tar.xz"
    download_path = os.path.join(PROJECT_ROOT, f"ffmpeg-temp{ext}")
    temp_extract_path = os.path.join(PROJECT_ROOT, "ffmpeg-extracted")

    try:
        progress_callback("Descargando FFmpeg...", 50)
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(download_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        progress_callback("Extrayendo archivos...", 85)
        if os.path.exists(temp_extract_path): shutil.rmtree(temp_extract_path)
        os.makedirs(temp_extract_path)
        
        if is_zip:
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_path)
        else:
            with tarfile.open(download_path, 'r:xz') as tar_ref:
                tar_ref.extractall(path=temp_extract_path)

        progress_callback("Instalando ejecutables...", 90)
        inner_folder_name = os.listdir(temp_extract_path)[0]
        bin_content_path = os.path.join(temp_extract_path, inner_folder_name, 'bin')
        
        for item_name in ["ffmpeg", "ffprobe"]:
            if platform.system() == "Windows":
                item_name += ".exe"
            
            source_path = os.path.join(bin_content_path, item_name)
            dest_path = os.path.join(BIN_DIR, item_name)
            
            if os.path.exists(source_path):
                shutil.move(source_path, dest_path)
                if platform.system() in ["Linux", "Darwin"]:
                    os.chmod(dest_path, 0o755)

        with open(FFMPEG_VERSION_FILE, 'w') as f:
            f.write(version)
        progress_callback("Instalación de FFmpeg completada.", 95)

    finally:
        if os.path.exists(download_path): os.remove(download_path)
        if os.path.exists(temp_extract_path): shutil.rmtree(temp_extract_path)

# --- FUNCIÓN 4: VERIFICACIÓN PRINCIPAL DEL ENTORNO (VERSIÓN RÁPIDA) ---
def check_environment_status(progress_callback):
    """Verifica el entorno de forma RÁPIDA y SIN CONEXIÓN A INTERNET para evitar bloqueos."""
    try:
        if not check_and_install_python_dependencies(progress_callback):
            return {"status": "error", "message": "Fallo crítico al instalar dependencias de Python."}
        
        progress_callback("Verificando FFmpeg local...", 40)
        
        local_tag = ""
        if os.path.exists(FFMPEG_VERSION_FILE):
            with open(FFMPEG_VERSION_FILE, 'r') as f:
                local_tag = f.read().strip()
        
        ffmpeg_exe = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
        ffmpeg_path_in_bin = os.path.join(BIN_DIR, ffmpeg_exe)

        if os.path.exists(ffmpeg_path_in_bin):
            return {
                "status": "success", 
                "message": "Se usará FFmpeg local.", 
                "ffmpeg_path_exists": True, 
                "local_version": local_tag or "Desconocida"
            }
        else:
            return {
                "status": "warning", 
                "message": "FFmpeg no encontrado. Usa el botón de mantenimiento para instalarlo.",
                "ffmpeg_path_exists": False,
                "local_version": "No instalado"
            }
            
    except Exception as e:
        return {"status": "error", "message": f"Error en la verificación del entorno: {e}"}
import sys
import os
import subprocess
import multiprocessing
import platform

# --- CONSTANTES DEL PROYECTO ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def install_dependencies():
    """Verifica si las dependencias están instaladas."""
    try:
        import customtkinter
        return True
    except ImportError:
        print("Dependencia 'customtkinter' no encontrada. Intentando instalar...")
        try:
            requirements_path = os.path.join(PROJECT_ROOT, "requirements.txt")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
            return True
        except Exception as e:
            print(f"ERROR CRÍTICO: No se pudieron instalar las dependencias: {e}")
            return False

if __name__ == "__main__":
    multiprocessing.freeze_support()

    # Define la ruta exacta de FFmpeg
    ffmpeg_path = "/opt/homebrew/bin/ffmpeg"
    
    # Añade la carpeta de FFmpeg al PATH del sistema por si acaso
    ffmpeg_dir = os.path.dirname(ffmpeg_path)
    if ffmpeg_dir not in os.environ['PATH']:
        os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ['PATH']
    
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)
    
    if not install_dependencies():
        sys.exit(1)
        
    print("Iniciando la aplicación...")
    from src.gui.main_window import MainWindow
    
    # Aquí está la corrección: le pasamos la ruta a la ventana al crearla
    app = MainWindow(ffmpeg_path=ffmpeg_path)
    app.mainloop()
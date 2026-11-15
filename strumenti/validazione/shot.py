"""Serve la cartella del sito sulla porta 8765 per le prove nel browser (usato da importazione_ccsds.py, angolo_beta.py, bordo_ellissoide.py)."""
import socket, subprocess, sys, time, pathlib
def serve():
    s=socket.socket()
    if s.connect_ex(('127.0.0.1',8765))!=0:
        subprocess.Popen([sys.executable,'-m','http.server','8765','--bind','127.0.0.1'],cwd=str(pathlib.Path(__file__).resolve().parents[2]),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(0.8)
    s.close()

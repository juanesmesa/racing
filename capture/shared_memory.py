# capture/shared_memory.py
import mmap
import struct

def get_assetto_data():
    """Lee la memoria compartida de Assetto Corsa y devuelve los datos crudos."""
    try:
        # Accedemos a la memoria de Assetto Corsa
        shm = mmap.mmap(0, 512, "Local\\acpmf_graphics", access=mmap.ACCESS_READ)
        
        # Unpack de datos según tus offsets calibrados
        vueltas = struct.unpack('i', shm[132:136])[0]
        tiempo_actual = struct.unpack('i', shm[140:144])[0]
        ultimo_tiempo = struct.unpack('i', shm[144:148])[0]
        
        shm.close()
        
        return {
            "vueltas": vueltas,
            "tiempo_actual": tiempo_actual,
            "ultimo_tiempo": ultimo_tiempo
        }
    except Exception:
        # Si el juego está cerrado o no lee la memoria, devuelve valores en 0
        return {"vueltas": -1, "tiempo_actual": 0, "ultimo_tiempo": 0}
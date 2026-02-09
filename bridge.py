import mmap
import struct
import asyncio
import json
import websockets
from supabase import create_client, Client

# === CONFIGURACIÓN SUPABASE ===
SUPABASE_URL = "https://knasnjakrhsxfanhfjha.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtuYXNuamFrcmhzeGZhbmhmamhhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA1NzAxMzYsImV4cCI6MjA4NjE0NjEzNn0.XGwk7EOVOH_RktntWtuIPvijzv2G-VIbktt27XhJstQ"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Variable global para saber a qué piloto guardarle el tiempo
active_driver_id = None

async def telemetry_server(websocket):
    global active_driver_id
    print("🏁 ORIÓN: Sistema conectado. Monitoreando pista...")
    last_lap_count = -1
    
    # Tarea para escuchar mensajes desde la web (como SELECT_DRIVER)
    async def listen_to_web():
        global active_driver_id
        try:
            async for message in websocket:
                data = json.loads(message)
                if data.get("type") == "SELECT_DRIVER":
                    active_driver_id = data.get("driver_id")
                    print(f"\n👤 Piloto activo en pista: {active_driver_id}")
        except:
            pass

    # Iniciamos la escucha en segundo plano
    asyncio.create_task(listen_to_web())

    while True:
        try:
            # Accedemos a la memoria de Assetto Corsa
            shm = mmap.mmap(0, 512, "Local\\acpmf_graphics", access=mmap.ACCESS_READ)
            
            # Unpack de datos según tus offsets calibrados
            vueltas = struct.unpack('i', shm[132:136])[0]
            tiempo_actual = struct.unpack('i', shm[140:144])[0]
            ultimo_tiempo = struct.unpack('i', shm[144:148])[0]

            if tiempo_actual > 0:
                # 1. Enviar tiempo en vivo a la web
                payload_live = {"type": "LIVE", "current_ms": tiempo_actual}
                await websocket.send(json.dumps(payload_live))

                print(f"Vuelta: {vueltas} | Cronómetro: {tiempo_actual}ms", end="\r")

                # 2. Detectar fin de vuelta (Meta)
                if vueltas > last_lap_count:
                    if last_lap_count != -1 and ultimo_tiempo > 0:
                        # Enviar a la web para efectos visuales
                        payload = {"type": "NEW_LAP", "time_ms": ultimo_tiempo}
                        await websocket.send(json.dumps(payload))
                        
                        print(f"\n✅ META DETECTADA: {ultimo_tiempo}ms")

                        # 3. GUARDAR AUTOMÁTICAMENTE EN SUPABASE
                        if active_driver_id:
                            try:
                                supabase.table("laps").insert({
                                    "driver_id": active_driver_id,
                                    "time_ms": ultimo_tiempo
                                }).execute()
                                print(f"☁️ Tiempo guardado en la nube para el piloto {active_driver_id}")
                            except Exception as e:
                                print(f"❌ Error al subir a la nube: {e}")
                        else:
                            print("⚠️ Vuelta terminada pero NO hay piloto seleccionado en la web. No se guardó en la nube.")
                    
                    last_lap_count = vueltas
            
            shm.close()
            await asyncio.sleep(0.05) # 20Hz de refresco (fluido y eficiente)

        except websockets.exceptions.ConnectionClosed:
            print("\n🔌 Conexión cerrada con el navegador.")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            await asyncio.sleep(1)

async def main():
    print("🚀 BRIDGE ORIÓN V8 - INTEGRACIÓN SUPABASE ACTIVA")
    async with websockets.serve(telemetry_server, "0.0.0.0", 8765):
        await asyncio.Future()  # Corre para siempre

if __name__ == "__main__":
    asyncio.run(main())
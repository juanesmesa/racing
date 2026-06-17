# bridge.py
import asyncio
import json
import websockets
import os  # <-- Asegúrate de tener importado 'os'
from supabase import create_client, Client

# === IMPORTACIONES DE CAPTURA ===
from capture.shared_memory import get_assetto_data
from capture.udp_receiver import get_f1_data

# 🕹️ CONFIGURACIÓN DEL JUEGO ACTUAL
# Ahora lee automáticamente lo que seleccionas en el archivo .bat
JUEGO_ACTUAL = os.environ.get("JUEGO_ACTUAL", "ASSETTO_CORSA")

active_driver_id = None
active_driver_name = "Nadie en pista"

# === CONFIGURACIÓN SUPABASE ===
SUPABASE_URL = "https://knasnjakrhsxfanhfjha.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtuYXNuamFrcmhzeGZhbmhmamhhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA1NzAxMzYsImV4cCI6MjA4NjE0NjEzNn0.XGwk7EOVOH_RktntWtuIPvijzv2G-VIbktt27XhJstQ"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def telemetry_server(websocket):
    global active_driver_id, active_driver_name
    print(f"🏁 ORIÓN: Sistema conectado en modo [{JUEGO_ACTUAL}]. Monitoreando pista...")
    last_lap_count = -1
    
    # Tarea para escuchar mensajes desde la web
    async def listen_to_web():
        global active_driver_id, active_driver_name
        try:
            async for message in websocket:
                data = json.loads(message)
                if data.get("type") == "SELECT_DRIVER":
                    active_driver_id = data.get("driver_id")
                    active_driver_name = data.get("driver_name")
                    print(f"\n👤 Piloto activo en pista: {active_driver_name}")
        except Exception as e:
            print(f"Error en comunicación web: {e}")

    async def listen_to_game():
        """Función interna para decidir dinámicamente qué juego leer."""
        if JUEGO_ACTUAL == "ASSETTO_CORSA":
            return get_assetto_data()
        elif JUEGO_ACTUAL == "F1":
            return get_f1_data()
        return {"vueltas": -1, "tiempo_actual": 0, "ultimo_tiempo": 0}

    # Iniciamos la escucha de la web en segundo plano
    asyncio.create_task(listen_to_web())

    while True:
        try:
            # Obtener datos estandarizados del juego seleccionado
            game_data = await listen_to_game()
            
            vueltas = game_data["vueltas"]
            tiempo_actual = game_data["tiempo_actual"]
            ultimo_tiempo = game_data["ultimo_tiempo"]
            print(f"📡 Datos leídos -> Vuelta: {vueltas} | Tiempo: {tiempo_actual}ms", end="\r")
            if tiempo_actual > 0:
                # 1. Enviar tiempo en vivo a la web
                payload_live = {
                    "type": "LIVE", 
                    "current_ms": tiempo_actual,
                    "driver_name": active_driver_name if active_driver_id else "Nadie en pista"
                }
                await websocket.send(json.dumps(payload_live))

                print(f"Juego: {JUEGO_ACTUAL} | Vuelta: {vueltas} | Cronómetro: {tiempo_actual}ms", end="\r")

                # 2. Detectar fin de vuelta (Meta)
                if vueltas > last_lap_count:
                    if last_lap_count != -1 and ultimo_tiempo > 0:
                        payload = {
                            "type": "NEW_LAP", 
                            "time_ms": ultimo_tiempo, 
                            "driver_name": active_driver_name
                        }
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
            
            await asyncio.sleep(0.05) # 20Hz de refresco

        except websockets.exceptions.ConnectionClosed:
            print("\n🔌 Conexión cerrada con el navegador.")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            await asyncio.sleep(1)

async def main():
    print(f"🚀 BRIDGE ORIÓN V8.1 - MODO MULTI-SIMULADOR [{JUEGO_ACTUAL}]")
    async with websockets.serve(telemetry_server, "0.0.0.0", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
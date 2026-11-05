# bridge.py
import asyncio
import json
import websockets
import os
import uuid
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
# Las claves privadas SOLO se configuran en Windows, nunca en GitHub.
SUPABASE_SECRET_KEY = os.environ.get("ORION_SUPABASE_SECRET_KEY", "").strip()
SUPABASE_ANON_KEY = os.environ.get("ORION_SUPABASE_ANON_KEY", "").strip()
ADMIN_USER_ID = os.environ.get("ORION_ADMIN_USER_ID", "").strip().lower()

if not SUPABASE_SECRET_KEY or not SUPABASE_SECRET_KEY.startswith("sb_secret_"):
    raise SystemExit("Falta ORION_SUPABASE_SECRET_KEY (sb_secret_...) en Windows.")
if not SUPABASE_ANON_KEY:
    raise SystemExit("Falta ORION_SUPABASE_ANON_KEY (clave publica) en Windows.")
try:
    ADMIN_USER_ID = str(uuid.UUID(ADMIN_USER_ID))
except ValueError:
    raise SystemExit("ORION_ADMIN_USER_ID debe ser el UUID de Authentication > Users.")

# Cliente privilegiado solo para insertar vueltas; cliente publico para validar sesiones.
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
auth_client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def verified_admin(token):
    if not isinstance(token, str) or not token or len(token) > 8192:
        return False
    try:
        response = auth_client.auth.get_user(token)
        return bool(response.user and str(response.user.id).lower() == ADMIN_USER_ID)
    except Exception:
        return False

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
                    # Un visitante puede mirar el cronometro, pero no seleccionar pilotos.
                    token = data.get("access_token")
                    authorized = await asyncio.to_thread(verified_admin, token)
                    if not authorized:
                        await websocket.send(json.dumps({"type": "ERROR", "message": "Seleccion de piloto no autorizada"}))
                        continue
                    try:
                        driver_id = str(uuid.UUID(str(data.get("driver_id", ""))))
                        # El nombre proviene de la BD, no del mensaje del navegador.
                        result = await asyncio.to_thread(
                            lambda: supabase.table("drivers").select("id,name").eq("id", driver_id).single().execute()
                        )
                        if not result.data:
                            raise ValueError("Piloto inexistente")
                        active_driver_id = driver_id
                        active_driver_name = result.data["name"]
                        print(f"\n👤 Piloto activo en pista: {active_driver_name}")
                    except Exception as exc:
                        print(f"\nSeleccion de piloto rechazada: {type(exc).__name__}")
                        await websocket.send(json.dumps({"type": "ERROR", "message": "Piloto no valido"}))
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

import mmap
import struct
import asyncio
import json
import websockets

async def telemetry_server(websocket):
    print("🏁 ORIÓN: Sistema conectado. Monitoreando pista...")
    last_lap_count = -1
    
    while True:
        try:
            # Accedemos a la memoria
            shm = mmap.mmap(0, 512, "Local\\acpmf_graphics", access=mmap.ACCESS_READ)
            
            vueltas = struct.unpack('i', shm[132:136])[0]
            tiempo_actual = struct.unpack('i', shm[140:144])[0]
            ultimo_tiempo = struct.unpack('i', shm[144:148])[0]

            if tiempo_actual > 0:
                # Enviamos el tiempo actual para el cronómetro en vivo
                payload_live = {"type": "LIVE", "current_ms": tiempo_actual}
                await websocket.send(json.dumps(payload_live))

                print(f"Vuelta: {vueltas} | Cronómetro: {tiempo_actual}ms", end="\r")

                # Detectar cuando el contador de vueltas sube
                if vueltas > last_lap_count:
                    if last_lap_count != -1 and ultimo_tiempo > 0:
                        payload = {"type": "NEW_LAP", "time_ms": ultimo_tiempo}
                        await websocket.send(json.dumps(payload))
                        print(f"\n✅ META DETECTADA: {ultimo_tiempo}ms enviando a ORIÓN...")
                    
                    last_lap_count = vueltas
            
            shm.close()
            await asyncio.sleep(0.05)

        # --- CORRECCIÓN PARA EL ERROR 1001 ---
        except websockets.exceptions.ConnectionClosedOK:
            break # Cierre normal, salimos del bucle silenciosamente
        except websockets.exceptions.ConnectionClosedError:
            print("\n🔌 Conexión perdida con el navegador. Esperando reconexión...")
            break # Cierre con error, salimos para esperar al nuevo cliente
        except Exception as e:
            print(f"\n❌ Error inesperado: {e}")
            await asyncio.sleep(1)

async def main():
    print("🚀 BRIDGE ORIÓN V7 - OFFSET CALIBRADO (140/144)")
    async with websockets.serve(telemetry_server, "127.0.0.1", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
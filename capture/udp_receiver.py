# capture/udp_receiver.py
import socket
import struct

UDP_IP = "0.0.0.0"
UDP_PORT = 20777

HEADER_SIZE = 29
LAP_DATA_SIZE = 57
PACKET_LAP_DATA = 2

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((UDP_IP, UDP_PORT))
sock.setblocking(False)

f1_vueltas = 0
f1_tiempo_actual = 0
f1_ultimo_tiempo = 0

print("F1 25 UDP escuchando en puerto 20777...")

def get_f1_data():
    global f1_vueltas, f1_tiempo_actual, f1_ultimo_tiempo

    try:
        for _ in range(30):
            try:
                data, addr = sock.recvfrom(2048)
            except BlockingIOError:
                break

            if len(data) < HEADER_SIZE:
                continue

            packet_format = struct.unpack_from("<H", data, 0)[0]
            packet_id = data[6]
            player_car_index = data[27]

            if packet_id != PACKET_LAP_DATA:
                continue

            if player_car_index >= 22:
                continue

            car_offset = HEADER_SIZE + (player_car_index * LAP_DATA_SIZE)

            if len(data) < car_offset + LAP_DATA_SIZE:
                continue

            last_lap_ms = struct.unpack_from("<I", data, car_offset + 0)[0]
            current_lap_ms = struct.unpack_from("<I", data, car_offset + 4)[0]
            current_lap_num = data[car_offset + 33]

            f1_ultimo_tiempo = last_lap_ms
            f1_tiempo_actual = current_lap_ms
            f1_vueltas = current_lap_num

            print(
                f"F1 {packet_format} | Vuelta: {f1_vueltas} | "
                f"Actual: {f1_tiempo_actual}ms | Ultima: {f1_ultimo_tiempo}ms",
                end="\r"
            )

    except Exception as e:
        print(f"\nError leyendo F1 UDP: {e}")

    return {
        "vueltas": f1_vueltas,
        "tiempo_actual": f1_tiempo_actual,
        "ultimo_tiempo": f1_ultimo_tiempo
    }
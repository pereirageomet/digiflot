#!/usr/bin/env python3
import serial, time, logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger()

def open_lidar(port="/dev/serial0", baud=115200, tout=0.5):
    ser = serial.Serial(port, baud, timeout=tout)
    ser.reset_input_buffer()
    log.info(f"LIDAR aberto em {port}")
    return ser

def read_distance(ser, timeout=2.0):
    start = time.time()
    while time.time() - start < timeout:
        if ser.in_waiting < 2:
            time.sleep(0.01)
            continue
        if ser.read(2) != b"\x59\x59":
            ser.reset_input_buffer()
            continue
        payload = ser.read(7)
        if len(payload) != 7:
            ser.reset_input_buffer()
            continue
        frame = b"\x59\x59" + payload
        dist = frame[2] + (frame[3] << 8)
        if frame[8] != (sum(frame[:8]) & 0xFF):
            log.warning("Checksum errado")
            ser.reset_input_buffer()
            continue
        return dist
    log.warning("Timeout LIDAR")
    return None

if __name__ == "__main__":
    try:
        ser = open_lidar()
        while True:
            d = read_distance(ser)
            print(f"Distância: {d if d is not None else '---'} cm")
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        if "ser" in locals() and ser.is_open:
            ser.close()

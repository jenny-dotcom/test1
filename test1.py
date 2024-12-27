from flask import Flask, render_template, request
import serial
import serial.tools.list_ports
import time
import psycopg2  # ไลบรารี PostgreSQL

app = Flask(__name__)  # แก้ไขพิมพ์ผิด

# ฟังก์ชันสำหรับเริ่มการเชื่อมต่อ Serial
def initialize_serial_connection():
    available_ports = [port.device for port in serial.tools.list_ports.comports()]
    target_port = 'COM9'

    if target_port in available_ports:
        try:
            arduino = serial.Serial(target_port, 9600, timeout=2)
            time.sleep(2)  # รอให้การเชื่อมต่อ Serial เสถียร
            print(f"เชื่อมต่อกับ {target_port} สำเร็จ")
            return arduino
        except serial.SerialException as e:
            print(f"ไม่สามารถเชื่อมต่อกับ {target_port}: {e}")
            raise
    else:
        raise serial.SerialException(f"ไม่พบ {target_port}. พอร์ตที่มีอยู่: " + ", ".join(available_ports))

# เริ่มการเชื่อมต่อ Serial
try:
    arduino = initialize_serial_connection()
except Exception as e:
    arduino = None
    print(f"ข้อผิดพลาดการเชื่อมต่อ Serial: {e}")

# การตั้งค่าการเชื่อมต่อฐานข้อมูล
DB_CONFIG = {
    'dbname': '',         # Your localhost default ip: 127.0.0.1
    'user': '',   # Your database name
    'password':'',             # Your password for login
    'host': '',
    'port':'5432'
}

# ฟังก์ชันสำหรับเชื่อมต่อฐานข้อมูล
def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("เชื่อมต่อกับฐานข้อมูลสำเร็จ!")
        return conn
    except Exception as e:
        print(f"ข้อผิดพลาดการเชื่อมต่อฐานข้อมูล: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/led', methods=['POST'])
def led():
    if arduino is None:
        return "การเชื่อมต่อ Serial ยังไม่พร้อม", 500

    status = request.form['status']
    try:
        if status == 'on':
            arduino.write(b'1')  # ส่งคำสั่งเปิด LED
        elif status == 'off':
            arduino.write(b'0')  # ส่งคำสั่งปิด LED
        
        # บันทึกสถานะของ LED ลงในฐานข้อมูล
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO led_status (status, timestamp) VALUES (%s, NOW())",
                (status,)
            )
            conn.commit()
            
            cursor.close()
            conn.close()
            print("สถานะ LED ถูกบันทึกในฐานข้อมูล")
        
        return 'OKey'
    except Exception as e:
        print(f"ข้อผิดพลาดการส่งข้อมูลไปยัง Arduino หรือฐานข้อมูล: {e}")
        return "ไม่สามารถสื่อสารกับอุปกรณ์ได้", 500

if __name__ == '__main__':  # แก้ไขพิมพ์ผิด
    app.run(host='127.0.0.1', port=5000, debug=True)

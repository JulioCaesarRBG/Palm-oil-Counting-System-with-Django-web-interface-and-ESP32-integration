from ultralytics import YOLO
import cv2
import json
import threading
from datetime import datetime
import os
from flask import Flask, jsonify
import numpy as np
import time
import requests
import serial
from config import Config

app = Flask(__name__)

class ESP32Handler:
    def __init__(self):
        self.ser = None
        self.is_connected = False
        self.last_send_time = 0
    
    def connect(self, port=None):
        """Connect to ESP32"""
        if not Config.ESP32_ENABLED:
            print("ESP32 communication disabled in config")
            return False
            
        try:
            # Use static port from config
            port = Config.ESP32_PORT
            
            print(f"Attempting to connect to ESP32 on {port}...")
            self.ser = serial.Serial(port, Config.ESP32_BAUDRATE, timeout=Config.ESP32_TIMEOUT)
            time.sleep(2)  # Give ESP32 time to initialize
            self.is_connected = True
            print(f"✅ Connected to ESP32 on {port}")
            return True
            
        except serial.SerialException as e:
            print(f"❌ Failed to connect to ESP32: {e}")
            self.is_connected = False
            return False
    
    def send_data(self, ripe_count, unripe_count, status):
        """Send data to ESP32"""
        if not self.is_connected or not self.ser or not self.ser.is_open:
            return False
            
        # Throttle sending to avoid overwhelming ESP32
        current_time = time.time()
        if current_time - self.last_send_time < Config.ESP32_SEND_INTERVAL:
            return True
            
        try:
            # Format: "RIPE:5,UNRIPE:3,STATUS:running"
            data_string = f"RIPE:{ripe_count},UNRIPE:{unripe_count},STATUS:{status}\n"
            self.ser.write(data_string.encode('utf-8'))
            self.last_send_time = current_time
            print(f"📡 Sent to ESP32: {data_string.strip()}")
            return True
            
        except serial.SerialException as e:
            print(f"❌ Error sending to ESP32: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from ESP32"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("ESP32 disconnected")
        self.is_connected = False

class DetectionState:
    def __init__(self):
        self.is_running = False
        self.is_paused = False
        self.cap = None
        self.current_frame = None
        self.suitable_count = 0
        self.unsuitable_count = 0
        self.show_debug_window = True
        self.is_initialized = False
        self.debug_window_shown = False
        # Anti-duplicate detection
        self.recently_counted_objects = {}  # {object_signature: frame_count}
        self.frame_count = 0
        # Auto-save tracking
        self.last_save_count = 0
        self.django_session_id = None
        # ESP32 integration
        self.esp32_handler = ESP32Handler()

detection_state = DetectionState()

def save_count_data(suitable_count, unsuitable_count):
    """Save count data to JSON file"""
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data = {
            "timestamp": timestamp,
            "suitable_count": suitable_count,
            "unsuitable_count": unsuitable_count,
            "total_count": suitable_count + unsuitable_count
        }
        
        # Create data directory if it doesn't exist
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Save to JSON file
        filename = f"count_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(data_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Data saved to: {filepath}")
        return filepath
    except Exception as e:
        print(f"Error saving data: {e}")
        return None

def send_data_to_django(suitable_count, unsuitable_count, frame=None):
    """Send count data to Django database via API"""
    try:
        # URL ke Django API untuk menyimpan data - menggunakan config
        django_url = f"http://{Config.DJANGO_HOST}:{Config.DJANGO_PORT}/api/save_count_data/"
        
        data = {
            "suitable_count": suitable_count,
            "unsuitable_count": unsuitable_count,
            "status": "running"
        }
        
        files = {}
        if frame is not None:
            # Simpan frame sebagai gambar
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            img_filename = f'palm_oil_{timestamp}.jpg'
            
            # Encode frame ke format JPEG
            ret, img_encoded = cv2.imencode('.jpg', frame)
            if ret:
                files['image'] = (img_filename, img_encoded.tobytes(), 'image/jpeg')
        
        if files:
            # Kirim dengan file
            response = requests.post(django_url, data=data, files=files, timeout=Config.DJANGO_TIMEOUT)
        else:
            # Kirim tanpa file
            response = requests.post(django_url, json=data, timeout=Config.DJANGO_TIMEOUT)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Data berhasil dikirim ke Django: {result}")
            return result
        else:
            print(f"Error sending to Django: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error sending data to Django: {e}")
        return None

def update_django_data(record_id, suitable_count, unsuitable_count):
    """Update existing Django record"""
    try:
        django_url = f"http://{Config.DJANGO_HOST}:{Config.DJANGO_PORT}/api/update_count_data/{record_id}/"
        
        data = {
            "suitable_count": suitable_count,
            "unsuitable_count": unsuitable_count,
            "status": "running"
        }
        
        response = requests.put(django_url, json=data, timeout=Config.DJANGO_TIMEOUT)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Data berhasil diupdate di Django: {result}")
            return result
        else:
            print(f"Error updating Django: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error updating data in Django: {e}")
        return None

def detect_objects_thread(model_path):
    try:
        print("Loading model and initializing camera...")
        model = YOLO(model_path)
        
        # Langsung buka webcam dengan index dari config
        cap = cv2.VideoCapture(Config.CAMERA_SOURCE)
        if not cap.isOpened():
            print(f"Error: Tidak dapat membuka kamera dengan index {Config.CAMERA_SOURCE}")
            detection_state.is_running = False
            return
            
        detection_state.cap = cap
        
        # Tunggu sebentar agar kamera siap
        time.sleep(3)
        
        # Set properti kamera
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, Config.CAMERA_FPS)
        
        # Verifikasi properti kamera
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        line_y = int(h * Config.LINE_POSITION)  # Gunakan posisi dari config

        previous_objects = set()
        
        # Buat window untuk debugging
        if detection_state.show_debug_window:
            cv2.namedWindow('Detection Debug', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('Detection Debug', 800, 600)
            detection_state.debug_window_shown = True
            detection_state.is_initialized = True
            print("Debug window created and system initialized")
        
        # Set flag bahwa sistem sudah berjalan
        detection_state.is_running = True
        detection_state.is_initialized = True
        
        # Send initial status to ESP32 (connection should already exist from startup)
        if Config.ESP32_ENABLED and detection_state.esp32_handler.is_connected:
            detection_state.esp32_handler.send_data(0, 0, "running")
            print("📤 Sent initial running status to ESP32")
        elif Config.ESP32_ENABLED:
            print("⚠️ Warning: ESP32 not connected, trying to reconnect...")
            if detection_state.esp32_handler.connect():
                detection_state.esp32_handler.send_data(0, 0, "running")
        
        while detection_state.is_running:
            detection_state.frame_count += 1
            
            # Clean up old counted objects every 100 frames
            if detection_state.frame_count % 100 == 0:
                old_objects = []
                for obj_id, frame_counted in detection_state.recently_counted_objects.items():
                    if detection_state.frame_count - frame_counted > Config.COOLDOWN_FRAMES:
                        old_objects.append(obj_id)
                for obj_id in old_objects:
                    del detection_state.recently_counted_objects[obj_id]
            
            if detection_state.is_paused:
                if detection_state.show_debug_window and detection_state.current_frame is not None:
                    cv2.imshow('Detection Debug', detection_state.current_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                time.sleep(0.1)  # Prevent high CPU usage during pause
                continue
            
            ret, frame = cap.read()
            if not ret:
                print("Error: Tidak dapat membaca frame")
                time.sleep(0.1)  # Tunggu sebentar sebelum mencoba lagi
                continue

            # Flip frame horizontal (opsional, jika gambar terbalik)
            frame = cv2.flip(frame, 1)

            # Proses deteksi
            results = model(frame, verbose=False)
            
            # Gambar garis horizontal
            cv2.line(frame, (0, line_y), (w, line_y), (0, 255, 0), 2)
            
            current_objects = set()
            
            if len(results) > 0:
                boxes = results[0].boxes
                
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    cls = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    
                    # Process detections with confidence above threshold from config
                    if conf < Config.CONFIDENCE_THRESHOLD:
                        continue
                        
                    center_x = (x1 + x2) / 2
                    center_y = (y1 + y2) / 2
                    
                    # Create object ID with region-based grouping to prevent duplicates
                    region_x = int(center_x // Config.TRACKING_DISTANCE_THRESHOLD) * Config.TRACKING_DISTANCE_THRESHOLD
                    obj_id = f"{cls}_{region_x}_{int(center_y)}"
                    current_objects.add(obj_id)
                    
                    # Check if object is crossing the line and hasn't been counted recently
                    if obj_id not in previous_objects:
                        crossing_tolerance = Config.MINIMUM_CROSSING_FRAMES
                        if center_y > line_y - crossing_tolerance and center_y < line_y + crossing_tolerance:
                            # Create signature to check recent counting
                            signature = f"{cls}_{region_x}_{line_y}"
                            
                            # Only count if this signature hasn't been counted recently
                            if signature not in detection_state.recently_counted_objects:
                                if cls == 0:
                                    detection_state.suitable_count += 1
                                    print(f"COUNTED: Ripe - Total: {detection_state.suitable_count}")
                                elif cls == 1:
                                    detection_state.unsuitable_count += 1
                                    print(f"COUNTED: Unripe - Total: {detection_state.unsuitable_count}")
                                
                                # Mark this signature as recently counted
                                detection_state.recently_counted_objects[signature] = detection_state.frame_count
                                
                                # Send to ESP32 display immediately when count changes
                                detection_state.esp32_handler.send_data(
                                    detection_state.suitable_count,  # ripe_count
                                    detection_state.unsuitable_count,  # unripe_count
                                    "running"
                                )
                                
                                # Auto-save ke Django setiap ada perubahan count
                                total_count = detection_state.suitable_count + detection_state.unsuitable_count
                                if total_count != detection_state.last_save_count:
                                    if detection_state.django_session_id:
                                        # Update record yang sudah ada
                                        django_result = update_django_data(
                                            detection_state.django_session_id,
                                            detection_state.suitable_count, 
                                            detection_state.unsuitable_count
                                        )
                                    else:
                                        # Buat record baru untuk session pertama kali dengan gambar
                                        django_result = send_data_to_django(
                                            detection_state.suitable_count, 
                                            detection_state.unsuitable_count,
                                            frame  # Kirim frame untuk gambar pertama
                                        )
                                        if django_result and "id" in django_result:
                                            detection_state.django_session_id = django_result["id"]
                                    
                                    detection_state.last_save_count = total_count
                    
                    color = (0, 255, 0) if cls == 0 else (0, 0, 255)
                    class_name = "Ripe" if cls == 0 else "Unripe"
                    label = f"{class_name} {conf:.2f}"
                    
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                    cv2.putText(frame, label, (int(x1), int(y1) - 20), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            previous_objects = current_objects

            # Tampilkan informasi
            cv2.putText(frame, f"Ripe: {detection_state.suitable_count} Unripe: {detection_state.unsuitable_count}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            # cv2.putText(frame, f"Line Y: {line_y}", (10, 60),
            #            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            detection_state.current_frame = frame.copy()

            # Tampilkan frame untuk debugging
            if detection_state.show_debug_window:
                cv2.imshow('Detection Debug', frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break

            # Tambahkan delay kecil untuk mengurangi penggunaan CPU
            time.sleep(0.01)

    except Exception as e:
        print(f"Error dalam thread deteksi: {e}")
        detection_state.is_running = False
        detection_state.is_initialized = False
        detection_state.debug_window_shown = False
    finally:
        if detection_state.cap:
            detection_state.cap.release()
            detection_state.cap = None
        if detection_state.show_debug_window:
            cv2.destroyAllWindows()
        # Don't disconnect ESP32 here - let it be handled by stop/start functions
        # detection_state.esp32_handler.disconnect()
        print("🔄 Detection thread cleanup completed (ESP32 connection preserved)")

@app.route('/start', methods=['POST'])
def start_detection():
    if detection_state.cap is not None:
        detection_state.cap.release()
        detection_state.cap = None
        
    if not detection_state.is_running:
        # Reset states
        detection_state.suitable_count = 0
        detection_state.unsuitable_count = 0
        detection_state.is_initialized = False
        # Reset anti-duplicate detection
        detection_state.recently_counted_objects = {}
        detection_state.frame_count = 0
        # Reset Django tracking
        detection_state.last_save_count = 0
        detection_state.django_session_id = None
        
        detection_state.is_running = True
        detection_state.is_paused = False
        model_path = "model.pt"
        thread = threading.Thread(target=detect_objects_thread, args=(model_path,))
        thread.daemon = True
        thread.start()
    return jsonify({"status": "started"})

@app.route('/pause', methods=['POST'])
def pause_detection():
    detection_state.is_paused = True
    # Send pause status to ESP32
    detection_state.esp32_handler.send_data(
        detection_state.suitable_count,
        detection_state.unsuitable_count,
        "paused"
    )
    return jsonify({"status": "paused"})

@app.route('/resume', methods=['POST'])
def resume_detection():
    detection_state.is_paused = False
    # Send resume status to ESP32
    detection_state.esp32_handler.send_data(
        detection_state.suitable_count,
        detection_state.unsuitable_count,
        "running"
    )
    return jsonify({"status": "resumed"})

@app.route('/stop', methods=['POST'])
def stop_detection():
    detection_state.is_running = False
    detection_state.is_initialized = False
    detection_state.debug_window_shown = False
    if detection_state.cap:
        detection_state.cap.release()
        detection_state.cap = None
    detection_state.current_frame = None
    
    # Reset counters FIRST
    detection_state.suitable_count = 0
    detection_state.unsuitable_count = 0
    
    # Check ESP32 connection and reconnect if needed
    if not detection_state.esp32_handler.is_connected and Config.ESP32_ENABLED:
        print("🔌 ESP32 not connected, attempting to reconnect...")
        detection_state.esp32_handler.connect()
    
    # THEN send stop status to ESP32 with reset counts (0,0)
    print("📤 Sending stop signal to ESP32...")
    success = detection_state.esp32_handler.send_data(0, 0, "stopped")
    
    if success:
        print("✅ Stop signal sent successfully")
        # Longer delay to ensure ESP32 processes the data
        time.sleep(1.0)  # Increased to 1 second
    else:
        print("❌ Failed to send stop signal")
    
    # Don't disconnect ESP32 immediately - keep connection for next session
    # detection_state.esp32_handler.disconnect()
    print("🔌 ESP32 connection maintained for next session")
    
    return jsonify({"status": "stopped"})

@app.route('/get_counts')
def get_counts():
    # Tentukan status berdasarkan state yang ada
    if detection_state.is_paused:
        status = "paused"
    elif detection_state.is_running and detection_state.is_initialized:
        status = "running"
    elif detection_state.is_running and not detection_state.is_initialized:
        status = "loading"
    else:
        status = "stopped"
    
    return jsonify({
        "suitable_count": detection_state.suitable_count,
        "unsuitable_count": detection_state.unsuitable_count,
        "is_initialized": detection_state.is_initialized,
        "debug_window_shown": detection_state.debug_window_shown,
        "is_paused": detection_state.is_paused,
        "is_running": detection_state.is_running,
        "status": status
    })

@app.route('/save_data', methods=['POST'])
def save_data():
    """Save current count data to file and send to Django"""
    try:
        # Simpan ke file JSON lokal
        filepath = save_count_data(detection_state.suitable_count, detection_state.unsuitable_count)
        
        # Kirim ke Django database
        django_result = send_data_to_django(
            detection_state.suitable_count, 
            detection_state.unsuitable_count,
            detection_state.current_frame  # Kirim frame saat ini
        )
        
        if filepath:
            response_data = {
                "status": "success", 
                "message": "Data saved successfully",
                "filepath": filepath,
                "data": {
                    "suitable_count": detection_state.suitable_count,
                    "unsuitable_count": detection_state.unsuitable_count,
                    "total_count": detection_state.suitable_count + detection_state.unsuitable_count
                }
            }
            
            # Tambahkan info Django jika berhasil
            if django_result:
                response_data["django_saved"] = True
                response_data["django_id"] = django_result.get("id")
            else:
                response_data["django_saved"] = False
                
            return jsonify(response_data)
        else:
            return jsonify({"status": "error", "message": "Failed to save data"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/get_all_data')
def get_all_data():
    """Get all saved data files"""
    try:
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        if not os.path.exists(data_dir):
            return jsonify({"status": "success", "data": []})
        
        all_data = []
        for filename in sorted(os.listdir(data_dir)):
            if filename.endswith('.json'):
                filepath = os.path.join(data_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        data['filename'] = filename
                        all_data.append(data)
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
        
        return jsonify({"status": "success", "data": all_data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/esp32/status')
def esp32_status():
    """Get ESP32 connection status"""
    return jsonify({
        "esp32_enabled": Config.ESP32_ENABLED,
        "esp32_connected": detection_state.esp32_handler.is_connected,
        "esp32_port": Config.ESP32_PORT
    })

@app.route('/esp32/connect', methods=['POST'])
def esp32_connect():
    """Manually connect to ESP32"""
    try:
        success = detection_state.esp32_handler.connect()
        if success:
            return jsonify({"status": "success", "message": "ESP32 connected"})
        else:
            return jsonify({"status": "error", "message": "Failed to connect to ESP32"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/esp32/disconnect', methods=['POST'])
def esp32_disconnect():
    """Manually disconnect from ESP32"""
    try:
        detection_state.esp32_handler.disconnect()
        return jsonify({"status": "success", "message": "ESP32 disconnected"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/esp32/send_test', methods=['POST'])
def esp32_send_test():
    """Send test data to ESP32"""
    try:
        success = detection_state.esp32_handler.send_data(99, 88, "test")
        if success:
            return jsonify({"status": "success", "message": "Test data sent to ESP32"})
        else:
            return jsonify({"status": "error", "message": "Failed to send test data"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/esp32/reset_display', methods=['POST'])
def esp32_reset_display():
    """Reset ESP32 display to show 0 counts"""
    try:
        # Check ESP32 connection and reconnect if needed
        if not detection_state.esp32_handler.is_connected and Config.ESP32_ENABLED:
            print("🔌 ESP32 not connected, attempting to reconnect...")
            detection_state.esp32_handler.connect()
        
        success = detection_state.esp32_handler.send_data(0, 0, "stopped")
        if success:
            return jsonify({"status": "success", "message": "ESP32 display reset to 0"})
        else:
            return jsonify({"status": "error", "message": "Failed to reset ESP32 display"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# Initialize ESP32 connection when server starts
def initialize_esp32():
    """Initialize ESP32 connection on server startup"""
    if Config.ESP32_ENABLED:
        print("🚀 Initializing ESP32 connection on startup...")
        success = detection_state.esp32_handler.connect()
        if success:
            # Send initial stopped status
            detection_state.esp32_handler.send_data(0, 0, "stopped")
            print("✅ ESP32 initialized successfully")
        else:
            print("⚠️ ESP32 initialization failed, will retry later")

# Initialize ESP32 when the module is loaded
initialize_esp32()

if __name__ == '__main__':
    app.run(host=Config.HOST, port=Config.PORT, threaded=True) 
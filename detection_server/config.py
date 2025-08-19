import os
import cv2

class Config:
    # Server settings - Use 0.0.0.0 to allow access from any IP
    HOST = '0.0.0.0'  # Changed from specific IP to allow external access
    PORT = 5000
    DEBUG = False

    # Django integration settings
    DJANGO_HOST = '127.0.0.1'  # IP where Django is running
    DJANGO_PORT = 8000
    DJANGO_TIMEOUT = 10

    # ESP32 integration settings
    ESP32_ENABLED = True  # Set to False to disable ESP32 communication
    ESP32_PORT = 'COM4'  # Static port for Raspberry Pi ESP32 connection /dev/ttyUSB0
    ESP32_BAUDRATE = 115200
    ESP32_TIMEOUT = 1
    ESP32_SEND_INTERVAL = 1  # Send data every second

    # Model settings
    MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model.pt')
    
    # Camera settings
    CAMERA_SOURCE = 0 # 0 untuk webcam lokal
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    CAMERA_FPS = 30
    
    # Retry settings
    CAMERA_MAX_ATTEMPTS = 3
    CAMERA_RETRY_DELAY = 1  # seconds
    
    # Detection settings
    CONFIDENCE_THRESHOLD = 0.5  # Increased for better accuracy
    LINE_POSITION = 0.5  # Posisi garis sebagai rasio dari tinggi frame (0.5 = tengah)

    # Line crossing detection settings
    TRACKING_DISTANCE_THRESHOLD = 80  # Increased distance to better track same object
    MINIMUM_CROSSING_FRAMES = 5       # Increased frames to confirm crossing and prevent false positives
    COOLDOWN_FRAMES = 30              # Frames to wait before allowing same object to be counted again

    # Storage settings
    SAVE_IMAGES = True
    IMAGE_SAVE_PATH = 'detected_images'

    @staticmethod
    def list_cameras():
        """List all available cameras"""
        cameras = []
        for i in range(10):  # Check first 10 indexes
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cameras.append(i)
                cap.release()
        return cameras
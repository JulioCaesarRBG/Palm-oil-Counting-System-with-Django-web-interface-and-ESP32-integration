# 🌴 Palm Oil Counting System

A comprehensive palm oil detection and counting system using AI-powered computer vision, Django web interface, and ESP32 integration for real-time display.

## 🚀 Features

- **Real-time Object Detection**: YOLO-based detection for ripe and unripe palm oil
- **Web Interface**: Django-powered dashboard for monitoring and control
- **ESP32 Integration**: Real-time data display on P10 LED matrix
- **Data Management**: Automatic data saving and database integration
- **Raspberry Pi Compatible**: Optimized for headless Raspberry Pi operation

## 🛠️ Tech Stack

- **Backend**: Python, Django, Flask
- **AI/ML**: YOLOv8, OpenCV, Ultralytics
- **Hardware**: ESP32, P10 LED Display, Camera
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript

## 📋 Requirements

```bash
# Python packages
ultralytics
opencv-python
django
flask
pyserial
requests
numpy
```

## 🔧 Installation

1. Clone repository:
```bash
git clone https://github.com/JulioCaesarRBG/Palm-oil-Counting-System-with-Django-web-interface-and-ESP32-integration.git
cd Palm-oil-Counting-System-with-Django-web-interface-and-ESP32-integration
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure settings in `detection_server/config.py`

4. Run Django server:
```bash
python manage.py runserver
```

5. Run detection server:
```bash
cd detection_server
python object_detection.py
```

## ⚙️ Configuration

Edit `detection_server/config.py` for:
- Camera settings
- ESP32 connection
- Detection parameters
- Debug options

## 🎯 Usage

1. Access web interface at `http://localhost:8000`
2. Start detection from control panel
3. Monitor real-time counts and status
4. View data in tables and dashboard

## 📊 Project Structure

```
myproject/
├── detection_server/     # AI detection engine
├── myapp/               # Django web application
├── media/               # Uploaded images
├── ESP32_P10_*.ino     # ESP32 Arduino code
└── manage.py           # Django management
```

## 🔗 ESP32 Integration

Upload `ESP32_P10_PalmOil_Display.ino` to ESP32 for LED display functionality.

## 📝 License

This project is part of a thesis research on AI-powered agriculture monitoring systems.

## 👨‍💻 Author

**Julio Caesar**
- GitHub: [@JulioCaesarRBG](https://github.com/JulioCaesarRBG)
- Email: julioray171@gmail.com
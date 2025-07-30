from ultralytics import YOLO
model = YOLO('yolov8n.pt')  # atau model custom Anda

# Ekspor model ke ONNX
model.export(format='onnx', opset=12, simplify=True)

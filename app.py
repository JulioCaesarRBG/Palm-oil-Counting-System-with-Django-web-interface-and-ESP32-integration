from ultralytics import YOLO
import cv2
from datetime import datetime
import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

# Import Django models after setup
from myapp.models import PalmOilCount

def save_initial_data(suitable_count, unsuitable_count, frame):
    try:
        # Buat nama file dengan format: YYYYMMDD_HHMMSS.jpg
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        img_filename = f'palm_oil_{timestamp}.jpg'
        
        # Buat direktori media jika belum ada
        media_path = 'media/palm_oil_images'
        os.makedirs(media_path, exist_ok=True)
        
        # Simpan gambar
        img_path = os.path.join(media_path, img_filename)
        cv2.imwrite(img_path, frame)
        
        # Simpan data ke database
        relative_path = f'palm_oil_images/{img_filename}'
        count = PalmOilCount.objects.create(
            suitable_count=suitable_count,
            unsuitable_count=unsuitable_count,
            status="running",
            image=relative_path
        )
        
        print(f"Data berhasil disimpan dengan ID: {count.id}")
        return count.id
            
    except Exception as e:
        print("Terjadi kesalahan saat menyimpan data:", e)
        return None

def update_count_data(count_id, suitable_count, unsuitable_count):
    try:
        count = PalmOilCount.objects.get(id=count_id)
        count.suitable_count = suitable_count
        count.unsuitable_count = unsuitable_count
        count.save()
        print(f"Data ID {count_id} berhasil diupdate")
    except Exception as e:
        print("Terjadi kesalahan saat update data:", e)

def detect_objects(model_path):
    # Inisialisasi YOLO model
    model = YOLO(model_path)
    
    # Inisialisasi webcam
    cap = cv2.VideoCapture(0)
    assert cap.isOpened(), "Error opening webcam"

    # Properti frame
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    line_y = h // 2  # Posisi garis horizontal
    # confidence_threshold = 0.7  # Komen threshold confidence

    image_sent = False
    suitable_count, unsuitable_count = 0, 0
    previous_objects = set()
    last_counts = {'suitable': 0, 'unsuitable': 0}
    count_id = None

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            results = model(frame, verbose=False)
            
            cv2.line(frame, (0, line_y), (w, line_y), (0, 255, 0), 2)
            
            current_objects = set()
            counts_changed = False
            
            if len(results) > 0:
                boxes = results[0].boxes
                
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    cls = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    
                    center_y = (y1 + y2) / 2
                    
                    obj_id = f"{cls}_{int(x1)}_{int(y1)}"
                    current_objects.add(obj_id)
                    
                    if obj_id not in previous_objects:
                        if center_y > line_y - 5 and center_y < line_y + 5:
                            if cls == 0:  # class 0 = suitable
                                suitable_count += 1
                                counts_changed = True
                            elif cls == 1:  # class 1 = unsuitable
                                unsuitable_count += 1
                                counts_changed = True
                    
                    # Beri warna berbeda untuk setiap kelas
                    color = (0, 255, 0) if cls == 0 else (0, 0, 255)  # Hijau untuk suitable, Merah untuk unsuitable
                    
                    # Perbaiki label sesuai kelas
                    class_name = "Suitable" if cls == 0 else "Unsuitable"
                    label = f"{class_name} {conf:.2f}"
                    cv2.putText(frame, label, (int(x1), int(y1) - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)

            previous_objects = current_objects

            # Tampilkan counts saja (tanpa threshold)
            cv2.putText(frame, f"Suitable: {suitable_count} Unsuitable: {unsuitable_count}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            # Komen tampilan threshold
            # cv2.putText(frame, f"Threshold: {confidence_threshold}", (10, 60),
            #            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Ganti pengiriman API dengan penyimpanan lokal
            if not image_sent and (suitable_count > 0 or unsuitable_count > 0):
                try:
                    count_id = save_initial_data(suitable_count, unsuitable_count, frame)
                    if count_id:
                        image_sent = True
                        last_counts['suitable'] = suitable_count
                        last_counts['unsuitable'] = unsuitable_count
                except Exception as e:
                    print(f"Error saat menyimpan data awal: {e}")

            # Update data ketika count berubah
            elif image_sent and counts_changed and count_id:
                if (last_counts['suitable'] != suitable_count or 
                    last_counts['unsuitable'] != unsuitable_count):
                    update_count_data(count_id, suitable_count, unsuitable_count)
                    last_counts['suitable'] = suitable_count
                    last_counts['unsuitable'] = unsuitable_count

            cv2.imshow("YOLO Detection", frame)

            # Komen kontrol threshold
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            # elif key == ord('+') and confidence_threshold < 0.95:
            #     confidence_threshold += 0.05
            # elif key == ord('-') and confidence_threshold > 0.25:
            #     confidence_threshold -= 0.05

    except Exception as e:
        print("Terjadi kesalahan saat deteksi:", e)

    finally:
        cap.release()
        cv2.destroyAllWindows()

# Jalankan YOLO
if __name__ == "__main__":
    model_path = "model.pt"  # Sesuaikan dengan path model Anda
    detect_objects(model_path) 
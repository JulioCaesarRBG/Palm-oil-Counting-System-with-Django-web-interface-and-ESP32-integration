import firebase_admin
from firebase_admin import credentials, db
from django.conf import settings
import base64
import cv2
import numpy as np

# Initialize Firebase
cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://palm-oil-count-default-rtdb.asia-southeast1.firebasedatabase.app/'
})

def decode_image(base64_string):
    """Decode base64 image to OpenCV format"""
    try:
        img_data = base64.b64decode(base64_string)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except:
        return None

def get_firebase_data():
    """Get data from Firebase Realtime Database"""
    ref = db.reference('/kelapa_sawit')
    data = ref.get()
    if data:
        processed_data = {}
        for key, value in data.items():
            if 'Image' in value and value['Image']:
                try:
                    # Decode base64 image
                    img = decode_image(value['Image'])
                    if img is not None:
                        # Convert back to base64 for display
                        _, buffer = cv2.imencode('.jpg', img)
                        value['Image'] = base64.b64encode(buffer).decode('utf-8')
                except:
                    value['Image'] = ''
            processed_data[key] = value
        return processed_data
    return None

def get_latest_count():
    """Get latest counting data"""
    ref = db.reference('/kelapa_sawit')
    data = ref.order_by_key().limit_to_last(1).get()
    if data:
        item = list(data.values())[0]
        if 'Image' in item and item['Image']:
            try:
                # Decode base64 image
                img = decode_image(item['Image'])
                if img is not None:
                    # Convert back to base64 for display
                    _, buffer = cv2.imencode('.jpg', img)
                    item['Image'] = base64.b64encode(buffer).decode('utf-8')
            except:
                item['Image'] = ''
        return item
    return None 
from flask import request, jsonify, Blueprint
from ultralytics import YOLO
import os
import cv2
import base64
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
from flasgger import swag_from
from flask_jwt_extended import jwt_required

fish_detection_bp = Blueprint('fish_detection', __name__)

# Load model YOLOv8
MODEL_PATH = 'routes/yolo_model/best.pt'  # Ganti path sesuai model kamu
model = YOLO(MODEL_PATH)

# Label Bahasa Indonesia
label_translation = {
    'karas': 'Ikan Mas Kecil',
    'karp': 'Ikan Mas Besar',
    'leszcz': 'Ikan Bream',
    'lin': 'Ikan Lin',
    'okon': 'Ikan Bass',
    'ploc': 'Ikan Roach',
    'szczupak': 'Ikan Pike',
    'ukleja': 'Ikan Bleak'
}

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def encode_image_to_base64(image):
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8')

@fish_detection_bp.route('/api/detect', methods=['POST'])
@jwt_required()
@swag_from('docs/fish/fish.yml')
def detect_fish_disease():
    if 'image' not in request.files:
        return jsonify({'error': 'Tidak ada file gambar yang dikirim'}), 400

    file = request.files['image']

    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'File tidak valid'}), 400

    filename = secure_filename(file.filename)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    filepath = os.path.join('uploads', f"{timestamp}_{filename}")
    os.makedirs('uploads', exist_ok=True)
    file.save(filepath)

    try:
        # Proses deteksi
        results = model.predict(source=filepath, save=False, conf=0.5, iou=0.45, stream=False)
        result = results[0]

        detections = []

        if result.boxes is not None:
            for box in result.boxes:
                b = box.xyxy[0].cpu().numpy().astype(int)
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                class_name = model.names[cls]
                translated_name = label_translation.get(class_name, class_name)

                detections.append({
                    'class': translated_name,
                    'confidence': round(conf, 3),
                    'bbox': {
                        'x1': int(b[0]),
                        'y1': int(b[1]),
                        'x2': int(b[2]),
                        'y2': int(b[3])
                    }
                })

        # Gambar hasil deteksi
        annotated_image = result.plot()
        encoded_image = encode_image_to_base64(annotated_image)

        return jsonify({
            'detections': detections,
            'total_detections': len(detections),
            'annotated_image_base64': encoded_image
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

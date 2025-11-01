"""
Forge Face Detection Microservice
Python Flask API for facial recognition using dlib
"""
import os
import logging
from flask import Flask, request, jsonify
import face_recognition
from PIL import Image
import numpy as np
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration from environment variables
MODEL_TYPE = os.getenv('FACE_DETECTION_MODEL', 'hog').lower()  # 'hog' or 'cnn'
MAX_IMAGE_SIZE = int(os.getenv('MAX_IMAGE_SIZE', '2000'))  # Max dimension for processing
FACE_DETECTION_TOLERANCE = float(os.getenv('FACE_TOLERANCE', '0.6'))  # Lower = more strict

logger.info(f"Face Detection Service Starting...")
logger.info(f"Model Type: {MODEL_TYPE}")
logger.info(f"Max Image Size: {MAX_IMAGE_SIZE}px")
logger.info(f"Face Tolerance: {FACE_DETECTION_TOLERANCE}")


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for Docker and monitoring
    Returns service status and configuration
    """
    return jsonify({
        'status': 'ready',
        'service': 'forge-face-detection',
        'model': MODEL_TYPE,
        'version': '1.0.0'
    }), 200


@app.route('/detect', methods=['POST'])
def detect_faces():
    """
    Detect faces in a photo and return face descriptors
    
    Request Body (JSON):
    {
        "fileId": "uuid-of-file",
        "filePath": "/app/private/user-id/photo.jpg"
    }
    
    Response:
    {
        "fileId": "uuid-of-file",
        "faces": [
            {
                "id": "face-uuid",
                "box": {"top": 100, "right": 300, "bottom": 250, "left": 150},
                "descriptor": [0.123, -0.456, ...],  # 128-dimensional vector
                "landmarks": {...},  # 68 facial landmark points
                "confidence": 0.95
            }
        ],
        "faceCount": 2,
        "processingTimeMs": 1523
    }
    """
    start_time = time.time()
    
    try:
        # Parse request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        file_id = data.get('fileId')
        file_path = data.get('filePath')
        
        if not file_id or not file_path:
            return jsonify({'error': 'Missing required fields: fileId, filePath'}), 400
        
        # Verify file exists
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return jsonify({'error': f'File not found: {file_path}'}), 404
        
        logger.info(f"Processing {file_id}: {Path(file_path).name}")
        
        # Load and resize image if needed
        try:
            image = face_recognition.load_image_file(file_path)
            
            # Resize if image is too large (improves speed)
            height, width = image.shape[:2]
            if max(height, width) > MAX_IMAGE_SIZE:
                scale = MAX_IMAGE_SIZE / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                
                pil_image = Image.fromarray(image)
                pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                image = np.array(pil_image)
                
                logger.info(f"Resized image: {width}x{height} → {new_width}x{new_height}")
        except Exception as e:
            logger.error(f"Failed to load image {file_path}: {str(e)}")
            return jsonify({'error': f'Failed to load image: {str(e)}'}), 400
        
        # Detect face locations
        face_locations = face_recognition.face_locations(image, model=MODEL_TYPE)
        
        if not face_locations:
            logger.info(f"No faces detected in {file_id}")
            processing_time = int((time.time() - start_time) * 1000)
            return jsonify({
                'fileId': file_id,
                'faces': [],
                'faceCount': 0,
                'processingTimeMs': processing_time
            }), 200
        
        # Get face encodings (128-dimensional descriptors)
        face_encodings = face_recognition.face_encodings(image, face_locations)
        
        # Get facial landmarks (68-point model)
        face_landmarks_list = face_recognition.face_landmarks(image, face_locations)
        
        # Build response
        faces = []
        for i, (location, encoding, landmarks) in enumerate(zip(face_locations, face_encodings, face_landmarks_list)):
            top, right, bottom, left = location
            
            face_data = {
                'id': f"{file_id}-face-{i}",
                'box': {
                    'top': int(top),
                    'right': int(right),
                    'bottom': int(bottom),
                    'left': int(left),
                    'width': int(right - left),
                    'height': int(bottom - top)
                },
                'descriptor': encoding.tolist(),  # Convert numpy array to list
                'landmarks': {
                    key: [(int(x), int(y)) for x, y in points]
                    for key, points in landmarks.items()
                },
                'confidence': 1.0  # dlib doesn't provide confidence scores
            }
            faces.append(face_data)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        logger.info(f"✓ Detected {len(faces)} face(s) in {file_id} ({processing_time}ms)")
        
        return jsonify({
            'fileId': file_id,
            'faces': faces,
            'faceCount': len(faces),
            'processingTimeMs': processing_time
        }), 200
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"Face detection error: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Face detection failed',
            'message': str(e),
            'processingTimeMs': processing_time
        }), 500


@app.route('/batch-detect', methods=['POST'])
def batch_detect_faces():
    """
    Detect faces in multiple photos (batch processing)
    
    Request Body (JSON):
    {
        "photos": [
            {"fileId": "uuid-1", "filePath": "/app/private/user/photo1.jpg"},
            {"fileId": "uuid-2", "filePath": "/app/private/user/photo2.jpg"}
        ]
    }
    
    Response:
    {
        "results": [
            {"fileId": "uuid-1", "faces": [...], "faceCount": 2},
            {"fileId": "uuid-2", "faces": [...], "faceCount": 1}
        ],
        "totalPhotos": 2,
        "totalFaces": 3,
        "processingTimeMs": 3500
    }
    """
    start_time = time.time()
    
    try:
        data = request.get_json()
        photos = data.get('photos', [])
        
        if not photos:
            return jsonify({'error': 'No photos provided'}), 400
        
        results = []
        total_faces = 0
        
        for photo in photos:
            file_id = photo.get('fileId')
            file_path = photo.get('filePath')
            
            if not file_id or not file_path:
                results.append({
                    'fileId': file_id or 'unknown',
                    'error': 'Missing fileId or filePath',
                    'faces': [],
                    'faceCount': 0
                })
                continue
            
            # Process each photo (reuse single photo logic)
            try:
                if not os.path.exists(file_path):
                    results.append({
                        'fileId': file_id,
                        'error': 'File not found',
                        'faces': [],
                        'faceCount': 0
                    })
                    continue
                
                image = face_recognition.load_image_file(file_path)
                
                # Resize if needed
                height, width = image.shape[:2]
                if max(height, width) > MAX_IMAGE_SIZE:
                    scale = MAX_IMAGE_SIZE / max(height, width)
                    pil_image = Image.fromarray(image)
                    pil_image = pil_image.resize(
                        (int(width * scale), int(height * scale)),
                        Image.Resampling.LANCZOS
                    )
                    image = np.array(pil_image)
                
                face_locations = face_recognition.face_locations(image, model=MODEL_TYPE)
                face_encodings = face_recognition.face_encodings(image, face_locations)
                face_landmarks_list = face_recognition.face_landmarks(image, face_locations)
                
                faces = []
                for i, (location, encoding, landmarks) in enumerate(zip(face_locations, face_encodings, face_landmarks_list)):
                    top, right, bottom, left = location
                    faces.append({
                        'id': f"{file_id}-face-{i}",
                        'box': {
                            'top': int(top),
                            'right': int(right),
                            'bottom': int(bottom),
                            'left': int(left),
                            'width': int(right - left),
                            'height': int(bottom - top)
                        },
                        'descriptor': encoding.tolist(),
                        'landmarks': {
                            key: [(int(x), int(y)) for x, y in points]
                            for key, points in landmarks.items()
                        },
                        'confidence': 1.0
                    })
                
                results.append({
                    'fileId': file_id,
                    'faces': faces,
                    'faceCount': len(faces)
                })
                
                total_faces += len(faces)
                
            except Exception as e:
                logger.error(f"Error processing {file_id}: {str(e)}")
                results.append({
                    'fileId': file_id,
                    'error': str(e),
                    'faces': [],
                    'faceCount': 0
                })
        
        processing_time = int((time.time() - start_time) * 1000)
        
        logger.info(f"✓ Batch processed {len(photos)} photos, found {total_faces} faces ({processing_time}ms)")
        
        return jsonify({
            'results': results,
            'totalPhotos': len(photos),
            'totalFaces': total_faces,
            'processingTimeMs': processing_time
        }), 200
        
    except Exception as e:
        logger.error(f"Batch detection error: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Batch detection failed',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    # Development server (use gunicorn in production)
    app.run(host='0.0.0.0', port=5000, debug=False)

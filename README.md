# Forge Face Detection Microservice

Python-based facial recognition microservice for the Forge photo backup system.

## Features

- **Fast Face Detection** using dlib's HOG model (~1-2 sec/photo)
- **Facial Descriptors** 128-dimensional vectors for face recognition
- **Batch Processing** support for multiple photos
- **Configurable Models** HOG (fast) or CNN (accurate)
- **Health Monitoring** Docker health checks
- **Production Ready** Gunicorn WSGI server

## API Endpoints

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "ready",
  "service": "forge-face-detection",
  "model": "hog",
  "version": "1.0.0"
}
```

### `POST /detect`
Detect faces in a single photo.

**Request:**
```json
{
  "fileId": "photo-uuid",
  "filePath": "/app/private/user-id/photo.jpg"
}
```

**Response:**
```json
{
  "fileId": "photo-uuid",
  "faces": [
    {
      "id": "photo-uuid-face-0",
      "box": {
        "top": 100,
        "right": 300,
        "bottom": 250,
        "left": 150,
        "width": 150,
        "height": 150
      },
      "descriptor": [0.123, -0.456, ...],
      "landmarks": {
        "chin": [[x, y], ...],
        "left_eyebrow": [[x, y], ...],
        ...
      },
      "confidence": 1.0
    }
  ],
  "faceCount": 1,
  "processingTimeMs": 1523
}
```

### `POST /batch-detect`
Process multiple photos in one request.

**Request:**
```json
{
  "photos": [
    {"fileId": "uuid-1", "filePath": "/app/private/user/photo1.jpg"},
    {"fileId": "uuid-2", "filePath": "/app/private/user/photo2.jpg"}
  ]
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FACE_DETECTION_MODEL` | `hog` | Model type: `hog` (fast) or `cnn` (accurate) |
| `MAX_IMAGE_SIZE` | `2000` | Max dimension for image resizing (px) |
| `FACE_TOLERANCE` | `0.6` | Face matching tolerance (0.0-1.0, lower = stricter) |

## Docker Usage

### Build Image
```bash
docker build -t ghcr.io/brwalknels/forge-face-detection:latest .
```

### Run Container
```bash
docker run -d \
  --name forge-face-detection \
  -p 5000:5000 \
  -v /mnt/pool/Forge/private:/app/private:ro \
  -e FACE_DETECTION_MODEL=hog \
  ghcr.io/brwalknels/forge-face-detection:latest
```

### Docker Compose
```yaml
services:
  forge-face-detection:
    image: ghcr.io/brwalknels/forge-face-detection:latest
    container_name: forge-face-detection
    ports:
      - "5000:5000"
    volumes:
      - /mnt/pool/Forge/private:/app/private:ro
      - /mnt/pool/Forge/metadata:/app/metadata
    environment:
      - FACE_DETECTION_MODEL=hog
      - MAX_IMAGE_SIZE=2000
      - FACE_TOLERANCE=0.6
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
    restart: unless-stopped
```

## Development

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python app/main.py

# Test health check
curl http://localhost:5000/health

# Test face detection
curl -X POST http://localhost:5000/detect \
  -H "Content-Type: application/json" \
  -d '{"fileId":"test","filePath":"/path/to/photo.jpg"}'
```

## Performance

| Model | Speed | Accuracy | CPU Usage |
|-------|-------|----------|-----------|
| HOG | ~1-2 sec/photo | Good | Medium |
| CNN | ~3-5 sec/photo | Excellent | High |

**Recommendations:**
- Use **HOG** for most deployments (balanced speed/accuracy)
- Use **CNN** for high-accuracy requirements (side profiles, difficult lighting)
- Set `MAX_IMAGE_SIZE=2000` to process large images faster
- Adjust `deploy.resources.limits` based on your server capacity

## License

MIT

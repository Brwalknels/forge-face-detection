# TrueNAS SCALE Deployment Guide - Face Detection Service

**Last Updated:** November 1, 2025

This guide walks you through deploying the forge-face-detection Python microservice on TrueNAS SCALE using the GUI.

## Prerequisites

- ✅ Forge main API container already running on TrueNAS
- ✅ Docker images built and pushed to GitHub Container Registry
- ✅ TrueNAS SCALE system with Docker/Apps capability
- ✅ Existing datasets: `/mnt/pool/Forge/private`, `/mnt/pool/Forge/metadata`, `/mnt/pool/Forge/data`

## Step 1: Build and Push Docker Images

**On your local Windows machine:**

```powershell
# Build and push Forge API (if you made changes)
cd "C:\Users\brigh\Visual Studio Code\Forge"
docker build -t ghcr.io/brwalknels/forge:latest .
docker push ghcr.io/brwalknels/forge:latest

# Build and push Face Detection service
cd "C:\Users\brigh\Visual Studio Code\forge-face-detection"
docker build -t ghcr.io/brwalknels/forge-face-detection:latest .
docker push ghcr.io/brwalknels/forge-face-detection:latest
```

**Or use the quick scripts:**
```powershell
cd forge-face-detection
.\push.ps1
```

Wait for both pushes to complete successfully.

---

## Step 2: Access TrueNAS Web GUI

1. Open browser: `http://10.0.0.120` (or your TrueNAS IP)
2. Login with admin credentials
3. Navigate to **Apps** in the left sidebar

---

## Step 3: Launch Custom App for Face Detection

1. Click **Discover Apps** (top right)
2. Click **Custom App** button
3. Fill in the Application Configuration:

### Application Name
```
forge-face-detection
```

### Image Configuration

**Image Repository:**
```
ghcr.io/brwalknels/forge-face-detection
```

**Image Tag:**
```
latest
```

**Image Pull Policy:**
- Select: `Always`

---

## Step 4: Container Configuration

### Container Command
Leave empty (uses Dockerfile CMD: `gunicorn`)

### Container Args
Leave empty

### Container Environment Variables

Click **Add** for each variable:

| Name | Value |
|------|-------|
| `MODEL_TYPE` | `hog` |
| `LOG_LEVEL` | `INFO` |

**Notes:**
- `MODEL_TYPE=hog` is faster (1-2s per photo), use `cnn` for more accuracy (3-5s per photo)
- `LOG_LEVEL=INFO` provides standard logging, use `DEBUG` for troubleshooting

---

## Step 5: Networking Configuration

### Network Mode
- Select: `Bridge`

### Port Forwarding

Click **Add** to create port mapping:

| Container Port | Host Port | Protocol |
|---------------|-----------|----------|
| `5000` | `5000` | `TCP` |

**Note:** Port 5000 is the Flask app port. Only accessible within TrueNAS network (Forge API communicates with it).

---

## Step 6: Storage Configuration

### Host Path Volumes

Click **Add** for each volume mount:

#### Volume 1: Private Files (Read-Only)
- **Host Path:** `/mnt/pool/Forge/private`
- **Container Path:** `/app/private`
- **Mode:** `Read Only` ✓

#### Volume 2: Metadata (Read-Only)
- **Host Path:** `/mnt/pool/Forge/metadata`
- **Container Path:** `/app/metadata`
- **Mode:** `Read Only` ✓

**Important:** Face detection only READS photos, never writes. This is a security best practice.

---

## Step 7: Resource Limits (Recommended)

### CPU Limit
```
2
```
(Allocates 2 CPU cores for face detection processing)

### Memory Limit
```
2048
```
(2 GB RAM - minimum required for dlib face detection)

**Notes:**
- Face detection is CPU-intensive
- dlib requires at least 1.5GB RAM for face encoding
- Adjust based on your system resources and workload

---

## Step 8: Advanced Settings

### Restart Policy
- Select: `Unless Stopped`

### Capabilities
Leave default (no special capabilities needed)

### Health Check
Leave empty (Flask app has built-in `/health` endpoint)

---

## Step 9: Deploy the Application

1. **Review all settings** - scroll up to verify everything is correct
2. Click **Install** (bottom right)
3. Wait for deployment (may take 2-5 minutes for first pull)
4. Status should show: `Active` with green indicator

---

## Step 10: Verify Face Detection Service

### Method 1: Check Container Logs

1. In TrueNAS Apps, click on **forge-face-detection**
2. Click **Logs** tab
3. Look for startup messages:
   ```
   [INFO] Starting gunicorn 21.2.0
   [INFO] Listening at: http://0.0.0.0:5000
   [INFO] Using worker: sync
   [INFO] Booting worker with pid: 7
   ```

### Method 2: Test Health Endpoint

SSH into TrueNAS and run:
```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "model": "hog",
  "timestamp": "2025-11-01T12:00:00Z"
}
```

### Method 3: Test from Forge Container

```bash
# SSH into TrueNAS
ssh truenas_admin@10.0.0.120

# Access Forge container
docker exec -it forge bash

# Test face detection service
curl http://forge-face-detection:5000/health
```

Expected response: Same as above

---

## Step 11: Update Forge Container to Connect to Face Detection

### Check Current Forge Configuration

SSH into TrueNAS:
```bash
docker exec forge cat docker-compose.yml
```

Look for `FACE_DETECTION_SERVICE_URL` in environment variables.

### If Not Set, Update Forge Container

1. In TrueNAS Apps, click on **forge**
2. Click **Edit** (top right)
3. Scroll to **Container Environment Variables**
4. Click **Add**
5. Add variable:
   - **Name:** `FACE_DETECTION_SERVICE_URL`
   - **Value:** `http://forge-face-detection:5000`
6. Click **Save** (bottom right)
7. Forge will restart automatically

---

## Step 12: Enable Face Detection in Admin Panel

1. Open Forge web interface: `https://photos.yourdomain.com` (or local IP)
2. Login as admin
3. Navigate to: **Admin Panel** → **Face Detection**
4. Click **Test Connection** button
5. Expected result: ✅ "Service is healthy (model: hog)"

### Configure Settings

- **Enable Automatic Processing:** Toggle ON
- **Model Type:** `hog` (or `cnn` for better accuracy)
- **Auto-process gallery photos:** Toggle ON (processes photos automatically on upload)

Click **Save Settings**

---

## Step 13: Test Face Detection with Real Photo

### Upload a Photo with Faces

1. Go to **Gallery** (user portal or admin)
2. Upload a photo containing faces
3. Check **Admin Panel** → **Face Detection** → **Queue Status**
4. Should see: Photo added to queue, processing, then completed

### Check Face Descriptors

SSH into TrueNAS:
```bash
# Check face descriptors file
docker exec forge cat /app/data/face-descriptors.json | jq
```

Expected output:
```json
{
  "photo-uuid-1": {
    "photoId": "photo-uuid-1",
    "faces": [
      {
        "location": { "top": 100, "right": 300, "bottom": 200, "left": 200 },
        "descriptor": [0.123, -0.456, ...] // 128-dimensional vector
      }
    ],
    "processedAt": "2025-11-01T12:00:00.000Z"
  }
}
```

---

## Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker logs forge-face-detection
```

**Common issues:**
- Memory too low (increase to 2GB minimum)
- Port 5000 already in use (change host port)
- Volume mounts incorrect (verify paths exist)

### "Service Unavailable" in Admin Panel

**Test connectivity from Forge:**
```bash
docker exec forge curl http://forge-face-detection:5000/health
```

**If fails:**
- Check both containers are on same Docker network
- Verify `FACE_DETECTION_SERVICE_URL` environment variable in Forge
- Restart both containers

### Face Detection Not Processing Photos

**Check queue status:**
```bash
docker exec forge cat /app/data/face-detection-queue.json | jq
```

**Check Forge logs:**
```bash
docker logs forge | grep -i face
```

**Common issues:**
- Automatic processing disabled (check admin settings)
- Service not healthy (test `/health` endpoint)
- Photos not in gallery (only gallery photos are processed)

### High CPU/Memory Usage

Face detection is resource-intensive. If system struggles:

1. **Switch to HOG model** (if using CNN):
   - Admin Panel → Face Detection → Model Type: `hog`
   
2. **Reduce concurrent processing**:
   - Edit Forge container environment
   - Add: `FACE_DETECTION_MAX_CONCURRENT=1`
   
3. **Increase resource limits**:
   - Edit forge-face-detection container
   - CPU: 4 cores, Memory: 4GB

---

## Updating the Service

### Update to Latest Image

```bash
# SSH into TrueNAS
ssh truenas_admin@10.0.0.120

# Pull latest image
docker pull ghcr.io/brwalknels/forge-face-detection:latest

# Restart container (TrueNAS GUI)
# Apps → forge-face-detection → Stop → Start
```

Or use TrueNAS GUI:
1. Apps → **forge-face-detection**
2. Click **Edit**
3. Change nothing (just trigger update check)
4. Click **Save**
5. Container pulls latest image automatically

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│ TrueNAS SCALE Host (10.0.0.120)                     │
│                                                       │
│  ┌────────────────┐         ┌──────────────────┐    │
│  │  Forge API     │         │  Face Detection  │    │
│  │  (Node.js)     │────────▶│  (Python/Flask)  │    │
│  │  Port 3000     │  HTTP   │  Port 5000       │    │
│  └────────────────┘         └──────────────────┘    │
│         │                            │               │
│         │                            │               │
│  ┌──────▼────────────────────────────▼─────────┐    │
│  │     Shared Storage                          │    │
│  │  /mnt/pool/Forge/                           │    │
│  │  ├── private/  (photos - read-only)         │    │
│  │  ├── metadata/ (file info - read-only)      │    │
│  │  └── data/     (face descriptors - R/W)     │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

**Flow:**
1. User uploads photo to gallery (Forge API)
2. Forge adds photo to face detection queue
3. Queue service sends photo to Python service
4. Python service detects faces, returns descriptors
5. Forge saves descriptors to `data/face-descriptors.json`
6. Future: Use descriptors for face-based search/albums

---

## Security Notes

- ✅ Face detection runs with **read-only** access to photos
- ✅ Service is **not exposed** to internet (internal port only)
- ✅ Only Forge API can communicate with face detection service
- ✅ All data stored locally (no external API calls)
- ✅ Face descriptors are anonymous vectors (no biometric data stored)

---

## Performance Expectations

### HOG Model (Default)
- **Speed:** 1-2 seconds per photo
- **Accuracy:** Good (suitable for most cases)
- **CPU Usage:** Moderate (2 cores recommended)
- **Memory:** 1.5-2 GB

### CNN Model (High Accuracy)
- **Speed:** 3-5 seconds per photo
- **Accuracy:** Excellent (better for difficult lighting/angles)
- **CPU Usage:** High (4 cores recommended)
- **Memory:** 2-4 GB

**Bulk Upload Performance:**
- 100 photos = ~3-5 minutes (HOG model)
- 1000 photos = ~30-50 minutes (HOG model)
- Processing happens in background, doesn't block UI

---

## Next Steps

After successful deployment:

1. **Phase 1: Testing** ✓
   - Upload photos with faces
   - Verify descriptors saved correctly
   - Monitor performance and resource usage

2. **Phase 2: Face Clustering** (Future)
   - Implement DBSCAN clustering algorithm
   - Group similar faces together
   - Create person entities in database

3. **Phase 3: Smart Albums** (Future)
   - Face-based gallery filtering
   - Auto-create albums per person
   - "Find all photos with this person"

4. **Phase 4: Advanced Features** (Future)
   - Manual face labeling (assign names)
   - Face recognition (identify known people)
   - Privacy controls (blur faces, opt-out)

---

## Support

**Documentation:**
- Main README: `forge-face-detection/README.md`
- Architecture: `Forge/docs/FACE_DETECTION_MICROSERVICE.md`
- GitHub Setup: `forge-face-detection/GITHUB_SETUP.md`

**Logs:**
```bash
# Face detection service
docker logs forge-face-detection

# Forge API (queue processing)
docker logs forge | grep -i face

# TrueNAS system logs
dmesg | tail -n 100
```

**Need Help?**
- Check logs first (most issues show clear error messages)
- Review troubleshooting section above
- Verify all prerequisites are met
- Test each component individually (health endpoints, connectivity)

---

**Deployment Complete!** 🎉

Your face detection microservice is now running alongside Forge API on TrueNAS SCALE.

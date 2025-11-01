# Creating the forge-face-detection GitHub Repository

## Step 1: Create GitHub Repository

1. Go to: https://github.com/new
2. Repository name: `forge-face-detection`
3. Description: `Python microservice for facial recognition in the Forge photo backup system`
4. Visibility: **Public** (or Private if you prefer)
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

## Step 2: Push Local Repository to GitHub

After creating the repo, run these commands:

```powershell
cd "c:\Users\brigh\Visual Studio Code\forge-face-detection"

# Add GitHub remote
git remote add origin https://github.com/Brwalknels/forge-face-detection.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 3: Configure GitHub Actions Permissions

The workflow needs permission to publish Docker images to GitHub Container Registry:

1. Go to: https://github.com/Brwalknels/forge-face-detection/settings/actions
2. Under "Workflow permissions":
   - Select: **Read and write permissions**
   - Check: **Allow GitHub Actions to create and approve pull requests**
3. Click "Save"

## Step 4: Verify GitHub Actions Build

1. Go to: https://github.com/Brwalknels/forge-face-detection/actions
2. You should see a workflow run starting automatically
3. Wait for build to complete (~5-10 minutes for first build)
4. Check for green checkmark ✓

## Step 5: Verify Docker Image Published

1. Go to: https://github.com/Brwalknels/forge-face-detection/pkgs/container/forge-face-detection
2. You should see the image tagged as `latest`
3. Copy the image URL: `ghcr.io/brwalknels/forge-face-detection:latest`

## Step 6: Test the Image

On your development machine or server:

```bash
# Pull the image
docker pull ghcr.io/brwalknels/forge-face-detection:latest

# Run standalone test
docker run -d \
  --name forge-face-detection-test \
  -p 5000:5000 \
  ghcr.io/brwalknels/forge-face-detection:latest

# Test health check
curl http://localhost:5000/health

# Expected response:
# {"status":"ready","service":"forge-face-detection","model":"hog","version":"1.0.0"}

# Clean up test container
docker stop forge-face-detection-test
docker rm forge-face-detection-test
```

## Step 7: Update Forge Repository

The Forge repo is already configured to use the external image. Just push your changes:

```powershell
cd "c:\Users\brigh\Visual Studio Code\Forge"
git push origin Server-API-Migration
```

## Step 8: Deploy to TrueNAS

Once both repos are updated:

```bash
# SSH to TrueNAS
ssh truenas_admin@your-server-ip

# Navigate to Forge directory
cd /mnt/pool/Forge

# Pull latest Forge image
docker-compose pull file-sync-api

# Pull face detection image
docker-compose pull forge-face-detection

# Restart both services
docker-compose down
docker-compose up -d

# Verify both running
docker ps | grep forge

# Test face detection health
curl http://localhost:5000/health
```

## Repository Structure

After setup, your workspace will look like this:

```
c:\Users\brigh\Visual Studio Code\
├── Forge/                          # Main API (MasterSync-2.0 repo)
│   ├── src/
│   ├── docker-compose.yml          # Uses: ghcr.io/brwalknels/forge-face-detection:latest
│   └── docker-compose.dev.yml      # Local dev: builds from ../forge-face-detection
├── mastersync-releaseclean/        # Android app (MasterSync-2.0 repo)
└── forge-face-detection/           # Face detection microservice (NEW REPO)
    ├── app/
    ├── .github/workflows/
    ├── Dockerfile
    └── README.md
```

## GitHub Repositories

1. **MasterSync-2.0** (existing)
   - Contains: Forge API + Android app
   - URL: https://github.com/Brwalknels/MasterSync-2.0

2. **forge-face-detection** (new)
   - Contains: Python microservice
   - URL: https://github.com/Brwalknels/forge-face-detection

## Development Workflow

### Working on Face Detection Only

```bash
cd forge-face-detection
# Make changes to app/main.py
git add .
git commit -m "feat: improve face detection accuracy"
git push origin main
# GitHub Actions automatically builds and publishes new image
```

### Testing Locally (Both Services)

```bash
cd Forge
docker-compose -f docker-compose.dev.yml up --build
# This builds forge-face-detection from ../forge-face-detection
```

### Deploying to Production

```bash
# Forge changes
cd Forge
git push origin main
# Wait for GitHub Actions to build

# Face detection changes
cd ../forge-face-detection
git push origin main
# Wait for GitHub Actions to build

# Then on TrueNAS:
docker-compose pull
docker-compose up -d
```

## Troubleshooting

### Issue: GitHub Actions fails with "permission denied"
**Solution:** Check Step 3 above - ensure workflow has write permissions.

### Issue: Can't pull image from ghcr.io
**Solution:** 
```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u Brwalknels --password-stdin
```

### Issue: Local build can't find ../forge-face-detection
**Solution:** Ensure both repos are cloned at the same level:
```
Visual Studio Code/
├── Forge/
└── forge-face-detection/  # Must be here!
```

### Issue: Image is private and can't be pulled
**Solution:** Make the package public:
1. Go to: https://github.com/users/Brwalknels/packages/container/forge-face-detection/settings
2. Under "Danger Zone" → "Change visibility"
3. Select "Public"

## Next Steps

After successful deployment:

1. ✅ Test face detection in admin panel (`/admin/face-detection`)
2. ✅ Upload a photo with faces to gallery
3. ✅ Verify queue processing
4. ✅ Check `data/face-descriptors.json` for results
5. ✅ Monitor logs: `docker logs -f forge-face-detection`

## Useful Commands

```bash
# View face detection logs
docker logs -f forge-face-detection

# Restart just face detection
docker-compose restart forge-face-detection

# Rebuild and deploy both services
docker-compose down && docker-compose pull && docker-compose up -d

# Check disk space used by images
docker images | grep forge

# Clean up old images
docker image prune -a
```

---

**Ready to create the GitHub repo? Follow Step 1 above!** 🚀

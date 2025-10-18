# Building and Publishing to Docker Hub

## Prerequisites

1. Docker Desktop installed
2. Docker Hub account created at https://hub.docker.com
3. Login to Docker Hub from terminal:
   ```bash
   docker login
   ```

## Build Multi-Architecture Image

Build for both AMD64 (most servers) and ARM64 (Apple Silicon, some NAS devices):

```bash
# Create and use buildx builder (one-time setup)
docker buildx create --name mybuilder --use
docker buildx inspect --bootstrap

# Build and push multi-arch image
docker buildx build --platform linux/amd64,linux/arm64 \
  -t okigan/revproxauth:latest \
  -t okigan/revproxauth:v0.1.0 \
  --push .
```

## Build Single Architecture (Faster for Testing)

```bash
# Build for your current architecture only
docker build -t okigan/revproxauth:latest .

# Test locally
docker run -d \
  -p 9000:9000 \
  -e RADIUS_SERVER=192.168.10.12 \
  -e RADIUS_SECRET=your-secret \
  okigan/revproxauth:latest

# Push to Docker Hub
docker push okigan/revproxauth:latest
```

## Tagging Strategy

```bash
# Tag with version
docker tag okigan/revproxauth:latest okigan/revproxauth:v0.1.0

# Tag with major version
docker tag okigan/revproxauth:latest okigan/revproxauth:v0

# Push all tags
docker push okigan/revproxauth:latest
docker push okigan/revproxauth:v0.1.0
docker push okigan/revproxauth:v0
```

## Automated Builds with GitHub Actions

See `.github/workflows/docker-publish.yml` for automated builds on:
- Push to main branch
- New tags (v*)
- Pull requests (build only, no push)

## Local Development

For development with live code reloading, use the dev compose file:

```bash
docker-compose -f docker-compose.dev.yml up
```

## Verify Image

```bash
# Check image size
docker images okigan/revproxauth

# Inspect image
docker inspect okigan/revproxauth:latest

# Check for vulnerabilities (optional)
docker scout cves okigan/revproxauth:latest
```

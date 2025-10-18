# RevProxAuth Setup Guide

Step-by-step walkthrough for Synology Container Manager

> ⚠️ **Important:** Due to a bug in Synology's Container Manager, port mappings on individual containers may not work correctly. **Using Docker Compose (Container Manager Projects) is strongly recommended.** This guide shows both methods.

## 1. Install RADIUS Server

First, install the RADIUS Server package from Synology Package Center. This provides authentication services for RevProxAuth.

![RADIUS Server Installation](images/image.png)

1. Open **Package Center** on your Synology NAS
2. Search for "RADIUS Server"
3. Click **Install**
4. After installation, open RADIUS Server and enable it on port 1812
5. Set a shared secret (remember this for later!)
6. Add client: `127.0.0.1` or `172.17.0.1` with the same secret



## 2. Choose Installation Method

**Recommended: Method A - Docker Compose (Container Manager Project)**

Due to a Synology bug where port mappings don't work reliably with individual containers, we recommend using Docker Compose through Container Manager Projects.

**Alternative: Method B - Individual Container (GUI)**

This method may not work due to the port mapping bug. Use only if Method A is not suitable for your needs.

---

## Method A: Docker Compose (Recommended)

### 3A. Create Project Directory

Use File Station to create the project structure.

1. Open **File Station**
2. Navigate to `/docker` (create this folder if it doesn't exist)
3. Create new folder: `revproxauth`
4. Inside `revproxauth`, create folder: `config`

### 4A. Create docker-compose.yml

Create the Docker Compose configuration file.

1. Inside `/docker/revproxauth`, create a new file named `docker-compose.yml`
2. Copy the following content and **replace all EXAMPLE values**:

```yaml
services:
  revproxauth:
    image: okigan/revproxauth:latest
    container_name: revproxauth
    ports:
      - "9000:9000"
    environment:
      # REQUIRED: Replace these example values with your actual configuration
      - RADIUS_SERVER=172.17.0.1              # EXAMPLE: Docker bridge gateway IP (use if RADIUS is on same NAS)
                                               # OR use your actual RADIUS server IP (e.g., 192.168.1.100)
      - RADIUS_SECRET=change-me-secret        # EXAMPLE: Replace with your actual RADIUS shared secret
      - LOGIN_DOMAIN=app.example.com          # EXAMPLE: Replace with your actual domain (e.g., app.mysynology.me)
      
      # OPTIONAL: Adjust these if needed
      - RADIUS_PORT=1812                      # Default RADIUS port (usually no change needed)
      - RADIUS_NAS_IDENTIFIER=revproxauth     # NAS identifier (usually no change needed)
      - REVPROXAUTH_ADMIN_USERS=admin         # EXAMPLE: Comma-separated admin usernames (e.g., admin,john)
                                               # Leave empty to allow all users to edit mappings
      
      # OPTIONAL: Logging configuration
      - LOG_LEVEL=INFO                        # Use DEBUG for troubleshooting, INFO for production
      - NO_COLOR=1                            # Cleaner logs without color codes
      - UV_NO_PROGRESS=1                      # Suppress progress bars in logs
    restart: unless-stopped
    volumes:
      - /volume1/docker/revproxauth/config:/app/config  # Persistent config storage
                                                         # Adjust /volume1 to your volume name if different
```

### 5A. Create Project in Container Manager

Set up the project in Container Manager.

1. Open **Container Manager**
2. Go to **Project** tab
3. Click **Create**
4. Project Name: `revproxauth`
5. Path: Browse and select `/docker/revproxauth`
6. Source: `Use existing docker-compose.yml`
7. Click **Next** to review settings
8. Click **Done**

### 6A. Launch Project

Launch your RevProxAuth project.

1. In the **Project** tab, select `revproxauth`
2. Click **Build** (first time only)
3. Click **Start**
4. Check logs by clicking on the project → **Action** → **View Logs**
3. Wait for build to complete
4. Select **Action** > **Start**
5. You should see: `RevProxAuth Starting` with your configuration

Container is now running on `http://YOUR-NAS-IP:9000`

**Skip to Step 9** (Configure Reverse Proxy) if using Method A.

---

## Method B: Individual Container (Alternative)

> ⚠️ **Warning:** This method may not work due to Synology's port mapping bug. If port 9000 is not accessible after setup, use Method A instead.

### 2B. Open Container Manager

### 2B. Open Container Manager

Navigate to Container Manager (Docker) on your Synology NAS. If you don't have it installed, get it from Package Center first.

1. Open **Container Manager** from the main menu
2. Go to the **Registry** tab



## 3B. Download RevProxAuth Image

## 3B. Download RevProxAuth Image

Pull the official RevProxAuth image from Docker Hub.

1. In the **Registry** tab, search for: `okigan/revproxauth`
2. Click on the result and select **Download**
3. Choose the **latest** tag
4. Wait for the download to complete (check the **Image** tab)



## 4B. Launch Container

## 4B. Launch Container

Create a new container from the downloaded image.

1. Go to **Container** tab
2. Click the downloaded `okigan/revproxauth` image
3. Click **Launch**
4. Set Container Name to: `revproxauth`
5. Click **Advanced Settings**



## 5B. Configure Port Mapping

## 5B. Configure Port Mapping

Map the container port to your host so you can access the web interface.

> ⚠️ **Note:** This step may not work due to Synology's bug. If port 9000 is not accessible, use Method A instead.

1. In Advanced Settings, go to **Port Settings** tab
2. Click **+ Add**
3. Local Port: `9000`
4. Container Port: `9000`
5. Type: `TCP`



## 6B. Configure Volume for Persistent Storage

## 6B. Configure Volume for Persistent Storage

Mount a volume to persist your configuration across container restarts.

1. Go to **Volume Settings** tab
2. Click **Add Folder**
3. Create new folder: `/docker/revproxauth/config`
4. Mount path: `/app/config`



## 7B. Set Environment Variables

## 7B. Set Environment Variables

Configure the essential settings. **Replace all EXAMPLE values with your actual configuration!**

1. Go to **Environment** tab
2. Click **+ Add** for each variable:

**Required Variables (REPLACE EXAMPLES):**
* RADIUS_SERVER=172.17.0.1   # EXAMPLE: Docker bridge gateway (use if RADIUS on same NAS) OR your actual RADIUS server IP
* RADIUS_SECRET=change-me-secret   # EXAMPLE: Replace with your actual RADIUS shared secret
* LOGIN_DOMAIN=app.example.com   # EXAMPLE: Replace with your actual domain (e.g., app.mysynology.me)

**Optional Variables:**
* RADIUS_PORT=1812   # Default RADIUS port (usually no change needed)
* RADIUS_NAS_IDENTIFIER=revproxauth   # NAS identifier (usually no change needed)
* REVPROXAUTH_ADMIN_USERS=admin   # EXAMPLE: Comma-separated admin usernames (e.g., admin,john) - leave empty for all users
* LOG_LEVEL=INFO   # Use DEBUG for troubleshooting
* NO_COLOR=1   # Cleaner logs
* UV_NO_PROGRESS=1   # Suppress progress bars



## 8B. Start Container

## 8B. Start Container

Review your settings and launch the container!

1. Click **Apply** then **Done**
2. The container will start automatically
3. Check logs to verify it started successfully
4. You should see: `RevProxAuth Starting` with your configuration

> ⚠️ **If port 9000 is not accessible:** The port mapping bug has occurred. Stop this container and use Method A (Docker Compose) instead.

Container should now be running on `http://YOUR-NAS-IP:9000`

---

## Step 4: Configure Reverse Proxy

Set up Synology's built-in reverse proxy to route traffic through RevProxAuth.

1. Open **Control Panel** → **Login Portal** → **Advanced**
2. Go to **Reverse Proxy** tab
3. Click **Create**
4. **Source:** `https://app.yourdomain.com:443`
5. **Destination:** `http://localhost:9000`
6. ✅ Enable **WebSocket**



## 10. Setup Complete 🎉

Your RevProxAuth is now ready to use!

Next Steps:

1. Visit `https://yourdomain.com/revproxauth`
2. Log in with your Synology credentials
3. Add your first application mapping
4. Start using centralized authentication!

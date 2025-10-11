# SynAuthProxy Setup Guide

Step-by-step walkthrough for Synology Container Manager

## 1. Install RADIUS Server

First, install the RADIUS Server package from Synology Package Center. This provides authentication services for SynAuthProxy.

![RADIUS Server Installation](images/image.png)

1. Open **Package Center** on your Synology NAS
2. Search for "RADIUS Server"
3. Click **Install**
4. After installation, open RADIUS Server and enable it on port 1812
5. Set a shared secret (remember this for later!)
6. Add client: `127.0.0.1` or `172.17.0.1` with the same secret



## 2. Open Container Manager

Navigate to Container Manager (Docker) on your Synology NAS. If you don't have it installed, get it from Package Center first.

1. Open **Container Manager** from the main menu
2. Go to the **Registry** tab



## 3. Download SynAuthProxy Image

Pull the official SynAuthProxy image from Docker Hub.

1. In the **Registry** tab, search for: `okigan/synauthproxy`
2. Click on the result and select **Download**
3. Choose the **latest** tag
4. Wait for the download to complete (check the **Image** tab)



## 4. Launch Container

Create a new container from the downloaded image.

1. Go to the **Container** tab
2. Click the downloaded `okigan/synauthproxy` image
3. Click **Launch**
4. Set Container Name to: `synauthproxy`
5. Click **Advanced Settings**



## 5. Configure Port Mapping

Map the container port to your host so you can access the web interface.

1. In Advanced Settings, go to **Port Settings** tab
2. Click **+ Add**
3. Local Port: `9000`
4. Container Port: `9000`
5. Type: `TCP`



## 6. Configure Volume for Persistent Storage

Mount a volume to persist your configuration across container restarts.

1. Go to **Volume Settings** tab
2. Click **Add Folder**
3. Create new folder: `/docker/synauthproxy/config`
4. Mount path: `/app/config`



## 7. Set Environment Variables

Configure the essential settings. The container will show these variables - you just need to fill in the values!

* RADIUS_SERVER=172.17.0.1   # Docker host IP (use if RADIUS is on same NAS)
* RADIUS_SECRET=your-secret-here   # From RADIUS Server configuration
* RADIUS_PORT=1812   # Default RADIUS port
* LOGIN_DOMAIN=https://nas.example.com:9000   # Your full domain URL with protocol
* SYNAUTHPROXY_ADMIN_USERS=admin   # Optional: comma-separated admin usernames



## 8. Start Container

Review your settings and launch the container!

1. Click **Apply** then **Done**
2. The container will start automatically
3. Check logs to verify it started successfully
4. You should see: `SynAuthProxy Starting` with your configuration

Container is now running on `http://YOUR-NAS-IP:9000`



## 9. Configure Reverse Proxy

Set up Synology's built-in reverse proxy to route traffic through SynAuthProxy.

1. Open **Control Panel** → **Login Portal** → **Advanced**
2. Go to **Reverse Proxy** tab
3. Click **Create**
4. **Source:** `https://app.yourdomain.com:443`
5. **Destination:** `http://localhost:9000`
6. ✅ Enable **WebSocket**



## 10. Setup Complete 🎉

Your SynAuthProxy is now ready to use!

Next Steps:

1. Visit `https://yourdomain.com/synauthproxy`
2. Log in with your Synology credentials
3. Add your first application mapping
4. Start using centralized authentication!

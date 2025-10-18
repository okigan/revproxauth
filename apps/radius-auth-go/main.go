package main

import (
	"context"
	"crypto/hmac"
	"crypto/md5"
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"html/template"
	"log"
	"net/http"
	"os"
	"strconv"
	"sync"
	"time"

	"layeh.com/radius"
	"layeh.com/radius/rfc2865"
)

// Configuration
type Config struct {
	RadiusServer        string
	RadiusSecret        string
	RadiusPort          int
	RadiusNASIdentifier string
	SessionTimeout      int
	ProxyType           string
	ProxyName           string
	Port                string
}

// Session represents a user session
type Session struct {
	Username  string
	ExpiresAt time.Time
}

// SessionStore manages user sessions
type SessionStore struct {
	mu       sync.RWMutex
	sessions map[string]*Session
}

var (
	config       Config
	sessionStore *SessionStore
)

func init() {
	config = Config{
		RadiusServer:        getEnv("RADIUS_SERVER", "radius"),
		RadiusSecret:        getEnv("RADIUS_SECRET", "testing123"),
		RadiusPort:          getEnvInt("RADIUS_PORT", 1812),
		RadiusNASIdentifier: getEnv("RADIUS_NAS_IDENTIFIER", "auth-backend"),
		SessionTimeout:      getEnvInt("SESSION_TIMEOUT", 3600),
		ProxyType:           getEnv("PROXY_TYPE", "generic"),
		ProxyName:           getEnv("PROXY_NAME", "Auth"),
		Port:                getEnv("PORT", "8999"),
	}

	sessionStore = &SessionStore{
		sessions: make(map[string]*Session),
	}

	// Start cleanup goroutine
	go sessionStore.cleanup()
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if i, err := strconv.Atoi(value); err == nil {
			return i
		}
	}
	return defaultValue
}

// ValidateSession checks if a session is valid
func (s *SessionStore) ValidateSession(sessionID string) (string, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	session, exists := s.sessions[sessionID]
	if !exists {
		return "", false
	}

	if time.Now().After(session.ExpiresAt) {
		return "", false
	}

	return session.Username, true
}

// CreateSession creates a new session
func (s *SessionStore) CreateSession(username string) string {
	s.mu.Lock()
	defer s.mu.Unlock()

	sessionID := generateSessionID()
	s.sessions[sessionID] = &Session{
		Username:  username,
		ExpiresAt: time.Now().Add(time.Duration(config.SessionTimeout) * time.Second),
	}

	return sessionID
}

// DeleteSession removes a session
func (s *SessionStore) DeleteSession(sessionID string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.sessions, sessionID)
}

// cleanup periodically removes expired sessions
func (s *SessionStore) cleanup() {
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()

	for range ticker.C {
		s.mu.Lock()
		now := time.Now()
		for id, session := range s.sessions {
			if now.After(session.ExpiresAt) {
				delete(s.sessions, id)
			}
		}
		s.mu.Unlock()
	}
}

func generateSessionID() string {
	b := make([]byte, 32)
	rand.Read(b)
	return base64.URLEncoding.EncodeToString(b)
}

// authenticateRADIUS performs RADIUS authentication
func authenticateRADIUS(username, password string) (bool, error) {
	packet := radius.New(radius.CodeAccessRequest, []byte(config.RadiusSecret))
	
	// Add User-Name attribute
	if err := rfc2865.UserName_AddString(packet, username); err != nil {
		return false, fmt.Errorf("failed to add username: %w", err)
	}
	
	// Add User-Password attribute
	if err := rfc2865.UserPassword_AddString(packet, password); err != nil {
		return false, fmt.Errorf("failed to add password: %w", err)
	}
	
	// Add NAS-Identifier attribute
	if err := rfc2865.NASIdentifier_AddString(packet, config.RadiusNASIdentifier); err != nil {
		return false, fmt.Errorf("failed to add NAS identifier: %w", err)
	}

	// Add Message-Authenticator (attribute 80) with proper HMAC-MD5 calculation per RFC 2869
	// Step 1: Add attribute with 16 zero bytes as placeholder
	packet.Add(80, make([]byte, 16))
	
	// Step 2: Marshal packet to wire format
	wirePacket, err := packet.MarshalBinary()
	if err != nil {
		return false, fmt.Errorf("failed to marshal packet: %w", err)
	}
	
	// Step 3: Calculate HMAC-MD5 over entire packet with shared secret as key
	h := hmac.New(md5.New, []byte(config.RadiusSecret))
	h.Write(wirePacket)
	messageAuth := h.Sum(nil)
	
	// Step 4: Find the Message-Authenticator attribute in the marshaled packet and replace it
	// RADIUS packet structure: Code(1) + Identifier(1) + Length(2) + Authenticator(16) + Attributes(variable)
	// We need to find attribute 80 in the attributes section and replace its value
	// Attribute structure: Type(1) + Length(1) + Value(Length-2)
	offset := 20 // Start after header (Code + ID + Length + Authenticator)
	for offset < len(wirePacket) {
		attrType := wirePacket[offset]
		attrLen := int(wirePacket[offset+1])
		
		if attrType == 80 && attrLen == 18 { // Message-Authenticator type=80, length=18 (2 header + 16 value)
			// Replace the 16-byte value (skip 2-byte header)
			copy(wirePacket[offset+2:offset+18], messageAuth)
			break
		}
		offset += attrLen
	}
	
	// Step 5: Parse the updated packet back (with correct Message-Authenticator)
	packet, err = radius.Parse(wirePacket, []byte(config.RadiusSecret))
	if err != nil {
		return false, fmt.Errorf("failed to parse packet with Message-Authenticator: %w", err)
	}

	// Send the packet
	client := &radius.Client{
		Retry: 3 * time.Second,
	}

	// Set a reasonable timeout for the RADIUS request
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	
	radiusAddr := fmt.Sprintf("%s:%d", config.RadiusServer, config.RadiusPort)
	response, err := client.Exchange(ctx, packet, radiusAddr)
	if err != nil {
		return false, fmt.Errorf("RADIUS exchange failed: %w", err)
	}

	return response.Code == radius.CodeAccessAccept, nil
}

// authHandler handles the /auth endpoint
func authHandler(w http.ResponseWriter, r *http.Request) {
	cookie, err := r.Cookie("session_id")
	if err == nil {
		if username, valid := sessionStore.ValidateSession(cookie.Value); valid {
			log.Printf("Authenticated request for user: %s", username)
			w.Header().Set("X-Auth-User", username)
			w.WriteHeader(http.StatusOK)
			w.Write([]byte("OK"))
			return
		}
	}

	// Handle unauthenticated request
	if config.ProxyType == "nginx" {
		log.Println("Unauthenticated request (nginx auth_request)")
		w.WriteHeader(http.StatusUnauthorized)
		w.Write([]byte("Unauthorized"))
		return
	}

	// Traefik/Caddy: Return 302 redirect
	originalURI := r.Header.Get("X-Forwarded-Uri")
	if originalURI == "" {
		originalURI = r.URL.Path
	}

	forwardedHost := r.Header.Get("X-Forwarded-Host")
	if forwardedHost == "" {
		forwardedHost = r.Host
	}

	forwardedProto := r.Header.Get("X-Forwarded-Proto")
	if forwardedProto == "" {
		forwardedProto = "http"
	}

	loginURL := fmt.Sprintf("%s://%s/login?next=%s", forwardedProto, forwardedHost, originalURI)
	log.Printf("Unauthenticated request, redirecting to %s", loginURL)
	http.Redirect(w, r, loginURL, http.StatusFound)
}

// loginHandler displays the login form
func loginHandler(w http.ResponseWriter, r *http.Request) {
	next := r.URL.Query().Get("next")
	if next == "" {
		next = "/"
	}
	errorMsg := r.URL.Query().Get("error")

	forwardedHost := r.Header.Get("X-Forwarded-Host")
	if forwardedHost == "" {
		forwardedHost = r.Host
	}

	forwardedProto := r.Header.Get("X-Forwarded-Proto")
	if forwardedProto == "" {
		forwardedProto = "http"
	}

	baseURL := fmt.Sprintf("%s://%s", forwardedProto, forwardedHost)

	tmpl := template.Must(template.New("login").Parse(`
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Login - {{.ProxyName}} RADIUS Auth</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f0f0f0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .login-box {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            width: 300px;
        }
        h1 {
            margin: 0 0 20px 0;
            color: #333;
            text-align: center;
            font-size: 24px;
        }
        .subtitle {
            color: #666;
            font-size: 14px;
            text-align: center;
            margin-bottom: 20px;
        }
        input {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-sizing: border-box;
        }
        button {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background: #0056b3;
        }
        .error {
            color: red;
            margin: 10px 0;
            text-align: center;
            font-size: 14px;
        }
        .info {
            color: #666;
            font-size: 12px;
            text-align: center;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>🔐 Login</h1>
        <div class="subtitle">{{.ProxyName}} + RADIUS Authentication</div>
        {{if .Error}}<div class="error">{{.Error}}</div>{{end}}
        <form method="post" action="{{.BaseURL}}/do-login">
            <input type="text" name="username" placeholder="Username" required autofocus>
            <input type="password" name="password" placeholder="Password" required>
            <input type="hidden" name="next" value="{{.Next}}">
            <button type="submit">Login</button>
        </form>
        <div class="info">
            Test credentials: testuser/testpass
        </div>
    </div>
</body>
</html>
`))

	data := map[string]interface{}{
		"ProxyName": config.ProxyName,
		"BaseURL":   baseURL,
		"Next":      next,
		"Error":     errorMsg,
	}

	w.Header().Set("Content-Type", "text/html")
	tmpl.Execute(w, data)
}

// doLoginHandler handles login form submission
func doLoginHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	username := r.FormValue("username")
	password := r.FormValue("password")
	next := r.FormValue("next")
	if next == "" {
		next = "/"
	}

	forwardedHost := r.Header.Get("X-Forwarded-Host")
	if forwardedHost == "" {
		forwardedHost = r.Host
	}

	forwardedProto := r.Header.Get("X-Forwarded-Proto")
	if forwardedProto == "" {
		forwardedProto = "http"
	}

	baseURL := fmt.Sprintf("%s://%s", forwardedProto, forwardedHost)

	log.Printf("Login attempt for user: %s", username)

	// Authenticate with RADIUS
	authenticated, err := authenticateRADIUS(username, password)
	if err != nil {
		log.Printf("RADIUS error for user %s: %v", username, err)
		redirectURL := fmt.Sprintf("%s/login?next=%s&error=Authentication%%20service%%20error", baseURL, next)
		http.Redirect(w, r, redirectURL, http.StatusSeeOther)
		return
	}

	if !authenticated {
		log.Printf("Login failed for user: %s", username)
		redirectURL := fmt.Sprintf("%s/login?next=%s&error=Invalid%%20username%%20or%%20password", baseURL, next)
		http.Redirect(w, r, redirectURL, http.StatusSeeOther)
		return
	}

	log.Printf("Login successful for user: %s", username)

	// Create session
	sessionID := sessionStore.CreateSession(username)

	// Set cookie
	cookie := &http.Cookie{
		Name:     "session_id",
		Value:    sessionID,
		Path:     "/",
		MaxAge:   config.SessionTimeout,
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
	}
	http.SetCookie(w, cookie)

	// Redirect to next URL
	redirectURL := next
	if !isRelativeURL(next) {
		redirectURL = "/"
	}
	http.Redirect(w, r, fmt.Sprintf("%s%s", baseURL, redirectURL), http.StatusSeeOther)
}

// logoutHandler handles logout
func logoutHandler(w http.ResponseWriter, r *http.Request) {
	cookie, err := r.Cookie("session_id")
	if err == nil {
		sessionStore.DeleteSession(cookie.Value)
	}

	// Clear cookie
	http.SetCookie(w, &http.Cookie{
		Name:     "session_id",
		Value:    "",
		Path:     "/",
		MaxAge:   -1,
		HttpOnly: true,
	})

	forwardedHost := r.Header.Get("X-Forwarded-Host")
	if forwardedHost == "" {
		forwardedHost = r.Host
	}

	forwardedProto := r.Header.Get("X-Forwarded-Proto")
	if forwardedProto == "" {
		forwardedProto = "http"
	}

	loginURL := fmt.Sprintf("%s://%s/login", forwardedProto, forwardedHost)
	http.Redirect(w, r, loginURL, http.StatusSeeOther)
}

// healthHandler handles health checks
func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("OK"))
}

func isRelativeURL(url string) bool {
	return len(url) > 0 && url[0] == '/'
}

func main() {
	log.Printf("Starting %s RADIUS Auth Backend", config.ProxyName)
	log.Printf("RADIUS Server: %s:%d", config.RadiusServer, config.RadiusPort)
	log.Printf("Proxy Type: %s", config.ProxyType)
	log.Printf("Session Timeout: %d seconds", config.SessionTimeout)

	http.HandleFunc("/auth", authHandler)
	http.HandleFunc("/login", loginHandler)
	http.HandleFunc("/do-login", doLoginHandler)
	http.HandleFunc("/logout", logoutHandler)
	http.HandleFunc("/health", healthHandler)

	addr := ":" + config.Port
	log.Printf("Server listening on %s", addr)
	if err := http.ListenAndServe(addr, nil); err != nil {
		log.Fatal(err)
	}
}

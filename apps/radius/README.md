# FreeRADIUS Server Stack

This is a pre-configured FreeRADIUS server for testing authentication.

## Features

- ✅ FreeRADIUS 3.x
- ✅ Pre-configured test users
- ✅ Simple configuration
- ✅ Works with all auth stacks

## Default Configuration

**Server:**
- Port: 1812 (RADIUS authentication)
- Shared Secret: `testing123`

**Test Users:**
- Username: `testuser` / Password: `testpass`
- Username: `admin` / Password: `admin123`

## Configuration Files

- `config/clients.conf` - RADIUS client configuration
- `config/users` - User database (plaintext for testing)

## Running

This stack is automatically included in the main docker-compose files, but you can also run it standalone:

```bash
docker run -d \
  --name radius \
  -p 1812:1812/udp \
  -v $(pwd)/config:/etc/raddb \
  freeradius/freeradius-server:latest
```

## Security Warning

⚠️ **This configuration is for TESTING ONLY!**

- Uses plaintext passwords
- Weak shared secret
- No encryption

For production:
1. Use encrypted password storage
2. Generate strong shared secrets
3. Configure EAP-TLS or EAP-TTLS
4. Enable proper logging and monitoring
5. Integrate with LDAP/Active Directory

## Testing

Test RADIUS authentication from command line:

```bash
# Using radtest (from freeradius-utils package)
radtest testuser testpass localhost 0 testing123

# Using eapol_test (for EAP testing)
echo 'network={
  key_mgmt=WPA-EAP
  eap=TTLS
  identity="testuser"
  password="testpass"
}' > test.conf
eapol_test -c test.conf -s testing123
```

## Logs

View RADIUS logs:

```bash
docker logs radius
```

Enable debug mode:

```bash
docker exec radius radiusd -X
```

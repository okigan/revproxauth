# Message-Authenticator Implementation

## Overview
This document explains the Message-Authenticator (RFC 2869 attribute 80) implementation in the Go RADIUS authentication backend.

## Problem
FreeRADIUS was configured with `require_message_authenticator = yes` for security, but the Go implementation was not calculating the Message-Authenticator HMAC-MD5 correctly. Initially, it was setting attribute 80 to 16 zero bytes, which caused FreeRADIUS to silently drop the packets, resulting in authentication timeouts.

## Solution
Implemented proper Message-Authenticator HMAC-MD5 calculation per RFC 2869 section 5.14.

### RFC 2869 Requirements
The Message-Authenticator attribute:
- **Type**: 80
- **Length**: 18 bytes (2-byte header + 16-byte HMAC-MD5 value)
- **Value**: HMAC-MD5 hash calculated over the entire RADIUS packet
- **Key**: Shared secret between client and server
- **Initial Value**: Must be set to 16 zero bytes before calculating the HMAC

### Implementation Steps

```go
// Step 1: Add attribute with 16 zero bytes as placeholder
packet.Add(80, make([]byte, 16))

// Step 2: Marshal packet to wire format
wirePacket, err := packet.MarshalBinary()

// Step 3: Calculate HMAC-MD5 over entire packet with shared secret as key
h := hmac.New(md5.New, []byte(config.RadiusSecret))
h.Write(wirePacket)
messageAuth := h.Sum(nil)

// Step 4: Find attribute 80 in marshaled packet and replace its value
// RADIUS packet: Code(1) + ID(1) + Length(2) + Authenticator(16) + Attributes
offset := 20  // Start after header
for offset < len(wirePacket) {
    attrType := wirePacket[offset]
    attrLen := int(wirePacket[offset+1])
    
    if attrType == 80 && attrLen == 18 {
        // Replace 16-byte value (skip 2-byte header)
        copy(wirePacket[offset+2:offset+18], messageAuth)
        break
    }
    offset += attrLen
}

// Step 5: Parse updated packet back with correct Message-Authenticator
packet, err = radius.Parse(wirePacket, []byte(config.RadiusSecret))
```

## Why This Approach?

### Library Limitations
The `layeh.com/radius` library (v0.0.0-20221205141417-e7fbddd11d68) does not provide a built-in method to calculate Message-Authenticator. Research of the library source code showed:

- Has HMAC-MD5 support for other attributes (User-Password, Tunnel-Password)
- No specific `AddMessageAuthenticator()` or similar method
- Requires manual calculation and insertion

### Python Comparison
The Python implementation using `pyrad` is much simpler:
```python
req.add_message_authenticator()  # Automatic HMAC-MD5 calculation
```

The `pyrad` library handles all the complexity internally.

## Security Benefits
- **Packet Integrity**: Ensures packet hasn't been tampered with in transit
- **Replay Protection**: HMAC includes packet authenticator which is unique per request
- **Required by FreeRADIUS**: `require_message_authenticator = yes` enforces this for Access-Request packets

## Testing
Both Caddy and Traefik stacks authenticate successfully with this implementation:
- Caddy: `http://localhost:9030/login`
- Traefik: `http://localhost:9020/login`

Test credentials: `testuser/testpass`

## References
- RFC 2869 Section 5.14: Message-Authenticator Attribute
- FreeRADIUS Documentation: Message-Authenticator requirement
- HMAC-MD5: RFC 2104

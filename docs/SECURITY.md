# Security Hardening Documentation

This document describes the security features implemented in the Rose the Healer Shaman application.

## Overview

The application implements multiple layers of security hardening to protect against common web vulnerabilities and ensure safe operation in production environments.

## Security Features

### 1. Environment-Based CORS Configuration

**Purpose**: Restrict which origins can make requests to the API, preventing unauthorized cross-origin requests.

**Configuration**:
```bash
# .env file
ALLOWED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
```

**Options**:
- `*` - Allow all origins (development only)
- Comma-separated list of specific origins (production)

**Implementation**:
- Configured in `src/ai_companion/settings.py`
- Applied in `src/ai_companion/interfaces/web/app.py`
- Restricts HTTP methods to `GET` and `POST`
- Restricts headers to `Content-Type` and `Authorization`

### 2. Rate Limiting

**Purpose**: Prevent API abuse, DoS attacks, and excessive costs from external API calls.

**Configuration**:
```bash
# .env file
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=10
```

**Implementation**:
- Uses `slowapi` library for rate limiting
- Limits requests per IP address per minute
- Applied to all API endpoints:
  - `/api/session/start` - 10 requests/minute (configurable)
  - `/api/voice/process` - 10 requests/minute (configurable)
  - `/api/health` - 60 requests/minute (higher for monitoring)

**Rate Limit Response**:
When rate limit is exceeded, the API returns:
```json
{
  "error": "Rate limit exceeded",
  "detail": "Too many requests"
}
```
HTTP Status: 429 (Too Many Requests)

### 3. Security Headers Middleware

**Purpose**: Add security headers to all responses to protect against various web vulnerabilities.

**Headers Added**:

#### Content Security Policy (CSP)
Restricts resource loading to prevent XSS attacks:
```
default-src 'self';
script-src 'self' 'unsafe-inline' 'unsafe-eval';
style-src 'self' 'unsafe-inline';
img-src 'self' data: https:;
font-src 'self' data:;
connect-src 'self';
media-src 'self' blob:;
frame-ancestors 'none';
```

#### HTTP Strict Transport Security (HSTS)
Enforces HTTPS connections:
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

#### X-Frame-Options
Prevents clickjacking attacks:
```
X-Frame-Options: DENY
```

#### X-Content-Type-Options
Prevents MIME type sniffing:
```
X-Content-Type-Options: nosniff
```

#### X-XSS-Protection
Enables browser XSS protection:
```
X-XSS-Protection: 1; mode=block
```

#### Referrer-Policy
Controls referrer information:
```
Referrer-Policy: strict-origin-when-cross-origin
```

#### Permissions-Policy
Restricts browser features:
```
Permissions-Policy: geolocation=(), microphone=(self), camera=()
```

**Configuration**:
```bash
# .env file
ENABLE_SECURITY_HEADERS=true
```

**Implementation**:
- Custom middleware in `src/ai_companion/interfaces/web/middleware.py`
- Applied to all responses automatically

### 4. Secure Temporary File Handling

**Purpose**: Ensure temporary audio files are created with secure permissions to prevent unauthorized access.

**Implementation**:
- Audio files created with owner-only read/write permissions (0o600 on Unix)
- Uses `os.open()` with secure flags:
  - `O_CREAT` - Create file
  - `O_WRONLY` - Write only
  - `O_EXCL` - Fail if file exists (prevents race conditions)
- Automatic cleanup of old files (24 hours)

**Location**: `src/ai_companion/interfaces/web/routes/voice.py`

## Production Deployment Checklist

### Required Configuration

1. **Set Allowed Origins**:
   ```bash
   ALLOWED_ORIGINS="https://yourdomain.com"
   ```

2. **Enable Rate Limiting**:
   ```bash
   RATE_LIMIT_ENABLED=true
   RATE_LIMIT_PER_MINUTE=10
   ```

3. **Enable Security Headers**:
   ```bash
   ENABLE_SECURITY_HEADERS=true
   ```

### Recommended Settings

- **Development**:
  ```bash
  ALLOWED_ORIGINS="*"
  RATE_LIMIT_ENABLED=false
  ENABLE_SECURITY_HEADERS=false
  ```

- **Staging**:
  ```bash
  ALLOWED_ORIGINS="https://staging.yourdomain.com"
  RATE_LIMIT_ENABLED=true
  RATE_LIMIT_PER_MINUTE=20
  ENABLE_SECURITY_HEADERS=true
  ```

- **Production**:
  ```bash
  ALLOWED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
  RATE_LIMIT_ENABLED=true
  RATE_LIMIT_PER_MINUTE=10
  ENABLE_SECURITY_HEADERS=true
  ```

## Testing Security Features

### Manual Testing

1. **Test CORS Configuration**:
   ```bash
   curl -H "Origin: https://unauthorized.com" \
        -H "Access-Control-Request-Method: POST" \
        -X OPTIONS \
        http://localhost:8080/api/health
   ```
   Should return CORS headers with your configured origins.

2. **Test Rate Limiting**:
   ```bash
   # Make multiple rapid requests
   for i in {1..15}; do
     curl -X POST http://localhost:8080/api/session/start
   done
   ```
   Should return 429 error after exceeding limit.

3. **Test Security Headers**:
   ```bash
   curl -I http://localhost:8080/api/health
   ```
   Should show all security headers in response.

### Automated Testing

Run the security test suite:
```bash
# Ensure .env file is configured
python -m pytest tests/test_security.py -v
```

## Security Best Practices

### API Keys
- Never commit API keys to version control
- Use environment variables for all sensitive credentials
- Rotate API keys regularly
- Use different keys for development and production

### HTTPS
- Always use HTTPS in production
- Configure HSTS header (already enabled)
- Use valid SSL/TLS certificates

### Monitoring
- Monitor rate limit violations
- Track failed authentication attempts
- Set up alerts for unusual traffic patterns
- Review security logs regularly

### Updates
- Keep dependencies up to date
- Monitor security advisories
- Apply security patches promptly

## Troubleshooting

### CORS Errors

**Problem**: Frontend can't connect to API
**Solution**: Add frontend domain to `ALLOWED_ORIGINS`

### Rate Limit Issues

**Problem**: Legitimate users hitting rate limits
**Solution**: Increase `RATE_LIMIT_PER_MINUTE` or implement user-based rate limiting

### Security Header Conflicts

**Problem**: CSP blocking legitimate resources
**Solution**: Adjust CSP policy in `middleware.py` to allow specific sources

## Additional Resources

- [OWASP Security Headers](https://owasp.org/www-project-secure-headers/)
- [Content Security Policy Reference](https://content-security-policy.com/)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
- [slowapi Documentation](https://slowapi.readthedocs.io/)

## Related Requirements

This implementation addresses the following requirements from the deployment readiness review:

- **Requirement 1.1**: Environment variables properly managed
- **Requirement 1.2**: API key validation and error handling
- **Requirement 1.4**: Error responses don't leak sensitive information
- **Requirement 1.5**: Temporary files have appropriate permissions

## Maintenance

### Regular Tasks

1. **Review Rate Limits**: Adjust based on usage patterns
2. **Update CORS Origins**: Add new domains as needed
3. **Monitor Security Headers**: Ensure headers are being applied
4. **Audit File Permissions**: Verify temporary files are secure

### Quarterly Review

- Review and update security headers
- Audit rate limiting effectiveness
- Check for new security best practices
- Update dependencies for security patches

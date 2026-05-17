# API Enhancements Verification Checklist

Use this checklist to verify the API enhancements are working correctly.

## 1. OpenAPI Documentation

### Test Documentation Access

```bash
# Start the server
uv run fastapi run src/ai_companion/interfaces/web/app.py

# Access Swagger UI
open http://localhost:8080/api/v1/docs

# Access ReDoc
open http://localhost:8080/api/v1/redoc

# Download OpenAPI JSON
curl http://localhost:8080/api/v1/openapi.json > openapi.json
```

**Expected Results:**
- ✅ Swagger UI loads with all endpoints visible
- ✅ ReDoc loads with beautiful documentation
- ✅ OpenAPI JSON is valid and complete
- ✅ All endpoints show examples and validation rules

### Test Documentation Toggle

```bash
# Disable documentation
export ENABLE_API_DOCS=false
uv run fastapi run src/ai_companion/interfaces/web/app.py

# Try to access docs (should return 404)
curl http://localhost:8080/api/v1/docs
```

**Expected Results:**
- ✅ Documentation endpoints return 404 when disabled
- ✅ API endpoints still work normally

---

## 2. API Versioning

### Test Versioned Endpoints

```bash
# Test v1 health endpoint
curl http://localhost:8080/api/v1/health

# Test v1 session endpoint
curl -X POST http://localhost:8080/api/v1/session/start
```

**Expected Results:**
- ✅ All v1 endpoints return 200 OK
- ✅ Responses match documented format

### Test Backward Compatibility

```bash
# Test deprecated (non-versioned) endpoints
curl http://localhost:8080/api/health
curl -X POST http://localhost:8080/api/session/start
```

**Expected Results:**
- ✅ Deprecated endpoints still work
- ✅ Marked as deprecated in OpenAPI docs
- ✅ Same responses as v1 endpoints

---

## 3. Response Examples

### Verify in OpenAPI Docs

1. Open Swagger UI: http://localhost:8080/api/v1/docs
2. Expand each endpoint
3. Check "Example Value" section

**Expected Results:**
- ✅ VoiceProcessResponse shows realistic example
- ✅ SessionStartResponse shows UUID and message
- ✅ HealthCheckResponse shows all services
- ✅ ErrorResponse shows error format

### Test Actual Responses

```bash
# Start session and verify format
curl -X POST http://localhost:8080/api/v1/session/start | jq

# Check health and verify format
curl http://localhost:8080/api/v1/health | jq
```

**Expected Results:**
- ✅ Responses match documented examples
- ✅ All fields present and correct types
- ✅ UUIDs are valid v4 format

---

## 4. Validation Documentation

### Check Endpoint Docstrings

1. Open Swagger UI: http://localhost:8080/api/v1/docs
2. Expand POST /api/v1/voice/process
3. Read the description

**Expected Results:**
- ✅ Validation rules clearly listed
- ✅ Processing flow documented
- ✅ Error codes with descriptions
- ✅ Rate limits documented

### Test Validation Rules

```bash
# Test file size limit (should fail with 413)
dd if=/dev/zero of=large.wav bs=1M count=15
curl -X POST http://localhost:8080/api/v1/voice/process \
  -F "audio=@large.wav" \
  -F "session_id=test-123"

# Test invalid session ID format (should fail with 400)
curl -X POST http://localhost:8080/api/v1/voice/process \
  -F "audio=@small.wav" \
  -F "session_id=invalid"
```

**Expected Results:**
- ✅ Large file returns 413 with clear message
- ✅ Invalid session returns appropriate error
- ✅ Error messages match documentation

---

## 5. Frontend Integration

### Test Frontend API Client

```bash
# Build frontend
cd frontend
npm install
npm run build

# Start backend
cd ..
uv run fastapi run src/ai_companion/interfaces/web/app.py

# Test frontend (in browser)
open http://localhost:8080
```

**Expected Results:**
- ✅ Frontend loads without errors
- ✅ Session starts successfully
- ✅ Voice recording works
- ✅ API calls use /api/v1/ prefix
- ✅ No console errors

### Verify Network Requests

1. Open browser DevTools (F12)
2. Go to Network tab
3. Interact with the app

**Expected Results:**
- ✅ All API calls use /api/v1/ prefix
- ✅ Requests include X-Request-ID header
- ✅ Responses include rate limit headers
- ✅ Error responses follow standard format

---

## 6. Error Response Format

### Test Error Scenarios

```bash
# Test rate limiting (make 11 requests quickly)
for i in {1..11}; do
  curl -X POST http://localhost:8080/api/v1/session/start
done

# Test invalid audio format
echo "not audio" > invalid.txt
curl -X POST http://localhost:8080/api/v1/voice/process \
  -F "audio=@invalid.txt" \
  -F "session_id=$(uuidgen)"

# Test missing audio file
curl -X POST http://localhost:8080/api/v1/voice/process \
  -F "session_id=$(uuidgen)"
```

**Expected Results:**
- ✅ Rate limit error includes error code and message
- ✅ Invalid audio returns validation error
- ✅ Missing file returns 422 with details
- ✅ All errors include request_id

---

## 7. Documentation Files

### Verify Documentation

```bash
# Check API documentation exists
cat docs/API_DOCUMENTATION.md

# Check summary exists
cat docs/API_ENHANCEMENTS_SUMMARY.md

# Check .env.example updated
grep ENABLE_API_DOCS .env.example
```

**Expected Results:**
- ✅ API_DOCUMENTATION.md is comprehensive
- ✅ Includes examples for all endpoints
- ✅ Client examples in multiple languages
- ✅ .env.example documents new setting

---

## 8. Code Quality

### Run Linting

```bash
# Format check
make format-check

# Lint check
make lint-check
```

**Expected Results:**
- ✅ No formatting issues
- ✅ No linting errors
- ✅ All imports organized

### Check Type Hints

```bash
# Verify Python syntax
python -c "import ast; ast.parse(open('src/ai_companion/interfaces/web/models.py').read())"
python -c "import ast; ast.parse(open('src/ai_companion/interfaces/web/app.py').read())"
```

**Expected Results:**
- ✅ All files have valid syntax
- ✅ No import errors
- ✅ Type hints present

---

## Summary Checklist

- [ ] OpenAPI documentation accessible at /api/v1/docs
- [ ] ReDoc documentation accessible at /api/v1/redoc
- [ ] Documentation can be disabled via ENABLE_API_DOCS
- [ ] All endpoints available at /api/v1/ prefix
- [ ] Backward compatible /api/ routes work (deprecated)
- [ ] Response examples visible in OpenAPI docs
- [ ] Validation rules documented in endpoint descriptions
- [ ] Error responses follow standardized format
- [ ] Frontend uses versioned API endpoints
- [ ] API documentation file is comprehensive
- [ ] .env.example updated with new setting
- [ ] No linting or formatting errors

---

## Troubleshooting

### Documentation Not Loading

**Issue:** /api/v1/docs returns 404

**Solution:**
```bash
# Check ENABLE_API_DOCS setting
echo $ENABLE_API_DOCS

# Set to true if not set
export ENABLE_API_DOCS=true

# Restart server
```

### Frontend API Errors

**Issue:** Frontend shows network errors

**Solution:**
```bash
# Check frontend API client baseURL
grep baseURL frontend/src/services/apiClient.ts

# Should be: baseURL: '/api/v1'

# Rebuild frontend
cd frontend && npm run build
```

### Validation Not Working

**Issue:** Invalid requests not rejected

**Solution:**
- Check rate limiting is enabled: `RATE_LIMIT_ENABLED=true`
- Verify audio size limits in code
- Check logs for validation errors

---

## Success Criteria

All items in the summary checklist should be checked (✅) for the implementation to be considered complete and verified.

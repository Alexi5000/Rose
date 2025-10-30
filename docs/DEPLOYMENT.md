# Deployment Guide: Rose the Healer Shaman

This guide covers deploying Rose the Healer Shaman to various cloud platforms.

## Table of Contents

- [Railway Deployment (Recommended)](#railway-deployment-recommended)
- [Alternative Platforms](#alternative-platforms)
  - [Render](#render)
  - [Fly.io](#flyio)
- [Environment Variables](#environment-variables)
- [Data Persistence](#data-persistence)
- [Troubleshooting](#troubleshooting)

---

## Railway Deployment (Recommended)

Railway provides the simplest deployment experience with automatic builds and zero-config deployments.

> **📖 Comprehensive Guide**: For detailed Railway setup instructions including volume configuration, environment-specific deployments, and troubleshooting, see **[Railway Setup Guide](RAILWAY_SETUP.md)**.

### Prerequisites

1. A [Railway account](https://railway.app/)
2. Railway CLI installed (optional): `npm i -g @railway/cli`
3. All required API keys (see [Environment Variables](#environment-variables))

### Deployment Steps

#### Option 1: Deploy via Railway Dashboard (Easiest)

1. **Create a New Project**
   - Go to [Railway Dashboard](https://railway.app/dashboard)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your GitHub account and select your repository

2. **Configure Environment Variables**
   - In your Railway project, go to the "Variables" tab
   - Add all required environment variables (see list below)
   - Railway automatically sets `PORT` - no need to configure it

3. **Deploy**
   - Railway will automatically detect the `railway.json` configuration
   - The build process will:
     - Install Python dependencies with `uv`
     - Build the React frontend
     - Start the FastAPI server
   - Wait for the deployment to complete (usually 3-5 minutes)

4. **Configure Persistent Volume** (Critical!)
   - In the Railway dashboard, go to your service
   - Navigate to the "Variables" tab
   - Scroll to "Volumes" section and click "+ New Volume"
   - Set mount path to `/app/data` and size to 1GB minimum
   - Redeploy the service to apply the volume
   - **Important**: Without this step, all conversation data will be lost on restart!
   - See [Data Persistence Guide](DATA_PERSISTENCE.md) for detailed instructions

5. **Access Your Application**
   - Railway will provide a public URL (e.g., `https://your-app.up.railway.app`)
   - Visit the URL to interact with Rose

#### Option 2: Deploy via Railway CLI

```bash
# Login to Railway
railway login

# Link to your project (or create new)
railway link

# Set environment variables
railway variables set GROQ_API_KEY=your_key_here
railway variables set ELEVENLABS_API_KEY=your_key_here
# ... (set all required variables)

# Deploy
railway up
```

### Railway Configuration

The `railway.json` file in the project root configures:

- **Build Command**: Installs Python deps and builds React frontend
- **Start Command**: Runs uvicorn server on Railway's assigned port
- **Health Check**: `/api/health` endpoint for monitoring
- **Restart Policy**: Automatic restart on failure (max 3 retries)

#### Environment-Specific Configurations

The project includes optimized configurations for different environments:

- **Development**: `config/dev.env` - Local development with verbose logging
- **Staging**: `config/railway-staging.json` - Testing environment with moderate resources
- **Production**: `config/railway-prod.json` - Production-ready with strict security

To deploy to a specific environment:
```bash
# For staging
cp config/railway-staging.json railway.json

# For production
cp config/railway-prod.json railway.json

# Commit and push
git add railway.json
git commit -m "Configure for [environment]"
git push
```

See `config/README.md` for detailed configuration differences.

---

## Alternative Platforms

### Render

Render is another excellent platform with a generous free tier.

#### Deployment Steps

1. **Create a New Web Service**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure Build Settings**
   - **Name**: `rose-healer-shaman`
   - **Environment**: `Docker`
   - **Region**: Choose closest to your users
   - **Branch**: `main` (or your default branch)
   - **Dockerfile Path**: `./Dockerfile`

3. **Set Environment Variables**
   - Add all required variables in the "Environment" section
   - Render automatically sets `PORT` - no need to configure

4. **Configure Health Check**
   - **Health Check Path**: `/api/health`
   - **Health Check Timeout**: 30 seconds

5. **Deploy**
   - Click "Create Web Service"
   - Wait for build and deployment (5-10 minutes)

#### Render Configuration File (Optional)

Create `render.yaml` in project root:

```yaml
services:
  - type: web
    name: rose-healer-shaman
    env: docker
    dockerfilePath: ./Dockerfile
    healthCheckPath: /api/health
    envVars:
      - key: GROQ_API_KEY
        sync: false
      - key: ELEVENLABS_API_KEY
        sync: false
      - key: ELEVENLABS_VOICE_ID
        sync: false
      - key: TOGETHER_API_KEY
        sync: false
      - key: QDRANT_URL
        sync: false
      - key: QDRANT_API_KEY
        sync: false
```

### Fly.io

Fly.io offers global deployment with edge computing capabilities.

#### Deployment Steps

1. **Install Fly CLI**
   ```bash
   # macOS/Linux
   curl -L https://fly.io/install.sh | sh

   # Windows
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```

2. **Login and Initialize**
   ```bash
   fly auth login
   fly launch
   ```

3. **Configure fly.toml**
   
   The `fly launch` command will create a `fly.toml` file. Update it:

   ```toml
   app = "rose-healer-shaman"
   primary_region = "sjc"  # Choose your region

   [build]
     dockerfile = "Dockerfile"

   [env]
     PORT = "8000"

   [[services]]
     internal_port = 8000
     protocol = "tcp"

     [[services.ports]]
       handlers = ["http"]
       port = 80

     [[services.ports]]
       handlers = ["tls", "http"]
       port = 443

     [[services.http_checks]]
       interval = 30000
       timeout = 5000
       grace_period = "10s"
       method = "GET"
       path = "/api/health"

   [[mounts]]
     source = "rose_data"
     destination = "/app/data"
   ```

4. **Set Secrets**
   ```bash
   fly secrets set GROQ_API_KEY=your_key_here
   fly secrets set ELEVENLABS_API_KEY=your_key_here
   fly secrets set ELEVENLABS_VOICE_ID=your_voice_id
   fly secrets set TOGETHER_API_KEY=your_key_here
   fly secrets set QDRANT_URL=your_qdrant_url
   fly secrets set QDRANT_API_KEY=your_qdrant_key
   ```

5. **Create Volume for Data Persistence**
   ```bash
   fly volumes create rose_data --size 1
   ```

6. **Deploy**
   ```bash
   fly deploy
   ```

7. **Access Your Application**
   ```bash
   fly open
   ```

---

## Production Build Process

### Understanding the Build

The application uses a multi-stage build process:

1. **Frontend Build** (Vite)
   - Compiles React/TypeScript to optimized JavaScript
   - Outputs to `src/ai_companion/interfaces/web/static/`
   - Includes all CSS, 3D assets, and audio files
   - Build command: `npm run build` (in frontend directory)

2. **Backend Setup** (FastAPI)
   - Serves the compiled frontend as static files
   - Provides REST API endpoints at `/api/v1/`
   - Handles voice processing and session management

### Build Configuration

The frontend build path is configured in `frontend/vite.config.ts`:

```typescript
build: {
  outDir: '../src/ai_companion/interfaces/web/static',
  emptyOutDir: true,
}
```

This ensures the frontend builds directly into the location where FastAPI expects to find it.

### Local Production Testing

Before deploying, test the production build locally:

```bash
# Build and serve production version
python scripts/build_and_serve.py
```

This will:
1. 🎨 Build the frontend with production optimizations
2. 🚀 Start FastAPI server serving both static files and API
3. Serve the application at http://localhost:8000

### Troubleshooting Build Issues

**Frontend Build Fails**:
- Ensure Node.js 18+ is installed
- Run `npm install` in frontend directory
- Check for TypeScript errors: `npm run type-check`
- Verify all environment variables are set in `frontend/.env`

**Static Files Not Loading**:
- Verify build output exists at `src/ai_companion/interfaces/web/static/`
- Check that `index.html` and `assets/` directory are present
- Ensure FastAPI is configured to serve from correct path
- Check browser console for 404 errors

**API Connection Issues**:
- Verify `VITE_API_BASE_URL` is set correctly in frontend `.env`
- For production, this should be `/api/v1` (relative path)
- For development, this should be `http://localhost:8000/api/v1`

---

## Environment Variables

### Required Variables

These variables **must** be set for the application to function:

| Variable | Description | Example |
|----------|-------------|---------|
| `GROQ_API_KEY` | API key for Groq (LLM and STT) | `gsk_...` |
| `ELEVENLABS_API_KEY` | API key for ElevenLabs (TTS) | `sk_...` |
| `ELEVENLABS_VOICE_ID` | Voice ID for Rose's voice | `21m00Tcm4TlvDq8ikWAM` |
| `TOGETHER_API_KEY` | API key for Together AI (image gen) | `...` |
| `QDRANT_URL` | Qdrant vector database URL | `https://xyz.qdrant.io` |
| `QDRANT_API_KEY` | Qdrant API key (if using cloud) | `...` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ROSE_VOICE_ID` | Override voice ID specifically for Rose | Uses `ELEVENLABS_VOICE_ID` |
| `PORT` | Server port (auto-set by platforms) | `8000` |
| `HOST` | Server host | `0.0.0.0` |
| `SHORT_TERM_MEMORY_DB_PATH` | Path to SQLite memory database | `/app/data/memory.db` |

### Frontend Environment Variables

The frontend requires configuration during the build process. These are set in `frontend/.env`:

| Variable | Description | Development | Production |
|----------|-------------|-------------|------------|
| `VITE_API_BASE_URL` | API endpoint base URL | `http://localhost:8000/api/v1` | `/api/v1` |

**Important Notes**:
- Frontend environment variables are **baked into the build** at compile time
- For production deployments, use relative paths (e.g., `/api/v1`) to avoid CORS issues
- Changes to frontend `.env` require rebuilding the frontend
- Most deployment platforms handle this automatically during the build process

### Frozen Features (Not Required)

These variables are for features currently disabled:

- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_TOKEN`
- `WHATSAPP_VERIFY_TOKEN`

---

## Data Persistence

**Critical**: The application requires persistent storage to retain conversation data and memories across deployments.

### Railway Volume Setup

Railway uses ephemeral storage by default. You **must** configure a persistent volume:

1. In Railway dashboard, navigate to your service
2. Go to "Variables" tab → "Volumes" section
3. Click "+ New Volume"
4. Configure:
   - **Mount Path**: `/app/data`
   - **Size**: 1GB minimum (recommended)
5. Redeploy service to apply changes

### Automatic Backups

The application includes automatic backup features:

- **Database Backups**: Daily at 2:00 AM (keeps 7 days)
- **Audio Cleanup**: Hourly cleanup of temporary files older than 24 hours
- **Backup Location**: `/app/data/backups/`

### Detailed Documentation

For comprehensive information about data persistence, backups, and disaster recovery, see:

**[Data Persistence Guide](DATA_PERSISTENCE.md)**

This guide covers:
- Step-by-step Railway volume configuration
- Automatic backup system details
- Manual backup and restore procedures
- Disaster recovery strategies
- Storage requirements and optimization
- Troubleshooting common issues

---

## Troubleshooting

### Build Failures

#### Frontend Build Fails

**Symptom**: Build fails during `npm run build` step

**Solutions**:
1. Ensure Node.js 18+ is available in build environment
2. Check `frontend/package.json` for correct dependencies
3. Verify `frontend/tsconfig.json` is valid
4. Check build logs for specific TypeScript errors

```bash
# Test frontend build locally
cd frontend
npm install
npm run build
```

#### Python Dependencies Fail

**Symptom**: Build fails during `uv sync` step

**Solutions**:
1. Ensure Python 3.12+ is available
2. Check `pyproject.toml` for syntax errors
3. Verify `uv.lock` is committed to repository
4. Try regenerating lock file: `uv lock --upgrade`

### Runtime Errors

#### Health Check Fails

**Symptom**: Platform reports unhealthy service

**Solutions**:
1. Check `/api/health` endpoint is accessible
2. Verify all required environment variables are set
3. Check application logs for startup errors
4. Ensure Qdrant and other external services are reachable

```bash
# Test health endpoint locally
curl http://localhost:8000/api/v1/health
```

#### Memory Database Errors

**Symptom**: Errors related to SQLite or memory persistence

**Solutions**:
1. Ensure `/app/data` directory exists and is writable
2. For Railway/Render: Add a persistent volume
3. Check `SHORT_TERM_MEMORY_DB_PATH` environment variable
4. Verify file permissions in container

#### API Connection Errors

**Symptom**: Errors connecting to Groq, ElevenLabs, or Qdrant

**Solutions**:
1. Verify all API keys are correctly set
2. Check API key validity (not expired/revoked)
3. Ensure no trailing spaces in environment variables
4. Test API connectivity from deployment region
5. Check API rate limits and quotas

### Performance Issues

#### Slow Response Times

**Solutions**:
1. Check Groq API latency (try different models)
2. Verify Qdrant connection speed
3. Consider deploying closer to users
4. Monitor memory usage (may need larger instance)

#### High Memory Usage

**Solutions**:
1. Reduce `MEMORY_TOP_K` value (default: 3)
2. Lower `TOTAL_MESSAGES_SUMMARY_TRIGGER` (default: 20)
3. Clear old session data periodically
4. Upgrade to larger instance size

### Logs and Monitoring

#### Railway
```bash
railway logs
```

#### Render
- View logs in dashboard under "Logs" tab
- Enable log streaming for real-time monitoring

#### Fly.io
```bash
fly logs
```

### Frontend-Backend Integration Issues

#### "Cannot connect to Rose" Error

**Symptom**: Frontend displays connection error on startup

**Solutions**:
1. Verify backend is running and accessible
2. Check `VITE_API_BASE_URL` environment variable
3. Ensure CORS is configured correctly for your domain
4. Test health endpoint: `curl https://your-app.com/api/v1/health`
5. Check browser console for specific error messages

#### Static Assets Not Loading (404 Errors)

**Symptom**: Blank page or missing styles/3D models

**Solutions**:
1. Verify frontend was built before deployment
2. Check build output exists at `src/ai_companion/interfaces/web/static/`
3. Ensure Dockerfile copies frontend build to correct location
4. Verify FastAPI static file mount path matches build output
5. Check platform build logs for frontend build errors

#### Voice Processing Fails

**Symptom**: Voice button doesn't work or returns errors

**Solutions**:
1. Verify Groq API key is set and valid
2. Check ElevenLabs API key and voice ID
3. Ensure microphone permissions are granted in browser
4. Test with different audio formats (browser compatibility)
5. Check backend logs for specific API errors

### Getting Help

If you encounter issues not covered here:

1. **Check Application Logs**: Most platforms provide log viewing
2. **Test Locally**: Run `python scripts/build_and_serve.py` to reproduce issues
3. **Verify Environment**: Double-check all environment variables
4. **API Status**: Check status pages for Groq, ElevenLabs, Qdrant
5. **Development Guide**: See [DEVELOPMENT.md](../DEVELOPMENT.md) for detailed troubleshooting
6. **Community**: Open an issue on GitHub with logs and error details

---

## Post-Deployment Checklist

After successful deployment:

- [ ] Test voice recording and playback
- [ ] Verify Rose's personality in responses
- [ ] Test memory persistence across sessions
- [ ] Check health endpoint: `https://your-app.com/api/health`
- [ ] Monitor logs for errors
- [ ] Test on mobile devices
- [ ] Set up monitoring/alerts (if available)
- [ ] Configure custom domain (optional)
- [ ] Enable HTTPS (usually automatic)
- [ ] Test error handling (invalid audio, API failures)

---

## Cost Considerations

### Railway
- Free tier: 500 hours/month, $5 credit
- Paid: ~$5-20/month depending on usage
- Charges for compute time and bandwidth

### Render
- Free tier: 750 hours/month (with limitations)
- Paid: Starting at $7/month for basic instance
- Free tier has cold starts (slower initial response)

### Fly.io
- Free tier: 3 shared VMs, 160GB bandwidth
- Paid: ~$2-10/month depending on resources
- Pay for what you use (compute + bandwidth)

### API Costs (All Platforms)
- **Groq**: Free tier available, pay-as-you-go
- **ElevenLabs**: Free tier: 10k characters/month, paid plans start at $5/month
- **Together AI**: Pay-as-you-go for image generation
- **Qdrant Cloud**: Free tier: 1GB storage, paid plans available

**Estimated Monthly Cost**: $10-30 for moderate usage (100-500 sessions/month)

---

## Security Best Practices

1. **Never commit API keys** to version control
2. **Rotate keys regularly** (every 90 days recommended)
3. **Use platform secrets management** for sensitive variables
4. **Enable HTTPS** (automatic on most platforms)
5. **Configure CORS** appropriately for production
6. **Monitor API usage** to detect anomalies
7. **Set up rate limiting** if exposing publicly
8. **Regular backups** of memory databases

---

## Next Steps

After deployment:

1. **Custom Domain**: Configure a custom domain for professional appearance
2. **Monitoring**: Set up uptime monitoring (UptimeRobot, Pingdom)
3. **Analytics**: Add usage analytics (optional)
4. **Backup Strategy**: Implement regular backups of memory data
5. **Scaling**: Monitor usage and scale resources as needed
6. **CI/CD**: Set up automatic deployments on git push

---

## Operational Documentation

For production operations, refer to these comprehensive guides:

- **[Operations Runbook](OPERATIONS_RUNBOOK.md)**: Troubleshooting and diagnostic procedures
- **[Rollback Procedures](ROLLBACK_PROCEDURES.md)**: Deployment rollback and data restoration
- **[Incident Response Plan](INCIDENT_RESPONSE_PLAN.md)**: Incident management and post-mortems
- **[Architecture Documentation](ARCHITECTURE.md)**: System architecture and diagrams
- **[External API Limits](EXTERNAL_API_LIMITS.md)**: API rate limits, quotas, and costs
- **[Monitoring and Observability](MONITORING_AND_OBSERVABILITY.md)**: Logging and metrics

---

For more information, refer to:
- [Railway Documentation](https://docs.railway.app/)
- [Render Documentation](https://render.com/docs)
- [Fly.io Documentation](https://fly.io/docs/)

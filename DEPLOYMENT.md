# PicMe Docker Deployment Guide

This guide provides comprehensive instructions for building, testing, and deploying the PicMe face recognition application using Docker.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development and Testing](#local-development-and-testing)
- [Cloud Platform Deployment](#cloud-platform-deployment)
  - [Vessel Deployment](#vessel-deployment)
  - [Railway Deployment](#railway-deployment)
  - [Render Deployment](#render-deployment)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying PicMe, ensure you have:

- Docker installed (version 20.10 or higher)
- A Neon PostgreSQL database instance
- Git (for cloud deployments)
- Access to your chosen cloud platform (Vessel, Railway, or Render)

## Local Development and Testing

### Step 1: Build the Docker Image

Build the Docker image from the project root directory:

```bash
docker build -t picme:latest .
```

This command:
- Uses the `Dockerfile` in the project root
- Tags the image as `picme:latest`
- Installs all system dependencies (dlib, OpenCV, etc.)
- Installs Python dependencies from `requirements.txt`
- Configures the application to run with Gunicorn

**Expected output**: The build should complete without errors and display "Successfully tagged picme:latest"

**Build time**: Approximately 5-10 minutes depending on your system

### Step 2: Prepare Environment Variables

Create a `.env.docker` file with your configuration (do not commit this file):

```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@host.neon.tech/dbname?sslmode=require

# Flask Configuration
FLASK_SECRET_KEY=your-random-secret-key-here-change-this

# Server Configuration
PORT=8080
```

**Example values for local testing**:

```bash
DATABASE_URL=postgresql://picme_user:mypassword123@ep-cool-cloud-123456.us-east-2.aws.neon.tech/picme_db?sslmode=require
FLASK_SECRET_KEY=dev-secret-key-replace-in-production-abc123xyz789
PORT=8080
```

**Important**: 
- Replace `DATABASE_URL` with your actual Neon database connection string
- Generate a secure random string for `FLASK_SECRET_KEY` (use `python -c "import secrets; print(secrets.token_hex(32))"`)
- The `sslmode=require` parameter is required for Neon databases

### Step 3: Run the Container Locally

Run the container with your environment variables:

```bash
docker run -p 8080:8080 \
  --env-file .env.docker \
  --name picme-container \
  picme:latest
```

**Alternative**: Pass environment variables directly:

```bash
docker run -p 8080:8080 \
  -e DATABASE_URL="postgresql://user:pass@host.neon.tech/db?sslmode=require" \
  -e FLASK_SECRET_KEY="your-secret-key" \
  -e PORT=8080 \
  --name picme-container \
  picme:latest
```

**Command explanation**:
- `-p 8080:8080`: Maps container port 8080 to host port 8080
- `--env-file .env.docker`: Loads environment variables from file
- `--name picme-container`: Names the container for easy reference
- `picme:latest`: The image to run

### Step 4: Test the Application

Once the container is running, test the application:

#### 1. Check Container Status

```bash
docker ps
```

You should see `picme-container` in the list with status "Up"

#### 2. View Container Logs

```bash
docker logs picme-container
```

Look for:
- "Booting worker" messages from Gunicorn
- No error messages about missing environment variables
- Successful database connection messages

#### 3. Test the Homepage

```bash
curl http://localhost:8080
```

Or open `http://localhost:8080` in your browser. You should see the PicMe homepage.

#### 4. Test API Endpoints

**Health check** (if implemented):
```bash
curl http://localhost:8080/health
```

**User registration**:
```bash
curl -X POST http://localhost:8080/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"testpass123"}'
```

**User login**:
```bash
curl -X POST http://localhost:8080/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'
```

#### 5. Test Database Connectivity

Check that the application can connect to your Neon database:

```bash
docker exec picme-container python -c "
import psycopg2
import os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
print('Database connection successful!')
conn.close()
"
```

#### 6. Test Face Recognition

Upload a test photo through the web interface or API to verify face recognition is working.

### Step 5: Stop and Clean Up

Stop the container:
```bash
docker stop picme-container
```

Remove the container:
```bash
docker rm picme-container
```

Remove the image (optional):
```bash
docker rmi picme:latest
```

## Cloud Platform Deployment

### Vessel Deployment

Vessel provides simple Docker container deployment with automatic SSL and scaling.

#### Prerequisites
- Vessel account (https://vessel.land)
- Git repository with your code
- Neon database connection string

#### Deployment Steps

1. **Connect Your Repository**
   - Log in to Vessel dashboard
   - Click "New Project"
   - Connect your GitHub/GitLab repository
   - Select the repository containing PicMe

2. **Configure Build Settings**
   - Vessel will auto-detect the Dockerfile
   - Build context: `/` (root directory)
   - Dockerfile path: `./Dockerfile`

3. **Set Environment Variables**
   
   In the Vessel dashboard, navigate to your project settings and add:
   
   ```
   DATABASE_URL=postgresql://user:pass@host.neon.tech/db?sslmode=require
   FLASK_SECRET_KEY=<generate-secure-random-key>
   PORT=8080
   ```

   **Important**: 
   - Use the "Secret" toggle for `DATABASE_URL` and `FLASK_SECRET_KEY`
   - Vessel automatically handles PORT configuration, but setting it explicitly ensures consistency

4. **Configure Port Mapping**
   - Container port: `8080`
   - Vessel will automatically assign a public URL

5. **Deploy**
   - Click "Deploy"
   - Vessel will build the Docker image and deploy it
   - Monitor the build logs for any errors

6. **Verify Deployment**
   - Once deployed, Vessel provides a URL (e.g., `https://picme-abc123.vessel.land`)
   - Visit the URL to verify the application is running
   - Test user registration and login
   - Upload a test photo to verify face recognition

#### Vessel-Specific Features

- **Auto-scaling**: Vessel automatically scales based on traffic
- **SSL/TLS**: Automatic HTTPS with Let's Encrypt certificates
- **Logs**: View real-time logs in the Vessel dashboard
- **Rollback**: Easy rollback to previous deployments

### Railway Deployment

Railway offers seamless Docker deployment with built-in PostgreSQL support.

#### Prerequisites
- Railway account (https://railway.app)
- Git repository with your code
- Neon database connection string (or use Railway's PostgreSQL)

#### Deployment Steps

1. **Create New Project**
   - Log in to Railway dashboard
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Authorize Railway to access your repository
   - Select the PicMe repository

2. **Configure Deployment**
   - Railway will auto-detect the Dockerfile
   - No additional configuration needed for build

3. **Set Environment Variables**
   
   In the Railway project settings, add variables:
   
   ```
   DATABASE_URL=postgresql://user:pass@host.neon.tech/db?sslmode=require
   FLASK_SECRET_KEY=<generate-secure-random-key>
   PORT=8080
   ```

   **Railway-specific notes**:
   - Railway automatically injects a `PORT` variable, but you can override it
   - If using Railway's PostgreSQL, use the `DATABASE_URL` provided by Railway

4. **Configure Service Settings**
   - Go to Settings → Networking
   - Ensure port `8080` is exposed
   - Railway will generate a public domain (e.g., `picme-production.up.railway.app`)

5. **Deploy**
   - Railway automatically deploys on push to main branch
   - Monitor deployment in the "Deployments" tab
   - View build logs for any errors

6. **Verify Deployment**
   - Click the generated URL to access your application
   - Test all functionality (registration, login, photo upload, face recognition)

#### Railway-Specific Features

- **Automatic Deployments**: Deploys on every git push
- **Built-in PostgreSQL**: Option to use Railway's managed PostgreSQL instead of Neon
- **Custom Domains**: Add your own domain in Settings
- **Metrics**: View CPU, memory, and network usage
- **Logs**: Real-time log streaming in the dashboard

### Render Deployment

Render provides free tier Docker deployment with automatic SSL.

#### Prerequisites
- Render account (https://render.com)
- Git repository with your code
- Neon database connection string

#### Deployment Steps

1. **Create New Web Service**
   - Log in to Render dashboard
   - Click "New +" → "Web Service"
   - Connect your GitHub/GitLab account
   - Select the PicMe repository

2. **Configure Service**
   
   Fill in the service configuration:
   - **Name**: `picme` (or your preferred name)
   - **Region**: Choose closest to your users
   - **Branch**: `main` (or your deployment branch)
   - **Runtime**: `Docker`
   - **Dockerfile Path**: `./Dockerfile`

3. **Set Environment Variables**
   
   In the "Environment" section, add:
   
   ```
   DATABASE_URL=postgresql://user:pass@host.neon.tech/db?sslmode=require
   FLASK_SECRET_KEY=<generate-secure-random-key>
   PORT=8080
   ```

   **Render-specific notes**:
   - Render automatically sets `PORT` to 10000, but our Dockerfile uses 8080
   - Make sure to explicitly set `PORT=8080` to match the Dockerfile EXPOSE directive

4. **Configure Instance Type**
   - **Free Tier**: 512 MB RAM, shared CPU (good for testing)
   - **Starter**: 1 GB RAM, shared CPU (recommended for production)
   - **Standard**: 2+ GB RAM, dedicated CPU (for high traffic)

5. **Advanced Settings** (Optional)
   - **Health Check Path**: `/` or `/health` if implemented
   - **Auto-Deploy**: Enable to deploy on every git push

6. **Create Web Service**
   - Click "Create Web Service"
   - Render will build and deploy your application
   - Monitor the logs during deployment

7. **Verify Deployment**
   - Render provides a URL (e.g., `https://picme.onrender.com`)
   - Visit the URL to verify the application
   - Test all functionality

#### Render-Specific Features

- **Free Tier**: Free tier available with some limitations (spins down after inactivity)
- **Automatic SSL**: Free SSL certificates for all services
- **Custom Domains**: Add custom domains with automatic SSL
- **Pull Request Previews**: Automatic preview deployments for PRs
- **Persistent Disks**: Add persistent storage if needed (for uploads/processed directories)

#### Important Note for Render Free Tier

The free tier spins down after 15 minutes of inactivity. The first request after spin-down will take 30-60 seconds to wake up the service. For production use, consider the paid tier.

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | Yes | PostgreSQL connection string with SSL | `postgresql://user:pass@host.neon.tech/db?sslmode=require` |
| `FLASK_SECRET_KEY` | Yes | Secret key for session encryption | `abc123xyz789...` (32+ characters) |
| `PORT` | No | Port for the application to listen on | `8080` (default) |
| `GUNICORN_WORKERS` | No | Number of Gunicorn worker processes | `4` (default) |
| `GUNICORN_TIMEOUT` | No | Request timeout in seconds | `120` (default) |

## Generating Secure Secrets

Generate a secure `FLASK_SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Or use OpenSSL:

```bash
openssl rand -hex 32
```

## Troubleshooting

### Build Errors

#### Error: "Could not find a version that satisfies the requirement dlib"

**Cause**: System dependencies for dlib are missing or incompatible.

**Solution**:
1. Verify the Dockerfile includes these packages:
   ```dockerfile
   RUN apt-get update && apt-get install -y \
       build-essential \
       cmake \
       libgl1 \
       libglib2.0-0
   ```

2. Ensure system dependencies are installed BEFORE Python packages

3. Try building with `--no-cache`:
   ```bash
   docker build --no-cache -t picme:latest .
   ```

#### Error: "COPY failed: file not found"

**Cause**: Required files are missing or .dockerignore is excluding necessary files.

**Solution**:
1. Verify all required files exist:
   - `backend/app.py`
   - `backend/requirements.txt`
   - `backend/shape_predictor_68_face_landmarks.dat`

2. Check `.dockerignore` isn't excluding necessary files

3. Ensure you're running `docker build` from the project root directory

#### Error: "failed to solve with frontend dockerfile.v0"

**Cause**: Syntax error in Dockerfile or Docker version incompatibility.

**Solution**:
1. Update Docker to the latest version
2. Check Dockerfile syntax for errors
3. Ensure line endings are Unix-style (LF, not CRLF)

### Runtime Errors

#### Error: "Address already in use" or "Port 8080 is already allocated"

**Cause**: Another process is using port 8080.

**Solution**:
1. Stop the conflicting container:
   ```bash
   docker ps
   docker stop <container-id>
   ```

2. Or use a different port:
   ```bash
   docker run -p 8081:8080 -e PORT=8080 picme:latest
   ```

#### Error: "Missing environment variable: DATABASE_URL"

**Cause**: Required environment variables not provided to container.

**Solution**:
1. Verify environment variables are set:
   ```bash
   docker run -p 8080:8080 \
     -e DATABASE_URL="your-database-url" \
     -e FLASK_SECRET_KEY="your-secret-key" \
     picme:latest
   ```

2. Or use an env file:
   ```bash
   docker run -p 8080:8080 --env-file .env.docker picme:latest
   ```

3. Check for typos in variable names (case-sensitive)

#### Error: Container starts but immediately exits

**Cause**: Application crashes during startup.

**Solution**:
1. Check container logs:
   ```bash
   docker logs <container-id>
   ```

2. Run container interactively to debug:
   ```bash
   docker run -it --entrypoint /bin/bash picme:latest
   ```

3. Verify all environment variables are set correctly

4. Check for Python import errors or missing dependencies

### Database Connection Issues

#### Error: "could not connect to server: Connection refused"

**Cause**: Database host is unreachable or connection string is incorrect.

**Solution**:
1. Verify DATABASE_URL format:
   ```
   postgresql://username:password@host:port/database?sslmode=require
   ```

2. Test connection from your local machine:
   ```bash
   psql "postgresql://user:pass@host.neon.tech/db?sslmode=require"
   ```

3. Check firewall rules allow connections from your container/cloud platform

4. Verify Neon database is running and accessible

#### Error: "SSL connection has been closed unexpectedly"

**Cause**: SSL/TLS configuration issue with database connection.

**Solution**:
1. Ensure `sslmode=require` is in DATABASE_URL:
   ```
   postgresql://user:pass@host.neon.tech/db?sslmode=require
   ```

2. For Neon databases, SSL is required - never use `sslmode=disable`

3. Check that psycopg2 is installed (not psycopg2-binary in production)

#### Error: "password authentication failed for user"

**Cause**: Incorrect database credentials.

**Solution**:
1. Verify username and password in DATABASE_URL
2. Check for special characters that need URL encoding:
   - `@` → `%40`
   - `:` → `%3A`
   - `/` → `%2F`

3. Reset database password in Neon dashboard if needed

### Face Recognition Issues

#### Error: "shape_predictor_68_face_landmarks.dat not found"

**Cause**: Face recognition model file is missing from the Docker image.

**Solution**:
1. Verify the file exists in `backend/` directory before building

2. Check that Dockerfile copies the backend directory:
   ```dockerfile
   COPY backend /app
   ```

3. Rebuild the image:
   ```bash
   docker build --no-cache -t picme:latest .
   ```

#### Error: "RuntimeError: Unable to open shape_predictor_68_face_landmarks.dat"

**Cause**: Model file is corrupted or incomplete.

**Solution**:
1. Re-download the model file from dlib's official source

2. Verify file size (approximately 99.7 MB)

3. Check file permissions in the container:
   ```bash
   docker exec picme-container ls -lh /app/shape_predictor_68_face_landmarks.dat
   ```

#### Error: Face recognition is very slow or times out

**Cause**: Insufficient resources or Gunicorn timeout too short.

**Solution**:
1. Increase Gunicorn timeout:
   ```bash
   docker run -p 8080:8080 \
     -e GUNICORN_TIMEOUT=300 \
     picme:latest
   ```

2. Allocate more memory to Docker (Docker Desktop settings)

3. For cloud platforms, upgrade to a higher tier with more CPU/RAM

4. Consider processing face recognition asynchronously with a task queue

### Cloud Platform Specific Issues

#### Vessel: "Build failed: out of memory"

**Solution**:
- Optimize Dockerfile to reduce memory usage during build
- Remove unnecessary files with .dockerignore
- Contact Vessel support for build resource limits

#### Railway: "Application failed to respond"

**Solution**:
- Check that PORT environment variable matches the exposed port
- Verify Gunicorn is binding to `0.0.0.0`, not `127.0.0.1`
- Check Railway logs for specific error messages

#### Render: "Service is unavailable" (Free Tier)

**Solution**:
- Free tier spins down after inactivity - wait 30-60 seconds for wake-up
- First request after spin-down will be slow
- Consider upgrading to paid tier for always-on service

## Performance Optimization

### Image Size Optimization

Current image size should be approximately 1.5-2 GB. To reduce:

1. Use multi-stage builds (advanced)
2. Remove unnecessary files with .dockerignore
3. Clean up apt cache (already done in Dockerfile)
4. Use alpine-based images (requires significant changes)

### Application Performance

1. **Increase Gunicorn workers** for better concurrency:
   ```bash
   docker run -e GUNICORN_WORKERS=8 picme:latest
   ```

2. **Enable connection pooling** for database (modify app.py)

3. **Use CDN** for static assets (frontend files)

4. **Implement caching** for face recognition results

## Monitoring and Logs

### View Container Logs

```bash
# Follow logs in real-time
docker logs -f picme-container

# View last 100 lines
docker logs --tail 100 picme-container

# View logs with timestamps
docker logs -t picme-container
```

### Monitor Resource Usage

```bash
# View resource usage
docker stats picme-container

# View detailed container info
docker inspect picme-container
```

### Cloud Platform Monitoring

- **Vessel**: Built-in metrics dashboard
- **Railway**: Metrics tab shows CPU, memory, network
- **Render**: Metrics available in service dashboard

## Security Best Practices

1. **Never commit secrets** to Git:
   - Add `.env.docker` to `.gitignore`
   - Use platform secret management for production

2. **Rotate secrets regularly**:
   - Change `FLASK_SECRET_KEY` periodically
   - Update database passwords

3. **Use HTTPS** for all production deployments:
   - All recommended platforms provide automatic SSL

4. **Keep dependencies updated**:
   - Regularly update `requirements.txt`
   - Rebuild Docker image with latest security patches

5. **Limit file upload sizes** in production

6. **Implement rate limiting** for API endpoints

## Support and Resources

- **Docker Documentation**: https://docs.docker.com
- **Vessel Documentation**: https://docs.vessel.land
- **Railway Documentation**: https://docs.railway.app
- **Render Documentation**: https://render.com/docs
- **Neon Documentation**: https://neon.tech/docs

For application-specific issues, check the project repository or contact the development team.

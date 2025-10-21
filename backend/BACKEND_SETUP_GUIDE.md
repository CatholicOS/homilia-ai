# Homilia AI Backend Setup Guide

This guide provides step-by-step instructions for setting up the Homilia AI backend service on your local development environment.

## Prerequisites

Before starting, ensure you have the following installed:

### Required Software
- **Python 3.8+** - Download from [python.org](https://www.python.org/downloads/)
- **Docker Desktop** - Download from [docker.com](https://www.docker.com/products/docker-desktop/)
- **Git** - Download from [git-scm.com](https://git-scm.com/downloads)

### Required API Keys and Services
- **OpenAI API Key** - Get from [platform.openai.com](https://platform.openai.com/api-keys)
- **AWS Account** with S3 access - Sign up at [aws.amazon.com](https://aws.amazon.com/)
- **AWS S3 Bucket** - Create a bucket for storing documents

## Step 1: Clone and Navigate to Project

```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd homilia-ai/backend
```

## Step 2: Create Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
venv\Scripts\Activate.ps1

# On Windows (Command Prompt):
venv\Scripts\activate.bat

# On macOS/Linux:
source venv/bin/activate
```

**Note:** You should see `(venv)` in your terminal prompt when the virtual environment is active.

## Step 3: Install Python Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

This will install all necessary packages including:
- FastAPI for the web framework
- OpenAI for AI capabilities
- OpenSearch client for search functionality
- AWS SDK (boto3) for S3 integration
- And other dependencies

## Step 4: Configure Environment Variables

1. **Copy the environment template:**
   ```bash
   copy env.example .env
   ```

2. **Edit the `.env` file** with your actual configuration values:

   ```env
   # OpenAI Configuration (REQUIRED)
   OPENAI_API_KEY=sk-your-actual-openai-api-key-here
   
   # AWS S3 Configuration (REQUIRED)
   AWS_ACCESS_KEY_ID=your-actual-aws-access-key
   AWS_SECRET_ACCESS_KEY=your-actual-aws-secret-key
   AWS_REGION=us-east-1
   S3_BUCKET_NAME=your-actual-bucket-name
   
   # OpenSearch Configuration (Default values work for local development)
   OPENSEARCH_HOST=localhost
   OPENSEARCH_PORT=9200
   OPENSEARCH_USERNAME=admin
   OPENSEARCH_PASSWORD=admin
   OPENSEARCH_USE_SSL=false
   OPENSEARCH_SECURITY_DISABLED=true
   
   # Application Configuration
   DEBUG=true
   LOG_LEVEL=INFO
   HOST=0.0.0.0
   PORT=8000
   ```

### Getting Your API Keys

#### OpenAI API Key
1. Go to [platform.openai.com](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)
5. Add it to your `.env` file

#### AWS S3 Configuration
1. Go to [AWS Console](https://console.aws.amazon.com/)
2. Navigate to IAM → Users → Create User
3. Attach the `AmazonS3FullAccess` policy
4. Create access keys for the user
5. Create an S3 bucket for storing documents
6. Add the credentials and bucket name to your `.env` file

## Step 5: Start Docker Desktop and OpenSearch

1. **Start Docker Desktop:**
   - Launch Docker Desktop application
   - Wait for it to fully start (green status indicator)

2. **Start OpenSearch services:**
   ```bash
   # From the backend directory
   docker-compose up -d
   ```

   This will start:
   - OpenSearch cluster (2 nodes)
   - OpenSearch Dashboards (for monitoring)

3. **Verify OpenSearch is running:**
   ```bash
   # Check if containers are running
   docker-compose ps
   
   # Test OpenSearch connection
   curl http://localhost:9200
   ```

   You should see a JSON response with cluster information.

## Step 6: Initialize OpenSearch Index

```bash
# Run the setup script to create the required index
python setup-scripts/init_opensearch_index.py
```

This script will:
- Connect to OpenSearch
- Create the `parish_docs` index with proper mapping
- Test the index functionality
- Insert a sample document

**Expected output:**
```
🚀 Initializing OpenSearch Index for Parish Documents
============================================================
📡 Connecting to OpenSearch...
✅ Connected to OpenSearch cluster: opensearch-cluster
📋 Version: 2.x.x
🏗️  Creating parish_docs index...
✅ Index 'parish_docs' created successfully!
🧪 Testing index functionality...
✅ Test document inserted: created
✅ Test document retrieved successfully
🎉 OpenSearch index initialization completed successfully!
```

## Step 7: Start the Backend Server

```bash
# Start the FastAPI server
python main.py
```

**Alternative start methods:**
```bash
# Using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Or with specific configuration
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info
```

**Expected output:**
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## Step 8: Verify Backend is Working

1. **Check the API documentation:**
   - Open your browser and go to: `http://localhost:8000/docs`
   - You should see the FastAPI interactive documentation

2. **Test the health endpoint:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Test the root endpoint:**
   ```bash
   curl http://localhost:8000/
   ```

## Service URLs

Once everything is running, you can access:

- **Backend API:** `http://localhost:8000`
- **API Documentation:** `http://localhost:8000/docs`
- **OpenSearch:** `http://localhost:9200`
- **OpenSearch Dashboards:** `http://localhost:5601`

## Troubleshooting

### Common Issues and Solutions

#### 1. Docker Desktop Not Starting
**Problem:** Docker Desktop fails to start or shows errors.

**Solutions:**
- Ensure virtualization is enabled in BIOS
- Restart your computer
- Check Windows features: Enable "Windows Subsystem for Linux" and "Virtual Machine Platform"
- Run Docker Desktop as administrator

#### 2. OpenSearch Connection Failed
**Problem:** `init_opensearch_index.py` fails to connect to OpenSearch.

**Solutions:**
```bash
# Check if OpenSearch containers are running
docker-compose ps

# Check OpenSearch logs
docker-compose logs opensearch-node1

# Restart OpenSearch services
docker-compose down
docker-compose up -d

# Wait a few minutes for OpenSearch to fully initialize
```

#### 3. Python Virtual Environment Issues
**Problem:** Package installation fails or import errors.

**Solutions:**
```bash
# Ensure virtual environment is activated
# You should see (venv) in your prompt

# Upgrade pip
python -m pip install --upgrade pip

# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

#### 4. OpenAI API Key Issues
**Problem:** OpenAI API calls fail with authentication errors.

**Solutions:**
- Verify your API key is correct in `.env` file
- Check if you have sufficient credits in your OpenAI account
- Ensure the API key has the necessary permissions

#### 5. AWS S3 Access Issues
**Problem:** S3 operations fail with access denied errors.

**Solutions:**
- Verify AWS credentials are correct
- Check S3 bucket permissions
- Ensure the AWS user has `AmazonS3FullAccess` policy
- Verify the bucket name exists and is accessible

#### 6. Port Already in Use
**Problem:** Port 8000 or 9200 is already in use.

**Solutions:**
```bash
# Find what's using the port
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or change the port in .env file
PORT=8001
```

### Getting Help

If you encounter issues not covered here:

1. **Check the logs:**
   ```bash
   # Backend logs
   python main.py
   
   # Docker logs
   docker-compose logs
   ```

2. **Verify all services are running:**
   ```bash
   # Check Docker containers
   docker-compose ps
   
   # Check if ports are open
   netstat -ano | findstr :8000
   netstat -ano | findstr :9200
   ```

3. **Test individual components:**
   ```bash
   # Test OpenSearch
   curl http://localhost:9200
   
   # Test backend
   curl http://localhost:8000/health
   ```

## Next Steps

Once your backend is running successfully:

1. **Upload Documents:** Use the `/documents/upload` endpoint to upload parish documents
2. **Process Documents:** Use the `/documents/process` endpoint to extract text and create embeddings
3. **Search Documents:** Use the `/search` endpoint to perform semantic searches
4. **Test AI Agent:** Use the `/agent/chat` endpoint to interact with the AI assistant

## Development Tips

- **Hot Reload:** The server runs with `--reload` flag, so changes to Python files will automatically restart the server
- **Logs:** Check the terminal output for detailed logs and error messages
- **API Testing:** Use the interactive docs at `http://localhost:8000/docs` to test endpoints
- **OpenSearch Monitoring:** Use OpenSearch Dashboards at `http://localhost:5601` to monitor your data

## Production Considerations

For production deployment:

1. **Security:** Change default passwords and enable SSL
2. **Environment Variables:** Use secure secret management
3. **Scaling:** Configure OpenSearch cluster for production load
4. **Monitoring:** Set up proper logging and monitoring
5. **Backup:** Implement regular backups of OpenSearch data

---

**Need Help?** If you're still having issues, check the troubleshooting section above or review the error logs for specific error messages.

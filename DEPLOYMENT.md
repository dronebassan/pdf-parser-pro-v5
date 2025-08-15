# PDF Parser Pro - Deployment Guide

## Overview
This guide covers deployment options for PDF Parser Pro, from local development to production cloud deployment.

## 🚀 Quick Start with Docker

### Prerequisites
- Docker & Docker Compose installed
- At least 4GB RAM available
- LLM API keys (optional but recommended)

### 1. Clone and Setup
```bash
cd /path/to/pdf_parser
cp .env.example .env
# Edit .env with your API keys and settings
```

### 2. Start Services
```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f pdf-parser

# Health check
curl http://localhost/health-check/
```

### 3. Access Application
- **Web Interface**: http://localhost
- **API Documentation**: http://localhost/docs
- **Performance Stats**: http://localhost/performance-stats/

## 🏗️ Local Development Setup

### Prerequisites
- Python 3.11+
- Tesseract OCR
- Redis (optional)
- PostgreSQL (optional)

### Installation
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Tesseract (Ubuntu/Debian)
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# Install Tesseract (macOS)
brew install tesseract

# Install Tesseract (Windows)
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

### Environment Setup
```bash
cp .env.example .env
# Edit .env with your configuration

# Set API keys
export OPENAI_API_KEY="your_key_here"
export ANTHROPIC_API_KEY="your_key_here"
```

### Start Development Server
```bash
uvicorn main:app --reload --port 8000
```

## ☁️ Cloud Deployment

### AWS Deployment

#### Option 1: ECS with Fargate
```bash
# Build and push to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-west-2.amazonaws.com
docker build -t pdf-parser-pro .
docker tag pdf-parser-pro:latest 123456789012.dkr.ecr.us-west-2.amazonaws.com/pdf-parser-pro:latest
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/pdf-parser-pro:latest

# Deploy using ECS task definition
aws ecs update-service --cluster pdf-parser-cluster --service pdf-parser-service --force-new-deployment
```

#### Option 2: EC2 with Docker
```bash
# On EC2 instance
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Clone repository
git clone https://your-repo/pdf_parser.git
cd pdf_parser

# Setup environment
cp .env.example .env
# Edit .env with production values

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

### Google Cloud Platform

#### Cloud Run Deployment
```bash
# Build and submit
gcloud builds submit --tag gcr.io/PROJECT_ID/pdf-parser-pro

# Deploy to Cloud Run
gcloud run deploy pdf-parser-pro \
  --image gcr.io/PROJECT_ID/pdf-parser-pro \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 900 \
  --set-env-vars OPENAI_API_KEY=$OPENAI_API_KEY,ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
```

### Azure Deployment

#### Container Instances
```bash
# Create resource group
az group create --name pdf-parser-rg --location eastus

# Deploy container
az container create \
  --resource-group pdf-parser-rg \
  --name pdf-parser-pro \
  --image your-registry/pdf-parser-pro:latest \
  --cpu 2 \
  --memory 4 \
  --dns-name-label pdf-parser-pro \
  --ports 8000 \
  --environment-variables OPENAI_API_KEY=$OPENAI_API_KEY ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
```

## 🔧 Production Configuration

### Environment Variables
```bash
# Core settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=warning

# Security
SECRET_KEY=your_very_secure_secret_key_here
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Performance
WORKER_PROCESSES=4
WORKER_TIMEOUT=300
MAX_FILE_SIZE=100MB

# Database (recommended for production)
DATABASE_URL=postgresql://user:pass@host:5432/pdf_parser

# Redis (recommended for caching)
REDIS_URL=redis://host:6379/0

# Monitoring
ENABLE_METRICS=true
```

### SSL/HTTPS Setup
```bash
# Using Let's Encrypt with Certbot
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# Update nginx.conf to enable SSL server block
# Restart nginx
sudo systemctl restart nginx
```

### Database Setup (Optional but Recommended)
```sql
-- PostgreSQL setup
CREATE DATABASE pdf_parser;
CREATE USER pdf_parser_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE pdf_parser TO pdf_parser_user;
```

### Redis Setup (Optional but Recommended)
```bash
# Install Redis
sudo apt-get install redis-server

# Configure Redis for production
sudo vim /etc/redis/redis.conf
# Set: bind 127.0.0.1
# Set: requirepass your_redis_password

sudo systemctl restart redis
```

## 📊 Monitoring & Logging

### Health Checks
The application provides several health check endpoints:
- `/health-check/` - Overall service health
- `/api/info` - Service capabilities and version
- `/performance-stats/` - Performance metrics

### Logging
Logs are structured and include:
- Request/response logging
- Performance metrics
- Error tracking
- LLM API usage

### Metrics Collection
Enable metrics collection by setting:
```bash
ENABLE_METRICS=true
METRICS_PORT=9090
```

## 🔒 Security Considerations

### API Keys Security
- Never commit API keys to version control
- Use environment variables or secret management services
- Rotate keys regularly
- Monitor API usage for anomalies

### File Upload Security
- File size limits enforced
- Only PDF files accepted
- Temporary files cleaned up
- Sandboxed processing

### Network Security
- Rate limiting enabled
- CORS configured
- Security headers set
- SSL/TLS encryption

## 🚨 Troubleshooting

### Common Issues

#### OCR Not Working
```bash
# Check Tesseract installation
tesseract --version

# Install additional languages
sudo apt-get install tesseract-ocr-fra tesseract-ocr-deu
```

#### LLM API Errors
```bash
# Check API key configuration
curl -X GET "http://localhost:8000/health-check/"

# Monitor API usage
tail -f logs/app.log | grep "LLM"
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# Monitor processing times
curl "http://localhost:8000/performance-stats/"

# Adjust worker processes
export WORKER_PROCESSES=8
```

#### Memory Issues
```bash
# Increase Docker memory limits
# In docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 8G
```

### Debug Mode
```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=debug

# Restart application
docker-compose restart pdf-parser
```

## 📈 Scaling

### Horizontal Scaling
- Deploy multiple instances behind load balancer
- Use Redis for session storage
- Database connection pooling
- File storage on shared volume/S3

### Performance Optimization
- Adjust worker processes based on CPU cores
- Enable Redis caching
- Use CDN for static files
- Optimize Docker image size

### Cost Optimization
- Monitor LLM API usage
- Implement usage quotas
- Use spot instances where appropriate
- Cache frequent requests

## 🔄 Updates & Maintenance

### Application Updates
```bash
# Pull latest changes
git pull origin main

# Rebuild and deploy
docker-compose build --no-cache
docker-compose up -d

# Run database migrations (if applicable)
docker-compose exec pdf-parser alembic upgrade head
```

### Backup Strategy
- Database backups (if using persistent storage)
- Configuration files backup
- SSL certificates backup
- Performance metrics export

### Monitoring Checklist
- [ ] Health checks passing
- [ ] Error rates acceptable
- [ ] Response times normal
- [ ] API key usage within limits
- [ ] Disk space sufficient
- [ ] Memory usage stable
- [ ] Security updates applied
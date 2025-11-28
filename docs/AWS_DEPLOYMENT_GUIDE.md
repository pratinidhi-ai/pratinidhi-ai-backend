# AWS App Runner Deployment & Debugging Guide

## Quick Reference

| Resource | Value |
|----------|-------|
| **Service ARN** | `arn:aws:apprunner:us-east-1:613820096948:service/Backend-AppRunner/20c56a0386754f7b8d196151179e2566` |
| **Service URL** | `https://mvh38xybk8.us-east-1.awsapprunner.com` |
| **ECR Repository** | `613820096948.dkr.ecr.us-east-1.amazonaws.com/backend-containers` |
| **Region** | `us-east-1` |

---

## 1. Deployment Commands

### Build and Deploy (Full Process)
```powershell
# Run the deployment script (builds, tags, and pushes to ECR)
.\deploy-aws.ps1
```

### Manual Build & Push
```powershell
# Build Docker image (use --no-cache when dependencies change)
docker build --no-cache -t backend-containers:latest .

# Tag for ECR
docker tag backend-containers:latest 613820096948.dkr.ecr.us-east-1.amazonaws.com/backend-containers:latest

# Authenticate Docker with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 613820096948.dkr.ecr.us-east-1.amazonaws.com

# Push to ECR
docker push 613820096948.dkr.ecr.us-east-1.amazonaws.com/backend-containers:latest
```

### Trigger Deployment on App Runner
```powershell
# Start a new deployment (after pushing new image to ECR)
aws apprunner start-deployment --service-arn "arn:aws:apprunner:us-east-1:613820096948:service/Backend-AppRunner/20c56a0386754f7b8d196151179e2566" --region us-east-1
```

---

## 2. Check Service Status

### Current Service Status
```powershell
aws apprunner describe-service --service-arn "arn:aws:apprunner:us-east-1:613820096948:service/Backend-AppRunner/20c56a0386754f7b8d196151179e2566" --region us-east-1 --query "Service.Status"
```

**Possible Status Values:**
- `RUNNING` - Service is healthy and running
- `OPERATION_IN_PROGRESS` - Deployment or update in progress
- `CREATE_FAILED` - Service creation failed
- `DELETE_FAILED` - Service deletion failed
- `DELETED` - Service has been deleted
- `PAUSED` - Service is paused

### Full Service Details
```powershell
aws apprunner describe-service --service-arn "arn:aws:apprunner:us-east-1:613820096948:service/Backend-AppRunner/20c56a0386754f7b8d196151179e2566" --region us-east-1
```

### Service URL and Status (Quick Check)
```powershell
aws apprunner describe-service --service-arn "arn:aws:apprunner:us-east-1:613820096948:service/Backend-AppRunner/20c56a0386754f7b8d196151179e2566" --region us-east-1 --query "Service.{Status: Status, ServiceUrl: ServiceUrl, AutoDeploymentsEnabled: SourceConfiguration.AutoDeploymentsEnabled}"
```

---

## 3. View Logs

### Application Logs (Last 50 entries)
```powershell
aws logs filter-log-events --log-group-name "/aws/apprunner/Backend-AppRunner/20c56a0386754f7b8d196151179e2566/application" --region us-east-1 --limit 50 --query "events[*].message"
```

### Application Logs (Last 30 minutes)
```powershell
aws logs filter-log-events --log-group-name "/aws/apprunner/Backend-AppRunner/20c56a0386754f7b8d196151179e2566/application" --region us-east-1 --start-time ([DateTimeOffset]::Now.AddMinutes(-30).ToUnixTimeMilliseconds()) --query "events[*].message"
```

### Application Logs (Last 1 hour)
```powershell
aws logs filter-log-events --log-group-name "/aws/apprunner/Backend-AppRunner/20c56a0386754f7b8d196151179e2566/application" --region us-east-1 --start-time ([DateTimeOffset]::Now.AddHours(-1).ToUnixTimeMilliseconds()) --query "events[*].message"
```

### Service/System Logs
```powershell
aws logs filter-log-events --log-group-name "/aws/apprunner/Backend-AppRunner/20c56a0386754f7b8d196151179e2566/service" --region us-east-1 --limit 50 --query "events[*].message"
```

### Search Logs for Errors
```powershell
aws logs filter-log-events --log-group-name "/aws/apprunner/Backend-AppRunner/20c56a0386754f7b8d196151179e2566/application" --region us-east-1 --filter-pattern "ERROR" --limit 30 --query "events[*].message"
```

### Search Logs for Specific Text
```powershell
aws logs filter-log-events --log-group-name "/aws/apprunner/Backend-AppRunner/20c56a0386754f7b8d196151179e2566/application" --region us-east-1 --filter-pattern "Failed to load" --limit 30 --query "events[*].message"
```

---

## 4. ECR Image Information

### List Images in Repository
```powershell
aws ecr describe-images --repository-name backend-containers --region us-east-1 --query "imageDetails[*].{pushedAt: imagePushedAt, sizeBytes: imageSizeInBytes, tags: imageTags}" --output table
```

### Check Latest Image Push Time
```powershell
aws ecr describe-images --repository-name backend-containers --region us-east-1 --query "imageDetails | sort_by(@, &imagePushedAt) | [-1].{pushedAt: imagePushedAt, digest: imageDigest, tags: imageTags}"
```

### Get Image Digest (for verification)
```powershell
aws ecr describe-images --repository-name backend-containers --region us-east-1 --image-ids imageTag=latest --query "imageDetails[0].imageDigest"
```

---

## 5. Deployment History

### Recent Deployments (Last 5)
```powershell
aws apprunner list-operations --service-arn "arn:aws:apprunner:us-east-1:613820096948:service/Backend-AppRunner/20c56a0386754f7b8d196151179e2566" --region us-east-1 --query "OperationSummaryList[0:5].{Id: Id, Type: Type, Status: Status, StartedAt: StartedAt, EndedAt: EndedAt}" --output table
```

### All Operations
```powershell
aws apprunner list-operations --service-arn "arn:aws:apprunner:us-east-1:613820096948:service/Backend-AppRunner/20c56a0386754f7b8d196151179e2566" --region us-east-1
```

---

## 6. Health Checks

### Test Root Endpoint
```powershell
Invoke-RestMethod -Uri "https://mvh38xybk8.us-east-1.awsapprunner.com/" -Method Get
```

### Test Health Endpoint
```powershell
Invoke-RestMethod -Uri "https://mvh38xybk8.us-east-1.awsapprunner.com/health" -Method Get
```

### Check if Docs Load (verifies all routers loaded)
```powershell
Invoke-WebRequest -Uri "https://mvh38xybk8.us-east-1.awsapprunner.com/docs" -Method Get | Select-Object StatusCode
```

---

## 7. Common Issues & Fixes

### Issue: `No module named 'xyz'`
**Cause:** Missing Python package in Docker image  
**Fix:** 
1. Add package to `requirements.txt`
2. Rebuild with `--no-cache`: `docker build --no-cache -t backend-containers:latest .`
3. Push and redeploy

### Issue: `No module named 'pkg_resources'`
**Cause:** Python 3.12+ slim images don't include setuptools  
**Fix:** Ensure Dockerfile has: `RUN pip install --no-cache-dir setuptools && pip install --no-cache-dir -r requirements.txt`

### Issue: Routes returning 404 but root works
**Cause:** Routers failed to load during startup  
**Debug:** Check logs for `Failed to load routers` error message
```powershell
aws logs filter-log-events --log-group-name "/aws/apprunner/Backend-AppRunner/20c56a0386754f7b8d196151179e2566/application" --region us-east-1 --filter-pattern "Failed to load routers" --limit 10 --query "events[*].message"
```

### Issue: Old code still running after merge
**Cause:** Docker image not rebuilt/pushed, or App Runner not redeployed  
**Fix:**
1. Check when last image was pushed (see ECR commands above)
2. Rebuild with `--no-cache` if dependencies changed
3. Push to ECR
4. Trigger deployment: `aws apprunner start-deployment ...`

### Issue: Deployment stuck in `OPERATION_IN_PROGRESS`
**Debug:** Wait 5-10 minutes. If still stuck, check service logs:
```powershell
aws logs filter-log-events --log-group-name "/aws/apprunner/Backend-AppRunner/20c56a0386754f7b8d196151179e2566/service" --region us-east-1 --start-time ([DateTimeOffset]::Now.AddMinutes(-15).ToUnixTimeMilliseconds()) --query "events[*].message"
```

---

## 8. Pause/Resume Service (Cost Saving)

### Pause Service
```powershell
aws apprunner pause-service --service-arn "arn:aws:apprunner:us-east-1:613820096948:service/Backend-AppRunner/20c56a0386754f7b8d196151179e2566" --region us-east-1
```

### Resume Service
```powershell
aws apprunner resume-service --service-arn "arn:aws:apprunner:us-east-1:613820096948:service/Backend-AppRunner/20c56a0386754f7b8d196151179e2566" --region us-east-1
```

---

## 9. Local Testing Before Deploy

### Run Locally with Docker
```powershell
docker build -t backend-containers:latest .
docker run -p 8080:8080 --env-file .env backend-containers:latest
```

### Test Import (Quick Check)
```powershell
C:/Users/shash/PycharmProjects/pratinidhi-ai-backend/.venv/Scripts/python.exe -c "import app; print('App loaded successfully')"
```

---

## 10. Useful AWS Console Links

- **App Runner Console:** https://us-east-1.console.aws.amazon.com/apprunner/home?region=us-east-1
- **ECR Console:** https://us-east-1.console.aws.amazon.com/ecr/repositories?region=us-east-1
- **CloudWatch Logs:** https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups

---

## Quick Deployment Checklist

1. ☐ Make code changes
2. ☐ Test locally: `python -c "import app"`
3. ☐ Build image: `docker build --no-cache -t backend-containers:latest .`
4. ☐ Push to ECR: `docker push 613820096948.dkr.ecr.us-east-1.amazonaws.com/backend-containers:latest`
5. ☐ Trigger deployment: `aws apprunner start-deployment ...`
6. ☐ Wait for status `RUNNING`
7. ☐ Test health endpoint
8. ☐ Check logs for errors


$Region = "us-east-1"
$AccountId = "613820096948"
$RepositoryName = "backend-containers"   
$ImageTag = "latest"        
$ImageName = "${RepositoryName}:${ImageTag}"
$EcrUri = "${AccountId}.dkr.ecr.${Region}.amazonaws.com/${RepositoryName}"

Write-Host "🚀 Starting ECR Push Process..." -ForegroundColor Cyan

# ======= STEP 1: AWS Login =======
Write-Host "🔐 Logging into AWS..."
aws sts get-caller-identity | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  AWS CLI not logged in. Please run 'aws configure' to set your credentials." -ForegroundColor Yellow
    exit 1
}

# ======= STEP 2: Authenticate Docker to ECR =======
Write-Host "🔐 Authenticating Docker to ECR..."
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "${AccountId}.dkr.ecr.${Region}.amazonaws.com"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker login failed. Check your AWS credentials or permissions." -ForegroundColor Red
    exit 1
}

# ======= STEP 3: Create ECR Repo (if not exists) =======
Write-Host "📦 Ensuring ECR Repository '$RepositoryName' exists..."
aws ecr describe-repositories --repository-names $RepositoryName --region $Region | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "📁 Repository not found. Creating new ECR repository..."
    aws ecr create-repository --repository-name $RepositoryName --region $Region | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create repository." -ForegroundColor Red
        exit 1
    }
}

# ======= STEP 4: Build Docker Image =======
Write-Host "🐳 Building Docker image '$ImageName'..."
docker build -t $ImageName .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed." -ForegroundColor Red
    exit 1
}

# ======= STEP 5: Tag Docker Image =======
Write-Host "🏷️  Tagging image as '${EcrUri}:${ImageTag}'..."
docker tag $ImageName "${EcrUri}:${ImageTag}"

# ======= STEP 6: Push Docker Image =======
Write-Host "⬆️  Pushing image to ECR..."
docker push "${EcrUri}:${ImageTag}"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Successfully pushed ${EcrUri}:${ImageTag}" -ForegroundColor Green
} else {
    Write-Host "❌ Push failed." -ForegroundColor Red
    exit 1
}

Write-Host "🎉 All Done!"

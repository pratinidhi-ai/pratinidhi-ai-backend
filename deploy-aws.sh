#!/bin/bash

Region="us-east-1"
AccountId="613820096948"
RepositoryName="backend-containers"
ImageTag="latest"
ImageName="${RepositoryName}:${ImageTag}"
EcrUri="${AccountId}.dkr.ecr.${Region}.amazonaws.com/${RepositoryName}"

echo "Starting ECR Push Process..."

# ======= STEP 1: AWS Login =======
echo "Logging into AWS..."
aws sts get-caller-identity > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "⚠️ AWS CLI not logged in. Please run 'aws configure' to set your credentials."
    exit 1
fi

# ======= STEP 2: Authenticate Docker to ECR =======
echo "Authenticating Docker to ECR..."
aws ecr get-login-password --region "$Region" | docker login --username AWS --password-stdin "${AccountId}.dkr.ecr.${Region}.amazonaws.com"
if [ $? -ne 0 ]; then
    echo "❌ Docker login failed. Check your AWS credentials or permissions."
    exit 1
fi

# ======= STEP 3: Create ECR Repo (if not exists) =======
echo "Ensuring ECR Repository '$RepositoryName' exists..."
aws ecr describe-repositories --repository-names "$RepositoryName" --region "$Region" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "📁 Repository not found. Creating new ECR repository..."
    aws ecr create-repository --repository-name "$RepositoryName" --region "$Region" > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create repository."
        exit 1
    fi
fi

# ======= STEP 4: Build Docker Image =======
echo "Building Docker image '$ImageName'..."
docker build -t "$ImageName" .
if [ $? -ne 0 ]; then
    echo "❌ Docker build failed."
    exit 1
fi

# ======= STEP 5: Tag Docker Image =======
echo "Tagging image as '${EcrUri}:${ImageTag}'..."
docker tag "$ImageName" "${EcrUri}:${ImageTag}"

# ======= STEP 6: Push Docker Image =======
echo "Pushing image to ECR..."
docker push "${EcrUri}:${ImageTag}"
if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed ${EcrUri}:${ImageTag}"
else
    echo "❌ Push failed."
    exit 1
fi

echo "All Done!"

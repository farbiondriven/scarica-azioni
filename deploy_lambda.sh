#!/bin/bash
# Deploy script for AWS Lambda

set -e

echo "Building Lambda deployment package..."

# Create deployment directory
rm -rf lambda-package
mkdir -p lambda-package

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -t lambda-package/

# Copy source code
echo "Copying source code..."
cp lambda_handler.py lambda-package/
cp titoli_check.txt lambda-package/

# Copy SMTP config if it exists
if [ -f "smtp_config.json" ]; then
    echo "Including smtp_config.json..."
    cp smtp_config.json lambda-package/
else
    echo "Note: smtp_config.json not found. Email functionality will be disabled."
fi

# Create zip file
echo "Creating deployment package..."
cd lambda-package
zip -r ../lambda-deployment.zip . -q
cd ..

echo "✅ Deployment package created: lambda-deployment.zip"
echo ""
echo "To deploy to AWS Lambda:"
echo "  aws lambda update-function-code \\"
echo "    --function-name scarica-azioni \\"
echo "    --zip-file fileb://lambda-deployment.zip"
echo ""
echo "Handler: lambda_handler.handler"
echo ""
echo "Or upload lambda-deployment.zip manually via AWS Console"

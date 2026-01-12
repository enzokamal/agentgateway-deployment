#!/bin/bash

# AgentGateway Helm Deployment Script
# This script deploys the AgentGateway system using Helm following the README instructions
# Usage: ./helm-deployment.sh [namespace] [environment]
# Default: namespace=agentgateway-system, environment=dev

set -e  # Exit on any error

# Parse arguments
NAMESPACE=${1:-agentgateway-system}
ENVIRONMENT=${2:-dev}
RELEASE_NAME=agentgateway-$ENVIRONMENT

# Determine values file
VALUES_FILE=""
if [ "$ENVIRONMENT" = "prod" ]; then
    VALUES_FILE="-f values-prod.yaml"
fi

echo "Starting AgentGateway deployment in namespace '$NAMESPACE' for environment '$ENVIRONMENT'..."

# Step 1: Install Required CRDs
echo "Step 1: Installing required CRDs..."

echo "Installing Gateway API CRDs..."
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.4.0/standard-install.yaml

echo "Installing AgentGateway CRDs..."
if helm list -q --namespace $NAMESPACE | grep -q "^agentgateway-crds$"; then
    echo "AgentGateway CRDs already installed, skipping..."
else
    helm install agentgateway-crds oci://cr.agentgateway.dev/charts/agentgateway-crds \
      --version v2.2.0-beta.4 \
      --namespace $NAMESPACE \
      --create-namespace \
      --wait
fi

# Step 2: Deploy the Control Plane First
echo "Step 2: Deploying the control plane (gateway and proxy) first..."

echo "Checking for existing releases..."
if helm list -q --namespace $NAMESPACE | grep -q "^$RELEASE_NAME$"; then
    echo "Uninstalling existing $RELEASE_NAME release..."
    helm uninstall $RELEASE_NAME --namespace $NAMESPACE
fi

echo "Updating Helm dependencies..."
helm dependency update

echo "Installing AgentGateway Control Plane..."
helm install agentgateway-controlplane ./charts/mcpagentcontrolplane \
  --namespace $NAMESPACE \
  --create-namespace \
  --wait

# Step 3: Deploy the Full Umbrella Chart
echo "Step 3: Deploying the full umbrella chart..."

echo "Installing AgentGateway for $ENVIRONMENT..."
helm upgrade --install $RELEASE_NAME . \
  $VALUES_FILE \
  --namespace $NAMESPACE \
  --set mcpagentcontrolplane.enabled=false \
  --wait

# Step 4: Verify Installation
echo "Step 4: Verifying installation..."

echo "Checking release status..."
helm status $RELEASE_NAME

echo "Viewing deployed resources..."
kubectl get all -n $NAMESPACE

echo "Deployment completed successfully!"
echo "To access the UI, run: kubectl port-forward svc/bmg-ui-service 5000:5000 -n $NAMESPACE"
echo "Then visit http://localhost:5000"
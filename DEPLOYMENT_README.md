# MCP UI Deployment Guide

This guide explains how to deploy the MCP UI application with chat functionality to your Kubernetes cluster.

## 📋 Prerequisites

- **kubectl** configured and connected to your cluster
- **Docker** installed and configured
- **Kubernetes Gateway API** installed (via kgateway)
- **Agent Gateway** already deployed

## 🚀 Quick Start

### Option 1: Full Automated Deployment

```bash
# Set your Docker Hub username
export MCP_UI_IMAGE=your-dockerhub-username/mcp-ui:latest

# Run full deployment (build, push, deploy)
./deploy-mcp-ui.sh --all
```

### Option 2: Step-by-Step Deployment

```bash
# 1. Build the Docker image
./deploy-mcp-ui.sh --build

# 2. Push to your registry
./deploy-mcp-ui.sh --push

# 3. Deploy to Kubernetes
./deploy-mcp-ui.sh --deploy
```

### Option 3: Deploy Only (if image already exists)

```bash
export MCP_UI_IMAGE=your-existing-image:latest
./deploy-mcp-ui.sh --deploy
```

## 📖 Script Options

```bash
./deploy-mcp-ui.sh [OPTIONS]

Options:
  -b, --build     Build Docker image from source
  -p, --push      Push Docker image to registry
  -d, --deploy    Deploy to Kubernetes cluster
  -a, --all       Build, push and deploy (full pipeline)
  -h, --help      Show help information
```

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_UI_IMAGE` | `kamalberrybytes/mcp-ui:latest` | Docker image name |
| `NAMESPACE` | `default` | Kubernetes namespace |

## 🏗️ What Gets Deployed

### 1. Service Account
- **Name**: `mcp-ui-sa`
- **Purpose**: Workload identity for Azure authentication
- **Annotation**: `azure.workload.identity/client-id`

### 2. Deployment
- **Name**: `mcp-ui`
- **Replicas**: 1
- **Container Port**: 3000
- **Environment Variables**: Azure config, Gateway URL

### 3. Service
- **Name**: `mcp-ui-service`
- **Type**: ClusterIP
- **Port**: 3000

### 4. HTTP Route
- **Name**: `mcp-ui`
- **Path**: `/ui`
- **Gateway**: `agentgateway` (kgateway-system namespace)

## 🌐 Access URLs

After deployment:

- **Via Gateway**: `http://your-gateway-url/ui`
- **Port Forward**: `kubectl port-forward svc/mcp-ui-service 3000:3000`

## 🔧 Configuration

### Custom Image
```bash
export MCP_UI_IMAGE=myregistry.com/my-ui:v1.0
./deploy-mcp-ui.sh --deploy
```

### Different Namespace
```bash
export NAMESPACE=my-namespace
./deploy-mcp-ui.sh --deploy
```

### Azure Configuration
Update these values in the script or deployment:
- `AZURE_CLIENT_ID`: Your Entra ID application ID
- `AZURE_TENANT_ID`: Your tenant ID
- `GATEWAY_URL`: Agent Gateway service URL

## 🐛 Troubleshooting

### Build Issues
```bash
# Check Docker is running
docker info

# Check mcp-ui-app directory exists
ls -la mcp-ui-app/

# Manual build
cd mcp-ui-app && docker build -t my-ui .
```

### Deployment Issues
```bash
# Check pod status
kubectl get pods -l app=mcp-ui

# Check pod logs
kubectl logs -l app=mcp-ui

# Check service
kubectl get svc mcp-ui-service

# Check HTTP route
kubectl get httproute mcp-ui
```

### Gateway Issues
```bash
# Check gateway status
kubectl get gateway -n kgateway-system

# Check gateway pods
kubectl get pods -n kgateway-system
```

## 🔄 Updates

To update the application:

```bash
# Rebuild and redeploy
./deploy-mcp-ui.sh --all

# Or just rebuild image
./deploy-mcp-ui.sh --build --push

# Then restart deployment
kubectl rollout restart deployment/mcp-ui
```

## 🧹 Cleanup

To remove the MCP UI deployment:

```bash
kubectl delete httproute mcp-ui
kubectl delete service mcp-ui-service
kubectl delete deployment mcp-ui
kubectl delete serviceaccount mcp-ui-sa
```

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify your Kubernetes cluster has Gateway API
3. Ensure Agent Gateway is running
4. Check Azure workload identity setup (if using authentication)

## 🎯 Features

- ✅ **Chat Interface**: Natural language chat with MCP servers
- ✅ **Real-time Communication**: WebSocket-based messaging
- ✅ **MCP Protocol**: Full JSON-RPC 2.0 support
- ✅ **Multi-Server**: Chat with different MCP servers
- ✅ **Authentication**: Configurable OAuth/mock auth
- ✅ **Responsive UI**: Modern web interface
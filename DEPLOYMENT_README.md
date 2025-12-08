# Agent Gateway MCP Deployment Guide

This guide provides a complete setup for deploying the Agent Gateway with MCP servers and UI to your Kubernetes cluster.

## 📋 Prerequisites

Before starting the deployment, ensure you have the following:

- **kubectl**: Kubernetes command-line tool, configured and connected to your cluster
- **Helm**: Kubernetes package manager (version 3.x or later)
- **Docker**: Container runtime for building and pushing images
- **Kubernetes Cluster**: A running Kubernetes cluster with Gateway API support
- **Azure AD Application** (optional): For authentication, with client ID, tenant ID, and client secret

### System Requirements
- Linux/macOS/Windows with WSL2
- At least 4GB RAM available for the cluster
- Network access to Docker registries and Azure services (if using authentication)

## 📥 Cloning the Repository

```bash
# Clone the repository
git clone <repository-url>
cd agentgateway-deployment
```

## 🚀 Installation

Follow these step-by-step instructions to deploy the complete Agent Gateway MCP system.

### Step 1: Deploy Agent Gateway

The agent gateway provides the core infrastructure for MCP protocol routing and includes the control plane, proxy, and an example MCP server.

```bash
# Deploy the complete agent gateway system
./deploy-agentgateway.sh
```

**What this script does:**
- ✅ Checks prerequisites (kubectl, helm, cluster connectivity)
- ✅ Deploys Kubernetes Gateway API CRDs
- ✅ Deploys kgateway CRDs and control plane with agentgateway enabled
- ✅ Creates the agentgateway proxy gateway
- ✅ Deploys an example MCP server for testing
- ✅ Configures Azure AD authentication policy (if credentials provided)
- ✅ Creates MCP backend and HTTP route configurations
- ✅ Deploys the MCP UI application
- ✅ Creates UI HTTP route
- ✅ Verifies deployment and provides access instructions

**Expected output:** The script will show progress and provide port-forwarding commands upon completion.

### Step 2: Deploy Additional MCP Servers

Deploy specific MCP servers based on your needs. Each server has its own directory with Kubernetes manifests.

#### Example MCP Server (Already Deployed)
The example server is deployed automatically in Step 1. To redeploy or modify:

```bash
kubectl apply -f mcp-server/mcp-example/
```

#### HubSpot MCP Server

```bash
kubectl apply -f mcp-server/mcp-hubspot/
```

#### MSSQL MCP Server

```bash
kubectl apply -f mcp-server/mcp-mssql/
```

**Each MCP server deployment includes:**
- Service Account with Azure workload identity annotations
- Deployment with the MCP server container
- Service exposing the server on port 8000
- AgentgatewayBackend configuration for routing
- HTTPRoute for path-based routing (e.g., `/mcp/mcp-hubspot`)

### Step 3: Deploy or Update MCP UI

If the UI was not deployed in Step 1, or to update it separately:

```bash
# Option 1: Full automated deployment
export AZURE_CLIENT_SECRET=your-client-secret-here
./deploy-mcp-ui.sh --all

# Option 2: Step-by-step deployment
./deploy-mcp-ui.sh --build
./deploy-mcp-ui.sh --push
./deploy-mcp-ui.sh --deploy

# Option 3: Deploy only (if image exists)
export MCP_UI_IMAGE=your-existing-image:latest
./deploy-mcp-ui.sh --deploy
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AZURE_TENANT_ID` | Azure AD tenant ID | - | Optional |
| `AZURE_CLIENT_ID` | Azure AD application client ID | - | Optional |
| `AZURE_CLIENT_SECRET` | Azure AD application client secret | - | For UI deployment |
| `MCP_UI_IMAGE` | Docker image for MCP UI | `kamalberrybytes/mcp-ui:latest` | No |
| `NAMESPACE` | Kubernetes namespace | `default` | No |
| `KGATEWAY_VERSION` | kgateway version | `v2.2.0-main` | No |

### Azure AD Authentication Setup

1. **Create Azure AD Application:**
   - Go to Azure Portal → Azure Active Directory → App registrations
   - Create a new registration
   - Note the Application (client) ID and Directory (tenant) ID

2. **Create Client Secret:**
   - In the app registration → Certificates & secrets
   - Create a new client secret
   - Copy the secret value (you won't see it again)

3. **Set Environment Variables:**
   ```bash
   export AZURE_TENANT_ID=your-tenant-id
   export AZURE_CLIENT_ID=your-client-id
   export AZURE_CLIENT_SECRET=your-client-secret
   ```

4. **Configure Workload Identity** (for production):
   - Enable Azure workload identity on your cluster
   - Update service account annotations with the client ID

## 🌐 Access and Usage

### Port Forwarding

```bash
# Port forward the agent gateway (exposes all services)
kubectl port-forward svc/agentgateway 8080:8080 --address 0.0.0.0

# Port forward the UI service directly (alternative)
kubectl port-forward svc/mcp-ui-service 3000:3000
```

### Access URLs

- **MCP UI Application**: `http://localhost:8080/ui`
- **MCP Servers**: `http://localhost:8080/mcp/{server-name}`
  - Example: `http://localhost:8080/mcp/mcp-example`
  - HubSpot: `http://localhost:8080/mcp/mcp-hubspot`
  - MSSQL: `http://localhost:8080/mcp/mcp-mssql`

### Authentication

- **UI Access**: If Azure AD is configured, you'll be redirected to authenticate
- **API Access**: Include Bearer token in Authorization header for direct API calls
- **Mock Auth**: Available for development/testing (configurable in UI)

## 🔧 Troubleshooting

### Common Issues

#### Gateway Not Ready
```bash
# Check gateway status
kubectl get gateway agentgateway

# Check gateway pods
kubectl get pods -n kgateway-system

# Check gateway logs
kubectl logs -n kgateway-system -l app.kubernetes.io/name=kgateway
```

#### MCP Server Connection Issues
```bash
# Check server deployment status
kubectl get deployment mcp-example

# Check server pod logs
kubectl logs -l app=mcp-example

# Check service endpoints
kubectl get endpoints mcp-example-service
```

#### UI Deployment Issues
```bash
# Check UI deployment
kubectl get deployment mcp-ui

# Check UI pod logs
kubectl logs -l app=mcp-ui

# Check UI service
kubectl get service mcp-ui-service

# Check HTTP route
kubectl get httproute mcp-ui
```

#### Build Issues
```bash
# Verify Docker is running
docker info

# Check mcp-ui-app directory
ls -la mcp-ui-app/

# Manual build test
cd mcp-ui-app && npm install && docker build -t test-ui .
```

### Verification Commands

```bash
# Check all deployments
kubectl get deployments

# Check all services
kubectl get services

# Check HTTP routes
kubectl get httproute

# Check agentgateway backends
kubectl get agentgatewaybackend

# Check authentication policies
kubectl get agentgatewaypolicy
```

## 🔄 Updates and Maintenance

### Updating MCP UI

```bash
# Rebuild and redeploy
./deploy-mcp-ui.sh --all

# Update only the image
kubectl set image deployment/mcp-ui mcp-ui=new-image:tag
kubectl rollout restart deployment/mcp-ui
```

### Scaling Components

```bash
# Scale MCP UI
kubectl scale deployment mcp-ui --replicas=3

# Scale MCP servers
kubectl scale deployment mcp-example --replicas=2
```

### Monitoring

```bash
# Check pod resource usage
kubectl top pods

# Check node resources
kubectl top nodes

# View logs with follow
kubectl logs -f -l app=mcp-ui
```

## 🧹 Cleanup

To remove all deployments:

```bash
# Remove MCP UI
kubectl delete httproute mcp-ui
kubectl delete service mcp-ui-service
kubectl delete deployment mcp-ui
kubectl delete serviceaccount mcp-ui-sa
kubectl delete secret mcp-ui-secret

# Remove MCP servers
kubectl delete -f mcp-server/mcp-example/
kubectl delete -f mcp-server/mcp-hubspot/
kubectl delete -f mcp-server/mcp-mssql/

# Remove agent gateway components
kubectl delete gateway agentgateway
kubectl delete agentgatewaypolicy azure-mcp-authn-policy
kubectl delete agentgatewaybackend mcp-example-backend
# Delete other backends as needed

# Remove kgateway control plane
helm uninstall kgateway -n kgateway-system

# Remove CRDs (optional, be careful)
kubectl delete crd gateways.gateway.networking.k8s.io
kubectl delete crd httproutes.gateway.networking.k8s.io
```

## 🎯 Features

- ✅ **Agent Gateway**: Full MCP protocol routing infrastructure
- ✅ **Multiple MCP Servers**: Support for example, HubSpot, and MSSQL servers
- ✅ **Web UI**: Modern chat interface for MCP server interaction
- ✅ **Authentication**: Azure AD integration with workload identity
- ✅ **Scalability**: Kubernetes-native horizontal pod scaling
- ✅ **Monitoring**: Health checks, logging, and resource monitoring
- ✅ **Security**: JWT authentication and authorization policies
- ✅ **Extensibility**: Easy addition of new MCP servers

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify your Kubernetes cluster meets prerequisites
3. Ensure Gateway API is properly installed
4. Check Azure AD configuration if using authentication
5. Review pod logs for detailed error messages

For additional help, check the project documentation or create an issue in the repository.
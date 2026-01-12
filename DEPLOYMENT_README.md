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
- ✅ Installs MSSQL server via Helm
- ✅ Deploys Kubernetes Gateway API CRDs
- ✅ Deploys kgateway CRDs and control plane with agentgateway enabled
- ✅ Creates the agentgateway proxy gateway
- ✅ Deploys MCP servers (example, HubSpot, MSSQL)
- ✅ Deploys cronjob for HubSpot token refresh
- ✅ Configures Azure AD authentication policy (if credentials provided)
- ✅ Creates MCP backend and HTTP route configurations
- ✅ Deploys the BMG UI application
- ✅ Creates UI HTTP route and port-forwarding in screen
- ✅ Verifies deployment and provides access instructions

**Expected output:** The script will show progress and provide port-forwarding commands upon completion.

### Step 2: Verify MCP Servers

The MCP servers are deployed automatically in Step 1. To check or redeploy individually:

```bash
# Check all MCP server deployments
kubectl get deployments -n agentgateway-system -l app.kubernetes.io/name=mcp

# Redeploy specific server
kubectl apply -f mcp-server/mcp-example/ -n agentgateway-system
kubectl apply -f mcp-server/mcp-hubspot/ -n agentgateway-system
kubectl apply -f mcp-server/mcp-mssql/ -n agentgateway-system
```

**Each MCP server deployment includes:**
- Service Account with Azure workload identity annotations
- Deployment with the MCP server container
- Service exposing the server on port 8000
- AgentgatewayBackend configuration for routing
- HTTPRoute for path-based routing (e.g., `/mcp/mcp-hubspot`)

### Step 3: Access the UI

The BMG UI is deployed automatically in Step 1. Access it at `http://localhost:5000` after the script completes.

The script sets up automatic port-forwarding in a screen session named `mcp-ui-forward`.

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AZURE_TENANT_ID` | Azure AD tenant ID | - | Optional |
| `AZURE_CLIENT_ID` | Azure AD application client ID | - | Optional |
| `AGENTGATEWAY_CRDS_VERSION` | Agentgateway CRDs version | `v2.2.0-beta.4` | No |
| `GATEWAY_API_VERSION` | Gateway API version | `v1.4.0` | No |

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

The deployment script automatically sets up port-forwarding in a detached screen session.

```bash
# Manual port-forward (if needed)
kubectl port-forward svc/bmg-ui-service 5000:5000 -n agentgateway-system

# Attach to the screen session
screen -r mcp-ui-forward
```

### Access URLs

- **BMG UI Application**: `http://localhost:5000`
- **MCP Servers**: Access via the UI or direct API calls
  - Example: `http://localhost:5000` (through UI)
  - HubSpot: Integrated in UI
  - MSSQL: Integrated in UI

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
kubectl get deployment bmg-ui -n agentgateway-system

# Check UI pod logs
kubectl logs -l app=bmg-ui -n agentgateway-system

# Check UI service
kubectl get service bmg-ui-service -n agentgateway-system

# Check HTTP route
kubectl get httproute bmg-ui -n agentgateway-system
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
kubectl get deployments -n agentgateway-system

# Check all services
kubectl get services -n agentgateway-system

# Check HTTP routes
kubectl get httproute -n agentgateway-system

# Check agentgateway backends
kubectl get agentgatewaybackend -n agentgateway-system

# Check authentication policies
kubectl get agentgatewaypolicy -n agentgateway-system

# Check cronjob
kubectl get cronjob -n agentgateway-system
```

## 🔄 Updates and Maintenance

### Updating BMG UI

The BMG UI is deployed automatically by the main script. To update:

```bash
# Redeploy with the script
./deploy-agentgateway.sh

# Or update manually
kubectl set image deployment/bmg-ui bmg-ui=new-image:tag -n agentgateway-system
kubectl rollout restart deployment/bmg-ui -n agentgateway-system
```

### Scaling Components

```bash
# Scale BMG UI
kubectl scale deployment bmg-ui --replicas=3 -n agentgateway-system

# Scale MCP servers
kubectl scale deployment mcp-example --replicas=2 -n agentgateway-system
```

### Monitoring

```bash
# Check pod resource usage
kubectl top pods -n agentgateway-system

# Check node resources
kubectl top nodes

# View logs with follow
kubectl logs -f -l app=bmg-ui -n agentgateway-system
```

## 🧹 Cleanup

To remove all deployments:

```bash
# Remove BMG UI
kubectl delete httproute bmg-ui -n agentgateway-system
kubectl delete service bmg-ui-service -n agentgateway-system
kubectl delete deployment bmg-ui -n agentgateway-system
kubectl delete serviceaccount bmg-ui-sa -n agentgateway-system

# Remove MCP servers
kubectl delete -f mcp-server/mcp-example/ -n agentgateway-system
kubectl delete -f mcp-server/mcp-hubspot/ -n agentgateway-system
kubectl delete -f mcp-server/mcp-mssql/ -n agentgateway-system

# Remove cronjob
kubectl delete -f cronjob/cronjob-deployment.yml -n agentgateway-system

# Remove agent gateway components
kubectl delete gateway agentgateway -n agentgateway-system
kubectl delete agentgatewaypolicy azure-mcp-authn-policy -n agentgateway-system
kubectl delete agentgatewaybackend mcp-example-backend -n agentgateway-system
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
- ✅ **BMG Web UI**: Modern chat interface for MCP server interaction
- ✅ **CronJob for Token Refresh**: Automated HubSpot token renewal
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
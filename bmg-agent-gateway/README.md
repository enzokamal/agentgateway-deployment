# BMG Agent Gateway Helm Chart

This Helm chart deploys the BMG Agent Gateway system, which includes the BMG Agent, BMG UI, MCP HubSpot, MCP MSSQL servers, and the associated Gateway and authentication policies.

## Helm Chart Overview for Beginners

If you're new to Helm charts, here's a quick introduction to help you understand this deployment:

### What is Helm?
Helm is a package manager for Kubernetes that simplifies deploying and managing applications. It uses "charts" (packages) that contain all the Kubernetes manifests needed to run an application.

### Key Concepts
- **Chart**: A collection of files that describe a related set of Kubernetes resources
- **Values.yaml**: A file containing default configuration values that can be customized
- **Templates**: YAML files with placeholders that get filled in with actual values during installation
- **Release**: An instance of a chart running in your cluster

### How Helm Works
1. You provide configuration values (or use defaults)
2. Helm processes templates with your values
3. Generates Kubernetes manifests
4. Applies them to your cluster

### This Chart's Structure
```
bmgAgentgateway/
├── Chart.yaml          # Chart metadata
├── values.yaml         # Default configuration
├── templates/          # Kubernetes manifest templates
│   ├── _helpers.tpl    # Reusable template functions
│   ├── *.yaml          # Component-specific templates
└── README.md           # This documentation
```

## How This Chart Works

### Component Overview
This chart deploys a multi-component system for agent-based interactions with external services:

1. **BMG Agent**: Core orchestration service that manages MCP server connections
2. **BMG UI**: Web interface for user interaction with the agent system
3. **MCP HubSpot**: MCP server providing HubSpot CRM integration
4. **MCP MSSQL**: MCP server providing Microsoft SQL Server database access
5. **Gateway**: Routes traffic between components and enforces authentication
6. **Policy**: Azure AD authentication policy for secure access

### Data Flow
```
User Request → Gateway (Auth) → BMG UI → BMG Agent → MCP Servers (HubSpot/MSSQL)
                                      ↓
External Services ←─────────────────────┘
```

### Component Interactions
- **Gateway** receives external requests and routes them based on paths
- **BMG UI** provides the user interface, authenticates via Azure AD
- **BMG Agent** orchestrates requests to appropriate MCP servers
- **MCP Servers** handle specific integrations (HubSpot API, MSSQL database)
- **Policy** ensures only authenticated requests reach protected endpoints

### Installation Flow
1. Helm processes templates with your custom values
2. Creates Kubernetes resources in the specified namespace
3. Deploys all components with proper networking
4. Configures authentication and routing rules
5. Services become available through the Gateway

## Prerequisites

Before installing the BMG Agent Gateway Helm chart, ensure your Kubernetes cluster meets the following requirements:

### Kubernetes Version
- Kubernetes 1.19 or higher

### Helm Version
- Helm 3.0 or higher

### Required Controllers and APIs
- **Gateway API**: The Gateway API must be installed in your cluster. This provides the Gateway, HTTPRoute, and related resources.
  - Install Gateway API CRDs: `kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.0.0/standard-install.yaml`
- **Agent Gateway Controller**: The Agent Gateway controller must be installed and running.
  - This provides custom resources like `AgentgatewayBackend` and `AgentgatewayPolicy`.
  - Install the Agent Gateway CRDs and controller:
    ```bash
    helm upgrade --install agentgateway-crds \
        oci://cr.agentgateway.dev/charts/agentgateway-crds \
        --version v2.2.0-beta.4 \
        --namespace "${AGENTGATEWAY_NAMESPACE}" \
        --create-namespace

    helm upgrade --install agentgateway \
        oci://cr.agentgateway.dev/charts/agentgateway \
        --version v2.2.0-beta.4 \
        --namespace "${AGENTGATEWAY_NAMESPACE}" \
        --create-namespace
    ```

### Cluster Permissions
- Ensure you have cluster-admin permissions or appropriate RBAC roles to create Gateway API resources and custom resources.

### External Dependencies
- **Azure AD**: For authentication, you need an Azure AD application registered with appropriate permissions.
- **Database**: For MCP MSSQL, ensure your MSSQL server is accessible from the cluster.
- **External Services**: Verify that external services (HubSpot API, etc.) are accessible.

### Namespace
- The chart deploys to `agentgateway-system` namespace by default. Create it if it doesn't exist:
  ```bash
  kubectl create namespace agentgateway-system
  ```

## Quick Start for Beginners

### Step 1: Prepare Your Environment
```bash
# Install Helm (if not already installed)
curl https://get.helm.sh/helm-v3.12.0-linux-amd64.tar.gz -o helm.tar.gz
tar -zxvf helm.tar.gz
sudo mv linux-amd64/helm /usr/local/bin/
```

### Step 2: Customize Configuration
1. Copy `values.yaml` to `my-values.yaml`
2. Edit the values:
   ```yaml
   # Set your Azure configuration
   azure:
     clientId: "your-azure-client-id"
     tenantId: "your-azure-tenant-id"

   # Configure database connection
   mcpMssql:
     deployment:
       env:
         mssqlServer: "your-sql-server"
         mssqlPassword: "your-password"
   ```

### Step 3: Install the Chart
```bash
# Dry run first to check for errors
helm install my-release ./bmgAgentgateway --dry-run --debug

# Install with your custom values
helm install my-release ./bmgAgentgateway -f my-values.yaml

# Check installation
kubectl get pods -n agentgateway-system
kubectl get svc -n agentgateway-system
```

### Step 4: Access Your Application
```bash
# Port forward to access locally
kubectl port-forward -n agentgateway-system svc/agentgateway-proxy 8080:8080

# Visit: http://localhost:8080/ui
```

## Installing the Chart

### Basic Installation

1. **Clone or download the chart**:
   ```bash
   # If using git
   git clone <repository-url>
   cd agentgateway-deployment/bmgAgentgateway
   ```

2. **Install with default settings**:
   ```bash
   helm install my-release ./bmg-agent-gateway --namespace agentgateway-system --create-namespace
   ```

   This installs the chart with the release name `my-release` in the `agentgateway-system` namespace.

### Custom Installation

#### Install in a Different Namespace
```bash
# Method 1: Override namespace value
helm install my-release ./bmg-agent-gateway --namespace your-namespace --set namespace=your-namespace

# Method 2: Edit values.yaml and set namespace: "your-namespace"
helm install my-release ./bmg-agent-gateway --namespace your-namespace
```

#### Install with Custom Values
```bash
# Using a custom values file
helm install my-release ./bmg-agent-gateway --namespace agentgateway-system -f my-values.yaml

# Override specific values
helm install my-release ./bmg-agent-gateway --namespace agentgateway-system \
  --set azure.clientId="your-client-id" \
  --set azure.tenantId="your-tenant-id" \
  --set bmgAgent.secret.deepseekApiKey="your-api-key"
```



## Uninstalling the Chart

### Standard Uninstall
```bash
helm uninstall my-release
```

This removes all resources created by the chart, including:
- Deployments and Pods
- Services
- ConfigMaps and Secrets
- Gateway API resources (Gateway, HTTPRoute)
- Custom resources (AgentgatewayBackend, AgentgatewayPolicy)

### Clean Up Namespace
If you want to remove the entire namespace:
```bash
kubectl delete namespace agentgateway-system
```

**Warning**: This will delete all resources in the namespace, including any manually created resources.

### Partial Cleanup
To keep some resources (like secrets with sensitive data):
```bash
# Delete specific resources
kubectl delete deployment,svc,configmap -l app.kubernetes.io/instance=my-release -n agentgateway-system

# Keep secrets for potential reuse
kubectl get secrets -l app.kubernetes.io/instance=my-release -n agentgateway-system
```

### Force Deletion (if stuck)
If resources are stuck in terminating state:
```bash
# Force delete pods
kubectl delete pods --force --grace-period=0 -l app.kubernetes.io/instance=my-release -n agentgateway-system

# Remove finalizers if needed
kubectl patch <resource-type> <resource-name> -p '{"metadata":{"finalizers":null}}' --type=merge
```

## Configuration

### Understanding Configuration
The `values.yaml` file contains all the settings for your deployment. Each component has its own section with parameters you can customize. When you install the chart, you can override any of these values using `--set` flags or a custom values file.

### Key Configuration Areas

### Global Configuration
These settings apply to the entire deployment:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `namespace` | Kubernetes namespace where all components will be deployed | `"agentgateway-system"` |

### Azure Configuration
Required for authentication. Get these values from your Azure AD app registration:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `azure.clientId` | Application (client) ID from Azure AD app registration | `"11ddc0cd-e6fc-48b6-8832-de61800fb41e"` |
| `azure.tenantId` | Directory (tenant) ID from Azure AD | `"6ba231bb-ad9e-41b9-b23d-674c80196bbd"` |

### BMG Agent Configuration
Core agent settings. The agent orchestrates requests between UI and MCP servers:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `bmgAgent.configMap.agentMode` | Operating mode (api, etc.) | `"api"` |
| `bmgAgent.configMap.agentPort` | Port the agent listens on | `"8070"` |
| `bmgAgent.configMap.agentHost` | Host binding for the agent | `"0.0.0.0"` |
| `bmgAgent.configMap.mcpServersJson` | JSON list of available MCP server endpoints | `'[{"url":"http://agentgateway-proxy.{{ .Release.Namespace }}.svc.cluster.local:8080/mcp/mcp-mssql"}]'` |
| `bmgAgent.deployment.replicas` | Number of agent pod replicas | `1` |
| `bmgAgent.deployment.image.repository` | Docker image repository | `"sawnjordan/multi-agent"` |
| `bmgAgent.deployment.image.tag` | Docker image tag/version | `"v0.8"` |
| `bmgAgent.deployment.image.pullPolicy` | When to pull the image | `"IfNotPresent"` |
| `bmgAgent.deployment.ports[0].containerPort` | First container port | `8000` |
| `bmgAgent.deployment.ports[1].containerPort` | Second container port | `8070` |
| `bmgAgent.service.name` | Kubernetes service name | `"bmg-agent-service"` |
| `bmgAgent.service.type` | Service type (ClusterIP, LoadBalancer, etc.) | `"ClusterIP"` |
| `bmgAgent.service.port` | Service port | `8070` |
| `bmgAgent.service.targetPort` | Container port to forward to | `8070` |
| `bmgAgent.secret.name` | Secret resource name | `"bmg-agent-secrets"` |
| `bmgAgent.secret.deepseekApiKey` | API key for DeepSeek service | `""` |

### BMG UI Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `bmgUi.deployment.replicas` | Number of replicas | `1` |
| `bmgUi.deployment.image.repository` | Image repository | `"kamalberrybytes/adk-web-ui"` |
| `bmgUi.deployment.image.tag` | Image tag | `"v5"` |
| `bmgUi.deployment.image.pullPolicy` | Image pull policy | `"Always"` |
| `bmgUi.deployment.port` | Container port | `5000` |
| `bmgUi.deployment.env.azureClientSecret` | Azure client secret | `""` |
| `bmgUi.deployment.env.redirectUri` | Redirect URI | `"http://localhost:5000/auth/callback"` |
| `bmgUi.deployment.env.secretKey` | Secret key | `"helloworld"` |
| `bmgUi.deployment.env.azureScopes` | Azure scopes | `"openid api://11ddc0cd-e6fc-48b6-8832-de61800fb41e/mcp.access"` |
| `bmgUi.service.name` | Service name | `"bmg-ui-service"` |
| `bmgUi.service.port` | Service port | `5000` |
| `bmgUi.service.targetPort` | Target port | `5000` |
| `bmgUi.httpRoute.name` | HTTPRoute name | `"bmg-ui"` |

### MCP HubSpot Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `mcpHubspot.backend.name` | Backend name | `"mcp-hubspot-backend"` |
| `mcpHubspot.backend.targetName` | Target name | `"mcp-hubspot-target"` |
| `mcpHubspot.backend.protocol` | Protocol | `"StreamableHTTP"` |
| `mcpHubspot.deployment.name` | Deployment name | `"mcp-hubspot"` |
| `mcpHubspot.deployment.image.repository` | Image repository | `"kamalberrybytes/mcp-hubspot"` |
| `mcpHubspot.deployment.image.tag` | Image tag | `"latest"` |
| `mcpHubspot.deployment.image.pullPolicy` | Image pull policy | `"Always"` |
| `mcpHubspot.service.name` | Service name | `"mcp-hubspot-service"` |
| `mcpHubspot.service.port` | Service port | `8000` |
| `mcpHubspot.service.targetPort` | Target port | `8000` |
| `mcpHubspot.service.appProtocol` | App protocol | `"kgateway.dev/mcp"` |
| `mcpHubspot.httpRoute.name` | HTTPRoute name | `"mcp-hubspot"` |

### MCP MSSQL Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `mcpMssql.backend.name` | Backend name | `"mcp-mssql-backend"` |
| `mcpMssql.backend.targetName` | Target name | `"mcp-mssql-target"` |
| `mcpMssql.backend.protocol` | Protocol | `"StreamableHTTP"` |
| `mcpMssql.deployment.name` | Deployment name | `"mcp-mssql"` |
| `mcpMssql.deployment.image.repository` | Image repository | `"kamalberrybytes/mssql-mcp"` |
| `mcpMssql.deployment.image.tag` | Image tag | `"v1"` |
| `mcpMssql.deployment.image.pullPolicy` | Image pull policy | `"Always"` |
| `mcpMssql.deployment.env.mssqlServer` | MSSQL server | `"my-mssqlserver-2022"` |
| `mcpMssql.deployment.env.mssqlDatabase` | MSSQL database | `"msdb"` |
| `mcpMssql.deployment.env.mssqlPort` | MSSQL port | `"1433"` |
| `mcpMssql.deployment.env.mssqlUser` | MSSQL user | `"sa"` |
| `mcpMssql.deployment.env.mssqlPassword` | MSSQL password | `""` |
| `mcpMssql.service.name` | Service name | `"mcp-mssql-service"` |
| `mcpMssql.service.port` | Service port | `8000` |
| `mcpMssql.service.targetPort` | Target port | `8000` |
| `mcpMssql.service.appProtocol` | App protocol | `"kgateway.dev/mcp"` |
| `mcpMssql.httpRoute.name` | HTTPRoute name | `"mcp-mssql"` |

### Gateway Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `gateway.name` | Gateway name | `"agentgateway-proxy"` |
| `gateway.gatewayClassName` | Gateway class name | `"agentgateway"` |
| `gateway.listeners[0].protocol` | Listener protocol | `"HTTP"` |
| `gateway.listeners[0].port` | Listener port | `8080` |
| `gateway.listeners[0].name` | Listener name | `"http"` |
| `gateway.listeners[0].allowedRoutes.namespaces.from` | Allowed routes | `"All"` |

### Policy Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `policy.name` | Policy name | `"azure-mcp-authn-policy"` |
| `policy.targetRefs[0].group` | Target group | `"gateway.networking.k8s.io"` |
| `policy.targetRefs[0].kind` | Target kind | `"Gateway"` |
| `policy.jwtAuthentication.mode` | JWT mode | `"Strict"` |
| `policy.jwtAuthentication.providers[0].cacheDuration` | Cache duration | `"5m"` |
| `policy.jwtAuthentication.providers[0].backendRef.group` | Backend group | `""` |
| `policy.jwtAuthentication.providers[0].backendRef.kind` | Backend kind | `"Service"` |
| `policy.jwtAuthentication.providers[0].backendRef.name` | Backend name | `"azure-ad-jwks"` |
| `policy.jwtAuthentication.providers[0].backendRef.port` | Backend port | `443` |
| `policy.jwksService.name` | JWKS service name | `"azure-ad-jwks"` |
| `policy.jwksService.externalName` | External name | `"login.microsoftonline.com"` |

## Example Configuration

Create a `values.yaml` file with your custom values:

```yaml
azure:
  clientId: "your-azure-client-id"
  tenantId: "your-azure-tenant-id"

bmgAgent:
  secret:
    deepseekApiKey: "your-api-key"

bmgUi:
  deployment:
    env:
      azureClientSecret: "your-client-secret"
      redirectUri: "https://your-domain.com/auth/callback"

mcpMssql:
  deployment:
    env:
      mssqlServer: "your-mssql-server"
      mssqlPassword: "your-password"
```

Then install with:

```bash
helm install my-release ./bmgAgentgateway -f values.yaml
```

## Post-Installation Steps

After successful installation, perform these verification and configuration steps:

### 1. Verify Installation
```bash
# Check all pods are running
kubectl get pods -n agentgateway-system

# Check services
kubectl get svc -n agentgateway-system

# Check gateway and routes
kubectl get gateway -n agentgateway-system
kubectl get httproute -n agentgateway-system

# Check custom resources
kubectl get agentgatewaybackend -n agentgateway-system
kubectl get agentgatewaypolicy -n agentgateway-system
```

### 2. Configure Secrets
Update the secrets with actual values:

```bash
# Update BMG Agent secret
kubectl patch secret bmg-agent-secrets -n agentgateway-system \
  --type string --patch '{"stringData":{"DEEPSEEK_API_KEY":"your-actual-api-key"}}'

# Update BMG UI secret (if needed)
kubectl patch secret bmg-ui-secret -n agentgateway-system \
  --type string --patch '{"stringData":{"AZURE_CLIENT_SECRET":"your-client-secret"}}'

# Update MCP MSSQL secret
kubectl patch secret mcp-mssql-secret -n agentgateway-system \
  --type string --patch '{"stringData":{"MSSQL_PASSWORD":"your-db-password"}}'
```

### 3. Access the Application
```bash
# Port forward the Gateway (if using port forwarding)
kubectl port-forward -n agentgateway-system svc/agentgateway-proxy 8080:8080

# Access BMG UI
# Visit: http://localhost:8080/ui

# Access API endpoints
# BMG Agent API: http://localhost:8080/api (if configured)
```

### 4. Configure External Access
For production deployments, configure ingress or load balancer:

```yaml
# Example Ingress for external access
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: bmg-ingress
  namespace: agentgateway-system
spec:
  rules:
  - host: bmg.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: agentgateway-proxy
            port:
              number: 8080
```

## Usage Guide

### Accessing BMG UI
1. Ensure the Gateway is accessible (via port-forward, ingress, or load balancer)
2. Navigate to the UI endpoint: `http://<gateway-url>/ui`
3. Authenticate using Azure AD (if configured)

### Using MCP Servers
The chart deploys two MCP servers:

- **MCP HubSpot**: Accessible at `http://<gateway-url>/mcp/mcp-hubspot`
- **MCP MSSQL**: Accessible at `http://<gateway-url>/mcp/mcp-mssql`

### API Endpoints
- **BMG Agent API**: `http://<gateway-url>/api` (port 8070 internally)
- **Gateway Proxy**: `http://<gateway-url>:8080`

### Monitoring and Logs
```bash
# View logs for each component
kubectl logs -n agentgateway-system deployment/bmg-agent
kubectl logs -n agentgateway-system deployment/bmg-ui
kubectl logs -n agentgateway-system deployment/mcp-hubspot
kubectl logs -n agentgateway-system deployment/mcp-mssql

# Check Gateway status
kubectl describe gateway agentgateway-proxy -n agentgateway-system
```

## Components

This chart deploys the following components, each serving a specific role in the agent gateway system:

### Core Components

#### BMG Agent
- **Purpose**: Central orchestration service that manages and routes requests to MCP servers
- **How it works**: Receives requests from BMG UI, determines which MCP server to use, and forwards requests
- **Configuration**: Defines MCP server endpoints in `mcpServersJson`
- **Ports**: Internal port 8070 for API, 8000 for other services

#### BMG UI
- **Purpose**: Web-based user interface for interacting with the agent system
- **How it works**: Provides a graphical interface for users to submit requests, displays responses
- **Authentication**: Integrates with Azure AD for user authentication
- **Routing**: Accessible via Gateway at `/ui` path

### MCP Servers

#### MCP HubSpot
- **Purpose**: Provides integration with HubSpot CRM API
- **How it works**: Translates agent requests into HubSpot API calls (contacts, deals, etc.)
- **Protocol**: Uses StreamableHTTP for real-time communication
- **Routing**: Accessible via Gateway at `/mcp/mcp-hubspot`

#### MCP MSSQL
- **Purpose**: Provides database access to Microsoft SQL Server
- **How it works**: Executes SQL queries and returns results to the agent
- **Configuration**: Requires database connection details (server, credentials, database)
- **Routing**: Accessible via Gateway at `/mcp/mcp-mssql`

### Infrastructure Components

#### Gateway
- **Purpose**: Routes external traffic to appropriate internal services
- **How it works**: Uses Gateway API to define routing rules based on URL paths
- **Listeners**: Configured for HTTP on port 8080
- **Routes**: `/ui` → BMG UI, `/mcp/*` → MCP servers

#### Authentication Policy
- **Purpose**: Enforces Azure AD authentication for protected endpoints
- **How it works**: Validates JWT tokens from Azure AD, blocks unauthorized requests
- **Configuration**: Uses JWKS endpoint to verify tokens
- **Scope**: Applies to Gateway, protecting all routes

#### Secrets and ConfigMaps
- **Purpose**: Store sensitive configuration and runtime settings
- **Types**:
  - Secrets: API keys, passwords, client secrets
  - ConfigMaps: Non-sensitive configuration (agent mode, ports, URLs)

## Component Interaction Flow

### Request Flow Example
1. **User Access**: User visits `http://your-gateway/ui`
2. **Gateway Routing**: Gateway receives request, applies authentication policy
3. **Azure AD Auth**: Policy validates JWT token from Azure AD
4. **UI Service**: Request reaches BMG UI service
5. **UI Processing**: BMG UI renders interface, user submits a request (e.g., "Get HubSpot contacts")
6. **Agent Communication**: BMG UI sends request to BMG Agent API
7. **Agent Orchestration**: BMG Agent parses request, determines it needs HubSpot data
8. **MCP Server Call**: BMG Agent calls MCP HubSpot server
9. **External API**: MCP HubSpot server queries HubSpot API
10. **Response Flow**: Data flows back: HubSpot → MCP Server → Agent → UI → User

### Network Flow
```
Internet → Gateway (8080) → Authentication Policy
                           ↓
                    ┌──────┴──────┐
                    │             │
               /ui │             │ /mcp/*
                    │             │
              BMG UI        MCP Servers
                    │             │
                    └──────┬──────┘
                           │
                    BMG Agent ←→ External APIs
```

### Configuration Flow
- **values.yaml**: Defines all component configurations
- **Templates**: Use values to generate Kubernetes manifests
- **Helpers**: Provide reusable functions for labels, selectors, and naming
- **Helm Rendering**: Combines templates + values → Kubernetes YAML
- **Kubernetes**: Applies manifests to create running resources

## Troubleshooting

### Common Issues and Solutions

#### 1. Installation Fails with CRD Errors
**Error**: `no matches for kind "Gateway" in version "gateway.networking.k8s.io/v1"`

**Solution**:
```bash
# Install Gateway API CRDs
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.0.0/standard-install.yaml

# Wait for CRDs to be established
kubectl wait --for=condition=established crd/gateways.gateway.networking.k8s.io
```

#### 2. Pods Not Starting
**Check pod status**:
```bash
kubectl get pods -n agentgateway-system
kubectl describe pod <pod-name> -n agentgateway-system
```

**Common causes**:
- Image pull errors: Check image names and registry access
- ConfigMap/Secret issues: Verify secrets are created and have correct data
- Resource constraints: Check node capacity and resource requests/limits

#### 3. Gateway Not Ready
**Check Gateway status**:
```bash
kubectl describe gateway agentgateway-proxy -n agentgateway-system
```

**Possible issues**:
- Gateway controller not running
- Invalid listener configuration
- Missing gateway class

#### 4. HTTPRoute Not Working
**Check HTTPRoute status**:
```bash
kubectl describe httproute <route-name> -n agentgateway-system
```

**Check**:
- Parent Gateway exists and is ready
- Hostnames and paths are correctly configured
- Backend services are accessible

#### 5. Authentication Issues
**For Azure AD authentication**:
- Verify Azure AD app registration settings
- Check JWT token format and claims
- Ensure JWKS endpoint is accessible

#### 6. Service Communication Issues
**Check service discovery**:
```bash
kubectl run test --image=busybox --rm -it --restart=Never -- nslookup bmg-agent-service.agentgateway-system.svc.cluster.local
```

**Check service endpoints**:
```bash
kubectl get endpoints -n agentgateway-system
```

### Logs and Debugging

#### View Component Logs
```bash
# BMG Agent logs
kubectl logs -n agentgateway-system -l app=bmg-agent --tail=100

# Gateway controller logs (if accessible)
kubectl logs -n <gateway-controller-namespace> deployment/<gateway-controller>

# Agent Gateway controller logs
kubectl logs -n <agent-gateway-namespace> deployment/<agent-gateway-controller>
```

#### Enable Debug Logging
For components that support it, enable debug logging by setting environment variables or config values.

#### Network Debugging
```bash
# Test connectivity between pods
kubectl exec -n agentgateway-system <pod-name> -- curl <service-url>

# Check network policies (if any)
kubectl get networkpolicy -n agentgateway-system
```

### Performance Issues

#### High Latency
- Check resource usage: `kubectl top pods -n agentgateway-system`
- Review Gateway configuration for bottlenecks
- Monitor external service response times

#### Memory/CPU Issues
- Adjust resource requests/limits in values.yaml
- Scale deployments: `kubectl scale deployment <name> --replicas=<count>`

### Upgrading

#### Helm Upgrade
```bash
# Upgrade with new values
helm upgrade my-release ./bmg-agent-gateway -f updated-values.yaml

# Rollback if needed
helm rollback my-release
```

#### Database Schema Updates
For MCP MSSQL, ensure database schema is compatible with the new version.

### Support

For additional support:
1. Check the [Gateway API documentation](https://gateway-api.sigs.k8s.io/)
2. Review [Agent Gateway documentation](https://agentgateway.dev/)
3. Check Kubernetes logs for underlying infrastructure issues
4. Verify external service configurations (Azure AD, databases, etc.)

## Development

### Local Development
For developing and testing the chart locally:

1. **Install chart dependencies** (if any):
   ```bash
   helm dependency update ./bmg-agent-gateway
   ```

2. **Validate templates**:
   ```bash
   helm template my-release ./bmg-agent-gateway --debug
   ```

3. **Dry-run installation**:
   ```bash
   helm install my-release ./bmg-agent-gateway --dry-run --debug
   ```

4. **Test with different values**:
   ```bash
   helm template my-release ./bmg-agent-gateway -f test-values.yaml
   ```

### Chart Testing
```bash
# Run helm unit tests (if configured)
helm test my-release

# Use chart-testing for CI/CD
ct lint ./bmg-agent-gateway
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make changes following Helm chart best practices
4. Update documentation
5. Test thoroughly
6. Submit a pull request

### Chart Versioning
This chart follows [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Security Considerations
- Regularly update base images
- Use secrets for sensitive data
- Implement network policies for production
- Enable RBAC with minimal permissions
- Monitor for security vulnerabilities in dependencies
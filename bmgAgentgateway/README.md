# BMG Agent Gateway Helm Chart

This Helm chart deploys the BMG Agent Gateway system, which includes the BMG Agent, BMG UI, MCP HubSpot, MCP MSSQL servers, and the associated Gateway and authentication policies.

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
    export AGENTGATEWAY_CRDS_VERSION="latest"  # Set to the desired version
    export AGENTGATEWAY_NAMESPACE="agentgateway-system"  # Set to your namespace

    helm upgrade --install agentgateway-crds \
        oci://cr.agentgateway.dev/charts/agentgateway-crds \
        --version "${AGENTGATEWAY_CRDS_VERSION}" \
        --namespace "${AGENTGATEWAY_NAMESPACE}" \
        --create-namespace

    helm upgrade --install agentgateway \
        oci://cr.agentgateway.dev/charts/agentgateway \
        --version "${AGENTGATEWAY_CRDS_VERSION}" \
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

### Pre-Installation Checklist

Before running the installation, verify:

1. **Gateway API CRDs are installed**:
   ```bash
   kubectl get crd gateways.gateway.networking.k8s.io
   kubectl get crd httproutes.gateway.networking.k8s.io
   ```

2. **Agent Gateway CRDs are installed**:
   ```bash
   kubectl get crd agentgatewaybackends.agentgateway.dev
   kubectl get crd agentgatewaypolicies.agentgateway.dev
   ```

3. **Namespace exists or will be created**:
   ```bash
   kubectl create namespace agentgateway-system --dry-run=client
   ```

4. **Required images are accessible** (optional, for air-gapped environments):
   ```bash
   kubectl run test-pod --image=sawnjordan/multi-agent:v0.8 --rm -it --restart=Never -- /bin/sh
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

The following table lists the configurable parameters of the BMG Agent Gateway chart and their default values.

### Global Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `namespace` | Namespace for all resources | `"agentgateway-system"` |

### Azure Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `azure.clientId` | Azure Client ID | `"11ddc0cd-e6fc-48b6-8832-de61800fb41e"` |
| `azure.tenantId` | Azure Tenant ID | `"6ba231bb-ad9e-41b9-b23d-674c80196bbd"` |

### BMG Agent Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `bmgAgent.configMap.agentMode` | Agent mode | `"api"` |
| `bmgAgent.configMap.agentPort` | Agent port | `"8070"` |
| `bmgAgent.configMap.agentHost` | Agent host | `"0.0.0.0"` |
| `bmgAgent.configMap.mcpServersJson` | MCP servers JSON configuration | `'[{"url":"http://agentgateway-proxy.{{ .Release.Namespace }}.svc.cluster.local:8080/mcp/mcp-mssql"}]'` |
| `bmgAgent.deployment.replicas` | Number of replicas | `1` |
| `bmgAgent.deployment.image.repository` | Image repository | `"sawnjordan/multi-agent"` |
| `bmgAgent.deployment.image.tag` | Image tag | `"v0.8"` |
| `bmgAgent.deployment.image.pullPolicy` | Image pull policy | `"IfNotPresent"` |
| `bmgAgent.deployment.ports[0].containerPort` | First container port | `8000` |
| `bmgAgent.deployment.ports[1].containerPort` | Second container port | `8070` |
| `bmgAgent.service.name` | Service name | `"bmg-agent-service"` |
| `bmgAgent.service.type` | Service type | `"ClusterIP"` |
| `bmgAgent.service.port` | Service port | `8070` |
| `bmgAgent.service.targetPort` | Target port | `8070` |
| `bmgAgent.secret.name` | Secret name | `"bmg-agent-secrets"` |
| `bmgAgent.secret.deepseekApiKey` | DeepSeek API key | `""` |

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

This chart deploys the following components:

- **BMG Agent**: The main agent service that orchestrates MCP server interactions
- **BMG UI**: Web-based user interface for interacting with the agent system
- **MCP HubSpot**: MCP server providing HubSpot CRM integration capabilities
- **MCP MSSQL**: MCP server providing Microsoft SQL Server database access
- **Gateway**: Gateway API resource that routes traffic to appropriate services
- **Policy**: Authentication policy enforcing Azure AD JWT validation
- **Secrets**: Kubernetes secrets for storing sensitive configuration data

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
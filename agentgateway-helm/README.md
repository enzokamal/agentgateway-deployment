# AgentGateway Helm Charts

This directory contains an optimized umbrella Helm chart for the AgentGateway system, following Helm best practices for multi-environment deployments.

## Architecture

The chart follows an **umbrella pattern** with:
- **Parent chart**: `agentgateway-helm/` - Manages all components
- **Subcharts**: Individual component charts in subdirectories
- **Global values**: Shared configuration across all components
- **Environment overrides**: Separate values files for different environments

## Charts Structure

```
agentgateway-helm/
├── Chart.yaml              # Umbrella chart metadata & dependencies
├── values.yaml             # Global default values
├── values-prod.yaml        # Production overrides
├── templates/              # Umbrella-level templates (if needed)
├── bmg-agent/              # Subchart for BMG Agent
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
├── bmg-ui/                 # Subchart for BMG UI
├── mcp-hubspot/            # Subchart for MCP HubSpot
├── mcp-mssql/              # Subchart for MCP MSSQL
└── mcpagentcontrolplane/   # Subchart for Control Plane
```

## Best Practices Implemented

### 1. **Global Values**
- Shared configuration (namespace, image registry, labels)
- Environment-specific settings
- Consistent labeling across components

### 2. **Helper Templates**
- Standardized naming conventions
- Common labels and selectors
- Reusable template functions

### 3. **Environment Management**
- Base `values.yaml` for development
- `values-prod.yaml` for production overrides
- Easy environment switching

### 4. **Proper Labeling**
- Kubernetes recommended labels
- Helm-managed metadata
- Component identification

### 5. **Dependency Management**
- Explicit subchart dependencies
- Version pinning
- Local repository references

## Prerequisites

1. **Kubernetes Cluster**: Running cluster (local or cloud)
2. **Helm 3.x**: Install from https://helm.sh/docs/intro/install/
3. **kubectl**: Configured to access your cluster

## Installation

### Step 1: Install Required CRDs

```bash
# Install Gateway API CRDs
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.4.0/standard-install.yaml

# Install AgentGateway CRDs (skip if already installed)
helm install agentgateway-crds oci://cr.agentgateway.dev/charts/agentgateway-crds \
  --version v2.2.0-beta.4 \
  --namespace agentgateway-system \
  --create-namespace \
  --wait

# If CRDs already exist, you can skip this step and proceed to Step 2
```

### Step 2: Deploy the Umbrella Chart

```bash
cd agentgateway-helm

# Update dependencies
helm dependency update

# Install for development
helm install agentgateway-dev . \
  --namespace agentgateway-system \
  --create-namespace \
  --wait

# Or install for production
helm install agentgateway-prod . \
  -f values-prod.yaml \
  --namespace agentgateway-prod \
  --create-namespace \
  --wait
```

### Step 3: Verify Installation

```bash
# Check release status
helm status agentgateway-dev

# View deployed resources
kubectl get all -n agentgateway-system

# Access the UI
kubectl port-forward svc/bmg-ui-service 5000:5000 -n agentgateway-system
# Visit http://localhost:5000
```

## Configuration

### Global Values
```yaml
global:
  namespace: agentgateway-system
  environment: development
  imagePullPolicy: Always
  labels:
    app.kubernetes.io/part-of: agentgateway
```

### Environment Overrides
Create `values-<env>.yaml` for environment-specific settings:
- Different image tags
- Environment URLs
- Resource limits
- Secrets management

### Component Customization
```bash
# Override subchart values
helm install agentgateway . \
  --set bmg-ui.image.tag=v2.0 \
  --set bmg-agent.secrets.DEEPSEEK_API_KEY=my-key
```

## Key Helm Concepts

### Templating
- `{{ .Values.global.namespace }}`: Access global values
- `{{ include "bmg-agent.fullname" . }}`: Use helper functions
- `{{- with .Values.global.labels }}`: Conditional blocks

### Releases
- Each `helm install` creates a release
- Releases are isolated by namespace
- Multiple releases can coexist

### Dependencies
- Subcharts are installed automatically
- Values merged from parent to child
- Dependencies resolved via `helm dependency update`

## Troubleshooting

### Common Issues
1. **CRD not found**: Install CRDs first
2. **Image pull errors**: Check image registry and credentials
3. **Service not accessible**: Verify namespace and service names

### Debug Commands
```bash
# View rendered templates
helm template agentgateway .

# Check release values
helm get values agentgateway

# View release manifest
helm get manifest agentgateway
```

## Operations

### Upgrade
```bash
helm upgrade agentgateway-dev . --namespace agentgateway-system
```

### Uninstall
```bash
helm uninstall agentgateway-dev --namespace agentgateway-system
```

### List Releases
```bash
helm list --namespace agentgateway-system
```

## Advanced Usage

### CI/CD Integration
```bash
# Automated deployment
helm install agentgateway . \
  --set bmg-ui.image.tag=$GIT_COMMIT \
  --set global.namespace=$ENVIRONMENT
```

### Custom Values Files
```bash
# Create values-staging.yaml
helm install agentgateway-staging . \
  -f values-staging.yaml \
  --namespace agentgateway-staging
```

## Learning Resources

1. **Helm Documentation**: https://helm.sh/docs/
2. **Chart Best Practices**: https://helm.sh/docs/chart_best_practices/
3. **Umbrella Charts**: https://www.un4uthorized.com/articles/umbrella-charts

## Components

- **bmg-agent**: Core agent service
- **bmg-ui**: Web interface
- **mcp-hubspot**: HubSpot MCP server
- **mcp-mssql**: MSSQL MCP server
- **mcpagentcontrolplane**: Gateway and authentication policies

This setup provides a production-ready, maintainable Helm deployment following industry best practices for complex multi-component applications.
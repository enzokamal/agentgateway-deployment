#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration variables
AZURE_TENANT_ID="${AZURE_TENANT_ID:-}"
AZURE_CLIENT_ID="${AZURE_CLIENT_ID:-}"
AZURE_CLIENT_SECRET="${AZURE_CLIENT_SECRET:-}"
KGATEWAY_VERSION="${KGATEWAY_VERSION:-v2.2.0-main}"
GATEWAY_API_VERSION="${GATEWAY_API_VERSION:-v1.4.0}"
MCP_SERVER_IMAGE="${MCP_SERVER_IMAGE:-kamalberrybytes/mcp:1.0.0}"

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    echo_info "Checking prerequisites..."
    
    if ! command -v kubectl &> /dev/null; then
        echo_error "kubectl not found. Please install kubectl first."
        exit 1
    fi
    
    if ! command -v helm &> /dev/null; then
        echo_error "helm not found. Please install helm first."
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        echo_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    echo_info "Prerequisites check passed!"
}

deploy_gateway_api_crds() {
    echo_info "Deploying Kubernetes Gateway API CRDs..."
    kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/${GATEWAY_API_VERSION}/standard-install.yaml
    echo_info "Gateway API CRDs deployed successfully!"
}

deploy_kgateway_crds() {
    echo_info "Deploying kgateway and agentgateway CRDs..."
    helm upgrade -i \
        --create-namespace \
        --namespace kgateway-system \
        --version ${KGATEWAY_VERSION} \
        kgateway-crds \
        oci://cr.kgateway.dev/kgateway-dev/charts/kgateway-crds
    echo_info "kgateway CRDs deployed successfully!"
}

deploy_kgateway_control_plane() {
    echo_info "Installing kgateway control plane with agentgateway enabled..."
    helm upgrade -i \
        --namespace kgateway-system \
        --version ${KGATEWAY_VERSION} \
        kgateway \
        oci://cr.kgateway.dev/kgateway-dev/charts/kgateway \
        --set agentgateway.enabled=true \
        --set controller.image.pullPolicy=Always
    echo_info "kgateway control plane deployed successfully!"
}

wait_for_kgateway() {
    echo_info "Waiting for kgateway control plane to be ready..."
    kubectl wait --for=condition=ready pod \
        -l app.kubernetes.io/name=kgateway \
        -n kgateway-system \
        --timeout=300s
    echo_info "kgateway control plane is ready!"
}

create_agentgateway_proxy() {
    echo_info "Creating agentgateway proxy..."
    
    cat <<EOF | kubectl apply -f -
kind: Gateway
apiVersion: gateway.networking.k8s.io/v1
metadata:
  name: agentgateway
  labels:
    app: agentgateway
spec:
  gatewayClassName: agentgateway
  listeners:
  - protocol: HTTP
    port: 8080
    name: http
    allowedRoutes:
      namespaces:
        from: All
EOF
    
    echo_info "agentgateway proxy created!"
}

wait_for_agentgateway() {
    echo_info "Waiting for agentgateway proxy to be ready..."
    sleep 10
    kubectl wait --for=condition=ready pod \
        -l app=agentgateway \
        --timeout=300s 2>/dev/null || echo_warn "Gateway pod may still be initializing..."
    echo_info "agentgateway proxy is ready!"
}

deploy_mcp_server() {
    echo_info "Deploying MCP example server..."

    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: mcp-example-sa
  namespace: default
  annotations:
    azure.workload.identity/client-id: "${AZURE_CLIENT_ID}"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-example
spec:
  selector:
    matchLabels:
      app: mcp-example
  template:
    metadata:
      labels:
        app: mcp-example
    spec:
      serviceAccountName: mcp-example-sa
      containers:
      - name: mcp-example
        image: ${MCP_SERVER_IMAGE}
        imagePullPolicy: Always
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-example-service
  labels:
    app: mcp-example
spec:
  selector:
    app: mcp-example
  ports:
  - port: 8000
    targetPort: 8000
    appProtocol: kgateway.dev/mcp
EOF

    echo_info "MCP server deployed successfully!"
}

create_azure_auth_policy() {
    if [[ -z "$AZURE_TENANT_ID" ]] || [[ -z "$AZURE_CLIENT_ID" ]]; then
        echo_warn "Azure credentials not provided. Skipping Azure AD authentication policy."
        echo_warn "Set AZURE_TENANT_ID and AZURE_CLIENT_ID environment variables to enable Azure AD auth."
        return
    fi
    
    echo_info "Creating Azure AD authentication policy..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayPolicy
metadata:
  name: azure-mcp-authn-policy
spec:
  targetRefs:
  - name: agentgateway
    kind: Gateway
    group: gateway.networking.k8s.io
  traffic:
    jwtAuthentication:
      mode: Strict
      providers:
      - issuer: https://sts.windows.net/${AZURE_TENANT_ID}/
        jwks:
          remote:
            uri: https://login.microsoftonline.com/${AZURE_TENANT_ID}/discovery/keys
            cacheDuration: 5m
        audiences:
      - "api://${AZURE_CLIENT_ID:-11ddc0cd-e6fc-48b6-8832-de61800fb41e}"
EOF
    
    echo_info "Azure AD authentication policy created!"
}

create_mcp_backend() {
    echo_info "Creating MCP backend..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: agentgateway.dev/v1alpha1
kind: AgentgatewayBackend
metadata:
  name: mcp-example-backend
spec:
  mcp:
    targets:
    - name: mcp-example-target
      static:
        host: mcp-example-service.default.svc.cluster.local
        port: 8000
        protocol: StreamableHTTP
EOF
    
    echo_info "MCP backend created!"
}

create_http_route() {
    echo_info "Creating HTTP route..."

    cat <<EOF | kubectl apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: mcp-example
spec:
  parentRefs:
  - name: agentgateway
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /mcp/mcp-example
    backendRefs:
    - name: mcp-example-backend
      group: agentgateway.dev
      kind: AgentgatewayBackend
EOF

    echo_info "HTTP route created!"
}

deploy_ui() {
    echo_info "Deploying MCP UI application..."

    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: mcp-ui-sa
  namespace: default
  annotations:
    azure.workload.identity/client-id: "${AZURE_CLIENT_ID:-11ddc0cd-e6fc-48b6-8832-de61800fb41e}"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-ui
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mcp-ui
  template:
    metadata:
      labels:
        app: mcp-ui
    spec:
      serviceAccountName: mcp-ui-sa  
      containers:
      - name: mcp-ui
        image: ${MCP_UI_IMAGE:-kamalberrybytes/mcp-ui:latest}
        imagePullPolicy: Always  
        ports:
        - containerPort: 3000
        env:
        - name: AZURE_CLIENT_ID
          value: "${AZURE_CLIENT_ID:-11ddc0cd-e6fc-48b6-8832-de61800fb41e}"
        - name: AZURE_TENANT_ID
          value: "${AZURE_TENANT_ID:-6ba231bb-ad9e-41b9-b23d-674c80196bbd}"
        - name: GATEWAY_URL
          value: "http://agentgateway.default.svc.cluster.local:8080"
        - name: REDIRECT_URI
          value: "http://localhost:3000/auth/callback"
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-ui-service
  labels:
    app: mcp-ui
spec:
  selector:
    app: mcp-ui
  ports:
  - port: 3000
    targetPort: 3000
    protocol: TCP
EOF

    echo_info "MCP UI deployed successfully!"
}

create_ui_route() {
    echo_info "Creating UI HTTP route..."

    cat <<EOF | kubectl apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: mcp-ui
spec:
  parentRefs:
  - name: agentgateway
    group: gateway.networking.k8s.io
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /ui
    backendRefs:
    - name: mcp-ui-service
      port: 3000
EOF

    echo_info "UI HTTP route created!"
}

verify_deployment() {
    echo_info "Verifying deployment..."
    echo ""
    echo_info "Gateway status:"
    kubectl get gateway agentgateway
    echo ""
    echo_info "AgentGateway deployment status:"
    kubectl get deployment agentgateway
    echo ""
    echo_info "MCP server status:"
    kubectl get deployment mcp-example
    echo ""
    echo_info "UI application status:"
    kubectl get deployment mcp-ui
    echo ""
    echo_info "AgentGateway configuration:"
    helm get values kgateway -n kgateway-system
}

print_usage_instructions() {
    echo ""
    echo_info "=========================================="
    echo_info "Deployment completed successfully!"
    echo_info "=========================================="
    echo ""
    echo_info "To port-forward the agentgateway service:"
    echo "  kubectl port-forward svc/agentgateway 8080:8080 --address 0.0.0.0"
    echo ""
    echo_info "UI Application:"
    echo "  Access the UI at: http://localhost:8080/ui"
    echo "  The UI handles automatic Entra ID authentication and provides access to MCP servers."
    echo ""

    if [[ -n "$AZURE_TENANT_ID" ]] && [[ -n "$AZURE_CLIENT_ID" ]] && [[ -n "$AZURE_CLIENT_SECRET" ]]; then
        echo_info "To generate an Azure AD token manually:"
        echo "  curl -X POST https://login.microsoftonline.com/${AZURE_TENANT_ID}/oauth2/v2.0/token \\"
        echo "    -H \"Content-Type: application/x-www-form-urlencoded\" \\"
        echo "    -d \"client_id=${AZURE_CLIENT_ID}\" \\"
        echo "    -d \"client_secret=${AZURE_CLIENT_SECRET}\" \\"
        echo "    -d \"scope=api://${AZURE_CLIENT_ID}/.default\" \\"
        echo "    -d \"grant_type=client_credentials\""
        echo ""
    fi

    echo_info "To access MCP servers directly through agentgateway:"
    echo "  curl -H \"Authorization: Bearer <your-token>\" http://localhost:8080/mcp/mcp-example"
    echo ""
}

main() {
    echo_info "Starting agentgateway deployment..."
    echo ""

    check_prerequisites
    deploy_gateway_api_crds
    deploy_kgateway_crds
    deploy_kgateway_control_plane
    wait_for_kgateway
    create_agentgateway_proxy
    wait_for_agentgateway
    deploy_mcp_server
    create_azure_auth_policy
    create_mcp_backend
    create_http_route
    deploy_ui
    create_ui_route
    verify_deployment
    print_usage_instructions
}

main "$@"

#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables
MCP_UI_IMAGE="${MCP_UI_IMAGE:-kamalberrybytes/mcp-ui:latest}"
NAMESPACE="${NAMESPACE:-default}"
AZURE_CLIENT_SECRET="${AZURE_CLIENT_SECRET:-}"

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {  
    echo -e "${RED}[ERROR]${NC} $1"
}

echo_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

check_prerequisites() {
    echo_step "Checking prerequisites..."

    if ! command -v kubectl &> /dev/null; then
        echo_error "kubectl not found. Please install kubectl first."
        exit 1
    fi

    if ! command -v docker &> /dev/null; then
        echo_error "docker not found. Please install docker first."
        exit 1
    fi

    if ! kubectl cluster-info &> /dev/null; then
        echo_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi

    echo_info "Prerequisites check passed!"
}

build_ui_image() {
    echo_step "Building MCP UI Docker image..."

    cd mcp-ui-app

    # Check if package.json exists
    if [ ! -f "package.json" ]; then
        echo_error "package.json not found in mcp-ui-app directory"
        exit 1
    fi

    # Install dependencies
    echo_info "Installing Node.js dependencies..."
    npm install

    # Build Docker image
    echo_info "Building Docker image: ${MCP_UI_IMAGE}"
    docker build -t "${MCP_UI_IMAGE}" .

    echo_info "Docker image built successfully!"
    cd ..
}

push_ui_image() {
    echo_step "Pushing MCP UI Docker image..."

    # Extract registry from image name
    if [[ "${MCP_UI_IMAGE}" == *"/"* ]]; then
        echo_info "Pushing image to registry: ${MCP_UI_IMAGE}"
        docker push "${MCP_UI_IMAGE}"
    else
        echo_warn "Image name doesn't contain registry. Skipping push."
        echo_warn "To push to Docker Hub, use: your-username/mcp-ui:latest"
    fi
}

deploy_ui_service_account() {
    echo_step "Creating MCP UI Service Account..."

    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: mcp-ui-sa
  namespace: ${NAMESPACE}
  annotations:
    azure.workload.identity/client-id: "11ddc0cd-e6fc-48b6-8832-de61800fb41e"
EOF

    echo_info "Service Account created!"
}

deploy_ui_secret() {
    echo_step "Creating MCP UI Secret..."

    # Check if secret already exists
    if kubectl get secret mcp-ui-secret -n ${NAMESPACE} &> /dev/null; then
        echo_info "Secret already exists, skipping creation"
        return
    fi

    # Prompt for client secret if not provided
    if [[ -z "${AZURE_CLIENT_SECRET}" ]]; then
        echo_warn "AZURE_CLIENT_SECRET not set. Please provide your Azure AD application client secret:"
        read -s -p "Client Secret: " AZURE_CLIENT_SECRET
        echo ""
    fi

    if [[ -z "${AZURE_CLIENT_SECRET}" ]]; then
        echo_error "Client secret is required for authentication"
        exit 1
    fi

    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: mcp-ui-secret
  namespace: ${NAMESPACE}
type: Opaque
data:
  client-secret: $(echo -n "${AZURE_CLIENT_SECRET}" | base64)
EOF

    echo_info "Secret created!"
}

deploy_ui_deployment() {
    echo_step "Deploying MCP UI Application..."

    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-ui
  namespace: ${NAMESPACE}
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
        image: ${MCP_UI_IMAGE}
        imagePullPolicy: Always
        ports:
        - containerPort: 3000
        env:
        - name: AZURE_CLIENT_ID
          value: "11ddc0cd-e6fc-48b6-8832-de61800fb41e"
        - name: AZURE_TENANT_ID
          value: "6ba231bb-ad9e-41b9-b23d-674c80196bbd"
        - name: GATEWAY_URL
          value: "http://agentgateway.default.svc.cluster.local:8080"
        - name: REDIRECT_URI
          value: "http://localhost:3000/auth/callback"
        - name: NODE_ENV
          value: "production"
EOF

    echo_info "MCP UI Deployment created!"
}

deploy_ui_service() {
    echo_step "Creating MCP UI Service..."

    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: mcp-ui-service
  namespace: ${NAMESPACE}
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

    echo_info "MCP UI Service created!"
}

deploy_ui_route() {
    echo_step "Creating MCP UI HTTP Route..."

    cat <<EOF | kubectl apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: mcp-ui
  namespace: ${NAMESPACE}
spec:
  parentRefs:
  - name: agentgateway
    namespace: kgateway-system
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

    echo_info "MCP UI HTTP Route created!"
}

wait_for_ui_deployment() {
    echo_step "Waiting for MCP UI deployment to be ready..."

    kubectl wait --for=condition=available --timeout=300s deployment/mcp-ui -n ${NAMESPACE}

    echo_info "MCP UI deployment is ready!"
}

verify_ui_deployment() {
    echo_step "Verifying MCP UI deployment..."

    echo ""
    echo_info "Deployment status:"
    kubectl get deployment mcp-ui -n ${NAMESPACE}

    echo ""
    echo_info "Service status:"
    kubectl get service mcp-ui-service -n ${NAMESPACE}

    echo ""
    echo_info "HTTP Route status:"
    kubectl get httproute mcp-ui -n ${NAMESPACE}

    echo ""
    echo_info "Pod status:"
    kubectl get pods -l app=mcp-ui -n ${NAMESPACE}
}

print_deployment_info() {
    echo ""
    echo_info "=========================================="
    echo_info "MCP UI Deployment Completed Successfully!"
    echo_info "=========================================="
    echo ""
    echo_info "Access URLs:"
    echo_info "  UI Application: http://localhost:8080/ui"
    echo ""
    echo_info "To port-forward for local access:"
    echo "  kubectl port-forward svc/mcp-ui-service 3000:3000 -n ${NAMESPACE}"
    echo ""
    echo_info "Features:"
    echo "  ✅ Chat interface with MCP servers"
    echo "  ✅ Real-time WebSocket communication"
    echo "  ✅ MCP protocol support"
    echo "  ✅ Multi-server chat capabilities"
    echo "  ✅ Automatic authentication (configurable)"
    echo ""
}

usage() {
    echo "MCP UI Deployment Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -b, --build     Build Docker image"
    echo "  -p, --push      Push Docker image"
    echo "  -d, --deploy    Deploy to Kubernetes"
    echo "  -a, --all       Build, push and deploy"
    echo "  -h, --help      Show this help"
    echo ""
    echo "Environment Variables:"
    echo "  MCP_UI_IMAGE    Docker image name (default: kamalberrybytes/mcp-ui:latest)"
    echo "  NAMESPACE       Kubernetes namespace (default: default)"
    echo ""
    echo "Examples:"
    echo "  $0 --all                                    # Full deployment"
    echo "  MCP_UI_IMAGE=myuser/mcp-ui:latest $0 --all  # Custom image"
    echo "  $0 --build --push                          # Just build and push"
    echo "  $0 --deploy                                # Just deploy"
}

main() {
    local build=false
    local push=false
    local deploy=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -b|--build)
                build=true
                shift
                ;;
            -p|--push)
                push=true
                shift
                ;;
            -d|--deploy)
                deploy=true
                shift
                ;;
            -a|--all)
                build=true
                push=true
                deploy=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                echo_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done

    # Default to deploy if no options specified
    if [[ "$build" == false && "$push" == false && "$deploy" == false ]]; then
        deploy=true
    fi

    echo_info "MCP UI Deployment Script"
    echo_info "Image: ${MCP_UI_IMAGE}"
    echo_info "Namespace: ${NAMESPACE}"
    echo ""

    check_prerequisites

    if [[ "$build" == true ]]; then
        build_ui_image
    fi

    if [[ "$push" == true ]]; then
        push_ui_image
    fi

    if [[ "$deploy" == true ]]; then
        deploy_ui_service_account
        deploy_ui_secret
        deploy_ui_deployment
        deploy_ui_service
        deploy_ui_route
        wait_for_ui_deployment
        verify_ui_deployment
        print_deployment_info
    fi

    echo_info "MCP UI deployment operations completed!"
}

main "$@"
#!/bin/bash

set -e

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

# Configuration variables
readonly AZURE_TENANT_ID="${AZURE_TENANT_ID:-}"
readonly AZURE_CLIENT_ID="${AZURE_CLIENT_ID:-}"
readonly KGATEWAY_VERSION="${KGATEWAY_VERSION:-v2.2.0-main}"
readonly GATEWAY_API_VERSION="${GATEWAY_API_VERSION:-v1.4.0}"
readonly SERVICE_NAME="mcp-ui-service"
readonly SCREEN_SESSION="mcp-ui-forward"
readonly KGATEWAY_NAMESPACE="kgateway-system"
readonly DEFAULT_TIMEOUT="300s"

# Logging functions
echo_info() { echo  "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo  "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo  "${RED}[ERROR]${NC} $1" >&2; }

# Check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Generic installer for binary tools
install_binary() {
    local name=$1
    local url=$2
    local binary_name=${3:-$name}
    
    echo_info "Installing $name..."
    curl -fsSL "$url" -o "/tmp/$binary_name"
    chmod +x "/tmp/$binary_name"
    sudo mv "/tmp/$binary_name" "/usr/local/bin/$binary_name"
    echo_info "$name installed successfully"
}

# Check and install kind
ensure_kind() {
    if command_exists kind; then
        echo_info "kind already installed: $(kind version)"
        return 0
    fi
    
    echo_info "Installing kind..."
    local version
    version=$(curl -fsSL https://api.github.com/repos/kubernetes-sigs/kind/releases/latest | \
              grep -Po '"tag_name": "\K[^"]+')
    install_binary "kind" "https://kind.sigs.k8s.io/dl/${version}/kind-linux-amd64" "kind"
    echo_info "kind installed: $(kind version)"
}

# Check and install kubectl
ensure_kubectl() {
    if command_exists kubectl; then
        echo_info "kubectl already installed: $(kubectl version --client --short 2>/dev/null || kubectl version --client)"
        return 0
    fi
    
    echo_info "Installing kubectl..."
    local version
    version=$(curl -fsSL https://dl.k8s.io/release/stable.txt)
    install_binary "kubectl" "https://dl.k8s.io/release/${version}/bin/linux/amd64/kubectl" "kubectl"
    echo_info "kubectl installed: $(kubectl version --client --short 2>/dev/null)"
}

# Check and install Helm
ensure_helm() {
    if command_exists helm; then
        echo_info "Helm already installed: $(helm version --short)"
        return 0
    fi
    
    echo_info "Installing Helm..."
    curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
    echo_info "Helm installed: $(helm version --short)"
}

# Deploy Gateway API CRDs
deploy_gateway_api_crds() {
    echo_info "Deploying Kubernetes Gateway API CRDs (${GATEWAY_API_VERSION})..."
    kubectl apply -f "https://github.com/kubernetes-sigs/gateway-api/releases/download/${GATEWAY_API_VERSION}/standard-install.yaml"
    echo_info "Gateway API CRDs deployed successfully!"
}

# Deploy kgateway CRDs
deploy_kgateway_crds() {
    echo_info "Deploying kgateway and agentgateway CRDs (${KGATEWAY_VERSION})..."
    helm upgrade -i \
        --create-namespace \
        --namespace "${KGATEWAY_NAMESPACE}" \
        --version "${KGATEWAY_VERSION}" \
        kgateway-crds \
        oci://cr.kgateway.dev/kgateway-dev/charts/kgateway-crds
    echo_info "kgateway CRDs deployed successfully!"
}

# Deploy kgateway control plane
deploy_kgateway_control_plane() {
    echo_info "Installing kgateway control plane with agentgateway enabled..."
    helm upgrade -i \
        --namespace "${KGATEWAY_NAMESPACE}" \
        --version "${KGATEWAY_VERSION}" \
        kgateway \
        oci://cr.kgateway.dev/kgateway-dev/charts/kgateway \
        --set agentgateway.enabled=true \
        --set controller.image.pullPolicy=Always
    echo_info "kgateway control plane deployed successfully!"
}

# Wait for kgateway
wait_for_kgateway() {
    echo_info "Waiting for kgateway control plane to be ready..."
    if kubectl wait --for=condition=ready pod \
        -l app.kubernetes.io/name=kgateway \
        -n "${KGATEWAY_NAMESPACE}" \
        --timeout="${DEFAULT_TIMEOUT}"; then
        echo_info "kgateway control plane is ready!"
    else
        echo_error "Timeout waiting for kgateway control plane"
        exit 1
    fi
}

# Create agentgateway proxy
create_agentgateway_proxy() {
    echo_info "Creating agentgateway proxy..."
    kubectl apply -f mcpagentcontrolplane/mcp-gateway-proxy.yml
    echo_info "agentgateway proxy created!"
}

# Wait for agentgateway
wait_for_agentgateway() {
    echo_info "Waiting for agentgateway proxy to be ready..."
    sleep 10
    kubectl wait --for=condition=ready pod \
        -l app=agentgateway \
        --timeout="${DEFAULT_TIMEOUT}" 2>/dev/null || \
        echo_warn "Gateway pod may still be initializing..."
    echo_info "agentgateway proxy is ready!"
}

# Deploy MCP servers
deploy_mcp_servers() {
    echo_info "Deploying MCP servers..."
    
    # Deploy mcp-example
    kubectl apply -f mcp-server/mcp-example/mcp-example-deployment.yml
    kubectl apply -f mcp-server/mcp-example/mcp-example-backend.yml
    kubectl apply -f mcp-server/mcp-example/mcp-example-http-route.yml

    # Deploy mcp-hubspot
    kubectl apply -f mcp-server/mcp-hubspot/mcp-hubspot-deployment.yml
    kubectl apply -f mcp-server/mcp-hubspot/mcp-hubspot-backend.yml
    kubectl apply -f mcp-server/mcp-hubspot/mcp-hubspot-http-route.yml

    # Deploy mcp-mssql
    kubectl apply -f mcp-server/mcp-mssql/mcp-sql-deployment.yml
    kubectl apply -f mcp-server/mcp-mssql/mcp-sql-backend.yml
    kubectl apply -f mcp-server/mcp-mssql/mcp-sql-http-route.yml
    
    echo_info "MCP servers deployed successfully!"
}

# # Create Azure AD authentication policy
# create_azure_auth_policy() {
#     if [[ -z "$AZURE_TENANT_ID" ]] || [[ -z "$AZURE_CLIENT_ID" ]]; then
#         echo_warn "Azure credentials not provided. Skipping Azure AD authentication policy."
#         echo_warn "Set AZURE_TENANT_ID and AZURE_CLIENT_ID environment variables to enable Azure AD auth."
#         return 0
#     fi

#     echo_info "Creating Azure AD authentication policy..."
#     kubectl apply -f mcpagentcontrolplane/agent-gateway-policy.yml
#     echo_info "Azure AD authentication policy created!"
# }

# Deploy MCP Agent Gateway UI
deploy_mcp_agentgateway_ui() {
    echo_info "Deploying MCP Agent Gateway UI..."
    kubectl apply -f mcp-ui/mcp-ui-deployment.yml
    kubectl apply -f mcp-ui/mcp-ui-http-route.yml
    echo_info "MCP Agentgateway UI deployed successfully!"
}

# ---------------------------------------
# 6. Check/install screen
# ---------------------------------------
check_screen() {
    if ! command -v screen >/dev/null 2>&1; then
        echo "📥 Installing screen..."
        sudo apt-get update && sudo apt-get install -y screen
    fi
}

# Start port-forward in detached screen
port_forward_service() {
    echo_info "Ensuring port-forward for ${SERVICE_NAME}..."

    # Check if session exists and port-forward is running
    if screen -list | grep -qw "$SCREEN_SESSION"; then
        if pgrep -f "kubectl port-forward.*${SERVICE_NAME}" >/dev/null; then
            echo_info "Port-forward already running."
            return 0
        else
            screen -S "$SCREEN_SESSION" -X quit 2>/dev/null || true
        fi
    fi

    # Start detached screen with auto-restart loop
    screen -dmS "$SCREEN_SESSION" bash -c \
        "while true; do kubectl port-forward svc/${SERVICE_NAME} 4000:3000; sleep 5; done"

    echo_info "Port-forward started in detached screen: ${SCREEN_SESSION}"
    echo_info "Access UI at: http://localhost:4000"
    echo_info "To attach: screen -r ${SCREEN_SESSION}"
}

# Verify deployment
verify_deployment() {
    echo_info "Verifying deployment..."
    echo ""
    
    echo_info "Gateway status:"
    kubectl get gateway agentgateway || echo_warn "Gateway not found"
    echo ""
    
    echo_info "AgentGateway deployment status:"
    kubectl get deployment agentgateway || echo_warn "Deployment not found"
    echo ""
    
    echo_info "MCP servers status:"
    kubectl get deployment mcp-example mcp-hubspot mcp-mssql || echo_warn "Some deployments not found"
    echo ""
    
    echo_info "AgentGateway configuration:"
    helm get values kgateway -n "${KGATEWAY_NAMESPACE}"
}

# Print usage instructions
print_usage_instructions() {
    cat << EOF

$(echo_info "==========================================")
$(echo_info "Deployment completed successfully!")
$(echo_info "==========================================")

Access the UI at: http://localhost:4000

To view port-forward logs:
  screen -r ${SCREEN_SESSION}

To detach from screen:
  Press Ctrl+A, then D

To stop port-forward:
  screen -S ${SCREEN_SESSION} -X quit

EOF
}

# Main execution
main() {
    echo_info "Starting agentgateway deployment..."
    echo ""


    # check_prerequisites
    ensure_kind
    ensure_helm
    deploy_gateway_api_crds
    deploy_kgateway_crds
    deploy_kgateway_control_plane
    wait_for_kgateway
    create_agentgateway_proxy
    wait_for_agentgateway
    deploy_mcp_servers
    # create_azure_auth_policy
    deploy_mcp_agentgateway_ui
    check_screen
    port_forward_service
    verify_deployment
    print_usage_instructions
}

main "$@"
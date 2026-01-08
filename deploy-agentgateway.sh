#!/bin/bash

set -euo pipefail


# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

# Configuration variables
readonly AGENTGATEWAY_CRDS_VERSION="${AGENTGATEWAY_CRDS_VERSION:-v2.2.0-beta.4}"
readonly GATEWAY_API_VERSION="${GATEWAY_API_VERSION:-v1.4.0}"
readonly UI_SERVICE_NAME="adk-ui-service"
readonly AGENTGATEWAY_NAMESPACE="agentgateway-system"
readonly DEFAULT_TIMEOUT="300s"

# Logging functions
echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

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
    kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.4.0/standard-install.yaml
    echo_info "Gateway API CRDs deployed successfully!"
}

# Deploy the CRDs for the Agentgateway  
deploy_agentgateway_crds() {
    echo_info "Deploying kgateway and agentgateway CRDs (${AGENTGATEWAY_CRDS_VERSION})..."
        
        helm upgrade --install agentgateway-crds \
        oci://cr.agentgateway.dev/charts/agentgateway-crds \
        --version "${AGENTGATEWAY_CRDS_VERSION}" \
        --namespace "${AGENTGATEWAY_NAMESPACE}" \
        --create-namespace 
       

    echo_info "Agentgateway CRDs installed / deployed successfully!"

}

# Deploy Agentgateway 
deploy_agentgateway() {
    echo_info "Installing Agentgateway..."

    echo "Installing/Upgrading AgentGateway..."

    helm upgrade --install agentgateway \
        oci://cr.agentgateway.dev/charts/agentgateway \
        --version "${AGENTGATEWAY_CRDS_VERSION}" \
        --namespace "${AGENTGATEWAY_NAMESPACE}" \
        --create-namespace

    echo_info "Agentgateway installed / deployed successfully!"
}

# Create agentgateway proxy
create_agentgateway_proxy() {
    echo_info "Creating agentgateway proxy..."
    kubectl apply -f mcpagentcontrolplane/mcp-gateway-proxy.yml -n "${AGENTGATEWAY_NAMESPACE}"
    echo_info "agentgateway proxy created!"
}

# Wait for agentgateway proxy
wait_for_agentgateway_proxy() {
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

    # Deploy mcp-hubspot
    kubectl apply -f mcp-server/mcp-hubspot/mcp-hubspot-deployment.yml -n "${AGENTGATEWAY_NAMESPACE}"
    kubectl apply -f mcp-server/mcp-hubspot/mcp-hubspot-backend.yml -n "${AGENTGATEWAY_NAMESPACE}"
    kubectl apply -f mcp-server/mcp-hubspot/mcp-hubspot-http-route.yml -n "${AGENTGATEWAY_NAMESPACE}"

    # Deploy mcp-mssql
    kubectl apply -f mcp-server/mcp-mssql/mcp-sql-deployment.yml -n "${AGENTGATEWAY_NAMESPACE}"
    kubectl apply -f mcp-server/mcp-mssql/mcp-sql-backend.yml -n "${AGENTGATEWAY_NAMESPACE}"
    kubectl apply -f mcp-server/mcp-mssql/mcp-sql-http-route.yml -n "${AGENTGATEWAY_NAMESPACE}"
    
    echo_info "MCP servers deployed successfully!"
}


# Create Azure AD authentication policy
create_azure_auth_policy() {

    echo_info "Creating Azure AD authentication policy..."
    kubectl apply -f mcpagentcontrolplane/agent-gateway-policy.yml -n "${AGENTGATEWAY_NAMESPACE}"
    echo_info "Azure AD authentication policy created!"
}


deploy_adk_agentgateway_ui() {
    echo_info "Deploying ADK Agent Gateway UI..."
    kubectl apply -f adk-ui-deployment/adk-ui-deployment.yml -n "${AGENTGATEWAY_NAMESPACE}"
    kubectl apply -f adk-ui-deployment/adk-ui-http-route.yml -n "${AGENTGATEWAY_NAMESPACE}"
    echo_info "ADK Agent Gateway UI deployed successfully!"
}

deploy_adk_agent_deployment(){
    echo_info "Deploying ADK Agent"
    kubectl apply -f adk-agent-deployment/adk-agent-deployment.yml -n "${AGENTGATEWAY_NAMESPACE}"
    kubectl apply -f adk-agent-deployment/adk-secret.yml -n "${AGENTGATEWAY_NAMESPACE}"

    echo_info "ADK Agent Deployed successfully!"
}

# Verify deployment
verify_deployment() {
    echo_info "Verifying deployment..."
    echo ""
     
    echo_info "AgentGateway deployment status:"
    kubectl get deployment agentgateway-proxy adk-agent-deployment adk-ui -n "${AGENTGATEWAY_NAMESPACE}" || echo_warn "Deployment not found"
    echo ""
    
    echo_info "MCP servers status:"
    kubectl get deployment mcp-hubspot mcp-mssql -n "${AGENTGATEWAY_NAMESPACE}" || echo_warn "Some deployments not found"
    echo ""
    
}

# Print usage instructions
print_usage_instructions() {
    echo_info "=========================================="
    echo_info "Deployment completed successfully!"
    echo_info "=========================================="
    echo ""
    echo "Access the UI at: http://localhost:5000"
    echo ""
}

# Main execution
main() {
    echo_info "Starting agentgateway deployment..."
    echo ""

    ensure_kubectl
    ensure_helm
    deploy_gateway_api_crds
    deploy_agentgateway_crds
    deploy_agentgateway
    create_agentgateway_proxy
    wait_for_agentgateway_proxy
    deploy_mcp_servers
    # deploy_cronjob
    create_azure_auth_policy
    deploy_adk_agentgateway_ui
    deploy_adk_agent_deployment
    verify_deployment
    print_usage_instructions
}

main "$@"

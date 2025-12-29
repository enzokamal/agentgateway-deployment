#!/bin/bash

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

# Configuration variables
readonly AZURE_TENANT_ID="${AZURE_TENANT_ID:-}"
readonly AZURE_CLIENT_ID="${AZURE_CLIENT_ID:-}"
readonly AGENTGATEWAY_CRDS_VERSION="${AGENTGATEWAY_CRDS_VERSION:-v2.2.0-beta.4}"
readonly GATEWAY_API_VERSION="${GATEWAY_API_VERSION:-v1.4.0}"
readonly UI_SERVICE_NAME="mcp-ui-service"
readonly SCREEN_SESSION="mcp-ui-forward"
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

# ---------------------------------------
# 1. Install Helm chart
# ---------------------------------------
install_mssql_helm() {
    RELEASE_NAME="my-mssqlserver-2022"
    CHART="simcube/mssqlserver-2022"
    VERSION="1.2.3"
    NAMESPACE="agentgateway-system"

    echo "🔹 Adding Helm repo simcube..."
    helm repo add simcube https://simcubeltd.github.io/simcube-helm-charts/
    helm repo update

    if helm list -n $NAMESPACE | grep -qw "$RELEASE_NAME"; then
        echo "✔ Helm release $RELEASE_NAME already installed."
    else
        echo "🚀 Installing Helm chart $CHART..."
        helm install $RELEASE_NAME $CHART --version $VERSION -n $NAMESPACE --create-namespace
    fi

    echo "⏳ Waiting for pods from Helm release $RELEASE_NAME..."
    while true; do
        NOT_READY=$(kubectl get pods -n $NAMESPACE -l "app.kubernetes.io/instance=$RELEASE_NAME" --no-headers 2>/dev/null \
            | awk '{split($2,a,"/"); if(a[1]!=a[2]) print $1, $2, $3}')
        if [[ -z "$NOT_READY" ]]; then
            echo "✔ All pods for Helm release $RELEASE_NAME are ready."
            break
        else
            echo "⌛ Pods not ready yet:"
            echo "$NOT_READY"
            sleep 5
        fi
    done

    # Fetch the auto-generated MSSQL password from the Helm secret
    PASSWORD=$(kubectl get secret -n $NAMESPACE ${RELEASE_NAME}-secret -o jsonpath="{.data.sapassword}" | base64 --decode)
    echo "🔑 Fetched MSSQL password from Helm chart: $PASSWORD"

    # Export for later use in POST request
    export MSSQL_PASSWORD="$PASSWORD"
}

# ---------------------------------------
# 2. Wait for pods in namespace
# ---------------------------------------
NAMESPACE="agentgateway-system"
wait_for_pods() {
    echo "⏳ Waiting for pods in namespace $NAMESPACE..."
    kubectl get ns "$NAMESPACE" >/dev/null 2>&1 || kubectl create ns "$NAMESPACE"

    while true; do
        NOT_READY=$(kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null \
            | awk '{split($2,a,"/"); if(a[1]!=a[2]) print $1, $2, $3}')
        
        if [[ -z "$NOT_READY" ]]; then
            echo "✔ All pods in $NAMESPACE are ready."
            break
        else
            echo "⌛ Pods not ready yet:"
            echo "$NOT_READY"
            sleep 10
        fi
    done
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

    # # Ensure namespace exists
    # kubectl get namespace "${AGENTGATEWAY_NAMESPACE}" >/dev/null 2>&1 || \
    #     kubectl create namespace "${AGENTGATEWAY_NAMESPACE}"

    echo "Installing/Upgrading AgentGateway..."

    helm upgrade --install agentgateway \
        oci://cr.agentgateway.dev/charts/agentgateway \
        --version "${AGENTGATEWAY_CRDS_VERSION}" \
        --namespace "${AGENTGATEWAY_NAMESPACE}" \
        --create-namespace

    echo_info "Agentgateway installed / deployed successfully!"
}




# # Wait for agentgateway control plane
# wait_for_agentgateway_control_plane() {
#     echo_info "Waiting for agentgateway Agentgateway be ready..."
#     if kubectl wait --for=condition=ready pod \
#         -l app.kubernetes.io/name=agentgateway \
#         -n "${AGENTGATEWAY_NAMESPACE}" \
#         --timeout="${DEFAULT_TIMEOUT}"; then
#         echo_info "agentgateway control plane is ready!"
#     else
#         echo_error "Timeout waiting for agentgateway control plane"
#         exit 1
#     fi
# }

# Create agentgateway proxy
create_agentgateway_proxy() {
    echo_info "Creating agentgateway proxy..."
    kubectl apply -f mcpagentcontrolplane/mcp-gateway-proxy.yml
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

# Deploy cronjob
deploy_cronjob() {
    echo_info "Deploying cronjob..."
    kubectl apply -f cronjob/cronjob-deployment.yml
    echo_info "Cronjob deployed successfully!"
}

# Create Azure AD authentication policy
create_azure_auth_policy() {
    if [[ -z "$AZURE_TENANT_ID" ]] || [[ -z "$AZURE_CLIENT_ID" ]]; then
        echo_warn "Azure credentials not provided. Skipping Azure AD authentication policy."
        echo_warn "Set AZURE_TENANT_ID and AZURE_CLIENT_ID environment variables to enable Azure AD auth."
        return 0
    fi

    echo_info "Creating Azure AD authentication policy..."
    kubectl apply -f mcpagentcontrolplane/agent-gateway-policy.yml
    echo_info "Azure AD authentication policy created!"
}

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
    echo_info "Ensuring port-forward for ${UI_SERVICE_NAME}..."

    # Check if session exists and port-forward is running
    if screen -list | grep -qw "$SCREEN_SESSION"; then
        if pgrep -f "kubectl port-forward.*${UI_SERVICE_NAME}" >/dev/null; then
            echo_info "Port-forward already running."
            return 0
        else
            screen -S "$SCREEN_SESSION" -X quit 2>/dev/null || true
        fi
    fi

    # Start detached screen with auto-restart loop
    screen -dmS "$SCREEN_SESSION" bash -c \
        "while true; do kubectl port-forward svc/${UI_SERVICE_NAME} 4000:3000 -n "${AGENTGATEWAY_NAMESPACE}" ; sleep 5; done"

    echo_info "Port-forward started in detached screen: ${SCREEN_SESSION}"
    echo_info "Access UI at: http://localhost:4000"
    echo_info "To attach: screen -r ${SCREEN_SESSION}"
}

# Verify deployment
verify_deployment() {
    echo_info "Verifying deployment..."
    echo ""
     
    echo_info "AgentGateway deployment status:"
    kubectl get deployment agentgateway-proxy -n "${AGENTGATEWAY_NAMESPACE}" || echo_warn "Deployment not found"
    echo ""
    
    echo_info "MCP servers status:"
    kubectl get deployment mcp-example mcp-hubspot mcp-mssql -n "${AGENTGATEWAY_NAMESPACE}" || echo_warn "Some deployments not found"
    echo ""
    
}

# Print usage instructions
print_usage_instructions() {
    echo_info "=========================================="
    echo_info "Deployment completed successfully!"
    echo_info "=========================================="
    echo ""
    echo "Access the UI at: http://localhost:4000"
    echo ""
    echo "To view port-forward logs:"
    echo "  screen -r ${SCREEN_SESSION}"
    echo ""
    echo "To detach from screen:"
    echo "  Press Ctrl+A, then D"
    echo ""
    echo "To stop port-forward:"
    echo "  screen -S ${SCREEN_SESSION} -X quit"
}

# Main execution
main() {
    echo_info "Starting agentgateway deployment..."
    echo ""

    # check_prerequisites
    # ensure_kind
    ensure_kubectl
    ensure_helm
    install_mssql_helm
    wait_for_pods
    deploy_gateway_api_crds
    deploy_agentgateway_crds
    deploy_agentgateway
    # wait_for_agentgateway_control_plane
    create_agentgateway_proxy
    wait_for_agentgateway_proxy
    deploy_mcp_servers
    deploy_cronjob
    create_azure_auth_policy
    deploy_mcp_agentgateway_ui
    check_screen
    port_forward_service
    verify_deployment
    print_usage_instructions
}

main "$@"
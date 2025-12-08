# #!/bin/bash

# set -e

# # Colors for output
# RED='\033[0;31m'
# GREEN='\033[0;32m'
# YELLOW='\033[1;33m'
# NC='\033[0m' # No Color

# # Configuration variables
# AZURE_TENANT_ID="${AZURE_TENANT_ID:-}"
# AZURE_CLIENT_ID="${AZURE_CLIENT_ID:-}"
# KGATEWAY_VERSION="${KGATEWAY_VERSION:-v2.2.0-main}"
# GATEWAY_API_VERSION="${GATEWAY_API_VERSION:-v1.4.0}"
# # CLUSTER_NAME="mcp"
# # DEPLOY_FILE="local-deployment.yaml"
# # NAMESPACE="adapter"
# SERVICE_NAME="mcp-ui-service"
# SCREEN_SESSION="mcp-ui-forward"

# echo_info() {
#     echo -e "${GREEN}[INFO]${NC} $1"
# }

# echo_warn() {
#     echo -e "${YELLOW}[WARN]${NC} $1"
# }

# echo_error() {
#     echo -e "${RED}[ERROR]${NC} $1"
# }

# check_prerequisites() {
#     echo_info "Checking prerequisites..."
    
#     if ! command -v kubectl &> /dev/null; then
#         echo_error "kubectl not found. Please install kubectl first."
#         exit 1
#     fi
    
#     if ! command -v helm &> /dev/null; then
#         echo_error "helm not found. Please install helm first."
#         exit 1
#     fi
    
#     if ! kubectl cluster-info &> /dev/null; then
#         echo_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
#         exit 1
#     fi
    
#     echo_info "Prerequisites check passed!"
# }

# deploy_gateway_api_crds() {
#     echo_info "Deploying Kubernetes Gateway API CRDs..."
#     kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.4.0/standard-install.yaml
#     echo_info "Gateway API CRDs deployed successfully!"
# }

# deploy_kgateway_crds() {
#     echo_info "Deploying kgateway and agentgateway CRDs..."
#     helm upgrade -i \
#         --create-namespace \
#         --namespace kgateway-system \
#         --version ${KGATEWAY_VERSION} \
#         kgateway-crds \
#         oci://cr.kgateway.dev/kgateway-dev/charts/kgateway-crds
#     echo_info "kgateway CRDs deployed successfully!"
# }

# deploy_kgateway_control_plane() {
#     echo_info "Installing kgateway control plane with agentgateway enabled..."
#     helm upgrade -i \
#         --namespace kgateway-system \
#         --version ${KGATEWAY_VERSION} \
#         kgateway \
#         oci://cr.kgateway.dev/kgateway-dev/charts/kgateway \
#         --set agentgateway.enabled=true \
#         --set controller.image.pullPolicy=Always
#     echo_info "kgateway control plane deployed successfully!"
# }

# wait_for_kgateway() {
#     echo_info "Waiting for kgateway control plane to be ready..."
#     kubectl wait --for=condition=ready pod \
#         -l app.kubernetes.io/name=kgateway \
#         -n kgateway-system \
#         --timeout=300s
#     echo_info "kgateway control plane is ready!"
# }

# create_agentgateway_proxy() {
#     echo_info "Creating agentgateway proxy..."
    
#     ## Deploy the agentgateway proxy
#     kubectl apply -f mcpagentcontrolplane/mcp-gateway-proxy.yml

    
#     echo_info "agentgateway proxy created!"
# }

# wait_for_agentgateway() {
#     echo_info "Waiting for agentgateway proxy to be ready..."
#     sleep 10
#     kubectl wait --for=condition=ready pod \
#         -l app=agentgateway \
#         --timeout=300s 2>/dev/null || echo_warn "Gateway pod may still be initializing..."
#     echo_info "agentgateway proxy is ready!"
# }

# deploy_mcp_servers() {
#     echo_info "Deploying MCP servers..."

#     # Deploy mcp-example
#     kubectl apply -f mcp-server/mcp-example/mcp-example-deployment.yml
#     kubectl apply -f mcp-server/mcp-example/mcp-example-backend.yml
#     kubectl apply -f mcp-server/mcp-example/mcp-example-http-route.yml

#     # Deploy mcp-hubspot
#     kubectl apply -f mcp-server/mcp-hubspot/mcp-hubspot-deployment.yml
#     kubectl apply -f mcp-server/mcp-hubspot/mcp-hubspot-backend.yml
#     kubectl apply -f mcp-server/mcp-hubspot/mcp-hubspot-http-route.yml

#     # Deploy mcp-mssql
#     kubectl apply -f mcp-server/mcp-mssql/mcp-sql-deployment.yml
#     kubectl apply -f mcp-server/mcp-mssql/mcp-sql-backend.yml
#     kubectl apply -f mcp-server/mcp-mssql/mcp-sql-http-route.yml

#     echo_info "MCP servers deployed successfully!"
# }

# create_azure_auth_policy() {
#     if [[ -z "$AZURE_TENANT_ID" ]] || [[ -z "$AZURE_CLIENT_ID" ]]; then
#         echo_warn "Azure credentials not provided. Skipping Azure AD authentication policy."
#         echo_warn "Set AZURE_TENANT_ID and AZURE_CLIENT_ID environment variables to enable Azure AD auth."
#         return
#     fi

#     echo_info "Creating Azure AD authentication policy..."

#     kubectl apply -f mcpagentcontrolplane/agent-gateway-policy.yml
    
#     echo_info "Azure AD authentication policy created!"
# }

# deploy_mcp_agentgateway_ui() {
#     echo_info "Deploying MCP Agent Gateway UI..."

#     # Deploy mcp-example
#     kubectl apply -f mcp-ui/mcp-ui-deployment.yml
#     kubectl apply -f mcp-ui/mcp-ui-http-route.yml
    

#     echo_info "MCP Agentgateway UI deployed successfully!"
# }

# # ---------------------------------------
# # 6. Check/install screen
# # ---------------------------------------
# check_screen() {
#     if ! command -v screen >/dev/null 2>&1; then
#         echo "📥 Installing screen..."
#         sudo apt-get update && sudo apt-get install -y screen
#     fi
# }

# # ---------------------------------------
# # 7. Start detached port-forward
# # ---------------------------------------
# # NAMESPACE="adapter"
# port_forward_service() {
#     echo "🚀 Ensuring port-forward for $SERVICE_NAME..."

#     # Kill old screen if exists but not running port-forward
#     if screen -list | grep -qw "$SCREEN_SESSION"; then
#         if ! pgrep -f "kubectl port-forward.*${SERVICE_NAME}" >/dev/null; then
#             screen -S "$SCREEN_SESSION" -X quit || true
#         else
#             echo "✔ Port-forward already running."
#             return
#         fi
#     fi

#     # Start detached screen with auto-restart loop
#     screen -dmS "$SCREEN_SESSION" bash -c \
#         "while true; do kubectl port-forward svc/${SERVICE_NAME} 4000:3000; sleep 5; done"

#     echo "📡 Port-forward started in DETACHED SCREEN: $SCREEN_SESSION"

# }

# verify_deployment() {
#     echo_info "Verifying deployment..."
#     echo ""
#     echo_info "Gateway status:"
#     kubectl get gateway agentgateway
#     echo ""
#     echo_info "AgentGateway deployment status:"
#     kubectl get deployment agentgateway
#     echo ""
#     echo_info "MCP servers status:"
#     kubectl get deployment mcp-example mcp-hubspot mcp-mssql
#     echo ""
#     echo_info "AgentGateway configuration:"
#     helm get values kgateway -n kgateway-system
# }

# print_usage_instructions() {
#     echo ""
#     echo_info "=========================================="
#     echo_info "Deployment completed successfully!"
#     echo_info "=========================================="
#     echo ""
#     # echo_info "To port-forward the agentgateway service:"
#     # echo "  kubectl port-forward svc/agentgateway 8080:8080 --address 0.0.0.0"
#     echo ""

#     # if [[ -n "$AZURE_TENANT_ID" ]] && [[ -n "$AZURE_CLIENT_ID" ]]; then
#     #     echo_info "To generate an Azure AD token manually:"
#     #     echo "  curl -X POST https://login.microsoftonline.com/${AZURE_TENANT_ID}/oauth2/v2.0/token \\"
#     #     echo "    -H \"Content-Type: application/x-www-form-urlencoded\" \\"
#     #     echo "    -d \"client_id=${AZURE_CLIENT_ID}\" \\"
#     #     echo "    -d \"client_secret=<your-client-secret>\" \\"
#     #     echo "    -d \"scope=api://${AZURE_CLIENT_ID}/.default\" \\"
#     #     echo "    -d \"grant_type=client_credentials\""
#     #     echo ""
#     # fi

#     # echo_info "To access MCP servers directly through agentgateway:"
#     # echo "  curl -H \"Authorization: Bearer <your-token>\" http://localhost:8080/mcp/mcp-example"
#     echo ""
# }

# main() {
#     echo_info "Starting agentgateway deployment..."
#     echo ""

#     check_prerequisites
#     deploy_gateway_api_crds
#     deploy_kgateway_crds
#     deploy_kgateway_control_plane
#     wait_for_kgateway
#     create_agentgateway_proxy
#     wait_for_agentgateway
#     deploy_mcp_servers
#     create_azure_auth_policy
#     deploy_mcp_agentgateway_ui
#     check_screen
#     port_forward_service
#     verify_deployment
#     print_usage_instructions
# }

# main "$@"




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
echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# Check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Check prerequisites
check_prerequisites() {
    echo_info "Checking prerequisites..."
    
    if ! command_exists kubectl; then
        echo_error "kubectl not found. Please install kubectl first."
        exit 1
    fi
    
    if ! command_exists helm; then
        echo_error "helm not found. Please install helm first."
        exit 1
    fi
    
    if ! kubectl cluster-info > /dev/null 2>&1; then
        echo_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    echo_info "Prerequisites check passed!"
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

    check_prerequisites
    deploy_gateway_api_crds
    deploy_kgateway_crds
    deploy_kgateway_control_plane
    wait_for_kgateway
    create_agentgateway_proxy
    wait_for_agentgateway
    deploy_mcp_servers
    create_azure_auth_policy
    deploy_mcp_agentgateway_ui
    check_screen
    port_forward_service
    verify_deployment
    print_usage_instructions
}

main "$@"
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
KGATEWAY_VERSION="${KGATEWAY_VERSION:-v2.2.0-main}"
GATEWAY_API_VERSION="${GATEWAY_API_VERSION:-v1.4.0}"

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
    kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.4.0/standard-install.yaml
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
    
    ## Deploy the agentgateway proxy
    kubectl apply -f mcpagentcontrolplane/mcp-gateway-proxy.yml

    
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

create_azure_auth_policy() {
    if [[ -z "$AZURE_TENANT_ID" ]] || [[ -z "$AZURE_CLIENT_ID" ]]; then
        echo_warn "Azure credentials not provided. Skipping Azure AD authentication policy."
        echo_warn "Set AZURE_TENANT_ID and AZURE_CLIENT_ID environment variables to enable Azure AD auth."
        return
    fi

    echo_info "Creating Azure AD authentication policy..."

    kubectl apply -f mcpagentcontrolplane/agent-gateway-policy.yml
    
    echo_info "Azure AD authentication policy created!"
}

deploy_mcp_agentgateway_ui() {
    echo_info "Deploying MCP Agent Gateway UI..."

    # Deploy mcp-example
    kubectl apply -f mcp-ui/mcp-ui-deployment.yml
    kubectl apply -f mcp-ui/mcp-ui-http-route.yml
    

    echo_info "MCP Agentgateway UI deployed successfully!"
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
    echo_info "MCP servers status:"
    kubectl get deployment mcp-example mcp-hubspot mcp-mssql
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
    # echo_info "To port-forward the agentgateway service:"
    # echo "  kubectl port-forward svc/agentgateway 8080:8080 --address 0.0.0.0"
    echo ""

    # if [[ -n "$AZURE_TENANT_ID" ]] && [[ -n "$AZURE_CLIENT_ID" ]]; then
    #     echo_info "To generate an Azure AD token manually:"
    #     echo "  curl -X POST https://login.microsoftonline.com/${AZURE_TENANT_ID}/oauth2/v2.0/token \\"
    #     echo "    -H \"Content-Type: application/x-www-form-urlencoded\" \\"
    #     echo "    -d \"client_id=${AZURE_CLIENT_ID}\" \\"
    #     echo "    -d \"client_secret=<your-client-secret>\" \\"
    #     echo "    -d \"scope=api://${AZURE_CLIENT_ID}/.default\" \\"
    #     echo "    -d \"grant_type=client_credentials\""
    #     echo ""
    # fi

    # echo_info "To access MCP servers directly through agentgateway:"
    # echo "  curl -H \"Authorization: Bearer <your-token>\" http://localhost:8080/mcp/mcp-example"
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
    deploy_mcp_servers
    create_azure_auth_policy
    deploy_mcp_agentgateway_ui
    verify_deployment
    print_usage_instructions
}

main "$@"

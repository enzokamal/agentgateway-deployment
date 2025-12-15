1. Apply the agentgateway crds that is in the folder agentgatewaycrds
```
kubectl apply -f agentgatewaycrds
```

2. Install Deploy the Kubernetes Gateway API CRDs (Experimental) 
```
kubectl apply --server-side -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.4.1/experimental-install.yaml
```

3. Install the kgateway control plane by using Helm. To use experimental Gateway API features, include the experimental feature gate, --set controller.extraEnv.KGW_ENABLE_GATEWAY_API_EXPERIMENTAL_FEATURES=true.
```
helm upgrade -i agentgateway oci://ghcr.io/kgateway-dev/charts/agentgateway \
  --namespace agentgateway-system \
  --version v2.2.0-main \
  --set controller.image.pullPolicy=Always \
  --set controller.extraEnv.KGW_ENABLE_GATEWAY_API_EXPERIMENTAL_FEATURES=true
```

4. apply the mcp-gateway that has gatewayClassName: agentgateway-v2
```
kubectl apply -f mcpagentcontrolplane/mcp-gateway-proxy.yml
```


5. apply the mcp-gateway that has gatewayClassName: agentgateway-v2
```
kubectl apply -f mcpagentcontrolplane/mcp-gateway-proxy.yml
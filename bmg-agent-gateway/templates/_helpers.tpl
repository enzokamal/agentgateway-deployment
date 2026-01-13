{{/*
Expand the name of the chart.
*/}}
{{- define "bmg-agent-gateway.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "bmg-agent-gateway.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}


{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "bmg-agent-gateway.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "bmg-agent-gateway.labels" -}}
helm.sh/chart: {{ include "bmg-agent-gateway.chart" . }}
{{ include "bmg-agent-gateway.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "bmg-agent-gateway.selectorLabels" -}}
app.kubernetes.io/name: {{ include "bmg-agent-gateway.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "bmg-agent-gateway.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "bmg-agent-gateway.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Agent labels
*/}}
{{- define "agent.labels" -}}
app.kubernetes.io/name: agent
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ include "bmg-agent-gateway.chart" . }}
{{- end }}

{{/*
Agent selector labels
*/}}
{{- define "agent.selectorLabels" -}}
app.kubernetes.io/name: agent
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
UI labels
*/}}
{{- define "ui.labels" -}}
app.kubernetes.io/name: ui
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ include "bmg-agent-gateway.chart" . }}
{{- end }}

{{/*
UI selector labels
*/}}
{{- define "ui.selectorLabels" -}}
app.kubernetes.io/name: ui
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
MCP Hubspot labels
*/}}
{{- define "mcp-hubspot.labels" -}}
app.kubernetes.io/name: mcp-hubspot
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ include "bmg-agent-gateway.chart" . }}
{{- end }}

{{/*
MCP Hubspot selector labels
*/}}
{{- define "mcp-hubspot.selectorLabels" -}}
app.kubernetes.io/name: mcp-hubspot
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
MCP MSSQL labels
*/}}
{{- define "mcp-mssql.labels" -}}
app.kubernetes.io/name: mcp-mssql
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ include "bmg-agent-gateway.chart" . }}
{{- end }}

{{/*
MCP MSSQL selector labels
*/}}
{{- define "mcp-mssql.selectorLabels" -}}
app.kubernetes.io/name: mcp-mssql
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Gateway labels
*/}}
{{- define "gateway.labels" -}}
app.kubernetes.io/name: agentgateway
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ include "bmg-agent-gateway.chart" . }}
{{- end }}

{{/*
Required values - will fail if not provided
*/}}
{{- define "bmg-agent-gateway.azure.clientId" -}}
{{- required "AZURE_CLIENT_ID is required in values.yaml" .Values.azure.clientId }}
{{- end }}

{{- define "bmg-agent-gateway.azure.tenantId" -}}
{{- required "AZURE_TENANT_ID is required in values.yaml" .Values.azure.tenantId }}
{{- end }}

{{- define "bmg-agent-gateway.ui.azureClientSecret" -}}
{{- required "ui.secret.azureClientSecret is required in values.yaml" .Values.ui.secret.azureClientSecret }}
{{- end }}

{{- define "bmg-agent-gateway.ui.secretKey" -}}
{{- required "ui.secret.secretKey is required in values.yaml" .Values.ui.secret.secretKey }}
{{- end }}

{{- define "bmg-agent-gateway.ui.secret.name" -}}
{{- if .Values.ui.secret -}}
{{- .Values.ui.secret.name | default "ui-secrets" -}}
{{- else -}}
ui-secrets
{{- end -}}
{{- end }}

{{- define "bmg-agent-gateway.ui.azureScopes" -}}
{{- required "ui.deployment.env.azureScopes is required in values.yaml" .Values.ui.deployment.env.azureScopes }}
{{- end }}

{{- define "bmg-agent-gateway.ui.redirectUri" -}}
{{- required "ui.deployment.env.redirectUri is required in values.yaml" .Values.ui.deployment.env.redirectUri }}
{{- end }}

{{/*
Default values with fallbacks
*/}}
{{- define "bmg-agent-gateway.ui.gatewayUrl" -}}
{{- default (printf "http://%s.%s.svc.cluster.local:%d" (include "bmg-agent-gateway.gateway.name" .) (include "bmg-agent-gateway.namespace" .) (index .Values.gateway.listeners 0).port) .Values.ui.deployment.env.gatewayUrl }}
{{- end }}


{{- define "bmg-agent-gateway.ui.adkApi" -}}
{{- default (printf "http://%s.%s.svc.cluster.local:%d" .Values.agent.service.name (include "bmg-agent-gateway.namespace" .) (int .Values.agent.service.port)) .Values.ui.deployment.env.adkApi }}
{{- end }}


{{/*
BMG Agent defaults and required
*/}}
{{- define "bmg-agent-gateway.agent.agentMode" -}}
{{- default "api" .Values.agent.configMap.agentMode }}
{{- end }}

{{- define "bmg-agent-gateway.agent.agentPort" -}}
{{- default "8070" (.Values.agent.configMap.agentPort | toString) }}
{{- end }}

{{- define "bmg-agent-gateway.agent.agentHost" -}}
{{- default "0.0.0.0" .Values.agent.configMap.agentHost }}
{{- end }}

{{- define "bmg-agent-gateway.agent.mcpServersJson" -}}
{{- default (printf "[{\"url\":\"http://%s.%s.svc.cluster.local:%d/mcp/mcp-mssql\"}]" (include "bmg-agent-gateway.gateway.name" .) (include "bmg-agent-gateway.namespace" .) (index .Values.gateway.listeners 0).port) .Values.agent.configMap.mcpServersJson }}
{{- end }}

{{- define "bmg-agent-gateway.agent.deepseekApiKey" -}}
{{- if .Values.agent.secret -}}
{{- required "agent.secret.deepseekApiKey is required in values.yaml" .Values.agent.secret.deepseekApiKey -}}
{{- else -}}
{{- required "agent.secret.deepseekApiKey is required in values.yaml" "" -}}
{{- end -}}
{{- end }}

{{- define "bmg-agent-gateway.agent.configMap.name" -}}
{{- if .Values.agent.configMap -}}
{{- .Values.agent.configMap.name | default "agent-config" -}}
{{- else -}}
agent-config
{{- end -}}
{{- end }}

{{- define "bmg-agent-gateway.agent.secret.name" -}}
{{- if .Values.agent.secret -}}
{{- .Values.agent.secret.name | default "agent-secrets" -}}
{{- else -}}
agent-secrets
{{- end -}}
{{- end }}

{{- define "bmg-agent-gateway.agent.image.repository" -}}
{{- default "sawnjordan/multi-agent" .Values.agent.deployment.image.repository }}
{{- end }}

{{- define "bmg-agent-gateway.agent.image.tag" -}}
{{- default .Chart.AppVersion .Values.agent.deployment.image.tag }}
{{- end }}

{{- define "bmg-agent-gateway.agent.image.pullPolicy" -}}
{{- default "IfNotPresent" .Values.agent.deployment.image.pullPolicy }}
{{- end }}

{{- define "bmg-agent-gateway.ui.image.repository" -}}
{{- default "kamalberrybytes/adk-web-ui" .Values.ui.deployment.image.repository }}
{{- end }}

{{- define "bmg-agent-gateway.ui.image.tag" -}}
{{- default "latest" .Values.ui.deployment.image.tag }}
{{- end }}

{{- define "bmg-agent-gateway.ui.image.pullPolicy" -}}
{{- default "Always" .Values.ui.deployment.image.pullPolicy }}
{{- end }}

{{- define "bmg-agent-gateway.mcpHubspot.image.repository" -}}
{{- default "kamalberrybytes/mcp-hubspot" .Values.mcpHubspot.deployment.image.repository }}
{{- end }}

{{- define "bmg-agent-gateway.mcpHubspot.image.tag" -}}
{{- default "latest" .Values.mcpHubspot.deployment.image.tag }}
{{- end }}

{{- define "bmg-agent-gateway.mcpHubspot.image.pullPolicy" -}}
{{- default "Always" .Values.mcpHubspot.deployment.image.pullPolicy }}
{{- end }}

{{- define "bmg-agent-gateway.mcpMssql.image.repository" -}}
{{- default "kamalberrybytes/mssql-mcp" .Values.mcpMssql.deployment.image.repository }}
{{- end }}

{{- define "bmg-agent-gateway.mcpMssql.image.tag" -}}
{{- default "latest" .Values.mcpMssql.deployment.image.tag }}
{{- end }}

{{- define "bmg-agent-gateway.mcpMssql.image.pullPolicy" -}}
{{- default "Always" .Values.mcpMssql.deployment.image.pullPolicy }}
{{- end }}

{{- define "bmg-agent-gateway.namespace" -}}
{{- default "agentgateway-system" .Values.namespace }}
{{- end }}

{{- define "bmg-agent-gateway.gateway.name" -}}
{{- default "agentgateway-proxy" .Values.gateway.name }}
{{- end }}

{{- define "bmg-agent-gateway.gateway.gatewayClassName" -}}
{{- default "agentgateway" .Values.gateway.gatewayClassName }}
{{- end }}

{{/*
MCP MSSQL required values
*/}}
{{- define "bmg-agent-gateway.mcpMssql.mssqlServer" -}}
{{- if .Values.mcpMssql.deployment.env -}}
{{- required "mcpMssql.deployment.env.mssqlServer is required in values.yaml" .Values.mcpMssql.deployment.env.mssqlServer -}}
{{- else -}}
{{- required "mcpMssql.deployment.env.mssqlServer is required in values.yaml" "" -}}
{{- end -}}
{{- end }}

{{- define "bmg-agent-gateway.mcpMssql.mssqlDatabase" -}}
{{- if .Values.mcpMssql.deployment.env -}}
{{- required "mcpMssql.deployment.env.mssqlDatabase is required in values.yaml" .Values.mcpMssql.deployment.env.mssqlDatabase -}}
{{- else -}}
{{- required "mcpMssql.deployment.env.mssqlDatabase is required in values.yaml" "" -}}
{{- end -}}
{{- end }}

{{- define "bmg-agent-gateway.mcpMssql.mssqlPort" -}}
{{- if .Values.mcpMssql.deployment.env -}}
{{- required "mcpMssql.deployment.env.mssqlPort is required in values.yaml" (.Values.mcpMssql.deployment.env.mssqlPort | toString) -}}
{{- else -}}
{{- required "mcpMssql.deployment.env.mssqlPort is required in values.yaml" "" -}}
{{- end -}}
{{- end }}

{{- define "bmg-agent-gateway.mcpMssql.mssqlUser" -}}
{{- if .Values.mcpMssql.deployment.env -}}
{{- required "mcpMssql.deployment.env.mssqlUser is required in values.yaml" .Values.mcpMssql.deployment.env.mssqlUser -}}
{{- else -}}
{{- required "mcpMssql.deployment.env.mssqlUser is required in values.yaml" "" -}}
{{- end -}}
{{- end }}

{{- define "bmg-agent-gateway.mcpMssql.mssqlPassword" -}}
{{- if .Values.mcpMssql.deployment.env -}}
{{- required "mcpMssql.deployment.env.mssqlPassword is required in values.yaml" .Values.mcpMssql.deployment.env.mssqlPassword -}}
{{- else -}}
{{- required "mcpMssql.deployment.env.mssqlPassword is required in values.yaml" "" -}}
{{- end -}}
{{- end }}

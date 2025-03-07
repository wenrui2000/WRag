{{/*
Define base name to be used throughout the templates
*/}}
{{- define "app.name" -}}
{{- default "hra" .Values.nameOverride }}
{{- end }}

{{/*
Expand the name of the chart.
*/}}
{{- define "app.chartName" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "app.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := include "app.name" . }}
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
{{- define "app.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "app.labels" -}}
helm.sh/chart: {{ include "app.chart" . }}
{{ include "app.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Get component full name
*/}}
{{- define "common.componentName" -}}
{{- if eq .group "frontend" }}
{{- printf "%s-%s" (include "app.fullname" .root) .name }}
{{- else }}
{{- printf "%s-%s-%s" (include "app.fullname" .root) .group .name }}
{{- end }}
{{- end }}

{{/*
Common labels with component group
*/}}
{{- define "common.componentLabels" -}}
{{- include "app.labels" .root }}
app.kubernetes.io/component: {{ .name }}
app.kubernetes.io/group: {{ .group }}
{{- end }}

{{/*
OpenSearch init container with credentials
*/}}
{{- define "common.opensearch.initContainer" -}}
initContainers:
  - name: wait-for-opensearch
    image: curlimages/curl-base:8.11.0
    command: ['sh', '-c', 'until curl -f --insecure -u "${OPENSEARCH_USER}:${OPENSEARCH_PASSWORD}" https://{{ include "app.fullname" . }}-search-opensearch:9200/_cluster/health; do echo "initContainers: waiting for opensearch"; sleep 2; done;']
    resources:
      requests:
        cpu: "100m"
        memory: "64Mi"
      limits:
        cpu: "200m"
        memory: "128Mi"
    env:
    - name: OPENSEARCH_USER
      valueFrom:
        secretKeyRef:
          name: {{ if .Values.global.secrets.useExternalSecrets }}
            {{- .Values.global.secrets.name }}
          {{- else }}
            {{- include "app.fullname" . }}-secrets
          {{- end }}
          key: opensearch-user
    - name: OPENSEARCH_PASSWORD
      valueFrom:
        secretKeyRef:
          name: {{ if .Values.global.secrets.useExternalSecrets }}
            {{- .Values.global.secrets.name }}
          {{- else }}
            {{- include "app.fullname" . }}-secrets
          {{- end }}
          key: opensearch-password
{{- end }}

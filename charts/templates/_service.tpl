{{/*
Common service template
*/}}
{{- define "common.service" -}}
apiVersion: v1
kind: Service
metadata:
  name: {{ .values.service.name | default (include "common.componentName" .) }}
  labels:
    {{- include "common.componentLabels" . | nindent 4 }}
spec:
  type: {{ .values.service.type }}
  {{- if .values.service.clusterIP }}
  clusterIP: {{ .values.service.clusterIP }}
  {{- end }}
  ports:
    {{- if .values.service.ports }}
    {{- range .values.service.ports }}
    - port: {{ .port }}
      targetPort: {{ .targetPort | default .port }}
      {{- if .name }}
      name: {{ .name }}
      {{- end }}
    {{- end }}
    {{- else }}
    - port: {{ .values.service.port }}
      targetPort: {{ .values.service.targetPort | default .values.service.port }}
      {{- if .name }}
      name: {{ .name }}
      {{- end }}
    {{- end }}
  selector:
    {{- include "app.selectorLabels" .root | nindent 4 }}
    app.kubernetes.io/component: {{ .name }}
    app.kubernetes.io/group: {{ .group }}
{{- end }}

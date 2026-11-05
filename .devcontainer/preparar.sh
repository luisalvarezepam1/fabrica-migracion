#!/usr/bin/env bash
# Se ejecuta una vez al crear el Codespace. Ningún paso es fatal: si algo falla,
# el ambiente queda abierto y /verificar-ambiente te dice qué falta.
set -u
echo "== Terraform (opcional, solo para validar la infraestructura) =="
if ! command -v terraform >/dev/null 2>&1; then
  V=1.9.8
  ARCH=$(dpkg --print-architecture 2>/dev/null || echo amd64)
  curl -fsSL -o /tmp/tf.zip "https://releases.hashicorp.com/terraform/${V}/terraform_${V}_linux_${ARCH}.zip" \
    && { command -v unzip >/dev/null || { sudo apt-get update -qq && sudo apt-get install -y -qq unzip; }; } \
    && sudo unzip -o -q /tmp/tf.zip -d /usr/local/bin \
    && terraform version | head -1 \
    || echo "No se pudo instalar Terraform; la fábrica funciona sin él."
fi
echo "== Paquetes de la plantilla .NET =="
dotnet restore plataforma/plantillas/dotnet-api/Plantilla.sln || echo "dotnet restore falló; se reintentará en la corrida."
echo "== Verificación =="
python3 herramientas/fabrica.py verificar || true

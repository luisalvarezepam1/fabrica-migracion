# Python 3.12 ya instalado (sin compilar). .NET 8 se agrega como feature.
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm
# Algunas imágenes base traen el repositorio apt de Yarn con una llave vencida y eso
# rompe cualquier apt-get update de las features. La fábrica no usa Yarn.
RUN rm -f /etc/apt/sources.list.d/yarn.list /etc/apt/sources.list.d/yarn*.list || true

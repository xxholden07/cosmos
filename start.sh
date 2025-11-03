#!/bin/bash
# Script para iniciar a interface web

echo "======================================"
echo "  Análise de Dados Cósmicos"
echo "======================================"
echo ""
echo "Iniciando interface web..."
echo "Acesse: http://localhost:8501"
echo ""
echo "Para parar: Ctrl+C"
echo ""

cd /home/matheus/Documentos/cosmos
streamlit run app.py

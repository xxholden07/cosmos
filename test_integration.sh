#!/bin/bash
# Script para testar a integração da API Exoplanet no Cosmos

echo "🧪 Testando integração da API Exoplanet Archive..."
echo ""

# Testar import
python3 << EOF
import sys
sys.path.insert(0, '/home/matheus/Documentos/cosmos')

try:
    from exoplanet_api import ExoplanetAPI
    print("✅ Import da ExoplanetAPI: OK")
    
    # Testar inicialização
    api = ExoplanetAPI()
    print("✅ Inicialização da API: OK")
    
    # Testar método simples
    query = "SELECT TOP 5 pl_name FROM ps WHERE disc_year > 2020"
    resultado = api.tap_query(query)
    print(f"✅ Query TAP funcionando: {len(resultado)} resultados")
    
    # Testar método helper
    planetas = api.get_confirmed_planets(limit=3)
    print(f"✅ get_confirmed_planets: {len(planetas)} planetas")
    
    print("\n🎉 Todas as funções básicas estão funcionando!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
EOF

echo ""
echo "Integração completa! Execute: streamlit run app.py"

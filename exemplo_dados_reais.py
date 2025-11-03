#!/usr/bin/env python3
"""
Exemplo: Como usar DADOS REAIS do Kepler
Execute: python exemplo_dados_reais.py
"""

import sys

def check_lightkurve():
    """Verifica se lightkurve está instalado"""
    try:
        import lightkurve as lk
        return True
    except ImportError:
        return False

def exemplo_com_lightkurve():
    """Exemplo usando dados reais do Kepler"""
    import lightkurve as lk
    from cosmic_analyzer import CosmicAnalyzer
    
    print("="*70)
    print("🛰️  USANDO DADOS REAIS DO TELESCÓPIO KEPLER")
    print("="*70)
    
    # 1. Buscar dados de uma estrela específica
    print("\n1️⃣  Buscando dados da estrela Kepler-10...")
    print("   (Esta estrela tem planetas confirmados!)")
    
    search_result = lk.search_lightcurve('Kepler-10', 
                                          author='Kepler', 
                                          cadence='long')
    
    print(f"   ✓ Encontrados {len(search_result)} trimestres de dados")
    
    # 2. Baixar dados
    print("\n2️⃣  Baixando dados... (pode demorar na primeira vez)")
    lc_collection = search_result.download_all()
    lc = lc_collection.stitch()  # Juntar todos os trimestres
    
    print(f"   ✓ Dados baixados: {len(lc.time)} pontos")
    print(f"   ✓ Período: {lc.time[0]:.1f} a {lc.time[-1]:.1f} dias")
    
    # 3. Extrair arrays
    time = lc.time.value
    flux = lc.flux.value
    
    # 4. Analisar com nosso sistema
    print("\n3️⃣  Analisando com nosso sistema...")
    print("="*70)
    
    analyzer = CosmicAnalyzer(sensitivity=5.0)  # Mais rigoroso para dados reais
    
    results = analyzer.analyze_lightcurve(
        time, flux,
        detect_planets=True,
        detect_transients=False,  # Dados do Kepler não têm transientes
        analyze_vibrations=False,  # Kepler-10 não é pulsante
        visualize=True
    )
    
    # 5. Mostrar resultados
    print("\n4️⃣  RESULTADOS:")
    print("="*70)
    
    if 'planets' in results:
        print(f"\n🪐 PLANETAS DETECTADOS: {len(results['planets'])}")
        print("\nPlanetas conhecidos de Kepler-10:")
        print("  • Kepler-10b: Período = 0.837 dias")
        print("  • Kepler-10c: Período = 45.3 dias")
        print("\nNossas detecções:")
        
        for i, p in enumerate(results['planets'][:5], 1):
            print(f"\n  Candidato {i}:")
            print(f"    Período:      {p['period_days']:.3f} dias")
            print(f"    Profundidade: {p['transit_depth']*100:.4f}%")
            print(f"    Confiança:    {p['confidence']:.1f}%")
            
            # Comparar com planetas conhecidos
            if 0.8 < p['period_days'] < 0.9:
                print("    → Possível match com Kepler-10b! ✓")
            elif 40 < p['period_days'] < 50:
                print("    → Possível match com Kepler-10c! ✓")
    
    print("\n" + "="*70)
    print("✅ Análise completa!")
    print("="*70)

def exemplo_salvar_dados():
    """Exemplo de como salvar dados do Kepler localmente"""
    import lightkurve as lk
    import pandas as pd
    
    print("\n" + "="*70)
    print("💾 SALVANDO DADOS LOCALMENTE")
    print("="*70)
    
    # Baixar dados
    search = lk.search_lightcurve('Kepler-10', author='Kepler', cadence='long')
    lc = search.download_all().stitch()
    
    # Salvar em CSV
    df = pd.DataFrame({
        'time': lc.time.value,
        'flux': lc.flux.value,
        'flux_err': lc.flux_err.value
    })
    
    filename = 'kepler10_lightcurve.csv'
    df.to_csv(filename, index=False)
    
    print(f"✓ Dados salvos em: {filename}")
    print(f"  Linhas: {len(df)}")
    print(f"  Colunas: {list(df.columns)}")
    
    # Mostrar como carregar depois
    print("\n📖 Para carregar depois:")
    print(f"   import pandas as pd")
    print(f"   data = pd.read_csv('{filename}')")
    print(f"   time = data['time'].values")
    print(f"   flux = data['flux'].values")

def exemplo_sem_lightkurve():
    """Exemplo usando dados sintéticos (sem lightkurve)"""
    import numpy as np
    from cosmic_analyzer import CosmicAnalyzer
    
    print("="*70)
    print("⚠️  LIGHTKURVE NÃO INSTALADO")
    print("="*70)
    print("\nUsando dados sintéticos como demonstração...")
    print("\nPara usar dados reais, instale lightkurve:")
    print("  pip install lightkurve")
    
    # Gerar dados sintéticos
    print("\nGerando dados sintéticos...")
    time = np.linspace(0, 100, 10000)
    flux = np.ones(10000)
    
    # Adicionar trânsito (simular Kepler-10b)
    period = 0.837
    depth = 0.001
    for t in np.arange(0, 100, period):
        mask = (time >= t) & (time < t + 0.03)
        flux[mask] *= (1 - depth)
    
    flux += np.random.normal(0, 0.0001, 10000)
    
    # Analisar
    print("Analisando dados sintéticos...")
    analyzer = CosmicAnalyzer()
    results = analyzer.analyze_lightcurve(time, flux, visualize=False)
    
    print(f"\n✓ Planetas detectados: {len(results.get('planets', []))}")
    
    if results.get('planets'):
        p = results['planets'][0]
        print(f"\nMelhor candidato:")
        print(f"  Período: {p['period_days']:.3f} dias")
        print(f"  Profundidade: {p['transit_depth']*100:.4f}%")

def main():
    print("\n" + "🌌"*35)
    print("EXEMPLO: COMO USAR DADOS REAIS")
    print("🌌"*35 + "\n")
    
    if check_lightkurve():
        print("✓ Lightkurve detectado!")
        
        while True:
            print("\nEscolha uma opção:")
            print("1. Analisar dados reais do Kepler-10")
            print("2. Salvar dados do Kepler localmente")
            print("3. Sair")
            
            choice = input("\nOpção (1/2/3): ").strip()
            
            if choice == '1':
                exemplo_com_lightkurve()
            elif choice == '2':
                exemplo_salvar_dados()
            elif choice == '3':
                break
            else:
                print("Opção inválida!")
    else:
        print("✗ Lightkurve NÃO instalado")
        exemplo_sem_lightkurve()
        
        print("\n" + "="*70)
        print("💡 DICA: Instale lightkurve para usar dados reais:")
        print("="*70)
        print("\n  pip install lightkurve")
        print("\nDepois execute este script novamente!")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Exemplo de uso do Sistema de Análise de Dados Cósmicos
Execute: python exemplo_simples.py
"""

import numpy as np
from cosmic_analyzer import CosmicAnalyzer

def main():
    print("="*70)
    print("🌌 SISTEMA DE ANÁLISE DE DADOS CÓSMICOS - EXEMPLO")
    print("="*70)
    
    # Gerar dados sintéticos
    print("\n1️⃣ Gerando dados sintéticos...")
    
    # Curva de luz com trânsito planetário
    time = np.linspace(0, 30, 5000)
    flux = np.ones(5000)
    
    # Adicionar trânsito planetário (período = 5 dias)
    period = 5.0
    transit_depth = 0.01
    transit_duration = 0.1
    
    for cycle_start in np.arange(0, 30, period):
        mask = (time >= cycle_start) & (time < cycle_start + transit_duration)
        flux[mask] *= (1 - transit_depth)
    
    # Adicionar vibrações estelares
    nu_max = 3000  # μHz
    freq_hz = nu_max * 1e-6
    flux += 0.0005 * np.sin(2 * np.pi * freq_hz * time * 86400)
    
    # Adicionar supernova em t=20
    event_mask = (time >= 20) & (time < 22)
    flux[event_mask] += 0.2 * np.exp(-(time[event_mask] - 20))
    
    # Ruído
    flux += np.random.normal(0, 0.001, len(time))
    
    print("   ✓ Curva de luz gerada")
    
    # Sinal SETI com padrão
    seti_signal = np.random.normal(0, 1, 10000)
    # Adicionar pulsos regulares
    for i in range(0, 10000, 100):
        seti_signal[i:i+10] += 5
    # Adicionar frequência portadora
    seti_signal += 2 * np.sin(2 * np.pi * 0.05 * np.arange(10000))
    
    print("   ✓ Sinal SETI gerado\n")
    
    # Inicializar analisador
    analyzer = CosmicAnalyzer(sensitivity=3.0)
    
    # Análise completa
    print("2️⃣ Executando análise completa...\n")
    
    results = analyzer.full_analysis(
        lightcurve_time=time,
        lightcurve_flux=flux,
        signal_data=seti_signal,
        signal_sample_rate=1.0
    )
    
    # Resumo dos resultados
    print("\n" + "="*70)
    print("📋 RESUMO DOS RESULTADOS")
    print("="*70)
    
    if 'lightcurve' in results:
        lc = results['lightcurve']
        
        if 'planets' in lc:
            print(f"\n🪐 PLANETAS DETECTADOS: {len(lc['planets'])}")
            for i, p in enumerate(lc['planets'][:3], 1):
                print(f"   {i}. Período: {p['period_days']:.2f} dias, "
                      f"Profundidade: {p['transit_depth']*100:.3f}%")
        
        if 'transients' in lc:
            print(f"\n💥 EVENTOS TRANSIENTES: {len(lc['transients'])}")
            for i, t in enumerate(lc['transients'], 1):
                print(f"   {i}. {t['type']} em t={t['peak_time']:.1f}d, "
                      f"Amplitude: {t['amplitude']:.2f} mag")
        
        if 'seismology' in lc:
            params = lc['seismology']['stellar_parameters']
            print(f"\n⭐ PARÂMETROS ESTELARES:")
            print(f"   Massa: {params['mass_solar']:.2f} M☉")
            print(f"   Raio: {params['radius_solar']:.2f} R☉")
            print(f"   Idade: {params['age_gyr']:.1f} Gyr")
            print(f"   Estágio: {params['evolutionary_stage']}")
    
    if 'signal' in results:
        sig = results['signal']
        score = sig['artificiality_score']
        
        print(f"\n📡 ANÁLISE SETI:")
        print(f"   Score de Artificialidade: {score['score']}/100")
        print(f"   Classificação: {score['classification']}")
        if score['reasons']:
            print(f"   Evidências:")
            for reason in score['reasons'][:3]:
                print(f"      • {reason}")
    
    print("\n" + "="*70)
    print("✅ Análise concluída! Verifique os gráficos gerados.")
    print("="*70)
    print("\n💡 Dica: Execute 'jupyter notebook analise_cosmica.ipynb'")
    print("   para ver exemplos mais detalhados e interativos!")


if __name__ == "__main__":
    main()

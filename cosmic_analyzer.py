"""
Sistema de Análise de Dados Cósmicos
Módulo principal que integra todas as funcionalidades
"""

from celestial_detector import CelestialBodyDetector
from stellar_seismology import StellarSeismologyAnalyzer
from pattern_detector import PatternDetector
from visualizer import CosmicVisualizer
import numpy as np
from typing import Dict, Optional


class CosmicAnalyzer:
    """Classe principal para análise completa de dados cósmicos"""
    
    def __init__(self, sensitivity: float = 3.0):
        """
        Inicializa o analisador cósmico
        
        Args:
            sensitivity: Sensibilidade de detecção (em sigmas)
        """
        self.celestial_detector = CelestialBodyDetector(sensitivity=sensitivity)
        self.seismo_analyzer = StellarSeismologyAnalyzer()
        self.pattern_detector = PatternDetector(significance_level=0.001)
        self.visualizer = CosmicVisualizer()
        
    def analyze_lightcurve(
        self,
        time: np.ndarray,
        flux: np.ndarray,
        detect_planets: bool = True,
        detect_transients: bool = True,
        analyze_vibrations: bool = False,
        visualize: bool = True
    ) -> Dict:
        """
        Análise completa de curva de luz
        
        Args:
            time: Array de tempos
            flux: Array de fluxo
            detect_planets: Detectar planetas em trânsito
            detect_transients: Detectar eventos transientes
            analyze_vibrations: Fazer asterosismologia
            visualize: Gerar visualizações
            
        Returns:
            Dicionário com todos os resultados
        """
        results = {}
        
        print("🌌 Iniciando análise de curva de luz...")
        print("="*70)
        
        # Detecção de planetas
        if detect_planets:
            print("\n🔭 Detectando exoplanetas...")
            results['planets'] = self.celestial_detector.detect_transiting_planets(
                time, flux
            )
            print(f"   ✓ {len(results['planets'])} planetas candidatos encontrados")
        
        # Detecção de transientes
        if detect_transients:
            print("\n💥 Detectando eventos transientes...")
            magnitude = -2.5 * np.log10(flux)
            results['transients'] = self.celestial_detector.detect_transient_events(
                time, magnitude
            )
            print(f"   ✓ {len(results['transients'])} eventos encontrados")
        
        # Asterosismologia
        if analyze_vibrations:
            print("\n⭐ Analisando vibrações estelares...")
            results['seismology'] = self.seismo_analyzer.analyze_stellar_vibrations(
                time, flux
            )
            params = results['seismology']['stellar_parameters']
            print(f"   ✓ Massa: {params['mass_solar']:.2f} M☉")
            print(f"   ✓ Raio: {params['radius_solar']:.2f} R☉")
        
        # Gerar relatórios
        if detect_planets or detect_transients:
            detection_results = {}
            if 'planets' in results:
                detection_results['planets'] = results['planets']
            if 'transients' in results:
                detection_results['transients'] = results['transients']
            
            report = self.celestial_detector.generate_report(detection_results)
            results['celestial_report'] = report
        
        if analyze_vibrations:
            results['seismology_report'] = self.seismo_analyzer.generate_seismology_report(
                results['seismology']
            )
        
        # Visualizações
        if visualize:
            print("\n📊 Gerando visualizações...")
            if detect_planets or detect_transients:
                self.visualizer.plot_celestial_detections(
                    time, flux,
                    results.get('planets', []),
                    results.get('transients', [])
                )
            
            if analyze_vibrations:
                self.visualizer.plot_stellar_seismology(results['seismology'])
        
        print("\n" + "="*70)
        print("✓ Análise concluída!")
        
        return results
    
    def analyze_signal(
        self,
        signal_data: np.ndarray,
        sample_rate: float = 1.0,
        visualize: bool = True
    ) -> Dict:
        """
        Análise de sinal para busca de padrões/mensagens
        
        Args:
            signal_data: Array de dados do sinal
            sample_rate: Taxa de amostragem (Hz)
            visualize: Gerar visualizações
            
        Returns:
            Dicionário com análise de padrões
        """
        print("📡 Iniciando análise de padrões...")
        print("="*70)
        
        # Analisar padrões
        results = self.pattern_detector.analyze_signal(signal_data, sample_rate)
        
        # Gerar relatório
        report = self.pattern_detector.generate_pattern_report(results)
        results['report'] = report
        
        print(report)
        
        # Visualização
        if visualize:
            print("\n📊 Gerando visualizações...")
            self.visualizer.plot_pattern_analysis(signal_data, results, sample_rate)
        
        print("="*70)
        print("✓ Análise concluída!")
        
        return results
    
    def full_analysis(
        self,
        lightcurve_time: Optional[np.ndarray] = None,
        lightcurve_flux: Optional[np.ndarray] = None,
        signal_data: Optional[np.ndarray] = None,
        signal_sample_rate: float = 1.0
    ) -> Dict:
        """
        Análise completa de todos os dados disponíveis
        
        Args:
            lightcurve_time: Tempo da curva de luz
            lightcurve_flux: Fluxo da curva de luz
            signal_data: Dados de sinal
            signal_sample_rate: Taxa de amostragem do sinal
            
        Returns:
            Dicionário com todos os resultados
        """
        results = {}
        
        print("\n" + "🌌"*35)
        print("SISTEMA DE ANÁLISE DE DADOS CÓSMICOS")
        print("🌌"*35 + "\n")
        
        # Análise de curva de luz
        if lightcurve_time is not None and lightcurve_flux is not None:
            lc_results = self.analyze_lightcurve(
                lightcurve_time,
                lightcurve_flux,
                detect_planets=True,
                detect_transients=True,
                analyze_vibrations=True,
                visualize=False
            )
            results['lightcurve'] = lc_results
        
        # Análise de sinal
        if signal_data is not None:
            signal_results = self.analyze_signal(
                signal_data,
                signal_sample_rate,
                visualize=False
            )
            results['signal'] = signal_results
        
        # Dashboard consolidado
        print("\n📊 Gerando dashboard consolidado...")
        
        celestial_data = None
        seismo_data = None
        pattern_data = None
        
        if 'lightcurve' in results:
            celestial_data = {
                'planets': results['lightcurve'].get('planets', []),
                'transients': results['lightcurve'].get('transients', [])
            }
            seismo_data = results['lightcurve'].get('seismology')
        
        if 'signal' in results:
            pattern_data = results['signal']
        
        self.visualizer.plot_summary_dashboard(
            celestial_results=celestial_data,
            seismology_results=seismo_data,
            pattern_results=pattern_data
        )
        
        print("\n" + "="*70)
        print("✅ ANÁLISE COMPLETA FINALIZADA!")
        print("="*70)
        
        return results


# Exemplo de uso
if __name__ == "__main__":
    print(__doc__)
    print("\nPara usar este sistema, execute o notebook 'analise_cosmica.ipynb'")
    print("ou importe a classe CosmicAnalyzer em seu código Python.")
    print("\nExemplo:")
    print("  from cosmic_analyzer import CosmicAnalyzer")
    print("  analyzer = CosmicAnalyzer()")
    print("  results = analyzer.analyze_lightcurve(time, flux)")

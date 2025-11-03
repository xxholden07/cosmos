"""
Módulo de Visualização para Análise de Dados Cósmicos
Cria gráficos e visualizações interativas
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.gridspec import GridSpec
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

# Configurar estilo
plt.style.use('dark_background')
sns.set_palette("husl")


class CosmicVisualizer:
    """Cria visualizações para análise de dados cósmicos"""
    
    def __init__(self, figsize: tuple = (15, 10)):
        self.figsize = figsize
        
    def plot_celestial_detections(
        self,
        time: np.ndarray,
        flux: np.ndarray,
        planets: List[Dict],
        transients: List[Dict],
        save_path: Optional[str] = None
    ):
        """Visualiza detecções de corpos celestes"""
        fig = plt.figure(figsize=self.figsize)
        gs = GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.3)
        
        # 1. Curva de luz completa
        ax1 = fig.add_subplot(gs[0, :])
        ax1.plot(time, flux, 'c-', alpha=0.6, linewidth=0.5)
        ax1.set_xlabel('Tempo (dias)')
        ax1.set_ylabel('Fluxo Normalizado')
        ax1.set_title('🔭 Curva de Luz - Detecção de Corpos Celestes', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Marcar eventos transientes
        for event in transients:
            ax1.axvspan(event['start_time'], event['end_time'], 
                       alpha=0.3, color='red', label='Transiente')
        
        # 2. Trânsitos de planetas
        if planets:
            ax2 = fig.add_subplot(gs[1, 0])
            planet = planets[0]  # Melhor candidato
            period = planet['period_days']
            
            # Dobrar curva de luz
            phase = (time % period) / period
            sort_idx = np.argsort(phase)
            
            ax2.plot(phase[sort_idx], flux[sort_idx], 'o', markersize=2, alpha=0.6, color='cyan')
            ax2.set_xlabel('Fase Orbital')
            ax2.set_ylabel('Fluxo Normalizado')
            ax2.set_title(f'🪐 Trânsito Planetário (P={period:.2f}d)', fontweight='bold')
            ax2.grid(True, alpha=0.3)
            
            # 3. Profundidade do trânsito
            ax3 = fig.add_subplot(gs[1, 1])
            depths = [p['transit_depth'] * 100 for p in planets[:5]]
            periods = [p['period_days'] for p in planets[:5]]
            colors = plt.cm.plasma(np.linspace(0, 1, len(depths)))
            
            bars = ax3.barh(range(len(depths)), depths, color=colors)
            ax3.set_yticks(range(len(depths)))
            ax3.set_yticklabels([f'P{i+1}\n{p:.1f}d' for i, p in enumerate(periods)])
            ax3.set_xlabel('Profundidade do Trânsito (%)')
            ax3.set_title('📊 Candidatos a Planetas', fontweight='bold')
            ax3.grid(True, alpha=0.3, axis='x')
        
        # 4. Eventos transientes
        if transients:
            ax4 = fig.add_subplot(gs[2, :])
            
            for i, event in enumerate(transients[:10]):
                duration = event['duration_days']
                amplitude = event['amplitude']
                
                # Plotar evento
                event_mask = (time >= event['start_time']) & (time <= event['end_time'])
                ax4.plot(time[event_mask] - event['start_time'], 
                        flux[event_mask], 
                        label=f"{event['type']} (Δm={amplitude:.1f})",
                        linewidth=2)
            
            ax4.set_xlabel('Tempo desde início (dias)')
            ax4.set_ylabel('Magnitude')
            ax4.set_title('💥 Eventos Transientes Detectados', fontweight='bold')
            ax4.legend(loc='best', fontsize=8)
            ax4.grid(True, alpha=0.3)
        
        plt.suptitle('ANÁLISE DE CORPOS CELESTES', fontsize=16, fontweight='bold', y=0.995)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_stellar_seismology(
        self,
        analysis: Dict,
        save_path: Optional[str] = None
    ):
        """Visualiza análise de asterosismologia"""
        fig = plt.figure(figsize=self.figsize)
        gs = GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.3)
        
        frequencies = analysis['power_spectrum']['frequencies']
        power = analysis['power_spectrum']['power']
        nu_max = analysis['nu_max_uHz']
        delta_nu = analysis['delta_nu_uHz']
        
        # 1. Espectro de potência completo
        ax1 = fig.add_subplot(gs[0, :])
        ax1.plot(frequencies, power, 'c-', linewidth=0.8, alpha=0.7)
        ax1.axvline(nu_max, color='red', linestyle='--', linewidth=2, 
                   label=f'ν_max = {nu_max:.1f} μHz')
        ax1.set_xlabel('Frequência (μHz)')
        ax1.set_ylabel('Potência')
        ax1.set_title('⭐ Espectro de Potência - Vibrações Estelares', fontsize=14, fontweight='bold')
        ax1.set_xlim(0, min(max(frequencies), nu_max * 3))
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Zoom em região de oscilação
        ax2 = fig.add_subplot(gs[1, 0])
        mask = (frequencies > nu_max - 5*delta_nu) & (frequencies < nu_max + 5*delta_nu)
        ax2.plot(frequencies[mask], power[mask], 'cyan', linewidth=1.5)
        
        # Marcar modos de oscilação
        modes = analysis['oscillation_modes']
        mode_freqs = [m['frequency_uHz'] for m in modes]
        mode_amps = [m['amplitude'] for m in modes]
        ax2.plot(mode_freqs, mode_amps, 'ro', markersize=8, label='Modos identificados')
        
        ax2.set_xlabel('Frequência (μHz)')
        ax2.set_ylabel('Potência')
        ax2.set_title(f'🎵 Modos de Oscilação (Δν={delta_nu:.1f} μHz)', fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Echelle diagram
        ax3 = fig.add_subplot(gs[1, 1])
        if len(mode_freqs) > 5:
            mode_freqs_arr = np.array(mode_freqs)
            mod_freqs = mode_freqs_arr % delta_nu
            order = mode_freqs_arr // delta_nu
            
            # Colorir por grau do modo
            degrees = [m['degree'] for m in modes]
            colors = ['red' if d==0 else 'blue' if d==1 else 'green' for d in degrees]
            
            ax3.scatter(mod_freqs, order, c=colors, s=100, alpha=0.7)
            ax3.set_xlabel(f'Frequência mod {delta_nu:.1f} μHz')
            ax3.set_ylabel('Ordem do Modo')
            ax3.set_title('📐 Diagrama Echelle', fontweight='bold')
            ax3.grid(True, alpha=0.3)
        
        # 4. Parâmetros estelares
        ax4 = fig.add_subplot(gs[2, 0])
        ax4.axis('off')
        
        params = analysis['stellar_parameters']
        param_text = f"""
        PARÂMETROS ESTELARES DERIVADOS
        ================================
        
        Massa:        {params['mass_solar']:.2f} M☉
        Raio:         {params['radius_solar']:.2f} R☉
        log g:        {params['log_g']:.2f}
        Densidade:    {params['density_solar']:.2f} ρ☉
        T_eff:        {params['teff_K']} K
        Idade:        {params['age_gyr']:.2f} Gyr
        
        Estágio:      {params['evolutionary_stage']}
        """
        
        ax4.text(0.1, 0.5, param_text, fontsize=11, family='monospace',
                verticalalignment='center', bbox=dict(boxstyle='round', 
                facecolor='black', alpha=0.8, edgecolor='cyan'))
        
        # 5. Qualidade da detecção
        ax5 = fig.add_subplot(gs[2, 1])
        
        metrics = analysis['quality_metrics']
        categories = ['SNR', 'N Modos', 'Qualidade']
        values = [
            min(metrics['signal_to_noise'], 10),
            min(metrics['n_modes_detected'], 20),
            10 if metrics['quality_flag'] == 'GOOD' else 
            5 if metrics['quality_flag'] == 'FAIR' else 2
        ]
        
        colors_bar = ['green' if v > 5 else 'yellow' if v > 2 else 'red' for v in values]
        bars = ax5.barh(categories, values, color=colors_bar)
        ax5.set_xlabel('Score')
        ax5.set_title(f"✓ Qualidade: {metrics['quality_flag']}", fontweight='bold')
        ax5.grid(True, alpha=0.3, axis='x')
        
        plt.suptitle('ASTEROSISMOLOGIA - ANÁLISE DE VIBRAÇÕES ESTELARES', 
                    fontsize=16, fontweight='bold', y=0.995)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_pattern_analysis(
        self,
        data: np.ndarray,
        analysis: Dict,
        sample_rate: float = 1.0,
        save_path: Optional[str] = None
    ):
        """Visualiza análise de padrões e sinais"""
        fig = plt.figure(figsize=self.figsize)
        gs = GridSpec(3, 3, figure=fig, hspace=0.35, wspace=0.4)
        
        time = np.arange(len(data)) / sample_rate
        
        # 1. Sinal original
        ax1 = fig.add_subplot(gs[0, :])
        ax1.plot(time, data, 'c-', linewidth=0.8, alpha=0.8)
        ax1.set_xlabel('Tempo (s)')
        ax1.set_ylabel('Amplitude')
        
        score = analysis['artificiality_score']['score']
        classification = analysis['artificiality_score']['classification']
        color = 'red' if score >= 70 else 'yellow' if score >= 50 else 'green'
        
        ax1.set_title(f'📡 Sinal Analisado - Score: {score}/100', 
                     fontsize=14, fontweight='bold', color=color)
        ax1.grid(True, alpha=0.3)
        
        # 2. Espectro de frequências
        ax2 = fig.add_subplot(gs[1, 0])
        periodicities = analysis['periodicity']['periodicities']
        if periodicities:
            freqs = [p['frequency_Hz'] for p in periodicities[:10]]
            powers = [p['power'] for p in periodicities[:10]]
            
            ax2.bar(range(len(freqs)), powers, color='cyan', alpha=0.7)
            ax2.set_xticks(range(len(freqs)))
            ax2.set_xticklabels([f'{f:.3f}' for f in freqs], rotation=45, ha='right', fontsize=8)
            ax2.set_xlabel('Frequência (Hz)')
            ax2.set_ylabel('Potência')
            ax2.set_title('📊 Periodicidades Detectadas', fontweight='bold', fontsize=10)
            ax2.grid(True, alpha=0.3, axis='y')
        
        # 3. Autocorrelação
        ax3 = fig.add_subplot(gs[1, 1])
        if 'correlation' in analysis:
            acf = analysis['correlation']['autocorrelation']
            lags = np.arange(len(acf))
            
            ax3.stem(lags, acf, linefmt='cyan', markerfmt='co', basefmt='w-')
            ax3.axhline(y=0, color='white', linestyle='-', linewidth=0.5)
            ax3.axhline(y=0.2, color='red', linestyle='--', linewidth=1, alpha=0.5)
            ax3.axhline(y=-0.2, color='red', linestyle='--', linewidth=1, alpha=0.5)
            ax3.set_xlabel('Lag')
            ax3.set_ylabel('Autocorrelação')
            ax3.set_title('🔄 Função de Autocorrelação', fontweight='bold', fontsize=10)
            ax3.grid(True, alpha=0.3)
        
        # 4. Entropia
        ax4 = fig.add_subplot(gs[1, 2])
        entropy_val = analysis['entropy']['normalized_entropy']
        
        # Gauge de entropia
        theta = np.linspace(0, np.pi, 100)
        r = 1
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        
        ax4.plot(x, y, 'w-', linewidth=2)
        ax4.fill_between(x[:int(entropy_val*100)], 0, y[:int(entropy_val*100)], 
                        color='cyan', alpha=0.7)
        
        # Marcador
        angle = entropy_val * np.pi
        ax4.plot([0, np.cos(angle)], [0, np.sin(angle)], 'r-', linewidth=3)
        ax4.plot(np.cos(angle), np.sin(angle), 'ro', markersize=10)
        
        ax4.text(0, -0.3, f'{entropy_val:.2f}', ha='center', fontsize=14, fontweight='bold')
        ax4.text(0, -0.5, analysis['entropy']['interpretation'], 
                ha='center', fontsize=9, style='italic')
        
        ax4.set_xlim(-1.2, 1.2)
        ax4.set_ylim(-0.6, 1.2)
        ax4.axis('off')
        ax4.set_title('📈 Entropia Normalizada', fontweight='bold', fontsize=10)
        
        # 5. Score de artificialidade
        ax5 = fig.add_subplot(gs[2, :2])
        ax5.axis('off')
        
        reasons = analysis['artificiality_score']['reasons']
        reasons_text = "EVIDÊNCIAS DETECTADAS:\n" + "="*40 + "\n\n"
        
        if reasons:
            for i, reason in enumerate(reasons, 1):
                reasons_text += f"{i}. {reason}\n"
        else:
            reasons_text += "Nenhuma evidência significativa de\npadrões não-naturais encontrada."
        
        reasons_text += f"\n{'='*40}\n"
        reasons_text += f"CLASSIFICAÇÃO:\n{classification}"
        
        text_color = 'red' if score >= 70 else 'yellow' if score >= 50 else 'lightgreen'
        
        ax5.text(0.05, 0.5, reasons_text, fontsize=10, family='monospace',
                verticalalignment='center', color=text_color,
                bbox=dict(boxstyle='round', facecolor='black', 
                         alpha=0.9, edgecolor=text_color, linewidth=2))
        
        # 6. Gauge de artificialidade
        ax6 = fig.add_subplot(gs[2, 2])
        
        # Criar gauge circular
        categories = ['Natural\n(0-30)', 'Estruturado\n(30-50)', 
                     'Possivelmente\nArtificial\n(50-70)', 'Altamente\nArtificial\n(70-100)']
        colors_gauge = ['green', 'yellow', 'orange', 'red']
        
        # Desenhar setores
        for i, (cat, col) in enumerate(zip(categories, colors_gauge)):
            theta = np.linspace(i*np.pi/4, (i+1)*np.pi/4, 50)
            x = np.cos(theta)
            y = np.sin(theta)
            
            if score >= i*25 and score < (i+1)*25:
                ax6.fill_between(x, 0, y, color=col, alpha=0.8)
            else:
                ax6.fill_between(x, 0, y, color=col, alpha=0.3)
        
        # Ponteiro
        angle = (score / 100) * np.pi
        ax6.plot([0, np.cos(angle)*0.8], [0, np.sin(angle)*0.8], 
                'w-', linewidth=4)
        ax6.plot(np.cos(angle)*0.8, np.sin(angle)*0.8, 'wo', markersize=12)
        
        ax6.text(0, -0.3, f'{score}', ha='center', fontsize=20, 
                fontweight='bold', color=text_color)
        
        ax6.set_xlim(-1.2, 1.2)
        ax6.set_ylim(-0.5, 1.2)
        ax6.axis('off')
        ax6.set_title('🎯 Score de Artificialidade', fontweight='bold', fontsize=10)
        
        plt.suptitle('ANÁLISE DE PADRÕES E SINAIS - BUSCA POR INTELIGÊNCIA', 
                    fontsize=16, fontweight='bold', y=0.995)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_summary_dashboard(
        self,
        celestial_results: Optional[Dict] = None,
        seismology_results: Optional[Dict] = None,
        pattern_results: Optional[Dict] = None,
        save_path: Optional[str] = None
    ):
        """Dashboard resumido com todos os resultados"""
        fig = plt.figure(figsize=(16, 10))
        gs = GridSpec(2, 3, figure=fig, hspace=0.3, wspace=0.3)
        
        # 1. Detecções de corpos celestes
        ax1 = fig.add_subplot(gs[0, 0])
        if celestial_results:
            labels = []
            values = []
            
            if 'planets' in celestial_results:
                labels.append('Planetas')
                values.append(len(celestial_results['planets']))
            if 'asteroids' in celestial_results:
                labels.append('Asteroides')
                values.append(len(celestial_results['asteroids']))
            if 'transients' in celestial_results:
                labels.append('Transientes')
                values.append(len(celestial_results['transients']))
            
            colors = ['cyan', 'orange', 'red'][:len(values)]
            ax1.pie(values, labels=labels, colors=colors, autopct='%d', 
                   startangle=90, textprops={'fontsize': 12})
            ax1.set_title('🔭 Corpos Celestes', fontweight='bold', fontsize=12)
        
        # 2. Parâmetros estelares
        ax2 = fig.add_subplot(gs[0, 1])
        if seismology_results and 'stellar_parameters' in seismology_results:
            params = seismology_results['stellar_parameters']
            
            param_names = ['Massa\n(M☉)', 'Raio\n(R☉)', 'log g', 'Idade\n(Gyr)']
            param_values = [
                params['mass_solar'],
                params['radius_solar'],
                params['log_g'] / 4.4,  # Normalizar
                params['age_gyr'] / 10   # Normalizar
            ]
            
            angles = np.linspace(0, 2*np.pi, len(param_names), endpoint=False).tolist()
            param_values += param_values[:1]
            angles += angles[:1]
            
            ax2 = plt.subplot(gs[0, 1], projection='polar')
            ax2.plot(angles, param_values, 'o-', linewidth=2, color='cyan')
            ax2.fill(angles, param_values, alpha=0.25, color='cyan')
            ax2.set_xticks(angles[:-1])
            ax2.set_xticklabels(param_names, fontsize=10)
            ax2.set_ylim(0, max(param_values) * 1.2)
            ax2.set_title('⭐ Parâmetros Estelares', fontweight='bold', fontsize=12, pad=20)
            ax2.grid(True)
        
        # 3. Score de artificialidade
        ax3 = fig.add_subplot(gs[0, 2])
        if pattern_results and 'artificiality_score' in pattern_results:
            score = pattern_results['artificiality_score']['score']
            
            # Thermometer style
            ax3.barh([0], [score], height=0.6, 
                    color='red' if score >= 70 else 'yellow' if score >= 50 else 'green',
                    alpha=0.7)
            ax3.set_xlim(0, 100)
            ax3.set_ylim(-0.5, 0.5)
            ax3.set_yticks([])
            ax3.set_xlabel('Score', fontsize=11)
            ax3.set_title('🎯 Artificialidade do Sinal', fontweight='bold', fontsize=12)
            ax3.text(score+2, 0, f'{score}', va='center', fontsize=16, fontweight='bold')
            ax3.grid(True, alpha=0.3, axis='x')
        
        # Área de texto com resumo
        ax_summary = fig.add_subplot(gs[1, :])
        ax_summary.axis('off')
        
        summary_text = "="*80 + "\n"
        summary_text += "RESUMO EXECUTIVO DA ANÁLISE CÓSMICA\n"
        summary_text += "="*80 + "\n\n"
        
        if celestial_results:
            n_planets = len(celestial_results.get('planets', []))
            n_asteroids = len(celestial_results.get('asteroids', []))
            n_transients = len(celestial_results.get('transients', []))
            
            summary_text += f"🔭 DETECÇÃO DE CORPOS CELESTES:\n"
            summary_text += f"   • Exoplanetas candidatos: {n_planets}\n"
            summary_text += f"   • Asteroides detectados: {n_asteroids}\n"
            summary_text += f"   • Eventos transientes: {n_transients}\n\n"
        
        if seismology_results:
            params = seismology_results.get('stellar_parameters', {})
            summary_text += f"⭐ ASTEROSISMOLOGIA:\n"
            summary_text += f"   • Massa estelar: {params.get('mass_solar', 0):.2f} M☉\n"
            summary_text += f"   • Raio estelar: {params.get('radius_solar', 0):.2f} R☉\n"
            summary_text += f"   • Estágio evolutivo: {params.get('evolutionary_stage', 'N/A')}\n"
            summary_text += f"   • Modos detectados: {len(seismology_results.get('oscillation_modes', []))}\n\n"
        
        if pattern_results:
            score_data = pattern_results.get('artificiality_score', {})
            summary_text += f"📡 ANÁLISE DE PADRÕES:\n"
            summary_text += f"   • Score de artificialidade: {score_data.get('score', 0)}/100\n"
            summary_text += f"   • Classificação: {score_data.get('classification', 'N/A')}\n"
            summary_text += f"   • Periodicidades: {pattern_results.get('periodicity', {}).get('n_significant_periods', 0)}\n\n"
        
        summary_text += "="*80
        
        ax_summary.text(0.05, 0.5, summary_text, fontsize=11, family='monospace',
                       verticalalignment='center',
                       bbox=dict(boxstyle='round', facecolor='black', 
                                alpha=0.9, edgecolor='cyan', linewidth=2))
        
        plt.suptitle('🌌 DASHBOARD DE ANÁLISE CÓSMICA 🌌', 
                    fontsize=18, fontweight='bold', y=0.98)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()

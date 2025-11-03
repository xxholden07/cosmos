"""
Detector de Padrões e Mensagens em Sinais Cósmicos
Busca por sinais não-aleatórios, periodicidades e possíveis mensagens (SETI)
"""

import numpy as np
from scipy import signal, stats, fft
from scipy.stats import entropy
from sklearn.decomposition import PCA
import pandas as pd
from typing import Dict, List, Tuple, Optional


class PatternDetector:
    """Detecta padrões não-aleatórios e possíveis mensagens em dados cósmicos"""
    
    def __init__(self, significance_level: float = 0.001):
        """
        Args:
            significance_level: Nível de significância estatística
        """
        self.significance_level = significance_level
        
    def analyze_signal(self, data: np.ndarray, sample_rate: float = 1.0) -> Dict:
        """
        Análise completa de sinal para detectar padrões
        
        Args:
            data: Array de dados do sinal
            sample_rate: Taxa de amostragem (Hz)
            
        Returns:
            Dicionário com análise completa
        """
        analysis = {}
        
        # 1. Testes de aleatoriedade
        analysis['randomness'] = self._test_randomness(data)
        
        # 2. Análise de periodicidade
        analysis['periodicity'] = self._detect_periodicity(data, sample_rate)
        
        # 3. Busca por padrões matemáticos
        analysis['mathematical_patterns'] = self._find_mathematical_patterns(data)
        
        # 4. Análise de entropia
        analysis['entropy'] = self._analyze_entropy(data)
        
        # 5. Detecção de pulsos
        analysis['pulses'] = self._detect_pulses(data)
        
        # 6. Análise espectral avançada
        analysis['spectral'] = self._advanced_spectral_analysis(data, sample_rate)
        
        # 7. Busca por modulações
        analysis['modulation'] = self._detect_modulation(data)
        
        # 8. Análise de correlação
        analysis['correlation'] = self._analyze_autocorrelation(data)
        
        # 9. Score geral de "artificialidade"
        analysis['artificiality_score'] = self._calculate_artificiality_score(analysis)
        
        return analysis
    
    def _test_randomness(self, data: np.ndarray) -> Dict:
        """Testa aleatoriedade do sinal usando múltiplos testes"""
        results = {}
        
        # 1. Teste de Runs (sequências)
        median = np.median(data)
        runs = np.diff(data > median).astype(int)
        n_runs = np.sum(np.abs(runs)) + 1
        n = len(data)
        n1 = np.sum(data > median)
        n2 = n - n1
        
        if n1 > 0 and n2 > 0:
            expected_runs = (2 * n1 * n2) / n + 1
            var_runs = (2 * n1 * n2 * (2 * n1 * n2 - n)) / (n**2 * (n - 1))
            z_runs = (n_runs - expected_runs) / np.sqrt(var_runs) if var_runs > 0 else 0
            p_runs = 2 * (1 - stats.norm.cdf(abs(z_runs)))
            
            results['runs_test'] = {
                'z_score': z_runs,
                'p_value': p_runs,
                'is_random': p_runs > self.significance_level
            }
        
        # 2. Teste de autocorrelação
        acf = self._compute_acf(data, nlags=min(100, len(data)//4))
        # Sinal aleatório deve ter autocorrelações próximas de zero
        max_acf = np.max(np.abs(acf[1:]))  # Excluir lag 0
        
        results['autocorrelation_test'] = {
            'max_autocorr': max_acf,
            'is_random': max_acf < 0.2  # Threshold arbitrário
        }
        
        # 3. Teste de normalidade (Shapiro-Wilk)
        if len(data) < 5000:
            stat, p_value = stats.shapiro(data)
            results['normality_test'] = {
                'statistic': stat,
                'p_value': p_value,
                'is_normal': p_value > self.significance_level
            }
        
        # 4. Análise de distribuição
        results['distribution'] = {
            'mean': np.mean(data),
            'std': np.std(data),
            'skewness': stats.skew(data),
            'kurtosis': stats.kurtosis(data)
        }
        
        return results
    
    def _detect_periodicity(self, data: np.ndarray, sample_rate: float) -> Dict:
        """Detecta periodicidades no sinal"""
        # Lomb-Scargle periodogram para dados irregularmente espaçados
        time = np.arange(len(data)) / sample_rate
        
        # FFT para análise rápida
        fft_data = fft.fft(data - np.mean(data))
        power = np.abs(fft_data) ** 2
        freqs = fft.fftfreq(len(data), 1/sample_rate)
        
        # Apenas frequências positivas
        positive_mask = freqs > 0
        freqs = freqs[positive_mask]
        power = power[positive_mask]
        
        # Encontrar picos significativos
        threshold = np.mean(power) + 5 * np.std(power)
        peaks, properties = signal.find_peaks(power, height=threshold, distance=5)
        
        periodicities = []
        for peak in peaks[:10]:  # Top 10 periodicidades
            freq = freqs[peak]
            period = 1 / freq if freq > 0 else np.inf
            power_val = power[peak]
            significance = (power_val - np.mean(power)) / np.std(power)
            
            periodicities.append({
                'frequency_Hz': freq,
                'period_seconds': period,
                'power': power_val,
                'significance_sigma': significance
            })
        
        return {
            'n_significant_periods': len(periodicities),
            'periodicities': periodicities,
            'is_periodic': len(periodicities) > 0
        }
    
    def _find_mathematical_patterns(self, data: np.ndarray) -> Dict:
        """Busca padrões matemáticos (números primos, Fibonacci, etc)"""
        patterns = {}
        
        # 1. Buscar sequências de números primos
        if self._is_integer_like(data):
            data_int = np.round(data).astype(int)
            prime_ratio = self._count_primes(data_int) / len(data_int)
            patterns['prime_numbers'] = {
                'ratio': prime_ratio,
                'significant': prime_ratio > 0.1  # >10% primos é suspeito
            }
        
        # 2. Buscar razões especiais (phi, pi, e)
        ratios = np.abs(np.diff(data))
        ratios = ratios[ratios > 0]
        
        if len(ratios) > 10:
            golden_ratio = 1.618033988749895
            pi = np.pi
            e = np.e
            
            # Verificar se ratios estão próximos de constantes especiais
            golden_matches = np.sum(np.abs(ratios - golden_ratio) < 0.01) / len(ratios)
            pi_matches = np.sum(np.abs(ratios - pi) < 0.01) / len(ratios)
            e_matches = np.sum(np.abs(ratios - e) < 0.01) / len(ratios)
            
            patterns['special_ratios'] = {
                'golden_ratio_frequency': golden_matches,
                'pi_frequency': pi_matches,
                'e_frequency': e_matches,
                'significant': max(golden_matches, pi_matches, e_matches) > 0.05
            }
        
        # 3. Buscar padrões de repetição
        patterns['repetition'] = self._find_repeating_sequences(data)
        
        return patterns
    
    def _analyze_entropy(self, data: np.ndarray) -> Dict:
        """Analisa entropia do sinal"""
        # Quantizar dados para calcular entropia
        n_bins = min(100, len(data) // 10)
        hist, _ = np.histogram(data, bins=n_bins)
        hist = hist / np.sum(hist)  # Normalizar
        
        # Entropia de Shannon
        shannon_entropy = entropy(hist[hist > 0])
        
        # Entropia máxima possível
        max_entropy = np.log2(n_bins)
        
        # Entropia normalizada
        normalized_entropy = shannon_entropy / max_entropy if max_entropy > 0 else 0
        
        # Sinal aleatório tem alta entropia (~1.0)
        # Sinal com padrão tem baixa entropia
        
        return {
            'shannon_entropy': shannon_entropy,
            'max_entropy': max_entropy,
            'normalized_entropy': normalized_entropy,
            'interpretation': 'High randomness' if normalized_entropy > 0.8 else
                             'Some structure' if normalized_entropy > 0.5 else
                             'Highly structured'
        }
    
    def _detect_pulses(self, data: np.ndarray) -> Dict:
        """Detecta pulsos discretos no sinal"""
        # Calcular derivada para encontrar mudanças abruptas
        diff = np.abs(np.diff(data))
        threshold = np.mean(diff) + 3 * np.std(diff)
        
        pulse_indices = np.where(diff > threshold)[0]
        
        if len(pulse_indices) > 1:
            # Analisar intervalos entre pulsos
            intervals = np.diff(pulse_indices)
            
            # Verificar se intervalos são regulares
            interval_std = np.std(intervals)
            interval_mean = np.mean(intervals)
            regularity = 1 - (interval_std / interval_mean) if interval_mean > 0 else 0
            
            return {
                'n_pulses': len(pulse_indices),
                'mean_interval': interval_mean,
                'interval_regularity': regularity,
                'is_regular': regularity > 0.8  # >80% regular
            }
        
        return {'n_pulses': len(pulse_indices), 'is_regular': False}
    
    def _advanced_spectral_analysis(self, data: np.ndarray, sample_rate: float) -> Dict:
        """Análise espectral avançada"""
        # Spectrogram para análise tempo-frequência
        f, t, Sxx = signal.spectrogram(data, fs=sample_rate, nperseg=min(256, len(data)//4))
        
        # Encontrar características espectrais
        spectral_centroid = np.sum(f[:, np.newaxis] * Sxx, axis=0) / np.sum(Sxx, axis=0)
        spectral_rolloff = self._calculate_spectral_rolloff(f, Sxx)
        
        # Verificar por linhas espectrais estreitas (sinal artificial?)
        narrow_line_score = self._detect_narrow_spectral_lines(f, np.mean(Sxx, axis=1))
        
        return {
            'spectral_centroid_mean': np.mean(spectral_centroid),
            'spectral_rolloff_mean': np.mean(spectral_rolloff),
            'narrow_line_score': narrow_line_score,
            'has_narrow_lines': narrow_line_score > 0.5
        }
    
    def _detect_modulation(self, data: np.ndarray) -> Dict:
        """Detecta modulação no sinal (AM, FM, etc)"""
        # Envelope do sinal (modulação em amplitude)
        analytic_signal = signal.hilbert(data)
        amplitude_envelope = np.abs(analytic_signal)
        instantaneous_phase = np.unwrap(np.angle(analytic_signal))
        instantaneous_frequency = np.diff(instantaneous_phase) / (2.0 * np.pi)
        
        # Verificar se envelope está modulado
        envelope_var = np.var(amplitude_envelope)
        envelope_mean = np.mean(amplitude_envelope)
        am_index = np.sqrt(envelope_var) / envelope_mean if envelope_mean > 0 else 0
        
        # Verificar se frequência está modulada
        freq_var = np.var(instantaneous_frequency)
        
        return {
            'amplitude_modulation_index': am_index,
            'has_am': am_index > 0.1,
            'frequency_variance': freq_var,
            'has_fm': freq_var > 0.01
        }
    
    def _analyze_autocorrelation(self, data: np.ndarray) -> Dict:
        """Analisa autocorrelação do sinal"""
        acf = self._compute_acf(data, nlags=min(500, len(data)//2))
        
        # Encontrar picos de autocorrelação
        peaks, _ = signal.find_peaks(acf[1:], height=0.3)
        
        return {
            'autocorrelation': acf[:100].tolist(),  # Primeiros 100 lags
            'n_significant_peaks': len(peaks),
            'max_autocorr': np.max(acf[1:]) if len(acf) > 1 else 0,
            'has_periodicity': len(peaks) > 0
        }
    
    def _calculate_artificiality_score(self, analysis: Dict) -> Dict:
        """Calcula score de probabilidade de ser sinal artificial"""
        score = 0
        reasons = []
        
        # Pontos por não-aleatoriedade
        if 'randomness' in analysis:
            if 'runs_test' in analysis['randomness']:
                if not analysis['randomness']['runs_test']['is_random']:
                    score += 20
                    reasons.append("Non-random pattern detected (runs test)")
        
        # Pontos por periodicidade
        if analysis['periodicity']['is_periodic']:
            n_periods = analysis['periodicity']['n_significant_periods']
            score += min(30, n_periods * 10)
            reasons.append(f"Strong periodicity ({n_periods} frequencies)")
        
        # Pontos por padrões matemáticos
        if 'mathematical_patterns' in analysis:
            if analysis['mathematical_patterns'].get('repetition', {}).get('has_repetition'):
                score += 15
                reasons.append("Repeating sequences found")
        
        # Pontos por baixa entropia (estrutura)
        if analysis['entropy']['normalized_entropy'] < 0.5:
            score += 15
            reasons.append("Low entropy (structured signal)")
        
        # Pontos por pulsos regulares
        if analysis['pulses'].get('is_regular'):
            score += 20
            reasons.append("Regular pulse pattern")
        
        # Pontos por linhas espectrais estreitas
        if analysis['spectral'].get('has_narrow_lines'):
            score += 15
            reasons.append("Narrow spectral lines (artificial signature)")
        
        # Pontos por modulação
        if analysis['modulation']['has_am'] or analysis['modulation']['has_fm']:
            score += 10
            reasons.append("Signal modulation detected")
        
        # Classificação
        if score >= 70:
            classification = "HIGHLY ARTIFICIAL - Strong candidate for intelligent signal"
        elif score >= 50:
            classification = "POSSIBLY ARTIFICIAL - Warrants further investigation"
        elif score >= 30:
            classification = "STRUCTURED - Some non-random patterns"
        else:
            classification = "NATURAL - Consistent with random/natural processes"
        
        return {
            'score': min(100, score),
            'classification': classification,
            'reasons': reasons
        }
    
    # Funções auxiliares
    
    def _compute_acf(self, data: np.ndarray, nlags: int) -> np.ndarray:
        """Calcula função de autocorrelação"""
        data_centered = data - np.mean(data)
        acf = np.correlate(data_centered, data_centered, mode='full')
        acf = acf[len(acf)//2:]
        acf = acf / acf[0]  # Normalizar
        return acf[:nlags]
    
    def _is_integer_like(self, data: np.ndarray) -> bool:
        """Verifica se dados são aproximadamente inteiros"""
        return np.allclose(data, np.round(data), atol=0.1)
    
    def _count_primes(self, numbers: np.ndarray) -> int:
        """Conta números primos em array"""
        count = 0
        for n in numbers:
            if n > 1 and self._is_prime(int(abs(n))):
                count += 1
        return count
    
    def _is_prime(self, n: int) -> bool:
        """Verifica se número é primo"""
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        for i in range(3, int(np.sqrt(n)) + 1, 2):
            if n % i == 0:
                return False
        return True
    
    def _find_repeating_sequences(self, data: np.ndarray, min_length: int = 3) -> Dict:
        """Encontra sequências que se repetem"""
        # Quantizar dados para facilitar comparação
        data_quant = np.round(data, decimals=2)
        
        max_repeats = 0
        best_sequence_length = 0
        
        for seq_len in range(min_length, min(20, len(data)//4)):
            for i in range(len(data) - seq_len):
                sequence = data_quant[i:i+seq_len]
                
                # Buscar esta sequência no resto dos dados
                repeats = 0
                for j in range(i+seq_len, len(data)-seq_len):
                    if np.allclose(data_quant[j:j+seq_len], sequence, atol=0.1):
                        repeats += 1
                
                if repeats > max_repeats:
                    max_repeats = repeats
                    best_sequence_length = seq_len
        
        return {
            'max_repetitions': max_repeats,
            'sequence_length': best_sequence_length,
            'has_repetition': max_repeats >= 2
        }
    
    def _calculate_spectral_rolloff(self, freqs: np.ndarray, power: np.ndarray, 
                                   percentile: float = 0.85) -> float:
        """Calcula frequência de rolloff espectral"""
        cumsum = np.cumsum(power, axis=0)
        total = cumsum[-1]
        rolloff_idx = np.argmax(cumsum >= percentile * total, axis=0)
        return np.mean(freqs[rolloff_idx])
    
    def _detect_narrow_spectral_lines(self, freqs: np.ndarray, power: np.ndarray) -> float:
        """Detecta linhas espectrais estreitas (característico de sinais artificiais)"""
        # Calcular largura dos picos
        peaks, properties = signal.find_peaks(power, height=np.median(power) * 3, prominence=np.std(power))
        
        if len(peaks) == 0:
            return 0.0
        
        # Estimar largura dos picos
        widths = signal.peak_widths(power, peaks, rel_height=0.5)[0]
        
        # Picos estreitos são suspeitos
        narrow_peaks = np.sum(widths < 5)
        
        return narrow_peaks / len(peaks) if len(peaks) > 0 else 0.0
    
    def generate_pattern_report(self, analysis: Dict) -> str:
        """Gera relatório de análise de padrões"""
        report = "="*70 + "\n"
        report += "RELATÓRIO DE ANÁLISE DE PADRÕES E SINAIS\n"
        report += "="*70 + "\n\n"
        
        score = analysis['artificiality_score']
        report += f"🎯 SCORE DE ARTIFICIALIDADE: {score['score']}/100\n"
        report += f"📊 CLASSIFICAÇÃO: {score['classification']}\n\n"
        
        if score['reasons']:
            report += "🔍 EVIDÊNCIAS ENCONTRADAS:\n"
            for reason in score['reasons']:
                report += f"  • {reason}\n"
            report += "\n"
        
        report += "📈 ANÁLISE DE ALEATORIEDADE:\n"
        report += "-"*70 + "\n"
        if 'runs_test' in analysis['randomness']:
            rt = analysis['randomness']['runs_test']
            report += f"  Teste de Runs: {'ALEATÓRIO' if rt['is_random'] else 'NÃO-ALEATÓRIO'}\n"
            report += f"    p-value: {rt['p_value']:.4f}\n"
        report += "\n"
        
        report += "🔄 PERIODICIDADE:\n"
        report += "-"*70 + "\n"
        report += f"  Períodos significativos: {analysis['periodicity']['n_significant_periods']}\n"
        for i, p in enumerate(analysis['periodicity']['periodicities'][:5], 1):
            report += f"    {i}. Frequência: {p['frequency_Hz']:.4f} Hz "
            report += f"(Período: {p['period_seconds']:.2f}s, σ={p['significance_sigma']:.1f})\n"
        report += "\n"
        
        report += "📊 ENTROPIA:\n"
        report += "-"*70 + "\n"
        ent = analysis['entropy']
        report += f"  Entropia normalizada: {ent['normalized_entropy']:.3f}\n"
        report += f"  Interpretação: {ent['interpretation']}\n\n"
        
        if analysis['pulses'].get('is_regular'):
            report += "⚡ PULSOS REGULARES DETECTADOS:\n"
            report += "-"*70 + "\n"
            report += f"  Número de pulsos: {analysis['pulses']['n_pulses']}\n"
            report += f"  Intervalo médio: {analysis['pulses']['mean_interval']:.2f}\n"
            report += f"  Regularidade: {analysis['pulses']['interval_regularity']*100:.1f}%\n\n"
        
        report += "="*70 + "\n"
        return report

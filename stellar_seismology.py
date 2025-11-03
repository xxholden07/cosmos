"""
Analisador de Vibrações Estelares (Asterosismologia)
Analisa oscilações e frequências de pulsação em estrelas
"""

import numpy as np
from scipy import signal, fft
from scipy.optimize import curve_fit
from scipy.stats import gaussian_kde
import pandas as pd
from typing import Dict, List, Tuple, Optional


class StellarSeismologyAnalyzer:
    """Analisa vibrações e oscilações estelares para determinar propriedades internas"""
    
    def __init__(self):
        self.solar_nu_max = 3090.0  # μHz (frequência de potência máxima do Sol)
        self.solar_delta_nu = 135.1  # μHz (grande separação do Sol)
        
    def analyze_stellar_vibrations(
        self,
        time: np.ndarray,
        flux: np.ndarray,
        cadence: float = 30.0  # minutos
    ) -> Dict:
        """
        Análise completa de vibrações estelares
        
        Args:
            time: Array de tempos (dias)
            flux: Array de fluxo normalizado
            cadence: Cadência de observação em minutos
            
        Returns:
            Dicionário com análise completa de asterosismologia
        """
        # 1. Preparar dados
        flux_prep = self._prepare_lightcurve(time, flux)
        
        # 2. Calcular espectro de potência
        frequencies, power = self._calculate_power_spectrum(time, flux_prep, cadence)
        
        # 3. Identificar frequência de potência máxima (nu_max)
        nu_max = self._find_nu_max(frequencies, power)
        
        # 4. Calcular grande separação (Delta nu)
        delta_nu = self._calculate_large_separation(frequencies, power, nu_max)
        
        # 5. Identificar modos de oscilação
        modes = self._identify_oscillation_modes(frequencies, power, nu_max, delta_nu)
        
        # 6. Estimar propriedades estelares
        stellar_params = self._estimate_stellar_parameters(nu_max, delta_nu)
        
        # 7. Calcular largura do envelope
        envelope_width = self._calculate_envelope_width(frequencies, power, nu_max)
        
        # 8. Detectar rotação estelar
        rotation = self._detect_stellar_rotation(frequencies, power, modes)
        
        return {
            'nu_max_uHz': nu_max,
            'delta_nu_uHz': delta_nu,
            'envelope_width_uHz': envelope_width,
            'oscillation_modes': modes,
            'stellar_parameters': stellar_params,
            'rotation': rotation,
            'power_spectrum': {
                'frequencies': frequencies,
                'power': power
            },
            'quality_metrics': self._calculate_quality_metrics(power, modes)
        }
    
    def _prepare_lightcurve(self, time: np.ndarray, flux: np.ndarray) -> np.ndarray:
        """Prepara curva de luz removendo tendências e normalizando"""
        # Remover outliers
        flux_median = np.median(flux)
        flux_std = np.std(flux)
        mask = np.abs(flux - flux_median) < 5 * flux_std
        
        flux_clean = flux.copy()
        flux_clean[~mask] = flux_median
        
        # Remover tendência de longo período
        window_size = min(len(flux_clean) // 10, 1000)
        if window_size > 10:
            trend = signal.savgol_filter(flux_clean, window_size | 1, 3)
            flux_detrended = flux_clean - trend + np.median(trend)
        else:
            flux_detrended = flux_clean
        
        # Normalizar
        flux_norm = (flux_detrended - np.mean(flux_detrended)) / np.std(flux_detrended)
        
        return flux_norm
    
    def _calculate_power_spectrum(
        self,
        time: np.ndarray,
        flux: np.ndarray,
        cadence: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Calcula espectro de potência usando FFT"""
        # Interpolar para grid regular se necessário
        dt = cadence / (24 * 60)  # Converter para dias
        time_regular = np.arange(time[0], time[-1], dt)
        flux_regular = np.interp(time_regular, time, flux)
        
        # Calcular FFT
        fft_flux = fft.fft(flux_regular)
        power = np.abs(fft_flux) ** 2
        
        # Frequências em microHertz
        n = len(flux_regular)
        freq_hz = fft.fftfreq(n, dt * 86400)  # Converter dias para segundos
        freq_uHz = freq_hz * 1e6
        
        # Apenas frequências positivas
        positive_mask = freq_uHz > 0
        frequencies = freq_uHz[positive_mask]
        power = power[positive_mask]
        
        # Suavizar espectro
        power_smooth = self._smooth_power_spectrum(frequencies, power)
        
        return frequencies, power_smooth
    
    def _smooth_power_spectrum(
        self,
        frequencies: np.ndarray,
        power: np.ndarray,
        box_size: int = 10
    ) -> np.ndarray:
        """Suaviza espectro de potência"""
        kernel = np.ones(box_size) / box_size
        power_smooth = np.convolve(power, kernel, mode='same')
        return power_smooth
    
    def _find_nu_max(self, frequencies: np.ndarray, power: np.ndarray) -> float:
        """Encontra frequência de potência máxima"""
        # Buscar em range típico de estrelas (10-5000 μHz)
        mask = (frequencies > 10) & (frequencies < 5000)
        if not np.any(mask):
            mask = np.ones(len(frequencies), dtype=bool)
        
        freq_range = frequencies[mask]
        power_range = power[mask]
        
        # Encontrar pico máximo
        peak_idx = np.argmax(power_range)
        nu_max = freq_range[peak_idx]
        
        # Refinar usando ajuste gaussiano
        try:
            # Região ao redor do pico
            width = 500  # μHz
            fit_mask = np.abs(freq_range - nu_max) < width
            
            if np.sum(fit_mask) > 10:
                popt, _ = curve_fit(
                    self._gaussian,
                    freq_range[fit_mask],
                    power_range[fit_mask],
                    p0=[np.max(power_range), nu_max, width/2]
                )
                nu_max = popt[1]
        except:
            pass
        
        return nu_max
    
    def _calculate_large_separation(
        self,
        frequencies: np.ndarray,
        power: np.ndarray,
        nu_max: float
    ) -> float:
        """Calcula grande separação (Delta nu) usando autocorrelação"""
        # Região ao redor de nu_max
        width = min(nu_max * 0.5, 1000)
        mask = np.abs(frequencies - nu_max) < width
        
        freq_region = frequencies[mask]
        power_region = power[mask]
        
        if len(power_region) < 20:
            # Usar relação de escala
            return 0.263 * (nu_max ** 0.772)
        
        # Autocorrelação
        autocorr = np.correlate(power_region, power_region, mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        
        # Encontrar primeiro pico após lag zero
        peaks, _ = signal.find_peaks(autocorr, distance=5)
        
        if len(peaks) > 0:
            # Converter lag para frequência
            delta_freq = np.mean(np.diff(freq_region))
            delta_nu = peaks[0] * delta_freq
        else:
            # Usar relação de escala como fallback
            delta_nu = 0.263 * (nu_max ** 0.772)
        
        return delta_nu
    
    def _identify_oscillation_modes(
        self,
        frequencies: np.ndarray,
        power: np.ndarray,
        nu_max: float,
        delta_nu: float
    ) -> List[Dict]:
        """Identifica modos de oscilação individuais"""
        # Região ao redor de nu_max
        width = 5 * delta_nu
        mask = np.abs(frequencies - nu_max) < width
        
        freq_region = frequencies[mask]
        power_region = power[mask]
        
        # Encontrar picos
        threshold = np.percentile(power_region, 75)
        peaks, properties = signal.find_peaks(
            power_region,
            height=threshold,
            distance=max(1, int(delta_nu / np.mean(np.diff(freq_region)) / 3))
        )
        
        modes = []
        for peak in peaks:
            freq = freq_region[peak]
            amplitude = power_region[peak]
            
            # Classificar modo (l=0, 1, 2, 3...)
            # l=0 são os modos radiais principais
            mode_order = int(round((freq - nu_max) / delta_nu))
            
            # Estimar grau do modo
            offset = (freq - (nu_max + mode_order * delta_nu)) / delta_nu
            
            if abs(offset) < 0.15:
                degree = 0  # Modo radial
            elif abs(offset - 0.5) < 0.15:
                degree = 1  # Modo dipolar
            elif abs(offset + 0.5) < 0.15:
                degree = 1  # Modo dipolar
            else:
                degree = 2  # Modo quadrupolar
            
            modes.append({
                'frequency_uHz': freq,
                'amplitude': amplitude,
                'mode_order': mode_order,
                'degree': degree,
                'type': self._classify_mode(degree)
            })
        
        return modes
    
    def _estimate_stellar_parameters(
        self,
        nu_max: float,
        delta_nu: float
    ) -> Dict:
        """Estima parâmetros estelares usando relações de escala"""
        # Relações de escala asterosísmicas
        # Referência: Chaplin & Miglio (2013)
        
        # Massa (em massas solares)
        mass = (nu_max / self.solar_nu_max) ** 3 * \
               (delta_nu / self.solar_delta_nu) ** -4
        
        # Raio (em raios solares)
        radius = (nu_max / self.solar_nu_max) * \
                 (delta_nu / self.solar_delta_nu) ** -2
        
        # Gravidade superficial (log g)
        log_g = np.log10(mass / radius ** 2) + 4.437  # log g do Sol = 4.437
        
        # Densidade média (em densidades solares)
        density = (delta_nu / self.solar_delta_nu) ** 2
        
        # Estimativa de idade (muito aproximada)
        # Estrelas mais massivas: evolução mais rápida
        if mass > 1.2:
            age_gyr = 5.0 / mass  # Vida mais curta
        else:
            age_gyr = 5.0 + (1.0 - mass) * 5.0  # Vida mais longa
        
        # Temperatura efetiva (estimativa grosseira)
        if nu_max > 2000:
            teff = 5777 + (nu_max - 3090) * 0.5  # Similar ao Sol
        else:
            teff = 5777 - (3090 - nu_max) * 1.0  # Gigante vermelha
        
        return {
            'mass_solar': mass,
            'radius_solar': radius,
            'log_g': log_g,
            'density_solar': density,
            'age_gyr': age_gyr,
            'teff_K': int(teff),
            'evolutionary_stage': self._classify_evolutionary_stage(mass, radius, log_g)
        }
    
    def _calculate_envelope_width(
        self,
        frequencies: np.ndarray,
        power: np.ndarray,
        nu_max: float
    ) -> float:
        """Calcula largura do envelope de oscilação"""
        # Ajustar gaussiana ao envelope
        mask = (frequencies > nu_max/2) & (frequencies < nu_max*2)
        freq_range = frequencies[mask]
        power_range = power[mask]
        
        try:
            popt, _ = curve_fit(
                self._gaussian,
                freq_range,
                power_range,
                p0=[np.max(power_range), nu_max, nu_max * 0.25]
            )
            width = abs(popt[2]) * 2.355  # FWHM
        except:
            width = nu_max * 0.25
        
        return width
    
    def _detect_stellar_rotation(
        self,
        frequencies: np.ndarray,
        power: np.ndarray,
        modes: List[Dict]
    ) -> Dict:
        """Detecta rotação estelar através de divisão rotacional"""
        if len(modes) < 3:
            return {'detected': False}
        
        # Buscar pares de picos separados por rotação
        # Rotação causa divisão dos modos l=1
        mode_freqs = np.array([m['frequency_uHz'] for m in modes])
        
        # Calcular diferenças entre modos próximos
        diffs = []
        for i in range(len(mode_freqs)-1):
            for j in range(i+1, len(mode_freqs)):
                diff = abs(mode_freqs[j] - mode_freqs[i])
                if 0.1 < diff < 2.0:  # Range típico de divisão rotacional
                    diffs.append(diff)
        
        if len(diffs) > 0:
            # Divisão rotacional típica
            rot_split = np.median(diffs)
            
            # Período de rotação (aproximado)
            # rot_split ≈ rotational_frequency / 2
            rot_period_days = 1 / (2 * rot_split * 1e-6) / 86400
            
            return {
                'detected': True,
                'rotational_splitting_uHz': rot_split,
                'rotation_period_days': rot_period_days,
                'angular_velocity_rad_s': 2 * np.pi / (rot_period_days * 86400)
            }
        
        return {'detected': False}
    
    def _calculate_quality_metrics(
        self,
        power: np.ndarray,
        modes: List[Dict]
    ) -> Dict:
        """Calcula métricas de qualidade da análise"""
        snr = np.max(power) / np.median(power)
        
        return {
            'signal_to_noise': snr,
            'n_modes_detected': len(modes),
            'quality_flag': 'GOOD' if (snr > 3 and len(modes) > 5) else 
                           'FAIR' if (snr > 2 and len(modes) > 2) else 'POOR'
        }
    
    def _gaussian(self, x: np.ndarray, amp: float, mu: float, sigma: float) -> np.ndarray:
        """Função gaussiana para ajustes"""
        return amp * np.exp(-(x - mu)**2 / (2 * sigma**2))
    
    def _classify_mode(self, degree: int) -> str:
        """Classifica tipo de modo de oscilação"""
        mode_types = {
            0: "Radial (l=0)",
            1: "Dipole (l=1)",
            2: "Quadrupole (l=2)",
            3: "Octupole (l=3)"
        }
        return mode_types.get(degree, f"l={degree}")
    
    def _classify_evolutionary_stage(
        self,
        mass: float,
        radius: float,
        log_g: float
    ) -> str:
        """Classifica estágio evolutivo da estrela"""
        if log_g > 4.0:
            return "Main Sequence"
        elif log_g > 3.5:
            return "Subgiant"
        elif log_g > 2.5:
            return "Red Giant Branch"
        else:
            return "Red Clump / Asymptotic Giant Branch"
    
    def generate_seismology_report(self, analysis: Dict) -> str:
        """Gera relatório detalhado de asterosismologia"""
        report = "="*70 + "\n"
        report += "RELATÓRIO DE ASTEROSISMOLOGIA - ANÁLISE DE VIBRAÇÕES ESTELARES\n"
        report += "="*70 + "\n\n"
        
        report += "📊 FREQUÊNCIAS DE OSCILAÇÃO:\n"
        report += "-"*70 + "\n"
        report += f"  ν_max (freq. potência máxima): {analysis['nu_max_uHz']:.2f} μHz\n"
        report += f"  Δν (grande separação):         {analysis['delta_nu_uHz']:.2f} μHz\n"
        report += f"  Largura do envelope:           {analysis['envelope_width_uHz']:.2f} μHz\n\n"
        
        params = analysis['stellar_parameters']
        report += "⭐ PARÂMETROS ESTELARES DERIVADOS:\n"
        report += "-"*70 + "\n"
        report += f"  Massa:                {params['mass_solar']:.2f} M☉\n"
        report += f"  Raio:                 {params['radius_solar']:.2f} R☉\n"
        report += f"  log g:                {params['log_g']:.2f}\n"
        report += f"  Densidade:            {params['density_solar']:.2f} ρ☉\n"
        report += f"  Temperatura efetiva:  {params['teff_K']} K\n"
        report += f"  Idade estimada:       {params['age_gyr']:.2f} Gyr\n"
        report += f"  Estágio evolutivo:    {params['evolutionary_stage']}\n\n"
        
        report += f"🎵 MODOS DE OSCILAÇÃO DETECTADOS: {len(analysis['oscillation_modes'])}\n"
        report += "-"*70 + "\n"
        for i, mode in enumerate(analysis['oscillation_modes'][:10], 1):
            report += f"  Modo {i}: {mode['frequency_uHz']:.2f} μHz - {mode['type']}\n"
        if len(analysis['oscillation_modes']) > 10:
            report += f"  ... e mais {len(analysis['oscillation_modes']) - 10} modos\n"
        report += "\n"
        
        if analysis['rotation']['detected']:
            rot = analysis['rotation']
            report += "🌀 ROTAÇÃO ESTELAR DETECTADA:\n"
            report += "-"*70 + "\n"
            report += f"  Divisão rotacional:   {rot['rotational_splitting_uHz']:.3f} μHz\n"
            report += f"  Período de rotação:   {rot['rotation_period_days']:.1f} dias\n\n"
        
        metrics = analysis['quality_metrics']
        report += f"✓ QUALIDADE DA ANÁLISE: {metrics['quality_flag']}\n"
        report += f"  SNR: {metrics['signal_to_noise']:.1f}\n\n"
        
        report += "="*70 + "\n"
        return report

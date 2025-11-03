"""
Detector de Corpos Celestes
Identifica asteroides, cometas, planetas e objetos transientes em dados astronômicos
"""

import numpy as np
from scipy import signal
from scipy.stats import chi2
import pandas as pd
from typing import Dict, List, Tuple, Optional


class CelestialBodyDetector:
    """Detecta e classifica diferentes tipos de corpos celestes"""
    
    def __init__(self, sensitivity: float = 3.0):
        """
        Args:
            sensitivity: Limiar de sensibilidade em sigmas para detecção
        """
        self.sensitivity = sensitivity
        
    def detect_transiting_planets(
        self, 
        time: np.ndarray, 
        flux: np.ndarray,
        min_period: float = 0.5,
        max_period: float = 50.0
    ) -> List[Dict]:
        """
        Detecta exoplanetas por método de trânsito
        
        Args:
            time: Array de tempos de observação
            flux: Array de fluxo normalizado
            min_period: Período mínimo orbital (dias)
            max_period: Período máximo orbital (dias)
            
        Returns:
            Lista de planetas detectados com parâmetros
        """
        # Remover outliers manualmente (evitar problema com masked arrays)
        flux_median = np.median(flux)
        flux_std = np.std(flux)
        mask = np.abs(flux - flux_median) < 5 * flux_std
        
        time_clean = time[mask]
        flux_clean = flux[mask]
        
        # Normalizar fluxo
        flux_norm = flux_clean / np.median(flux_clean)
        
        # Buscar períodos usando Lomb-Scargle
        frequency = np.linspace(1/max_period, 1/min_period, 10000)
        power = signal.lombscargle(time_clean, flux_norm - 1, frequency, normalize=True)
        
        # Encontrar picos
        peaks, properties = signal.find_peaks(power, height=0.1, distance=100)
        
        planets = []
        for i, peak in enumerate(peaks[:5]):  # Top 5 candidatos
            period = 1 / frequency[peak]
            power_val = power[peak]
            
            # Dobrar curva de luz no período
            phase = (time_clean % period) / period
            sort_idx = np.argsort(phase)
            phase_sorted = phase[sort_idx]
            flux_sorted = flux_norm[sort_idx]
            
            # Detectar profundidade do trânsito
            transit_depth = self._calculate_transit_depth(flux_sorted)
            transit_duration = self._estimate_transit_duration(phase_sorted, flux_sorted)
            
            if transit_depth > 0.001:  # Trânsito significativo (>0.1%)
                planets.append({
                    'period_days': period,
                    'transit_depth': transit_depth,
                    'transit_duration_hours': transit_duration * period * 24,
                    'signal_power': power_val,
                    'confidence': self._calculate_confidence(power_val, transit_depth)
                })
        
        return sorted(planets, key=lambda x: x['confidence'], reverse=True)
    
    def detect_comets(
        self,
        time: np.ndarray,
        flux: np.ndarray,
        positions: Optional[np.ndarray] = None
    ) -> List[Dict]:
        """
        Detecta cometas por variação de brilho não-periódica e movimento
        
        Args:
            time: Array de tempos
            flux: Array de fluxo
            positions: Array Nx2 de posições (RA, Dec) opcional
            
        Returns:
            Lista de cometas detectados
        """
        comets = []
        
        # Normalizar fluxo
        flux_norm = flux / np.median(flux)
        
        # Detectar tendência de aumento/diminuição de brilho (característica de cometas)
        # Cometas geralmente aumentam brilho ao se aproximar do Sol
        window = min(len(flux) // 10, 50)
        flux_smooth = np.convolve(flux_norm, np.ones(window)/window, mode='same')
        
        # Calcular taxa de mudança de brilho
        brightness_change = np.diff(flux_smooth)
        mean_change = np.mean(brightness_change)
        std_change = np.std(brightness_change)
        
        # Detectar padrão de "outburst" típico de cometas
        # Aumento súbito seguido de decaimento gradual
        for i in range(len(flux_smooth) - window):
            segment = flux_smooth[i:i+window]
            
            # Procurar padrão: aumento rápido + platô/decaimento lento
            if len(segment) > 10:
                first_half = segment[:len(segment)//2]
                second_half = segment[len(segment)//2:]
                
                rise = np.max(first_half) - np.min(first_half)
                decay = np.max(second_half) - np.min(second_half)
                
                # Cometa típico: rise rápido, decay lento
                if rise > 0.05 and rise > decay * 1.5:
                    peak_idx = i + np.argmax(segment)
                    
                    comet_data = {
                        'detection_time': time[peak_idx],
                        'peak_brightness': flux_smooth[peak_idx],
                        'brightness_increase': rise,
                        'activity_type': 'outburst',
                        'confidence': min(rise / 0.1, 1.0)
                    }
                    
                    # Se temos dados de posição, calcular movimento
                    if positions is not None and len(positions) > i:
                        velocity = self._calculate_velocity(positions, time, i, window)
                        comet_data['velocity_deg_day'] = velocity
                        comet_data['moving'] = velocity > 0.001
                    
                    comets.append(comet_data)
        
        # Remover duplicatas (cometas detectados múltiplas vezes)
        if comets:
            comets = self._remove_duplicate_detections(comets, time_threshold=5.0)
        
        return comets
    
    def detect_meteors_and_fast_transients(
        self,
        time: np.ndarray,
        flux: np.ndarray,
        min_duration_hours: float = 0.01,
        max_duration_hours: float = 0.5
    ) -> List[Dict]:
        """
        Detecta meteoros e eventos transientes ultra-rápidos
        
        Args:
            time: Array de tempos (dias)
            flux: Array de fluxo
            min_duration_hours: Duração mínima em horas
            max_duration_hours: Duração máxima em horas
            
        Returns:
            Lista de meteoros/eventos rápidos detectados
        """
        meteors = []
        
        flux_norm = flux / np.median(flux)
        
        # Calcular diferenças ponto-a-ponto
        time_diff = np.diff(time) * 24  # Converter para horas
        flux_diff = np.diff(flux_norm)
        
        # Detectar picos súbitos e curtos
        threshold = self.sensitivity * np.std(flux_norm)
        
        i = 0
        while i < len(flux_norm) - 2:
            if flux_norm[i] > 1 + threshold:
                # Encontrar duração do evento
                event_start = i
                event_end = i
                
                # Avançar enquanto o fluxo está elevado
                while event_end < len(flux_norm) - 1 and flux_norm[event_end] > 1 + threshold/2:
                    event_end += 1
                
                duration_hours = (time[event_end] - time[event_start]) * 24
                
                # Verificar se está na faixa de duração esperada
                if min_duration_hours <= duration_hours <= max_duration_hours:
                    peak_flux = np.max(flux_norm[event_start:event_end+1])
                    peak_time = time[event_start + np.argmax(flux_norm[event_start:event_end+1])]
                    
                    meteors.append({
                        'detection_time': peak_time,
                        'peak_brightness': peak_flux,
                        'duration_hours': duration_hours,
                        'amplitude': peak_flux - 1.0,
                        'event_type': 'meteor' if duration_hours < 0.1 else 'fast_transient',
                        'confidence': min((peak_flux - 1.0) / threshold, 1.0)
                    })
                
                i = event_end + 1
            else:
                i += 1
        
        return meteors

    def detect_asteroids(
        self,
        positions: np.ndarray,
        times: np.ndarray,
        velocity_threshold: float = 0.01
    ) -> List[Dict]:
        """
        Detecta asteroides por movimento aparente
        
        Args:
            positions: Array Nx2 de posições (RA, Dec) em graus
            times: Array de tempos correspondentes
            velocity_threshold: Velocidade mínima em graus/dia
            
        Returns:
            Lista de asteroides detectados
        """
        asteroids = []
        
        if len(positions) < 3:
            return asteroids
        
        # Calcular velocidades
        velocities = np.diff(positions, axis=0) / np.diff(times)[:, np.newaxis]
        speeds = np.linalg.norm(velocities, axis=1)
        
        # Detectar objetos em movimento
        moving_mask = speeds > velocity_threshold
        
        if np.any(moving_mask):
            mean_velocity = np.mean(velocities[moving_mask], axis=0)
            mean_speed = np.linalg.norm(mean_velocity)
            
            # Estimar órbita
            orbit_params = self._estimate_orbit(positions, times, velocities)
            
            asteroids.append({
                'mean_velocity_deg_day': mean_speed,
                'velocity_ra': mean_velocity[0],
                'velocity_dec': mean_velocity[1],
                'orbit_type': orbit_params['type'],
                'eccentricity': orbit_params['eccentricity'],
                'first_position': positions[0],
                'last_position': positions[-1],
                'observation_span_days': times[-1] - times[0]
            })
        
        return asteroids
    
    def detect_transient_events(
        self,
        time: np.ndarray,
        magnitude: np.ndarray,
        reference_mag: Optional[float] = None
    ) -> List[Dict]:
        """
        Detecta eventos transientes (supernovas, novas, flares)
        
        Args:
            time: Array de tempos
            magnitude: Array de magnitudes
            reference_mag: Magnitude de referência (baseline)
            
        Returns:
            Lista de eventos transientes detectados
        """
        if reference_mag is None:
            reference_mag = np.median(magnitude)
        
        # Calcular diferenças de magnitude
        delta_mag = magnitude - reference_mag
        
        # Detectar aumentos súbitos de brilho
        threshold = self.sensitivity * np.std(delta_mag)
        
        transients = []
        in_event = False
        event_start = None
        
        for i in range(len(time)):
            if delta_mag[i] < -threshold and not in_event:  # Magnitude menor = mais brilhante
                in_event = True
                event_start = i
            elif (delta_mag[i] > -threshold/2 or i == len(time)-1) and in_event:
                in_event = False
                event_end = i
                
                # Caracterizar evento
                event_mags = magnitude[event_start:event_end+1]
                event_times = time[event_start:event_end+1]
                
                peak_mag = np.min(event_mags)
                peak_time = event_times[np.argmin(event_mags)]
                duration = event_times[-1] - event_times[0]
                
                # Classificar tipo de evento
                event_type = self._classify_transient(
                    peak_mag - reference_mag,
                    duration
                )
                
                transients.append({
                    'start_time': event_times[0],
                    'peak_time': peak_time,
                    'end_time': event_times[-1],
                    'duration_days': duration,
                    'peak_magnitude': peak_mag,
                    'amplitude': reference_mag - peak_mag,
                    'type': event_type,
                    'rise_time': peak_time - event_times[0],
                    'decay_time': event_times[-1] - peak_time
                })
        
        return transients
    
    def _calculate_velocity(self, positions, times, start_idx, window):
        """Calcula velocidade média em uma janela"""
        end_idx = min(start_idx + window, len(positions))
        if end_idx - start_idx < 2:
            return 0.0
        
        pos_segment = positions[start_idx:end_idx]
        time_segment = times[start_idx:end_idx]
        
        # Regressão linear para posição vs tempo
        velocities = np.diff(pos_segment, axis=0) / np.diff(time_segment)[:, np.newaxis]
        return np.linalg.norm(np.mean(velocities, axis=0))
    
    def _remove_duplicate_detections(self, detections, time_threshold=5.0):
        """Remove detecções duplicadas próximas no tempo"""
        if not detections:
            return []
        
        # Ordenar por tempo
        sorted_det = sorted(detections, key=lambda x: x['detection_time'])
        
        unique = [sorted_det[0]]
        for det in sorted_det[1:]:
            if det['detection_time'] - unique[-1]['detection_time'] > time_threshold:
                unique.append(det)
        
        return unique

    def _calculate_transit_depth(self, flux_folded: np.ndarray) -> float:
        """Calcula profundidade do trânsito"""
        baseline = np.percentile(flux_folded, 90)  # Fora do trânsito
        transit = np.percentile(flux_folded, 10)   # Durante o trânsito
        return (baseline - transit) / baseline
    
    def _estimate_transit_duration(self, phase: np.ndarray, flux: np.ndarray) -> float:
        """Estima duração do trânsito como fração do período"""
        threshold = np.percentile(flux, 25)
        in_transit = flux < threshold
        if np.any(in_transit):
            transit_phases = phase[in_transit]
            return np.ptp(transit_phases)  # Range de fases
        return 0.0
    
    def _calculate_confidence(self, power: float, depth: float) -> float:
        """Calcula confiança da detecção"""
        # Combinar poder do sinal e profundidade do trânsito
        confidence = (power * 0.5 + np.log10(depth * 1000) * 0.5)
        return np.clip(confidence * 100, 0, 100)
    
    def _estimate_orbit(
        self,
        positions: np.ndarray,
        times: np.ndarray,
        velocities: np.ndarray
    ) -> Dict:
        """Estima parâmetros orbitais aproximados"""
        # Análise simplificada de órbita
        mean_speed = np.mean(np.linalg.norm(velocities, axis=1))
        
        # Classificar tipo orbital baseado em velocidade
        if mean_speed > 1.0:  # graus/dia
            orbit_type = "NEO"  # Near-Earth Object
            ecc = 0.3
        elif mean_speed > 0.1:
            orbit_type = "Main Belt"
            ecc = 0.15
        else:
            orbit_type = "Outer Belt"
            ecc = 0.1
        
        return {
            'type': orbit_type,
            'eccentricity': ecc
        }
    
    def _classify_transient(self, amplitude: float, duration: float) -> str:
        """Classifica tipo de evento transiente"""
        if amplitude > 5:  # Muito brilhante
            if duration < 1:
                return "Stellar Flare"
            elif duration < 100:
                return "Nova"
            else:
                return "Supernova"
        elif amplitude > 2:
            if duration < 10:
                return "Dwarf Nova"
            else:
                return "Variable Star"
        else:
            return "Minor Transient"
    
    def generate_report(self, detections: Dict) -> str:
        """Gera relatório de detecções"""
        report = "="*60 + "\n"
        report += "RELATÓRIO DE DETECÇÃO DE CORPOS CELESTES\n"
        report += "="*60 + "\n\n"
        
        if 'planets' in detections and detections['planets']:
            report += f"🪐 EXOPLANETAS DETECTADOS: {len(detections['planets'])}\n"
            report += "-"*60 + "\n"
            for i, planet in enumerate(detections['planets'], 1):
                report += f"\nPlaneta Candidato #{i}:\n"
                report += f"  Período Orbital: {planet['period_days']:.2f} dias\n"
                report += f"  Profundidade Trânsito: {planet['transit_depth']*100:.3f}%\n"
                report += f"  Duração Trânsito: {planet['transit_duration_hours']:.2f} horas\n"
                report += f"  Confiança: {planet['confidence']:.1f}%\n"
        
        if 'asteroids' in detections and detections['asteroids']:
            report += f"\n☄️ ASTEROIDES DETECTADOS: {len(detections['asteroids'])}\n"
            report += "-"*60 + "\n"
            for i, asteroid in enumerate(detections['asteroids'], 1):
                report += f"\nAsteroide #{i}:\n"
                report += f"  Velocidade: {asteroid['mean_velocity_deg_day']:.4f} graus/dia\n"
                report += f"  Tipo Orbital: {asteroid['orbit_type']}\n"
                report += f"  Excentricidade: {asteroid['eccentricity']:.2f}\n"
        
        if 'transients' in detections and detections['transients']:
            report += f"\n💥 EVENTOS TRANSIENTES: {len(detections['transients'])}\n"
            report += "-"*60 + "\n"
            for i, event in enumerate(detections['transients'], 1):
                report += f"\nEvento #{i}:\n"
                report += f"  Tipo: {event['type']}\n"
                report += f"  Amplitude: {event['amplitude']:.2f} mag\n"
                report += f"  Duração: {event['duration_days']:.2f} dias\n"
                report += f"  Magnitude Pico: {event['peak_magnitude']:.2f}\n"
        
        report += "\n" + "="*60 + "\n"
        return report

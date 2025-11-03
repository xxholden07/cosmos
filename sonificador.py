"""
Módulo de Sonificação de Dados Astronômicos
Transforma ondulações estelares e variações de brilho em som
"""

import numpy as np
import io
import wave
from scipy.io import wavfile
from scipy import signal

class SonificadorEstelar:
    """Converte dados astronômicos em áudio"""
    
    def __init__(self, sample_rate=44100):
        """
        Inicializa sonificador
        
        Args:
            sample_rate: Taxa de amostragem em Hz (padrão: 44100 Hz - qualidade CD)
        """
        self.sample_rate = sample_rate
    
    def sonificar_curva_luz(self, time, flux, duracao_segundos=10, freq_min=200, freq_max=2000):
        """
        Converte curva de luz em som
        Variações de brilho → Variações de pitch (frequência)
        
        Args:
            time: Array de tempos
            flux: Array de fluxos
            duracao_segundos: Duração do áudio em segundos
            freq_min: Frequência mínima em Hz
            freq_max: Frequência máxima em Hz
            
        Returns:
            tuple: (audio_data, sample_rate)
        """
        # Normalizar fluxo para range 0-1
        flux_norm = (flux - np.min(flux)) / (np.max(flux) - np.min(flux))
        
        # Interpolar para ter pontos suficientes para o áudio
        n_samples = int(self.sample_rate * duracao_segundos)
        time_interp = np.linspace(time[0], time[-1], n_samples)
        flux_interp = np.interp(time_interp, time, flux_norm)
        
        # Mapear fluxo para frequências
        frequencies = freq_min + (freq_max - freq_min) * flux_interp
        
        # Gerar áudio
        t = np.arange(n_samples) / self.sample_rate
        audio = np.zeros(n_samples)
        
        # Síntese de frequência modulada
        phase = 0
        for i in range(n_samples):
            audio[i] = np.sin(2 * np.pi * phase)
            phase += frequencies[i] / self.sample_rate
            if phase > 1:
                phase -= 1
        
        # Aplicar envelope para suavizar início e fim
        envelope = np.ones(n_samples)
        fade_samples = int(0.1 * n_samples)  # 10% fade
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        
        audio = audio * envelope * 0.5  # Volume 50%
        
        return audio, self.sample_rate
    
    def sonificar_vibracoes(self, frequencies, power, duracao_segundos=10, volume=0.3):
        """
        Converte espectro de potência (asterosismologia) em som
        Cada pico de frequência vira um tom audível
        
        Args:
            frequencies: Array de frequências em μHz
            power: Array de potências
            duracao_segundos: Duração do áudio
            volume: Volume (0-1)
            
        Returns:
            tuple: (audio_data, sample_rate)
        """
        # Encontrar picos principais
        peaks, properties = signal.find_peaks(power, height=np.percentile(power, 90))
        
        if len(peaks) == 0:
            # Sem picos, usar frequências distribuídas
            peaks = np.linspace(0, len(frequencies)-1, 10).astype(int)
        
        # Limitar a 20 picos (evitar cacofonia)
        if len(peaks) > 20:
            # Pegar os 20 mais fortes
            peak_powers = power[peaks]
            top_indices = np.argsort(peak_powers)[-20:]
            peaks = peaks[top_indices]
        
        # Gerar áudio
        n_samples = int(self.sample_rate * duracao_segundos)
        t = np.linspace(0, duracao_segundos, n_samples)
        audio = np.zeros(n_samples)
        
        # Cada pico vira uma nota
        for peak_idx in peaks:
            freq_uHz = frequencies[peak_idx]
            # Converter μHz para Hz audível (escala logarítmica)
            # μHz típico: 100-3000 → Hz audível: 200-2000
            freq_hz = 200 + (freq_uHz / 3000) * 1800
            freq_hz = np.clip(freq_hz, 200, 2000)
            
            # Amplitude proporcional à potência
            amplitude = power[peak_idx] / np.max(power) * volume
            
            # Adicionar tom
            audio += amplitude * np.sin(2 * np.pi * freq_hz * t)
        
        # Normalizar
        audio = audio / (np.max(np.abs(audio)) + 1e-10)
        audio = audio * volume
        
        # Aplicar fade
        fade_samples = int(0.1 * n_samples)
        envelope = np.ones(n_samples)
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        audio = audio * envelope
        
        return audio, self.sample_rate
    
    def sonificar_transito(self, time, flux, transit_times, duracao_segundos=15):
        """
        Sonifica trânsitos planetários
        Cria um 'blip' cada vez que o planeta passa na frente da estrela
        
        Args:
            time: Array de tempos
            flux: Array de fluxos
            transit_times: Lista de tempos de trânsito
            duracao_segundos: Duração do áudio
            
        Returns:
            tuple: (audio_data, sample_rate)
        """
        # Áudio base da curva de luz
        audio_base, sr = self.sonificar_curva_luz(time, flux, duracao_segundos)
        
        # Adicionar 'blips' nos trânsitos
        n_samples = len(audio_base)
        time_min, time_max = time[0], time[-1]
        
        for transit_time in transit_times:
            # Posição no áudio
            pos_norm = (transit_time - time_min) / (time_max - time_min)
            pos_sample = int(pos_norm * n_samples)
            
            if 0 <= pos_sample < n_samples:
                # Criar blip (tom curto e grave)
                blip_duration = 0.1  # 100ms
                blip_samples = int(blip_duration * sr)
                blip_t = np.arange(blip_samples) / sr
                
                # Tom grave (100 Hz)
                blip = 0.5 * np.sin(2 * np.pi * 100 * blip_t)
                
                # Envelope exponencial
                blip = blip * np.exp(-blip_t * 10)
                
                # Adicionar ao áudio
                end_pos = min(pos_sample + blip_samples, n_samples)
                actual_blip_len = end_pos - pos_sample
                audio_base[pos_sample:end_pos] += blip[:actual_blip_len]
        
        # Normalizar
        audio_base = audio_base / (np.max(np.abs(audio_base)) + 1e-10) * 0.5
        
        return audio_base, sr
    
    def criar_wav_bytes(self, audio_data, sample_rate):
        """
        Converte array de áudio em bytes WAV para download
        
        Args:
            audio_data: Array numpy com dados de áudio
            sample_rate: Taxa de amostragem
            
        Returns:
            bytes: Dados WAV
        """
        # Converter para int16
        audio_int16 = np.int16(audio_data * 32767)
        
        # Criar buffer
        buffer = io.BytesIO()
        wavfile.write(buffer, sample_rate, audio_int16)
        buffer.seek(0)
        
        return buffer.getvalue()
    
    def descrever_sonificacao(self, tipo):
        """
        Retorna descrição de como a sonificação funciona
        
        Args:
            tipo: 'curva_luz', 'vibracoes', 'transito'
            
        Returns:
            str: Descrição
        """
        descricoes = {
            'curva_luz': """
**Como funciona a sonificação da curva de luz:**

- 🔆 **Brilho mais alto** → Tom mais agudo (frequência alta)
- 🔅 **Brilho mais baixo** → Tom mais grave (frequência baixa)
- ⏱️ **Tempo** → Progresso do áudio

Você está ouvindo a "voz" da estrela através de suas variações de brilho!
            """,
            
            'vibracoes': """
**Como funciona a sonificação das vibrações estelares:**

- 🎵 Cada pico no espectro de potência vira uma **nota musical**
- 📊 **Potência alta** → Volume mais alto
- 🎼 Frequências combinadas criam uma **"harmonia estelar"**
- 🔬 Diferentes tipos de estrelas produzem diferentes "acordes"

Isso é a asterosismologia transformada em música!
            """,
            
            'transito': """
**Como funciona a sonificação de trânsitos:**

- 🌊 Áudio base segue a curva de luz (variações de brilho)
- 🪐 **Cada trânsito** = Um "blip" grave (tom de 100 Hz)
- ⏱️ **Periodicidade** dos blips = Período orbital do planeta

Você pode "ouvir" o planeta passando na frente da estrela!
            """
        }
        
        return descricoes.get(tipo, "Descrição não disponível")

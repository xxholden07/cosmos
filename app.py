"""
Interface Web - Análise de Dados Cósmicos
Sistema profissional com dados REAIS do Kepler/TESS
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import lightkurve as lk
from plotly.subplots import make_subplots

from celestial_detector import CelestialBodyDetector
from stellar_seismology import StellarSeismologyAnalyzer
from pattern_detector import PatternDetector

# Configuração da página
st.set_page_config(
    page_title="Análise de Dados Cósmicos",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .stAlert {margin-top: 1rem;}
    .metric-card {
        background: #1e1e1e;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)

# Cache para dados - retorna arrays simples em vez de objetos complexos
@st.cache_data(ttl=3600, show_spinner=False)
def buscar_estrela(nome_estrela, missao, cadencia):
    """Busca dados de estrela no Kepler/TESS e retorna arrays numpy"""
    try:
        search_result = lk.search_lightcurve(nome_estrela, author=missao, cadence=cadencia)
        if len(search_result) == 0:
            return None, None, "Estrela não encontrada"
        
        lc_collection = search_result.download_all()
        lc = lc_collection.stitch()
        
        # Retornar arrays numpy (serializáveis) em vez do objeto LightCurve
        time = lc.time.value
        flux = lc.flux.value
        
        return time, flux, None
    except Exception as e:
        return None, None, str(e)

@st.cache_data(show_spinner=False)
def analisar_planetas(time, flux):
    """Analisa dados para detectar planetas"""
    detector = CelestialBodyDetector(sensitivity=5.0)
    planets = detector.detect_transiting_planets(time, flux, min_period=0.5, max_period=50.0)
    return planets

@st.cache_data(show_spinner=False)
def analisar_cometas(time, flux):
    """Analisa dados para detectar cometas"""
    detector = CelestialBodyDetector(sensitivity=3.0)
    comets = detector.detect_comets(time, flux)
    return comets

@st.cache_data(show_spinner=False)
def analisar_meteoros(time, flux):
    """Analisa dados para detectar meteoros e eventos rápidos"""
    detector = CelestialBodyDetector(sensitivity=4.0)
    meteors = detector.detect_meteors_and_fast_transients(time, flux)
    return meteors

@st.cache_data(show_spinner=False)
def analisar_transientes(time, flux):
    """Analisa eventos transientes (supernovas, flares)"""
    detector = CelestialBodyDetector(sensitivity=3.0)
    # Converter fluxo para magnitude (aproximado)
    mag = -2.5 * np.log10(flux / np.median(flux))
    transients = detector.detect_transient_events(time, mag)
    return transients

@st.cache_data(show_spinner=False)
def analisar_vibrações(time, flux, cadence):
    """Analisa vibrações estelares"""
    seismo = StellarSeismologyAnalyzer()
    analysis = seismo.analyze_stellar_vibrations(time, flux, cadence=cadence)
    return analysis

# Título
st.title("Análise de Dados Astronômicos Reais")
st.markdown("Sistema de análise usando dados do Kepler e TESS")

# Sidebar
with st.sidebar:
    st.header("Configurações")
    
    # Seleção de missão
    missao = st.selectbox(
        "Missão Espacial",
        ["Kepler", "TESS"],
        help="Escolha o telescópio espacial"
    )
    
    # Input da estrela
    st.subheader("Buscar Estrela")
    
    # Exemplos rápidos
    exemplo = st.selectbox(
        "Exemplos de estrelas",
        [
            "Pesquisa personalizada",
            "Kepler-10 (2 planetas confirmados)",
            "Kepler-90 (8 planetas!)",
            "KIC 11904151 (oscilações)",
            "HD 209458 (Hot Jupiter)"
        ]
    )
    
    if exemplo != "Pesquisa personalizada":
        nome_base = exemplo.split(" ")[0]
        nome_estrela = st.text_input("Nome da Estrela", value=nome_base)
    else:
        nome_estrela = st.text_input("Nome da Estrela", value="Kepler-10")
    
    cadencia = st.selectbox(
        "Cadência",
        ["long", "short"],
        help="Long: ~30min, Short: ~1min"
    )
    
    # Análises
    st.subheader("Tipos de Detecção")
    detect_planets = st.checkbox("Planetas (trânsitos)", value=True)
    detect_comets = st.checkbox("Cometas (variação de brilho)", value=False)
    detect_meteors = st.checkbox("Meteoros (eventos rápidos)", value=False)
    detect_transients = st.checkbox("Transientes (supernovas/flares)", value=False)
    detect_seismo = st.checkbox("Asterosismologia (vibrações)", value=False)
    
    # Botão de busca
    buscar = st.button("Buscar e Analisar", type="primary", use_container_width=True)

# Área principal
if buscar:
    with st.spinner(f"Buscando dados de {nome_estrela}..."):
        time, flux, erro = buscar_estrela(nome_estrela, missao, cadencia)
    
    if erro:
        st.error(f"Erro ao buscar dados: {erro}")
        st.info("Dicas: Verifique o nome da estrela ou tente outra missão")
        st.stop()
    
    # Dados já são arrays numpy, prontos para usar
    # Remover outliers básicos
    flux_median = np.median(flux)
    flux_std = np.std(flux)
    mask = np.abs(flux - flux_median) < 5 * flux_std
    time = time[mask]
    flux = flux[mask]
    
    # Informações dos dados
    st.success(f"Dados baixados com sucesso!")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Pontos de Dados", f"{len(time):,}")
    with col2:
        st.metric("Período", f"{time[-1] - time[0]:.1f} dias")
    with col3:
        st.metric("Cadência", cadencia)
    with col4:
        st.metric("Missão", missao)
    
    st.divider()
    
    # Curva de luz original
    st.subheader("Curva de Luz Original")
    
    fig_lc = go.Figure()
    fig_lc.add_trace(go.Scatter(
        x=time,
        y=flux,
        mode='lines',
        name='Fluxo',
        line=dict(color='cyan', width=0.5),
        opacity=0.7
    ))
    
    fig_lc.update_layout(
        template='plotly_dark',
        xaxis_title="Tempo (dias)",
        yaxis_title="Fluxo",
        height=400,
        hovermode='x unified',
        showlegend=False
    )
    
    st.plotly_chart(fig_lc, use_container_width=True)
    
    # Análise de Planetas
    if detect_planets:
        st.divider()
        st.subheader("Detecção de Planetas")
        
        with st.spinner("Analisando trânsitos planetários..."):
            planets = analisar_planetas(time, flux)
        
        if len(planets) == 0:
            st.warning("Nenhum planeta detectado com os parâmetros atuais")
        else:
            st.success(f"**{len(planets)} planetas candidatos detectados!**")
            
            # Tabela de planetas
            df_planets = pd.DataFrame(planets)
            df_planets['period_days'] = df_planets['period_days'].round(3)
            df_planets['transit_depth'] = (df_planets['transit_depth'] * 100).round(4)
            df_planets['transit_duration_hours'] = df_planets['transit_duration_hours'].round(2)
            df_planets['confidence'] = df_planets['confidence'].round(1)
            
            # Estimar raio do planeta (assumindo estrela tipo solar)
            df_planets['radius_earth'] = (np.sqrt(df_planets['transit_depth'] / 100) * 109).round(2)
            
            # Renomear colunas
            df_display = df_planets[[
                'period_days', 'transit_depth', 'transit_duration_hours', 
                'radius_earth', 'confidence'
            ]].copy()
            df_display.columns = [
                'Período (dias)', 'Profundidade (%)', 'Duração (h)', 
                'Raio (R⊕)', 'Confiança (%)'
            ]
            
            st.dataframe(df_display, use_container_width=True)
            
            # Gráfico de curva dobrada (phase-folded)
            if len(planets) > 0:
                st.subheader("Curva de Luz Dobrada - Melhor Candidato")
                
                best_planet = planets[0]
                period = best_planet['period_days']
                
                # Dobrar curva
                phase = (time % period) / period
                sort_idx = np.argsort(phase)
                phase_sorted = phase[sort_idx]
                flux_sorted = flux[sort_idx]
                
                fig_phase = go.Figure()
                fig_phase.add_trace(go.Scatter(
                    x=phase_sorted,
                    y=flux_sorted,
                    mode='markers',
                    marker=dict(size=2, color='cyan', opacity=0.6),
                    name='Dados'
                ))
                
                fig_phase.update_layout(
                    template='plotly_dark',
                    xaxis_title="Fase Orbital",
                    yaxis_title="Fluxo Normalizado",
                    height=400,
                    showlegend=False
                )
                
                st.plotly_chart(fig_phase, use_container_width=True)
                
                # Detalhes do planeta
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Período Orbital",
                        f"{period:.3f} dias",
                        help="Tempo para completar uma órbita"
                    )
                with col2:
                    st.metric(
                        "Profundidade do Trânsito",
                        f"{best_planet['transit_depth']*100:.4f}%",
                        help="Redução de brilho durante o trânsito"
                    )
                with col3:
                    radius_earth = np.sqrt(best_planet['transit_depth']) * 109
                    st.metric(
                        "Raio Estimado",
                        f"{radius_earth:.2f} R⊕",
                        help="Raio em relação à Terra"
                    )
    
    # Detecção de Cometas
    if detect_comets:
        st.divider()
        st.subheader("Detecção de Cometas")
        
        with st.spinner("Procurando por cometas..."):
            comets = analisar_cometas(time, flux)
        
        if len(comets) == 0:
            st.info("Nenhum cometa detectado. Cometas são raros e requerem padrões específicos de variação de brilho.")
        else:
            st.success(f"**{len(comets)} possíveis cometas/eventos cometários detectados!**")
            
            # Mostrar visualização do primeiro cometa DIRETO (sem expander)
            if len(comets) > 0:
                comet = comets[0]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Tempo de Detecção", f"{comet['detection_time']:.2f} dias")
                with col2:
                    st.metric("Aumento de Brilho", f"{comet['brightness_increase']*100:.1f}%")
                with col3:
                    st.metric("Confiança", f"{comet['confidence']*100:.0f}%")
                
                if 'velocity_deg_day' in comet:
                    st.info(f"Movimento detectado: {comet['velocity_deg_day']:.6f} °/dia")
                
                # Visualização do evento
                st.subheader("Visualização do Cometa")
                detection_time = comet['detection_time']
                window = 20  # dias antes e depois
                mask = (time >= detection_time - window) & (time <= detection_time + window)
                
                if np.any(mask):
                    fig_comet = go.Figure()
                    
                    # Curva de luz completa na janela
                    fig_comet.add_trace(go.Scatter(
                        x=time[mask],
                        y=flux[mask],
                        mode='lines',
                        name='Fluxo',
                        line=dict(color='cyan', width=1.5)
                    ))
                    
                    # Marcar momento da detecção
                    fig_comet.add_vline(
                        x=detection_time,
                        line_dash="dash",
                        line_color="red",
                        annotation_text="Detecção",
                        annotation_position="top"
                    )
                    
                    fig_comet.update_layout(
                        template='plotly_dark',
                        xaxis_title="Tempo (dias)",
                        yaxis_title="Fluxo",
                        height=400,
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig_comet, use_container_width=True)
            
            # Outros cometas em expanders
            if len(comets) > 1:
                st.subheader("Outros Cometas Detectados")
                for i, comet in enumerate(comets[1:], 2):
                    with st.expander(f"Cometa Candidato #{i} - {comet['activity_type']}"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Tempo de Detecção", f"{comet['detection_time']:.2f} dias")
                        with col2:
                            st.metric("Aumento de Brilho", f"{comet['brightness_increase']*100:.1f}%")
                        with col3:
                            st.metric("Confiança", f"{comet['confidence']*100:.0f}%")
                        
                        if 'velocity_deg_day' in comet:
                            st.info(f"Movimento detectado: {comet['velocity_deg_day']:.6f} °/dia")
                        
                    # Visualização do evento
                    detection_time = comet['detection_time']
                    window = 20  # dias antes e depois
                    mask = (time >= detection_time - window) & (time <= detection_time + window)
                    
                    if np.any(mask):
                        fig_comet = go.Figure()
                        
                        # Curva de luz completa na janela
                        fig_comet.add_trace(go.Scatter(
                            x=time[mask],
                            y=flux[mask],
                            mode='lines',
                            name='Fluxo',
                            line=dict(color='cyan', width=1)
                        ))
                        
                        # Marcar momento da detecção
                        fig_comet.add_vline(
                            x=detection_time,
                            line_dash="dash",
                            line_color="red",
                            annotation_text="Detecção"
                        )
                        
                        fig_comet.update_layout(
                            template='plotly_dark',
                            xaxis_title="Tempo (dias)",
                            yaxis_title="Fluxo",
                            height=300,
                            showlegend=False
                        )
                        
                        st.plotly_chart(fig_comet, use_container_width=True)
    
    # Detecção de Meteoros
    if detect_meteors:
        st.divider()
        st.subheader("Detecção de Meteoros e Eventos Rápidos")
        
        with st.spinner("Procurando eventos rápidos..."):
            meteors = analisar_meteoros(time, flux)
        
        if len(meteors) == 0:
            st.info("Nenhum meteoro ou evento ultra-rápido detectado.")
        else:
            st.success(f"**{len(meteors)} eventos rápidos detectados!**")
            
            # Visualização de eventos PRIMEIRO (antes da tabela)
            st.subheader("Visualização dos Eventos")
            
            fig_meteors = go.Figure()
            
            # Curva de luz completa
            fig_meteors.add_trace(go.Scatter(
                x=time,
                y=flux,
                mode='lines',
                name='Fluxo',
                line=dict(color='lightblue', width=0.5),
                opacity=0.5
            ))
            
            # Marcar cada evento detectado
            for meteor in meteors:
                detection_time = meteor['detection_time']
                fig_meteors.add_vline(
                    x=detection_time,
                    line_dash="solid",
                    line_color="red",
                    line_width=2,
                    opacity=0.7
                )
            
            fig_meteors.update_layout(
                template='plotly_dark',
                xaxis_title="Tempo (dias)",
                yaxis_title="Fluxo",
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig_meteors, use_container_width=True)
            
            # Zoom no primeiro evento
            st.subheader("Zoom - Primeiro Evento")
            first_event = meteors[0]
            event_time = first_event['detection_time']
            window = 0.5  # meio dia antes e depois
            
            mask = (time >= event_time - window) & (time <= event_time + window)
            
            if np.any(mask):
                fig_zoom = go.Figure()
                
                fig_zoom.add_trace(go.Scatter(
                    x=time[mask],
                    y=flux[mask],
                    mode='lines+markers',
                    name='Fluxo',
                    line=dict(color='cyan', width=2),
                    marker=dict(size=4)
                ))
                
                fig_zoom.add_vline(
                    x=event_time,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Evento ({first_event['duration_hours']:.4f}h)"
                )
                
                fig_zoom.update_layout(
                    template='plotly_dark',
                    xaxis_title="Tempo (dias)",
                    yaxis_title="Fluxo",
                    height=350,
                    showlegend=False
                )
                
                st.plotly_chart(fig_zoom, use_container_width=True)
            
            # Tabela de dados
            st.subheader("Dados dos Eventos")
            df_meteors = pd.DataFrame(meteors)
            
            # Criar tabela formatada manualmente
            table_data = []
            for meteor in meteors:
                try:
                    amplitude = float(meteor.get('amplitude', 0))
                    detection_time = float(meteor.get('detection_time', 0))
                    duration_hours = float(meteor.get('duration_hours', 0))
                    confidence = float(meteor.get('confidence', 0))
                    
                    table_data.append({
                        'Tempo (dias)': round(detection_time, 3),
                        'Duração (h)': round(duration_hours, 4),
                        'Amplitude': round(amplitude, 3),
                        'Tipo': meteor.get('event_type', 'desconhecido'),
                        'Confiança': f"{round(confidence * 100, 0):.0f}%"
                    })
                except (ValueError, TypeError, KeyError) as e:
                    # Pular eventos com dados inválidos
                    continue
            
            if table_data:
                df_display = pd.DataFrame(table_data)
                st.dataframe(df_display, use_container_width=True)
            else:
                st.warning("Não foi possível formatar os dados dos eventos.")
    
    # Detecção de Transientes
    if detect_transients:
        st.divider()
        st.subheader("Eventos Transientes (Supernovas, Flares)")
        
        with st.spinner("Procurando eventos transientes..."):
            transients = analisar_transientes(time, flux)
        
        if len(transients) == 0:
            st.info("Nenhum evento transiente significativo detectado.")
        else:
            st.success(f"**{len(transients)} eventos transientes detectados!**")
            
            for i, event in enumerate(transients, 1):
                with st.expander(f"Evento #{i} - {event['type']}"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Tipo", event['type'])
                    with col2:
                        st.metric("Duração", f"{event['duration_days']:.2f} dias")
                    with col3:
                        st.metric("Amplitude", f"{event['amplitude']:.2f} mag")
                    with col4:
                        st.metric("Pico", f"{event['peak_time']:.2f} dias")
                    
                    # Visualização do evento
                    start_t = event['start_time']
                    end_t = event['end_time']
                    window = event['duration_days'] * 2  # 2x a duração do evento
                    
                    mask = (time >= start_t - window) & (time <= end_t + window)
                    
                    if np.any(mask):
                        fig_trans = go.Figure()
                        
                        # Curva de luz na janela
                        fig_trans.add_trace(go.Scatter(
                            x=time[mask],
                            y=flux[mask],
                            mode='lines',
                            name='Fluxo',
                            line=dict(color='cyan', width=1.5)
                        ))
                        
                        # Marcar início, pico e fim
                        fig_trans.add_vline(x=start_t, line_dash="dot", line_color="green", annotation_text="Início")
                        fig_trans.add_vline(x=event['peak_time'], line_dash="solid", line_color="red", annotation_text="Pico")
                        fig_trans.add_vline(x=end_t, line_dash="dot", line_color="orange", annotation_text="Fim")
                        
                        fig_trans.update_layout(
                            template='plotly_dark',
                            xaxis_title="Tempo (dias)",
                            yaxis_title="Fluxo",
                            height=350,
                            showlegend=False
                        )
                        
                        st.plotly_chart(fig_trans, use_container_width=True)
    
    # Asterosismologia
    if detect_seismo:
        st.divider()
        st.subheader("Asterosismologia - Vibrações Estelares")
        
        cadence_min = 30.0 if cadencia == "long" else 1.0
        
        with st.spinner("Analisando oscilações estelares..."):
            seismo_analysis = analisar_vibrações(time, flux, cadence_min)
        
        # Parâmetros estelares
        params = seismo_analysis['stellar_parameters']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Massa", f"{params['mass_solar']:.2f} M☉")
        with col2:
            st.metric("Raio", f"{params['radius_solar']:.2f} R☉")
        with col3:
            st.metric("log g", f"{params['log_g']:.2f}")
        with col4:
            st.metric("Idade", f"{params['age_gyr']:.1f} Gyr")
        
        st.info(f"**Estágio Evolutivo:** {params['evolutionary_stage']}")
        
        # Espectro de potência
        st.subheader("Espectro de Potência")
        
        frequencies = seismo_analysis['power_spectrum']['frequencies']
        power = seismo_analysis['power_spectrum']['power']
        
        fig_power = go.Figure()
        fig_power.add_trace(go.Scatter(
            x=frequencies,
            y=power,
            mode='lines',
            line=dict(color='cyan', width=1),
            name='Potência'
        ))
        
        # Marcar nu_max
        nu_max = seismo_analysis['nu_max_uHz']
        fig_power.add_vline(
            x=nu_max,
            line_dash="dash",
            line_color="red",
            annotation_text=f"ν_max = {nu_max:.1f} μHz"
        )
        
        fig_power.update_layout(
            template='plotly_dark',
            xaxis_title="Frequência (μHz)",
            yaxis_title="Potência",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig_power, use_container_width=True)
        
        # Modos de oscilação
        modes = seismo_analysis['oscillation_modes']
        if len(modes) > 0:
            st.subheader(f"Modos de Oscilação Detectados: {len(modes)}")
            
            df_modes = pd.DataFrame(modes[:10])  # Top 10
            df_modes['frequency_uHz'] = df_modes['frequency_uHz'].round(2)
            df_modes['amplitude'] = df_modes['amplitude'].round(6)
            
            df_display_modes = df_modes[['frequency_uHz', 'type', 'mode_order']].copy()
            df_display_modes.columns = ['Frequência (μHz)', 'Tipo', 'Ordem']
            
            st.dataframe(df_display_modes, use_container_width=True)

else:
    # Página inicial
    st.info("Configure os parâmetros na barra lateral e clique em 'Buscar e Analisar'")
    
    st.markdown("""
    ### Como usar
    
    1. **Escolha uma missão**: Kepler ou TESS
    2. **Selecione uma estrela**: Use os exemplos ou digite o nome
    3. **Configure as análises**: Escolha quais análises executar
    4. **Clique em 'Buscar e Analisar'**
    
    ### Exemplos de Estrelas Interessantes
    
    - **Kepler-10**: Primeiro planeta rochoso confirmado pelo Kepler
    - **Kepler-90**: Sistema com 8 planetas (como o Sistema Solar!)
    - **KIC 11904151**: Excelente para asterosismologia
    - **HD 209458**: Primeiro exoplaneta detectado em trânsito
    
    ### Tipos de Análise
    
    - **Detecção de Planetas**: Identifica trânsitos planetários e calcula parâmetros orbitais
    - **Asterosismologia**: Analisa vibrações estelares para determinar massa, raio e idade
    """)

# Footer
st.divider()
st.caption("Dados: NASA Kepler/TESS | Processamento: lightkurve | Interface: Streamlit")

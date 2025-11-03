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
from database import CelestialDatabase

# Inicializar banco de dados
db = CelestialDatabase()

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
    """Busca dados de estrela no Kepler/TESS e retorna arrays numpy + coordenadas"""
    try:
        search_result = lk.search_lightcurve(nome_estrela, author=missao, cadence=cadencia)
        if len(search_result) == 0:
            return None, None, None, None, "Estrela não encontrada"
        
        lc_collection = search_result.download_all()
        lc = lc_collection.stitch()
        
        # Retornar arrays numpy (serializáveis) e coordenadas
        time = lc.time.value
        flux = lc.flux.value
        
        # Obter coordenadas (RA, Dec)
        ra = lc.ra if hasattr(lc, 'ra') else None
        dec = lc.dec if hasattr(lc, 'dec') else None
        
        return time, flux, ra, dec, None
    except Exception as e:
        return None, None, None, None, str(e)

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

def criar_mapa_ceu(ra, dec, nome_estrela):
    """Cria mapa do céu mostrando localização do objeto"""
    if ra is None or dec is None:
        return None
    
    # Criar grade de coordenadas ao redor do objeto
    ra_grid = np.linspace(ra - 5, ra + 5, 100)
    dec_grid = np.linspace(dec - 5, dec + 5, 100)
    
    fig = go.Figure()
    
    # Adicionar ponto do objeto
    fig.add_trace(go.Scatter(
        x=[ra],
        y=[dec],
        mode='markers+text',
        marker=dict(size=20, color='red', symbol='star'),
        text=[nome_estrela],
        textposition='top center',
        textfont=dict(size=14, color='red'),
        name='Objeto Alvo'
    ))
    
    fig.update_layout(
        template='plotly_dark',
        xaxis_title="Ascensão Reta (graus)",
        yaxis_title="Declinação (graus)",
        height=400,
        showlegend=True,
        xaxis=dict(range=[ra - 5, ra + 5]),
        yaxis=dict(range=[dec - 5, dec + 5])
    )
    
    return fig

def verificar_novidade(planetas, cometas, meteoros, nome_estrela):
    """Analisa se as detecções podem ser descobertas novas"""
    descobertas_potenciais = []
    
    # Verificar planetas
    if planetas and len(planetas) > 0:
        for i, p in enumerate(planetas):
            # Critérios para possível descoberta:
            # 1. Alta confiança (>70%)
            # 2. Período não comum (evitar artefatos)
            # 3. Profundidade significativa
            if p['confidence'] > 70 and 0.5 < p['period_days'] < 50:
                descobertas_potenciais.append({
                    'tipo': 'Planeta',
                    'indice': i + 1,
                    'confianca': p['confidence'],
                    'parametros': f"Período: {p['period_days']:.2f}d, Raio: {np.sqrt(p['transit_depth'])*109:.1f}R⊕",
                    'status': 'NOVO' if p['confidence'] > 85 else 'CANDIDATO'
                })
    
    # Verificar cometas
    if cometas and len(cometas) > 0:
        for i, c in enumerate(cometas):
            if c['confidence'] > 0.8:
                descobertas_potenciais.append({
                    'tipo': 'Cometa/Evento Variável',
                    'indice': i + 1,
                    'confianca': c['confidence'] * 100,
                    'parametros': f"Aumento: {c['brightness_increase']*100:.1f}%",
                    'status': 'NOVO'
                })
    
    # Verificar meteoros/transientes
    if meteoros and len(meteoros) > 0:
        eventos_rapidos = [m for m in meteoros if m.get('confidence', 0) > 0.7]
        if len(eventos_rapidos) > 0:
            descobertas_potenciais.append({
                'tipo': 'Eventos Transientes Rápidos',
                'indice': len(eventos_rapidos),
                'confianca': np.mean([m.get('confidence', 0) for m in eventos_rapidos]) * 100,
                'parametros': f"{len(eventos_rapidos)} eventos detectados",
                'status': 'ANALISAR'
            })
    
    return descobertas_potenciais

def salvar_monitoramento(nome_estrela, resultados, ra, dec):
    """Salva resultados no banco de dados"""
    try:
        # Salvar objeto
        objeto_id = db.salvar_objeto(nome_estrela, ra if ra else 0.0, dec if dec else 0.0, resultados.get('missao', 'Unknown'))
        
        # Salvar observação
        observacao_id = db.salvar_observacao(
            objeto_id,
            resultados.get('cadencia', 'unknown'),
            resultados.get('pontos_dados', 0),
            resultados.get('periodo_dias', 0)
        )
        
        # Salvar detecções
        if 'planetas' in resultados and resultados['planetas']:
            db.salvar_planetas(observacao_id, resultados['planetas'])
        
        if 'cometas' in resultados and resultados['cometas']:
            db.salvar_cometas(observacao_id, resultados['cometas'])
        
        if 'meteoros' in resultados and resultados['meteoros']:
            db.salvar_meteoros(observacao_id, resultados['meteoros'])
        
        if 'transientes' in resultados and resultados['transientes']:
            db.salvar_transientes(observacao_id, resultados['transientes'])
        
        if 'descobertas' in resultados and resultados['descobertas']:
            db.salvar_descobertas(observacao_id, resultados['descobertas'])
        
        return True
    except Exception as e:
        print(f"Erro ao salvar no banco: {e}")
        return False

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
    
    st.divider()
    
    # Opção de monitoramento
    st.subheader("Monitoramento")
    enable_monitoring = st.checkbox("Ativar monitoramento", value=True, 
                                    help="Salva resultados no banco de dados para comparação futura")
    
    # Botão para ver histórico
    if st.button("Ver Histórico/Estatísticas", use_container_width=True):
        st.session_state['mostrar_historico'] = True
    
    # Botão de busca
    buscar = st.button("Buscar e Analisar", type="primary", use_container_width=True)

# Área principal
if buscar:
    with st.spinner(f"Buscando dados de {nome_estrela}..."):
        time, flux, ra, dec, erro = buscar_estrela(nome_estrela, missao, cadencia)
    
    if erro:
        st.error(f"Erro ao buscar dados: {erro}")
        st.info("Dicas: Verifique o nome da estrela ou tente outra missão")
        st.stop()
    
    # Converter para arrays numpy puros (remover qualquer máscara do Astropy)
    time = np.asarray(time, dtype=np.float64)
    flux = np.asarray(flux, dtype=np.float64)
    
    # Remover NaN e infinitos
    valid_mask = np.isfinite(time) & np.isfinite(flux)
    time = time[valid_mask]
    flux = flux[valid_mask]
    
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
    
    # Mapa do céu
    if ra is not None and dec is not None:
        st.divider()
        st.subheader("Localização no Céu")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            fig_mapa = criar_mapa_ceu(ra, dec, nome_estrela)
            if fig_mapa:
                st.plotly_chart(fig_mapa, use_container_width=True)
        
        with col2:
            st.metric("Ascensão Reta (RA)", f"{ra:.4f}°")
            st.metric("Declinação (Dec)", f"{dec:.4f}°")
            
            # Converter para coordenadas sexagesimais
            ra_h = int(ra / 15)
            ra_m = int((ra / 15 - ra_h) * 60)
            ra_s = ((ra / 15 - ra_h) * 60 - ra_m) * 60
            
            dec_sign = '+' if dec >= 0 else '-'
            dec_d = int(abs(dec))
            dec_m = int((abs(dec) - dec_d) * 60)
            dec_s = ((abs(dec) - dec_d) * 60 - dec_m) * 60
            
            st.info(f"**Coordenadas (J2000)**\n\n"
                   f"RA: {ra_h:02d}h {ra_m:02d}m {ra_s:05.2f}s\n\n"
                   f"Dec: {dec_sign}{dec_d:02d}° {dec_m:02d}' {dec_s:05.2f}\"")
    
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
    
    # ANÁLISE DE DESCOBERTAS POTENCIAIS
    st.divider()
    st.header("Análise de Descobertas")
    
    # Coletar todas as detecções
    planetas_detectados = analisar_planetas(time, flux) if detect_planets else []
    cometas_detectados = analisar_cometas(time, flux) if detect_comets else []
    meteoros_detectados = analisar_meteoros(time, flux) if detect_meteors else []
    
    descobertas = verificar_novidade(planetas_detectados, cometas_detectados, meteoros_detectados, nome_estrela)
    
    if len(descobertas) > 0:
        st.warning(f"**ATENÇÃO: {len(descobertas)} possíveis descobertas ou objetos de interesse detectados!**")
        
        for desc in descobertas:
            status_color = "🔴" if desc['status'] == 'NOVO' else "🟡" if desc['status'] == 'CANDIDATO' else "🔵"
            
            with st.expander(f"{status_color} {desc['tipo']} #{desc['indice']} - Status: {desc['status']}", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Confiança", f"{desc['confianca']:.1f}%")
                with col2:
                    st.metric("Status", desc['status'])
                
                st.info(f"**Parâmetros:** {desc['parametros']}")
                
                if desc['status'] == 'NOVO':
                    st.success("**Potencial descoberta!** Este objeto apresenta características únicas e alta confiança.")
                    
                    st.markdown("### Próximos Passos:")
                    
                    tab1, tab2, tab3 = st.tabs(["Verificação", "Monitoramento", "Publicação"])
                    
                    with tab1:
                        st.markdown("""
                        **Verificar se já é conhecido:**
                        
                        1. 🔍 Buscar coordenadas no SIMBAD
                        2. 🔍 Verificar NASA Exoplanet Archive
                        3. 🔍 Consultar catálogos recentes
                        
                        **Se NÃO encontrar nada = POSSÍVEL DESCOBERTA!**
                        """)
                        
                        if ra is not None and dec is not None:
                            st.code(f"""
Links diretos para verificação:

SIMBAD: http://simbad.u-strasbg.fr/simbad/sim-coo?Coord={ra}+{dec}&Radius=2

NASA Exoplanet: https://exoplanetarchive.ipac.caltech.edu/

VizieR: https://vizier.u-strasbg.fr/viz-bin/VizieR?-c={ra}+{dec}&-c.rs=2
                            """)
                    
                    with tab2:
                        st.markdown("""
                        **Continue observando:**
                        
                        - ✓ Faça pelo menos 3 observações em datas diferentes
                        - ✓ Use cadência curta (short) para maior precisão
                        - ✓ Tente outras missões (Kepler + TESS)
                        - ✓ Documente todas as observações
                        
                        O sistema já está salvando automaticamente no banco de dados.
                        """)
                    
                    with tab3:
                        st.markdown("""
                        **Como reportar sua descoberta:**
                        
                        **Para Planetas:**
                        - 📧 NASA Exoplanet Archive
                        - 📧 Exoplanet.eu
                        - 📄 Publicar paper em journals: AJ, ApJ, MNRAS
                        
                        **Para Cometas/Asteroides:**
                        - 📧 Minor Planet Center (MPC)
                        - 📧 Central Bureau for Astronomical Telegrams
                        
                        **Para Transientes (Supernovas):**
                        - 📧 Transient Name Server (TNS)
                        - 📧 AAVSO
                        
                        **Dica:** Aguarde confirmação de pelo menos 3 observações independentes!
                        """)
                
                elif desc['status'] == 'CANDIDATO':
                    st.info("**Candidato interessante.** Necessita mais observações para confirmação.")
                    st.markdown("""
                    **Ações recomendadas:**
                    - Continue monitorando este objeto
                    - Faça mais 2-3 observações
                    - Use diferentes configurações de cadência
                    """)
    else:
        st.info("Nenhuma descoberta potencial detectada com os critérios atuais. Objetos detectados parecem corresponder a padrões conhecidos.")
    
    # Sistema de Monitoramento
    if enable_monitoring:
        st.divider()
        st.subheader("Sistema de Monitoramento")
        
        resultados_monitoramento = {
            'missao': missao,
            'cadencia': cadencia,
            'pontos_dados': len(time),
            'periodo_dias': float(time[-1] - time[0]),
            'planetas': planetas_detectados,
            'cometas': cometas_detectados,
            'meteoros': meteoros_detectados,
            'transientes': analisar_transientes(time, flux) if detect_transients else [],
            'descobertas': descobertas
        }
        
        sucesso = salvar_monitoramento(nome_estrela, resultados_monitoramento, ra, dec)
        
        if sucesso:
            st.success("✓ Dados salvos no banco de dados!")
            
            # Mostrar estatísticas
            historico = db.obter_historico_objeto(nome_estrela)
            if historico:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total de Observações", historico['objeto']['total_observacoes'])
                with col2:
                    st.metric("Planetas Detectados", len(historico['planetas']))
                with col3:
                    st.metric("Descobertas Potenciais", len(historico['descobertas']))
        else:
            st.error("Erro ao salvar no banco de dados")

# Seção de Histórico e Estatísticas
if 'mostrar_historico' in st.session_state and st.session_state['mostrar_historico']:
    st.divider()
    st.header("Histórico e Estatísticas do Banco de Dados")
    
    # Estatísticas gerais
    stats = db.estatisticas_gerais()
    
    st.subheader("Estatísticas Gerais")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Objetos Monitorados", stats['total_objetos'])
    with col2:
        st.metric("Total de Observações", stats['total_observacoes'])
    with col3:
        st.metric("Planetas Detectados", stats['total_planetas'])
    with col4:
        st.metric("Planetas Novos", stats['planetas_novos'], delta=f"+{stats['planetas_novos']}")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Cometas", stats['total_cometas'])
    with col2:
        st.metric("Meteoros", stats['total_meteoros'])
    with col3:
        st.metric("Descobertas Novas", stats['descobertas_novas'], delta=f"+{stats['descobertas_novas']}")
    with col4:
        st.metric("Candidatos", stats['candidatos'], delta=f"+{stats['candidatos']}")
    
    # Lista de descobertas
    st.subheader("Últimas Descobertas Potenciais")
    descobertas_db = db.listar_descobertas_novas(limit=20)
    
    if descobertas_db:
        for desc in descobertas_db:
            status_color = "🔴" if desc['status'] == 'NOVO' else "🟡"
            with st.expander(f"{status_color} {desc['nome']} - {desc['tipo']} (Confiança: {desc['confianca']:.1f}%)"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Status:** {desc['status']}")
                    st.write(f"**Tipo:** {desc['tipo']}")
                with col2:
                    st.write(f"**RA:** {desc['ra']:.4f}°")
                    st.write(f"**Dec:** {desc['dec']:.4f}°")
                with col3:
                    st.write(f"**Data:** {desc['timestamp']}")
                
                st.info(f"**Parâmetros:** {desc['parametros']}")
                
                # GUIA DE AÇÕES
                st.divider()
                st.subheader("O que fazer agora?")
                
                if desc['status'] == 'NOVO':
                    st.warning("**POSSÍVEL DESCOBERTA!** Siga estes passos:")
                    
                    st.markdown("""
                    **1. Verificar em Catálogos Profissionais:**
                    - 🔗 [SIMBAD](http://simbad.u-strasbg.fr/simbad/sim-fcoo) - Busque por coordenadas
                    - 🔗 [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/) - Verificar planetas conhecidos
                    - 🔗 [VizieR](https://vizier.u-strasbg.fr/viz-bin/VizieR) - Catálogos astronômicos
                    
                    **2. Coletar Mais Dados:**
                    - Faça novas observações em datas diferentes
                    - Use cadência "short" para maior precisão
                    - Procure em outras missões (TESS se usou Kepler, ou vice-versa)
                    
                    **3. Análise Detalhada:**
                    - Calcule parâmetros físicos (massa, raio, temperatura)
                    - Verifique periodicidade consistente
                    - Descarte falsos positivos (artefatos instrumentais)
                    
                    **4. Reportar Descoberta:**
                    - 📧 [Telegram do Minor Planet Center](https://www.minorplanetcenter.net/) (asteroides/cometas)
                    - 📧 [Transient Name Server](https://www.wis-tns.org/) (supernovas/transientes)
                    - 📧 [AAVSO](https://www.aavso.org/) (estrelas variáveis)
                    - 📧 Publicar em [arXiv](https://arxiv.org/) ou journals especializados
                    """)
                    
                    # Coordenadas para copiar
                    ra_h = int(desc['ra'] / 15)
                    ra_m = int((desc['ra'] / 15 - ra_h) * 60)
                    ra_s = ((desc['ra'] / 15 - ra_h) * 60 - ra_m) * 60
                    
                    dec_sign = '+' if desc['dec'] >= 0 else '-'
                    dec_d = int(abs(desc['dec']))
                    dec_m = int((abs(desc['dec']) - dec_d) * 60)
                    dec_s = ((abs(desc['dec']) - dec_d) * 60 - dec_m) * 60
                    
                    st.code(f"""
Coordenadas para busca em catálogos:
RA (decimal): {desc['ra']:.4f}°
Dec (decimal): {desc['dec']:.4f}°

RA (sexagesimal): {ra_h:02d}h {ra_m:02d}m {ra_s:05.2f}s
Dec (sexagesimal): {dec_sign}{dec_d:02d}° {dec_m:02d}' {dec_s:05.2f}"

Busca SIMBAD: 
http://simbad.u-strasbg.fr/simbad/sim-coo?Coord={desc['ra']}+{desc['dec']}&Radius=2

Busca NASA Exoplanet:
https://exoplanetarchive.ipac.caltech.edu/cgi-bin/nstedAPI/nph-nstedAPI?table=exoplanets&select=*&where=ra>{desc['ra']-1}+and+ra<{desc['ra']+1}
                    """, language="text")
                
                elif desc['status'] == 'CANDIDATO':
                    st.info("**Candidato interessante.** Recomendações:")
                    st.markdown("""
                    1. **Continue monitorando** - Faça mais 2-3 observações
                    2. **Aumente a confiança** - Use dados de cadência curta
                    3. **Verifique consistência** - O padrão se repete?
                    4. **Aguarde confirmação** antes de reportar
                    """)
                
                # Botão para criar relatório
                if st.button(f"Gerar Relatório PDF", key=f"relatorio_{desc['id']}"):
                    st.info("Funcionalidade de relatório PDF será implementada em breve!")
    else:
        st.info("Nenhuma descoberta potencial registrada ainda")
    
    if st.button("Fechar Histórico"):
        st.session_state['mostrar_historico'] = False
        st.rerun()

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

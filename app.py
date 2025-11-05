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
from simbad_checker import SimbadChecker
from cds_professional import CDSProfessionalChecker
from sonificador import SonificadorEstelar
from alvos_promissores import GeradorAlvosPromissores

# Inicializar banco de dados e verificadores
db = CelestialDatabase()
simbad = SimbadChecker(radius_arcmin=2.0)
cds_pro = CDSProfessionalChecker(radius_arcsec=120)
sonificador = SonificadorEstelar()
gerador_alvos = GeradorAlvosPromissores()

# Configuração da página
st.set_page_config(
    page_title="Análise de Dados Cósmicos",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado - TEMA ESCURO
st.markdown("""
<style>
    /* Tema escuro global */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* Sidebar escura */
    [data-testid="stSidebar"] {
        background-color: #161b22;
    }
    
    /* Métricas */
    [data-testid="stMetricValue"] {
        color: #58a6ff;
        font-size: 2rem;
    }
    
    /* Alertas e info boxes */
    .stAlert {
        margin-top: 1rem;
        background-color: #161b22;
        border-left: 4px solid #58a6ff;
    }
    
    /* Cards de métricas */
    .metric-card {
        background: #1e1e1e;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #333;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #161b22;
        border: 1px solid #30363d;
    }
    
    /* Tabelas */
    .dataframe {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    /* Botões */
    .stButton>button {
        background-color: #238636;
        color: white;
        border: none;
        border-radius: 6px;
    }
    
    .stButton>button:hover {
        background-color: #2ea043;
    }
    
    /* Links */
    a {
        color: #58a6ff;
    }
    
    a:hover {
        color: #79c0ff;
    }
    
    /* Code blocks */
    code {
        background-color: #161b22;
        color: #79c0ff;
        padding: 2px 6px;
        border-radius: 3px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #0d1117;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #8b949e;
    }
    
    .stTabs [aria-selected="true"] {
        color: #58a6ff;
        border-bottom-color: #58a6ff;
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
    """Cria mapa do céu mostrando localização do objeto (estilo SIMBAD)"""
    if ra is None or dec is None:
        return None
    
    # Criar grade de coordenadas ao redor do objeto (raio de 5 graus)
    ra_min, ra_max = ra - 5, ra + 5
    dec_min, dec_max = dec - 5, dec + 5
    
    # Grade de fundo (estilo SIMBAD)
    ra_grid = np.linspace(ra_min, ra_max, 50)
    dec_grid = np.linspace(dec_min, dec_max, 50)
    
    fig = go.Figure()
    
    # Adicionar grade de fundo (linhas RA)
    for ra_line in np.linspace(ra_min, ra_max, 11):
        fig.add_trace(go.Scatter(
            x=[ra_line, ra_line],
            y=[dec_min, dec_max],
            mode='lines',
            line=dict(color='#30363d', width=0.5, dash='dot'),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Adicionar grade de fundo (linhas Dec)
    for dec_line in np.linspace(dec_min, dec_max, 11):
        fig.add_trace(go.Scatter(
            x=[ra_min, ra_max],
            y=[dec_line, dec_line],
            mode='lines',
            line=dict(color='#30363d', width=0.5, dash='dot'),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Adicionar círculo indicando raio de busca (2 arcmin = 0.0333 graus)
    theta = np.linspace(0, 2*np.pi, 100)
    radius_deg = 2 / 60  # 2 arcmin em graus
    circle_ra = ra + radius_deg * np.cos(theta)
    circle_dec = dec + radius_deg * np.sin(theta)
    
    fig.add_trace(go.Scatter(
        x=circle_ra,
        y=circle_dec,
        mode='lines',
        line=dict(color='#58a6ff', width=2, dash='dash'),
        name='Raio de busca (2 arcmin)',
        hoverinfo='name'
    ))
    
    # Adicionar ponto do objeto alvo (estilo SIMBAD)
    fig.add_trace(go.Scatter(
        x=[ra],
        y=[dec],
        mode='markers+text',
        marker=dict(
            size=20,
            color='#ff4444',
            symbol='star',
            line=dict(color='#ffffff', width=2)
        ),
        text=[nome_estrela],
        textposition='top center',
        textfont=dict(size=14, color='#ff4444', family='Arial Black'),
        name='Objeto Alvo',
        hovertemplate=f'<b>{nome_estrela}</b><br>RA: {ra:.6f}°<br>Dec: {dec:.6f}°<extra></extra>'
    ))
    
    # Adicionar cruz de mira no centro
    fig.add_trace(go.Scatter(
        x=[ra-0.5, ra+0.5, None, ra, ra],
        y=[dec, dec, None, dec-0.5, dec+0.5],
        mode='lines',
        line=dict(color='#ff4444', width=1),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        template='plotly_dark',
        plot_bgcolor='#0d1117',
        paper_bgcolor='#0d1117',
        xaxis_title="Ascensão Reta (J2000) [graus]",
        yaxis_title="Declinação (J2000) [graus]",
        height=500,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99,
            bgcolor='rgba(22, 27, 34, 0.8)',
            bordercolor='#30363d',
            borderwidth=1
        ),
        xaxis=dict(
            range=[ra_max, ra_min],  # Invertido (estilo astronômico)
            gridcolor='#21262d',
            showgrid=True,
            zeroline=False
        ),
        yaxis=dict(
            range=[dec_min, dec_max],
            gridcolor='#21262d',
            showgrid=True,
            zeroline=False,
            scaleanchor="x",
            scaleratio=1
        ),
        font=dict(color='#c9d1d9'),
        title=dict(
            text=f"Localização Celeste - {nome_estrela}",
            font=dict(size=18, color='#58a6ff'),
            x=0.5,
            xanchor='center'
        )
    )
    
    return fig

def verificar_novidade(planetas, cometas, meteoros, nome_estrela, ra=None, dec=None, modo='rapido'):
    """Analisa se as detecções podem ser descobertas novas (com verificação SIMBAD ou CDS profissional)"""
    descobertas_potenciais = []
    
    # Determinar qual verificador usar
    usar_cds_pro = (modo == 'profissional' and ra is not None and dec is not None)
    
    # Verificar planetas
    if planetas and len(planetas) > 0:
        for i, p in enumerate(planetas):
            # Critérios para possível descoberta:
            # 1. Alta confiança (>70%)
            # 2. Período não comum (evitar artefatos)
            # 3. Profundidade significativa
            if p['confidence'] > 70 and 0.5 < p['period_days'] < 50:
                descoberta = {
                    'tipo': 'Planeta',
                    'indice': i + 1,
                    'confianca': p['confidence'],
                    'parametros': f"Período: {p['period_days']:.2f}d, Raio: {np.sqrt(p['transit_depth'])*109:.1f}R⊕",
                    'status': 'NOVO' if p['confidence'] > 85 else 'CANDIDATO',
                    'simbad': None,
                    'cds_profissional': None
                }
                
                # Verificar no SIMBAD/CDS
                if ra is not None and dec is not None:
                    try:
                        if usar_cds_pro:
                            # Modo profissional
                            resultado_cds = cds_pro.verificacao_completa(ra, dec, tipo_deteccao='planeta')
                            descoberta['cds_profissional'] = resultado_cds
                            descoberta['status'] = resultado_cds['classificacao_final']['status']
                            descoberta['prioridade'] = resultado_cds['classificacao_final']['prioridade']
                            descoberta['recomendacao_simbad'] = resultado_cds['classificacao_final']['mensagem']
                        else:
                            # Modo rápido
                            resultado_simbad = simbad.verificar_coordenadas(ra, dec)
                            classificacao = simbad.classificar_descoberta(resultado_simbad, p['confidence'])
                            descoberta['simbad'] = resultado_simbad
                            descoberta['status'] = classificacao['status']
                            descoberta['prioridade'] = classificacao['prioridade']
                            descoberta['recomendacao_simbad'] = classificacao['recomendacao']
                    except Exception as e:
                        descoberta['simbad_erro'] = str(e)
                
                descobertas_potenciais.append(descoberta)
    
    # Verificar cometas
    if cometas and len(cometas) > 0:
        for i, c in enumerate(cometas):
            if c['confidence'] > 0.8:
                descoberta = {
                    'tipo': 'Cometa/Evento Variável',
                    'indice': i + 1,
                    'confianca': c['confidence'] * 100,
                    'parametros': f"Aumento: {c['brightness_increase']*100:.1f}%",
                    'status': 'NOVO',
                    'simbad': None,
                    'cds_profissional': None
                }
                
                # Verificar no SIMBAD/CDS
                if ra is not None and dec is not None:
                    try:
                        if usar_cds_pro:
                            resultado_cds = cds_pro.verificacao_completa(ra, dec, tipo_deteccao='variavel')
                            descoberta['cds_profissional'] = resultado_cds
                            descoberta['status'] = resultado_cds['classificacao_final']['status']
                            descoberta['prioridade'] = resultado_cds['classificacao_final']['prioridade']
                            descoberta['recomendacao_simbad'] = resultado_cds['classificacao_final']['mensagem']
                        else:
                            resultado_simbad = simbad.verificar_coordenadas(ra, dec)
                            classificacao = simbad.classificar_descoberta(resultado_simbad, c['confidence'] * 100)
                            descoberta['simbad'] = resultado_simbad
                            descoberta['status'] = classificacao['status']
                            descoberta['prioridade'] = classificacao['prioridade']
                            descoberta['recomendacao_simbad'] = classificacao['recomendacao']
                    except Exception as e:
                        descoberta['simbad_erro'] = str(e)
                
                descobertas_potenciais.append(descoberta)
    
    # Verificar meteoros/transientes
    if meteoros and len(meteoros) > 0:
        eventos_rapidos = [m for m in meteoros if m.get('confidence', 0) > 0.7]
        if len(eventos_rapidos) > 0:
            descoberta = {
                'tipo': 'Eventos Transientes Rápidos',
                'indice': len(eventos_rapidos),
                'confianca': np.mean([m.get('confidence', 0) for m in eventos_rapidos]) * 100,
                'parametros': f"{len(eventos_rapidos)} eventos detectados",
                'status': 'ANALISAR',
                'simbad': None,
                'cds_profissional': None
            }
            
            # Verificar no SIMBAD/CDS
            if ra is not None and dec is not None:
                try:
                    confianca_media = np.mean([m.get('confidence', 0) for m in eventos_rapidos]) * 100
                    
                    if usar_cds_pro:
                        resultado_cds = cds_pro.verificacao_completa(ra, dec, tipo_deteccao='transiente')
                        descoberta['cds_profissional'] = resultado_cds
                        descoberta['status'] = resultado_cds['classificacao_final']['status']
                        descoberta['prioridade'] = resultado_cds['classificacao_final'].get('prioridade', 2)
                        descoberta['recomendacao_simbad'] = resultado_cds['classificacao_final']['mensagem']
                    else:
                        resultado_simbad = simbad.verificar_coordenadas(ra, dec)
                        classificacao = simbad.classificar_descoberta(resultado_simbad, confianca_media)
                        descoberta['simbad'] = resultado_simbad
                        descoberta['status'] = classificacao['status']
                        descoberta['prioridade'] = classificacao.get('prioridade', 2)
                        descoberta['recomendacao_simbad'] = classificacao['recomendacao']
                except Exception as e:
                    descoberta['simbad_erro'] = str(e)
            
            descobertas_potenciais.append(descoberta)
    
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

# =====================================
# EXPLORADOR DE DADOS DISPONÍVEIS
# =====================================
if st.session_state.get('mostrar_explorador', False):
    st.markdown("---")
    st.header("📊 Explorar Dados Disponíveis")
    
    col_fechar, col_vazio = st.columns([1, 5])
    with col_fechar:
        if st.button("❌ Fechar"):
            st.session_state['mostrar_explorador'] = False
            st.rerun()
    
    tabs = st.tabs(["🔭 Kepler - Exoplanetas", "🌟 TESS - Novos Dados", "🎯 Casos Famosos", "🔍 Buscar por Tipo"])
    
    # TAB 1: Kepler - Exoplanetas Confirmados
    with tabs[0]:
        st.subheader("Estrelas Kepler com Planetas Confirmados")
        st.markdown("Estes são exemplos **REAIS** de sistemas planetários descobertos pelo Kepler:")
        
        kepler_planetas = pd.DataFrame({
            'Nome': ['Kepler-10', 'Kepler-11', 'Kepler-16', 'Kepler-22', 'Kepler-62', 'Kepler-90', 'Kepler-186', 'Kepler-442', 'Kepler-452'],
            'Planetas': [2, 6, 1, 1, 5, 8, 5, 1, 1],
            'Nota': [
                'Primeiro planeta rochoso (Kepler-10b)',
                'Sistema compacto com 6 planetas',
                'Planeta circumbinário (2 sóis!)',
                'Primeiro na zona habitável',
                '5 planetas, 2 na zona habitável',
                'RECORDE: 8 planetas (mini sistema solar)',
                'Primeiro planeta tamanho Terra em zona habitável',
                'Super-Terra na zona habitável',
                'Primo da Terra (zona habitável, estrela tipo Sol)'
            ],
            'KIC': ['KIC 11904151', 'KIC 6541920', 'KIC 12644769', 'KIC 10593626', 'KIC 9002278', 'KIC 11442793', 'KIC 8120608', 'KIC 9603725', 'KIC 10666592']
        })
        
        st.dataframe(kepler_planetas, width="stretch", hide_index=True)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            estrela_selecionada = st.selectbox("Escolha uma estrela para analisar:", kepler_planetas['Nome'].tolist(), key="kepler_sel")
        with col2:
            if st.button("🔍 Analisar Esta Estrela", width="stretch"):
                st.session_state['nome_estrela_preenchido'] = estrela_selecionada
                st.session_state['missao_selecionada'] = 'Kepler'
                st.session_state['mostrar_explorador'] = False
                st.rerun()
    
    # TAB 2: TESS - Dados Recentes
    with tabs[1]:
        st.subheader("Dados TESS - Missão Mais Recente")
        st.markdown("TESS (2018-presente) está descobrindo **NOVOS** planetas:")
        
        tess_exemplos = pd.DataFrame({
            'Nome': ['TOI-700', 'TOI-1452', 'TOI-270', 'TOI-178', 'HD 21749', 'LTT 1445A', 'GJ 357'],
            'Status': ['Confirmado', 'Candidato', 'Confirmado', 'Confirmado', 'Confirmado', 'Confirmado', 'Confirmado'],
            'Nota': [
                'Planeta tamanho Terra em zona habitável',
                'Mundo oceânico (água!)',
                '3 planetas, 1 super-Terra',
                '6 planetas em ressonância',
                'Sub-Netuno (36 dias)',
                'Sistema triplo com planetas',
                'Super-Terra + 2 candidatos'
            ],
            'TIC': ['TIC 150428135', 'TIC 301256664', 'TIC 259377017', 'TIC 52368076', 'TIC 12422937', 'TIC 87998380', 'TIC 109820622']
        })
        
        st.dataframe(tess_exemplos, width="stretch", hide_index=True)
        
        st.info("💡 **Dica:** TESS tem dados mais recentes! Maior chance de fazer novas descobertas.")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            estrela_selecionada_tess = st.selectbox("Escolha uma estrela TESS:", tess_exemplos['Nome'].tolist(), key="tess_sel")
        with col2:
            if st.button("🔍 Analisar TESS", width="stretch"):
                st.session_state['nome_estrela_preenchido'] = estrela_selecionada_tess
                st.session_state['missao_selecionada'] = 'TESS'
                st.session_state['mostrar_explorador'] = False
                st.rerun()
    
    # TAB 3: Casos Famosos
    with tabs[2]:
        st.subheader("⭐ Objetos Astronômicos Famosos")
        
        famosos = pd.DataFrame({
            'Nome': ['KIC 8462852', 'KIC 9832227', 'KIC 12557548', 'HD 209458', 'WASP-12'],
            'Apelido': ['Estrela de Tabby', 'Estrela da Fusão', 'Planeta Evaporante', 'Osiris', 'Planeta Condenado'],
            'Fenômeno': [
                '🔥 MISTÉRIO: Escurecimentos de até 22%! Mega-estrutura alienígena?',
                '💥 Pode colidir/fundir em 2022 (PREVISTO!)',
                '☄️ Planeta se desintegrando em tempo real',
                '🌡️ Primeiro trânsito planetário detectado (2000)',
                '🕳️ Sendo devorado por sua estrela'
            ],
            'Missão': ['Kepler', 'Kepler', 'Kepler', 'Kepler/TESS', 'TESS']
        })
        
        st.dataframe(famosos, width="stretch", hide_index=True)
        
        st.warning("⚠️ **ATENÇÃO:** Estes objetos têm comportamento EXTREMO e ÚNICO!")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            estrela_famosa = st.selectbox("Escolha um caso famoso:", famosos['Nome'].tolist(), key="famoso_sel")
        with col2:
            if st.button("🔥 Analisar Caso Famoso", width="stretch"):
                st.session_state['nome_estrela_preenchido'] = estrela_famosa
                # Determinar missão
                idx = famosos[famosos['Nome'] == estrela_famosa].index[0]
                st.session_state['missao_selecionada'] = famosos.iloc[idx]['Missão'].split('/')[0]
                st.session_state['mostrar_explorador'] = False
                st.rerun()
    
    # TAB 4: Buscar por Tipo
    with tabs[3]:
        st.subheader("🔍 Buscar por Tipo de Objeto")
        
        tipo = st.selectbox("Tipo de objeto que procura:", [
            "Planetas rochosos (tipo Terra)",
            "Hot Jupiters (gigantes próximos)",
            "Planetas em zona habitável",
            "Sistemas multi-planetários",
            "Estrelas variáveis",
            "Estrelas binárias eclipsantes",
            "Eventos de microlente gravitacional"
        ])
        
        if tipo == "Planetas rochosos (tipo Terra)":
            sugestoes = ['Kepler-10b', 'Kepler-20e', 'Kepler-20f', 'Kepler-78b', 'Kepler-186f']
        elif tipo == "Hot Jupiters (gigantes próximos)":
            sugestoes = ['HD 209458', 'WASP-12', 'Kepler-7b', 'HAT-P-7b', 'CoRoT-1b']
        elif tipo == "Planetas em zona habitável":
            sugestoes = ['Kepler-22b', 'Kepler-62e', 'Kepler-62f', 'Kepler-186f', 'Kepler-442b', 'Kepler-452b']
        elif tipo == "Sistemas multi-planetários":
            sugestoes = ['Kepler-11', 'Kepler-90', 'Kepler-62', 'Kepler-186', 'TRAPPIST-1']
        elif tipo == "Estrelas variáveis":
            sugestoes = ['KIC 11904151', 'KIC 8462852', 'KIC 9832227', 'RR Lyrae', 'Delta Cephei']
        elif tipo == "Estrelas binárias eclipsantes":
            sugestoes = ['Kepler-16', 'Kepler-34', 'Kepler-35', 'Kepler-38', 'Algol']
        else:
            sugestoes = ['MOA-2011-BLG-293', 'OGLE-2016-BLG-1190']
        
        st.markdown("**Exemplos deste tipo:**")
        for sug in sugestoes:
            st.markdown(f"- {sug}")
        
        nome_busca = st.text_input("Ou digite o nome completo:", key="busca_tipo")
        if st.button("🎯 Buscar Este Objeto", width="stretch"):
            if nome_busca:
                st.session_state['nome_estrela_preenchido'] = nome_busca
                st.session_state['mostrar_explorador'] = False
                st.rerun()
    
    st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("Configurações")
    
    # NOVA SEÇÃO: Alvos Promissores
    st.subheader("🎯 Alvos Promissores")
    
    if st.button("Ver Alvos Recomendados", width="stretch"):
        st.session_state['mostrar_alvos'] = True
    
    st.divider()
    
    # Seleção de missão
    missao = st.selectbox(
        "Missão Espacial",
        ["Kepler", "TESS"],
        help="Escolha o telescópio espacial"
    )
    
    # Input da estrela
    st.subheader("Buscar Estrela")
    
    # Botão para explorar dados disponíveis
    if st.button("📊 Explorar Dados Disponíveis", width="stretch"):
        st.session_state['mostrar_explorador'] = True
    
    # Exemplos rápidos
    exemplo = st.selectbox(
        "Exemplos de estrelas",
        [
            "Pesquisa personalizada",
            "Kepler-10 (2 planetas confirmados)",
            "Kepler-90 (8 planetas!)",
            "KIC 11904151 (oscilações)",
            "HD 209458 (Hot Jupiter)",
            "Kepler-16 (planeta circumbinário)",
            "Kepler-22 (zona habitável)",
            "KIC 8462852 (Estrela de Tabby)"
        ]
    )
    
    if exemplo != "Pesquisa personalizada":
        nome_base = exemplo.split(" ")[0]
        nome_estrela = st.text_input("Nome da Estrela", value=nome_base)
    else:
        # Verificar se tem alvo pré-selecionado
        valor_padrao = st.session_state.get('nome_estrela_preenchido', 'Kepler-10')
        nome_estrela = st.text_input("Nome da Estrela", value=valor_padrao)
        
        # Limpar após uso
        if 'nome_estrela_preenchido' in st.session_state:
            del st.session_state['nome_estrela_preenchido']
    
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
    
    # Opção de verificação profissional
    st.subheader("Verificação de Descobertas")
    modo_verificacao = st.radio(
        "Modo de Verificação",
        ["Rápido (HTTP)", "Profissional (Astroquery CDS)"],
        help="Rápido: HTTP direto ao SIMBAD. Profissional: APIs oficiais da CDS (SIMBAD + VizieR + catálogos especializados)"
    )
    
    st.divider()
    
    # Opção de monitoramento
    st.subheader("Monitoramento")
    enable_monitoring = st.checkbox("Ativar monitoramento", value=True, 
                                    help="Salva resultados no banco de dados para comparação futura")
    
    # Botão para ver histórico
    if st.button("Ver Histórico/Estatísticas", width="stretch"):
        st.session_state['mostrar_historico'] = True
    
    # Botão de busca
    buscar = st.button("Buscar e Analisar", type="primary", width="stretch")

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
                st.plotly_chart(fig_mapa, width="stretch")
        
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
    
    st.plotly_chart(fig_lc, width="stretch")
    
    # NOVA SEÇÃO: Sonificação da Curva de Luz
    st.divider()
    st.subheader("🔊 Sonificação - Ouça as Ondulações")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info(sonificador.descrever_sonificacao('curva_luz'))
    
    with col2:
        duracao_audio = st.slider("Duração do áudio (s)", 5, 30, 10, key='duracao_curva')
        if st.button("🎵 Gerar Áudio da Curva de Luz", width="stretch"):
            with st.spinner("Gerando áudio..."):
                audio_data, sample_rate = sonificador.sonificar_curva_luz(
                    time, flux, duracao_segundos=duracao_audio
                )
                audio_bytes = sonificador.criar_wav_bytes(audio_data, sample_rate)
                
                st.audio(audio_bytes, format='audio/wav')
                st.download_button(
                    label="⬇️ Baixar Áudio",
                    data=audio_bytes,
                    file_name=f"{nome_estrela}_curva_luz.wav",
                    mime="audio/wav"
                )
    
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
            
            st.dataframe(df_display, width="stretch")
            
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
                
                st.plotly_chart(fig_phase, width="stretch")
                
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
                    
                    st.plotly_chart(fig_comet, width="stretch")
            
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
                        
                        st.plotly_chart(fig_comet, width="stretch")
    
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
            
            st.plotly_chart(fig_meteors, width="stretch")
            
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
                
                st.plotly_chart(fig_zoom, width="stretch")
            
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
                st.dataframe(df_display, width="stretch")
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
                        
                        st.plotly_chart(fig_trans, width="stretch")
    
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
        
        st.plotly_chart(fig_power, width="stretch")
        
        # SONIFICAÇÃO DAS VIBRAÇÕES
        st.divider()
        st.subheader("🔊 Ouça as Vibrações Estelares")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.info(sonificador.descrever_sonificacao('vibracoes'))
        
        with col2:
            duracao_vibr = st.slider("Duração (s)", 5, 20, 10, key='duracao_vibr')
            if st.button("🎵 Gerar Áudio das Vibrações", width="stretch"):
                with st.spinner("Sintetizando frequências estelares..."):
                    audio_vibr, sr_vibr = sonificador.sonificar_vibracoes(
                        frequencies, power, duracao_segundos=duracao_vibr
                    )
                    audio_vibr_bytes = sonificador.criar_wav_bytes(audio_vibr, sr_vibr)
                    
                    st.audio(audio_vibr_bytes, format='audio/wav')
                    st.download_button(
                        label="⬇️ Baixar Áudio",
                        data=audio_vibr_bytes,
                        file_name=f"{nome_estrela}_vibracoes.wav",
                        mime="audio/wav",
                        key='download_vibr'
                    )
        
        # Modos de oscilação
        modes = seismo_analysis['oscillation_modes']
        if len(modes) > 0:
            st.subheader(f"Modos de Oscilação Detectados: {len(modes)}")
            
            df_modes = pd.DataFrame(modes[:10])  # Top 10
            df_modes['frequency_uHz'] = df_modes['frequency_uHz'].round(2)
            df_modes['amplitude'] = df_modes['amplitude'].round(6)
            
            df_display_modes = df_modes[['frequency_uHz', 'type', 'mode_order']].copy()
            df_display_modes.columns = ['Frequência (μHz)', 'Tipo', 'Ordem']
            
            st.dataframe(df_display_modes, width="stretch")
    
    # ANÁLISE DE DESCOBERTAS POTENCIAIS
    st.divider()
    st.header("Análise de Descobertas")
    
    # Coletar todas as detecções
    planetas_detectados = analisar_planetas(time, flux) if detect_planets else []
    cometas_detectados = analisar_cometas(time, flux) if detect_comets else []
    meteoros_detectados = analisar_meteoros(time, flux) if detect_meteors else []
    
    # Verificar com SIMBAD (passar coordenadas e modo)
    usar_modo_profissional = (modo_verificacao == "Profissional (Astroquery CDS)")
    
    if usar_modo_profissional:
        with st.spinner("Verificando em múltiplos catálogos profissionais (SIMBAD + VizieR + NASA)..."):
            descobertas = verificar_novidade(
                planetas_detectados, 
                cometas_detectados, 
                meteoros_detectados, 
                nome_estrela,
                ra,
                dec,
                modo='profissional'
            )
    else:
        with st.spinner("Verificando descobertas no SIMBAD..."):
            descobertas = verificar_novidade(
                planetas_detectados, 
                cometas_detectados, 
                meteoros_detectados, 
                nome_estrela,
                ra,
                dec,
                modo='rapido'
            )
    
    if len(descobertas) > 0:
        st.warning(f"**ATENÇÃO: {len(descobertas)} possíveis descobertas ou objetos de interesse detectados!**")
        
        for desc in descobertas:
            # Ícone baseado no status SIMBAD
            if desc['status'] == 'NOVA':
                status_color = "�"
                status_msg = "POTENCIAL DESCOBERTA!"
            elif desc['status'] == 'CONHECIDA':
                status_color = "⚪"
                status_msg = "OBJETO CONHECIDO"
            elif desc['status'] == 'CANDIDATA':
                status_color = "🟡"
                status_msg = "CANDIDATO"
            else:
                status_color = "🔵"
                status_msg = "ANALISAR"
            
            prioridade = desc.get('prioridade', 2)
            
            with st.expander(
                f"{status_color} {desc['tipo']} #{desc['indice']} - {status_msg} (Prioridade: {prioridade}/5)", 
                expanded=(prioridade >= 4)
            ):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Confiança Detecção", f"{desc['confianca']:.1f}%")
                with col2:
                    st.metric("Status SIMBAD", desc['status'])
                with col3:
                    st.metric("Prioridade", f"{prioridade}/5")
                
                st.info(f"**Parâmetros:** {desc['parametros']}")
                
                # Mostrar resultado SIMBAD
                if 'simbad' in desc and desc['simbad']:
                    st.divider()
                    st.subheader("Verificação SIMBAD (Modo Rápido)")
                    
                    resultado_simbad = desc['simbad']
                    
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        total_objetos = resultado_simbad.get('total_objetos', 0)
                        
                        if total_objetos == 0:
                            st.success("✅ **Nenhum objeto conhecido encontrado nestas coordenadas!**")
                        else:
                            st.warning(f"⚠️ **{total_objetos} objetos encontrados no campo**")
                            
                            obj_principal = resultado_simbad.get('objeto_principal')
                            if obj_principal:
                                st.markdown(f"""
**Objeto mais próximo:**
- **Nome:** {obj_principal.get('identificador', 'N/A')}
- **Tipo:** {obj_principal.get('tipo', 'N/A')}
- **Distância:** {obj_principal.get('distancia_arcsec', 0):.2f} arcsec
- **Referências:** {obj_principal.get('referencias', 0)} papers
                                """)
                                
                                if obj_principal.get('distancia_arcsec', 999) < 5:
                                    st.info("🎯 Objeto muito próximo (< 5 arcsec) - Provavelmente é o mesmo objeto")
                                elif obj_principal.get('distancia_arcsec', 999) < 30:
                                    st.warning("📍 Objeto moderadamente próximo - Pode ser o mesmo ou campo estelar")
                                else:
                                    st.success("📍 Objeto distante - Sua detecção pode ser algo novo no campo!")
                    
                    with col2:
                        url_simbad = resultado_simbad.get('url_busca', '')
                        if url_simbad:
                            st.markdown(f"[🔗 Ver no SIMBAD]({url_simbad})")
                
                # Mostrar resultado CDS Profissional
                if 'cds_profissional' in desc and desc['cds_profissional']:
                    st.divider()
                    st.subheader("🎓 Verificação Profissional CDS")
                    
                    resultado_cds = desc['cds_profissional']
                    
                    # Relatório completo
                    relatorio = cds_pro.gerar_relatorio_profissional(resultado_cds)
                    st.markdown(relatorio)
                    
                    # Detalhes adicionais em expanders
                    if resultado_cds['simbad']['total_objetos'] > 0:
                        with st.expander("Ver todos os objetos SIMBAD encontrados"):
                            for obj in resultado_cds['simbad']['objetos']:
                                st.markdown(f"""
**{obj['nome']}**
- Tipo: {obj['tipo']}
- Separação: {obj['separacao_arcsec']:.2f} arcsec
- Mag V: {obj['mag_v'] if obj['mag_v'] else 'N/A'}
- Referências: {obj['referencias']}
                                """)
                                st.divider()
                    
                    # Exoplanetas
                    if resultado_cds['exoplanetas'] and resultado_cds['exoplanetas']['total_planetas'] > 0:
                        with st.expander(f"Ver {resultado_cds['exoplanetas']['total_planetas']} planetas conhecidos"):
                            for planeta in resultado_cds['exoplanetas']['planetas']:
                                st.json(planeta['dados'])
                    
                    # Variáveis
                    if resultado_cds['variaveis'] and resultado_cds['variaveis']['total_variaveis'] > 0:
                        with st.expander(f"Ver {resultado_cds['variaveis']['total_variaveis']} estrelas variáveis"):
                            for var in resultado_cds['variaveis']['variaveis']:
                                periodo_str = f"{var['periodo']:.2f}d" if var['periodo'] else 'N/A'
                                st.markdown(f"""
**{var['nome']}**
- Tipo: {var['tipo']}
- Período: {periodo_str}
- Amplitude: {var['max_mag']:.2f} - {var['min_mag']:.2f} mag
                                """)
                                st.divider()
                
                # Recomendação do sistema
                if 'recomendacao_simbad' in desc:
                    st.divider()
                    if desc['status'] == 'NOVA':
                        st.success(f"**Recomendação:** {desc['recomendacao_simbad']}")
                    elif desc['status'] == 'CONHECIDA':
                        st.info(f"**Análise:** {desc['recomendacao_simbad']}")
                    else:
                        st.warning(f"**Recomendação:** {desc['recomendacao_simbad']}")
                
                # Erro na verificação SIMBAD
                if 'simbad_erro' in desc:
                    st.error(f"⚠️ Erro ao verificar SIMBAD: {desc['simbad_erro']}")
                    st.info("Verifique manualmente no link acima ou tente novamente mais tarde.")
                
                # Próximos passos baseado no status
                if desc['status'] == 'NOVA':
                    st.divider()
                    st.success("### 🎉 POSSÍVEL DESCOBERTA!")
                    
                    st.markdown("### Próximos Passos:")
                    
                    tab1, tab2, tab3 = st.tabs(["Verificação", "Monitoramento", "Publicação"])
                    
                    with tab1:
                        st.markdown("""
                        **Verificações adicionais:**
                        
                        1. ✅ Verificado no SIMBAD - Não encontrado
                        2. 🔍 Verificar em outros catálogos:
                           - NASA Exoplanet Archive
                           - VizieR (catálogos variados)
                           - Minor Planet Center (se for cometa/asteroide)
                        3. 🔍 Buscar em papers recentes (últimos 6 meses)
                        
                        **Se continuar não encontrando = DESCOBERTA CONFIRMADA!**
                        """)
                        
                        if ra is not None and dec is not None:
                            st.code(f"""
Links para verificação adicional:

NASA Exoplanet Archive:
https://exoplanetarchive.ipac.caltech.edu/

VizieR:
https://vizier.u-strasbg.fr/viz-bin/VizieR?-c={ra}+{dec}&-c.rs=2

ArXiv recentes (últimos 6 meses):
https://arxiv.org/search/?query={ra}+{dec}&searchtype=all&order=-announced_date_first&size=50
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
                
                elif desc['status'] == 'CONHECIDA':
                    st.info("""
                    **Validação bem-sucedida!** 
                    
                    Seu sistema detectou corretamente um objeto conhecido, confirmando que:
                    - ✅ Os algoritmos de detecção estão funcionando
                    - ✅ A análise de dados está precisa
                    - ✅ O sistema pode encontrar objetos reais
                    
                    Continue procurando em outras estrelas menos estudadas!
                    """)
                
                elif desc['status'] == 'CANDIDATA':
                    st.warning("""
                    **Candidato interessante.** Necessita mais observações para confirmação.
                    
                    **Ações recomendadas:**
                    - Continue monitorando este objeto
                    - Faça mais 2-3 observações
                    - Use diferentes configurações de cadência
                    - Verifique se o padrão se repete
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

# Seção de Alvos Promissores
if 'mostrar_alvos' in st.session_state and st.session_state['mostrar_alvos']:
    st.divider()
    st.header("🎯 Alvos Promissores para Descobertas")
    
    st.info("""
    **Estes alvos têm maior potencial de revelar descobertas novas!**
    
    - Estrelas pouco estudadas (menos referências)
    - Regiões menos exploradas do campo Kepler/TESS  
    - Sistemas com comportamentos anômalos conhecidos
    - KIC/TIC de alto número (estatisticamente menos analisados)
    """)
    
    # Tabs para categorias
    tab1, tab2, tab3, tab4 = st.tabs([
        "⭐ Alta Prioridade",
        "🎲 Kepler Aleatórios",
        "🛰️ TESS Aleatórios",
        "📍 Coordenadas Especiais"
    ])
    
    with tab1:
        st.subheader("Alvos de Alta Prioridade")
        st.warning("**Estes são os alvos MAIS promissores para descobertas únicas!**")
        
        alvos_alta = [
            {
                'nome': 'KIC 8462852',
                'missao': 'Kepler',
                'razao': '🌟 **Estrela de Tabby** - A mais misteriosa conhecida! Variações de até 22% no brilho',
                'prioridade': 5,
                'dica': 'Use cadência "short" para capturar eventos rápidos'
            },
            {
                'nome': 'KIC 9832227',
                'missao': 'Kepler',
                'razao': '💥 **Candidata a fusão estelar** - Sistema binário com período orbital diminuindo',
                'prioridade': 5,
                'dica': 'Pode ser evento único na história da astronomia!'
            },
            {
                'nome': 'KIC 12557548',
                'missao': 'Kepler',
                'razao': '🪐 **Planeta evaporando** - Trânsitos extremamente variáveis',
                'prioridade': 5,
                'dica': 'Planeta em desintegração - padrões únicos'
            },
            {
                'nome': 'TIC 400799224',
                'missao': 'TESS',
                'razao': '🌑 **Disintegrating planet candidate** - Dados TESS recentes',
                'prioridade': 5,
                'dica': 'Dados novos - possível descoberta não publicada ainda'
            },
        ]
        
        for alvo in alvos_alta:
            with st.expander(f"{'⭐' * alvo['prioridade']} {alvo['nome']} - Prioridade {alvo['prioridade']}/5"):
                st.markdown(alvo['razao'])
                st.info(f"**Dica:** {alvo['dica']}")
                
                if st.button(f"Usar '{alvo['nome']}'", key=f"usar_{alvo['nome']}"):
                    st.session_state['nome_estrela_preenchido'] = alvo['nome']
                    st.session_state['missao_selecionada'] = alvo['missao']
                    st.session_state['mostrar_alvos'] = False
                    st.success(f"✅ '{alvo['nome']}' selecionado! Role para cima e clique em 'Buscar e Analisar'")
    
    with tab2:
        st.subheader("Alvos Kepler Aleatórios")
        st.info("KICs de alto número - estatisticamente menos estudados")
        
        alvos_kepler = gerador_alvos.gerar_alvos_kepler(20)
        
        for i, alvo in enumerate(alvos_kepler):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{alvo['nome']}**")
            with col2:
                st.write(f"Prioridade: {alvo['prioridade']}/5")
            with col3:
                if st.button("Usar", key=f"usar_kepler_{i}"):
                    st.session_state['nome_estrela_preenchido'] = alvo['nome']
                    st.session_state['missao_selecionada'] = 'Kepler'
                    st.session_state['mostrar_alvos'] = False
                    st.success(f"✅ Selecionado! Role para cima.")
    
    with tab3:
        st.subheader("Alvos TESS Aleatórios")
        st.info("TICs de alto número - dados mais recentes, maior chance de descobertas não publicadas")
        
        alvos_tess = gerador_alvos.gerar_alvos_tess(20)
        
        for i, alvo in enumerate(alvos_tess):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{alvo['nome']}**")
            with col2:
                st.write(f"Prioridade: {alvo['prioridade']}/5")
            with col3:
                if st.button("Usar", key=f"usar_tess_{i}"):
                    st.session_state['nome_estrela_preenchido'] = alvo['nome']
                    st.session_state['missao_selecionada'] = 'TESS'
                    st.session_state['mostrar_alvos'] = False
                    st.success(f"✅ Selecionado! Role para cima.")
    
    with tab4:
        st.subheader("Coordenadas Especiais")
        st.info("Regiões menos exploradas do campo Kepler")
        
        alvos_coord = gerador_alvos.gerar_coordenadas_aleatorias_kepler(15)
        
        for i, alvo in enumerate(alvos_coord):
            with st.expander(f"📍 Região {i+1}: RA={alvo['ra']:.4f}°, Dec={alvo['dec']:.4f}°"):
                st.write(f"**Coordenadas:** {alvo['coordenadas']}")
                st.write(f"**Razão:** {alvo['razao']}")
                st.code(f"RA: {alvo['ra']:.6f}°\nDec: {alvo['dec']:.6f}°")
                
                if st.button(f"Usar coordenadas", key=f"usar_coord_{i}"):
                    st.info("Use estas coordenadas diretamente na busca do lightkurve")
    
    if st.button("Fechar Alvos"):
        st.session_state['mostrar_alvos'] = False
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

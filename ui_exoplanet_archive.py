"""
Interface UI para NASA Exoplanet Archive
Módulo separado para manter app.py limpo
"""

import streamlit as st
import pandas as pd
import plotly.express as px


def render_exoplanet_archive_ui(api):
    """Renderiza interface completa do Exoplanet Archive"""
    
    st.divider()
    st.header("🪐 NASA Exoplanet Archive")
    
    st.info("""
    **Acesse dados oficiais de exoplanetas confirmados e candidatos do NASA Exoplanet Archive!**
    
    - Planetas confirmados de todas as missões (Kepler, TESS, etc.)
    - KOI (Kepler Objects of Interest) candidatos
    - Busca por características específicas (zona habitável, método de descoberta, etc.)
    """)
    
    # Tabs para diferentes tipos de busca
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Busca Rápida",
        "🌍 Zona Habitável",
        "📊 Por Método",
        "🎯 Query ADQL",
        "🗺️ Cone Search"
    ])
    
    with tab1:
        _render_busca_rapida(api)
    
    with tab2:
        _render_zona_habitavel(api)
    
    with tab3:
        _render_por_metodo(api)
    
    with tab4:
        _render_query_personalizada(api)
    
    with tab5:
        _render_cone_search(api)
    
    # Botão para fechar
    if st.button("✖️ Fechar", use_container_width=True):
        st.session_state['mostrar_exoplanets'] = False
        st.rerun()


def _render_busca_rapida(api):
    """Tab de busca rápida"""
    st.subheader("Busca Rápida de Exoplanetas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        tipo_busca = st.selectbox(
            "Tipo de dados",
            ["Planetas Confirmados", "KOI Candidatos", "Buscar por Nome"]
        )
    
    with col2:
        limite = st.number_input("Limite", min_value=5, max_value=500, value=50)
    
    if tipo_busca == "Planetas Confirmados":
        col1, col2 = st.columns(2)
        
        with col1:
            ano_min = st.number_input("Ano mínimo", min_value=1990, max_value=2025, value=2020)
        
        with col2:
            metodo = st.selectbox(
                "Método (opcional)",
                ["Todos", "Transit", "Radial Velocity", "Microlensing", "Imaging"]
            )
        
        if st.button("🔍 Buscar", type="primary"):
            with st.spinner("Consultando NASA..."):
                try:
                    where = f"disc_year >= {ano_min}"
                    if metodo != "Todos":
                        where += f" AND discoverymethod = '{metodo}'"
                    
                    df = api.get_confirmed_planets(where=where, limit=limite)
                    
                    st.success(f"✓ {len(df)} planetas encontrados")
                    st.dataframe(df, use_container_width=True, height=400)
                    
                    # Métricas
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total", len(df))
                    with col2:
                        if 'sy_dist' in df.columns:
                            st.metric("Distância Média", f"{df['sy_dist'].mean():.1f} pc")
                    with col3:
                        if 'disc_year' in df.columns:
                            st.metric("Mais Recente", int(df['disc_year'].max()))
                    
                    # Download
                    csv = df.to_csv(index=False)
                    st.download_button("⬇️ CSV", csv, f"exoplanets_{ano_min}.csv", "text/csv")
                    
                except Exception as e:
                    st.error(f"Erro: {e}")
    
    elif tipo_busca == "KOI Candidatos":
        col1, col2 = st.columns(2)
        
        with col1:
            periodo_min = st.number_input("Período mín (dias)", min_value=0.0, value=0.0, step=10.0)
        
        with col2:
            raio_max = st.number_input("Raio máx (Re)", min_value=0.0, value=10.0, step=0.5)
        
        if st.button("🔍 Buscar KOIs", type="primary"):
            with st.spinner("Consultando..."):
                try:
                    df = api.get_koi_candidates(
                        period_min=periodo_min if periodo_min > 0 else None,
                        radius_max=raio_max if raio_max > 0 else None,
                        limit=limite
                    )
                    
                    st.success(f"✓ {len(df)} KOIs encontrados")
                    st.dataframe(df, use_container_width=True, height=400)
                    
                    csv = df.to_csv(index=False)
                    st.download_button("⬇️ CSV", csv, "koi_candidates.csv", "text/csv")
                    
                except Exception as e:
                    st.error(f"Erro: {e}")
    
    else:  # Buscar por nome
        nome = st.text_input("Nome do planeta", value="Kepler-452 b")
        
        if st.button("🔍 Buscar", type="primary"):
            with st.spinner(f"Buscando {nome}..."):
                try:
                    df = api.search_by_name(nome)
                    
                    if len(df) > 0:
                        st.success("✓ Encontrado!")
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.warning("Não encontrado")
                    
                except Exception as e:
                    st.error(f"Erro: {e}")


def _render_zona_habitavel(api):
    """Tab de zona habitável"""
    st.subheader("🌍 Candidatos na Zona Habitável")
    
    st.markdown("Temperatura 180-310K, Raio 0.5-2.0 Re")
    
    col1, col2 = st.columns(2)
    
    with col1:
        temp_min = st.number_input("Temp mín (K)", value=180, step=10)
        raio_min = st.number_input("Raio mín (Re)", value=0.5, step=0.1)
    
    with col2:
        temp_max = st.number_input("Temp máx (K)", value=310, step=10)
        raio_max = st.number_input("Raio máx (Re)", value=2.0, step=0.1)
    
    if st.button("🌍 Buscar", type="primary"):
        with st.spinner("Buscando..."):
            try:
                df = api.get_habitable_zone_candidates(
                    temp_min=temp_min,
                    temp_max=temp_max,
                    radius_min=raio_min,
                    radius_max=raio_max,
                    limit=100
                )
                
                st.success(f"✓ {len(df)} candidatos")
                st.dataframe(df, use_container_width=True, height=400)
                
                # Mais próximos
                if 'sy_dist' in df.columns:
                    proximos = df.nsmallest(5, 'sy_dist')
                    st.subheader("🎯 5 Mais Próximos")
                    st.dataframe(proximos)
                
                csv = df.to_csv(index=False)
                st.download_button("⬇️ CSV", csv, "habitable_zone.csv", "text/csv")
                
            except Exception as e:
                st.error(f"Erro: {e}")


def _render_por_metodo(api):
    """Tab de busca por método"""
    st.subheader("📊 Por Método de Descoberta")
    
    metodo = st.selectbox(
        "Método",
        ["Transit", "Radial Velocity", "Microlensing", "Imaging", 
         "Transit Timing Variations", "Eclipse Timing Variations"]
    )
    
    if st.button(f"🔍 Buscar ({metodo})", type="primary"):
        with st.spinner(f"Buscando {metodo}..."):
            try:
                df = api.get_planets_by_method(metodo, limit=100)
                
                st.success(f"✓ {len(df)} planetas")
                st.dataframe(df, use_container_width=True, height=400)
                
                # Gráfico por ano
                if 'disc_year' in df.columns:
                    st.subheader("📈 Descobertas por Ano")
                    counts = df['disc_year'].value_counts().sort_index()
                    
                    fig = px.bar(
                        x=counts.index,
                        y=counts.values,
                        labels={'x': 'Ano', 'y': 'Descobertas'},
                        title=f'{metodo}'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                csv = df.to_csv(index=False)
                st.download_button("⬇️ CSV", csv, f"{metodo.lower()}.csv", "text/csv")
                
            except Exception as e:
                st.error(f"Erro: {e}")


def _render_query_personalizada(api):
    """Tab de query ADQL"""
    st.subheader("🎯 Query ADQL Personalizada")
    
    exemplo = st.selectbox(
        "Exemplos",
        [
            "Query personalizada",
            "SELECT TOP 10 * FROM ps WHERE disc_year > 2020",
            "SELECT pl_name, pl_rade FROM ps WHERE pl_rade > 11",
            "SELECT hostname, COUNT(*) as num FROM ps GROUP BY hostname ORDER BY num DESC"
        ]
    )
    
    query = st.text_area(
        "Query ADQL",
        value=exemplo if exemplo != "Query personalizada" else "SELECT TOP 100 * FROM ps",
        height=100
    )
    
    formato = st.selectbox("Formato", ["csv", "json"])
    
    if st.button("▶️ Executar", type="primary"):
        with st.spinner("Executando..."):
            try:
                resultado = api.tap_query(query, format=formato)
                
                if formato == 'csv':
                    st.success(f"✓ {len(resultado)} linhas")
                    st.dataframe(resultado, use_container_width=True, height=400)
                    
                    csv = resultado.to_csv(index=False)
                    st.download_button("⬇️ CSV", csv, "query.csv", "text/csv")
                else:
                    st.success("✓ Executada")
                    st.json(resultado)
                
            except Exception as e:
                st.error(f"Erro: {e}")


def _render_cone_search(api):
    """Tab de cone search"""
    st.subheader("🗺️ Cone Search")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ra = st.number_input("RA (graus)", min_value=0.0, max_value=360.0, value=291.0)
    
    with col2:
        dec = st.number_input("Dec (graus)", min_value=-90.0, max_value=90.0, value=48.0)
    
    with col3:
        radius = st.number_input("Raio (graus)", min_value=0.01, value=1.0)
    
    tabela = st.selectbox("Tabela", ["missionstars", "mission_exocat"])
    
    if st.button("🔍 Buscar", type="primary"):
        with st.spinner(f"Buscando RA={ra}°, Dec={dec}°..."):
            try:
                df = api.cone_search(
                    table=tabela,
                    ra=ra,
                    dec=dec,
                    radius=radius,
                    radius_unit='degree'
                )
                
                st.success(f"✓ {len(df)} objetos")
                st.dataframe(df, use_container_width=True, height=400)
                
                csv = df.to_csv(index=False)
                st.download_button("⬇️ CSV", csv, f"cone_ra{ra}_dec{dec}.csv", "text/csv")
                
            except Exception as e:
                st.error(f"Erro: {e}")

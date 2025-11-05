"""
Exoplanet Archive API Interface
================================
Interface para acessar dados do NASA Exoplanet Archive através da API.

Nota: A maioria das tabelas migrou para o serviço TAP (Table Access Protocol).
Este módulo oferece suporte para queries básicas da API legada e TAP service.

Author: Generated for Cosmos Project
Date: 2025-11-05
"""

import requests
import pandas as pd
from typing import Optional, List, Dict, Any
from urllib.parse import urlencode, quote
import json


class ExoplanetAPI:
    """
    Cliente para interagir com a API do NASA Exoplanet Archive.
    
    Suporta tanto a API legada quanto o serviço TAP (Table Access Protocol).
    """
    
    BASE_URL = "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/nstedAPI/nph-nstedAPI"
    TAP_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
    
    FORMATS = {
        'csv': 'csv',
        'json': 'json',
        'xml': 'xml',
        'votable': 'votable',
        'ascii': 'ascii',
        'ipac': 'ipac',
        'tsv': 'tsv',
        'pipe': 'pipe'
    }
    
    TABLES_LEGACY_API = {
        'missionstars': 'Mission Star List',
        'mission_exocat': 'Mission and ExoCat Star List',
    }
    
    TABLES_TAP = {
        'ps': 'Planetary Systems',
        'pscomppars': 'Planetary Systems Composite Parameters',
        'cumulative': 'KOI Cumulative Delivery',
        'q1_q17_dr25_koi': 'KOI Q1-Q17 DR25 Delivery',
        'q1_q17_dr25_sup_koi': 'KOI Q1-Q17 DR25 Supplemental Delivery',
        'q1_q17_dr24_koi': 'KOI Q1-Q17 DR24 Delivery',
        'q1_q16_koi': 'KOI Q1-Q16 Delivery',
        'q1_q12_koi': 'KOI Q1-Q12 Delivery',
        'q1_q8_koi': 'KOI Q1-Q8 Delivery',
        'q1_q6_koi': 'KOI Q1-Q6 Delivery',
        'q1_q17_dr25_tce': 'TCE Q1-Q17 DR25 Delivery',
        'q1_q17_dr24_tce': 'TCE Q1-Q17 DR24 Delivery',
        'q1_q16_tce': 'TCE Q1-Q16 Delivery',
        'q1_q12_tce': 'TCE Q1-Q12 Delivery',
        'keplerstellar': 'Kepler Stellar',
        'q1_q17_dr25_sup_ks': 'Kepler Stellar Supplemental Delivery',
        'q1_q17_dr25_ks': 'Kepler Stellar Q1-Q17 DR25',
        'q1_q17_dr24_ks': 'Kepler Stellar Q1-Q17 DR24',
        'q1_q16_ks': 'Kepler Stellar Q1-Q16',
        'q1_q12_ks': 'Kepler Stellar Q1-Q12',
        'keplertimeseries': 'Kepler Time Series',
        'keplernames': 'Kepler Names',
        'kelttimeseries': 'KELT Time Series',
        'superwasptimeseries': 'SuperWASP Time Series',
        'k2targets': 'K2 Targets',
        'k2pandc': 'K2 Planets and Candidates',
        'k2names': 'K2 Confirmed Names',
    }
    
    def __init__(self):
        """Inicializa o cliente da API."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Cosmos-ExoplanetAPI/1.0'
        })
    
    def build_query_url(self, 
                       table: str,
                       select: Optional[str] = None,
                       where: Optional[str] = None,
                       order: Optional[str] = None,
                       format: str = 'csv',
                       ra: Optional[float] = None,
                       dec: Optional[float] = None,
                       radius: Optional[str] = None) -> str:
        """
        Constrói a URL da query para a API legada.
        
        Args:
            table: Nome da tabela a consultar
            select: Colunas a retornar (separadas por vírgula ou 'count(*)')
            where: Cláusula WHERE para filtrar resultados
            order: Ordem dos resultados (ex: 'dec' ou 'dec desc')
            format: Formato de saída (csv, json, xml, votable, ascii, ipac, tsv, pipe)
            ra: Right Ascension para cone search (graus)
            dec: Declination para cone search (graus)
            radius: Raio para cone search (ex: "1 degree", "30 arcmin", "60 arcsec")
        
        Returns:
            URL completa da query
        """
        params = {'table': table}
        
        if select:
            params['select'] = select
        
        if where:
            params['where'] = where
        
        if order:
            params['order'] = order
        
        if format in self.FORMATS:
            params['format'] = self.FORMATS[format]
        
        if ra is not None and dec is not None and radius is not None:
            params['ra'] = ra
            params['dec'] = dec
            params['radius'] = radius
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.BASE_URL}?{query_string}"
    
    def query(self,
             table: str,
             select: Optional[str] = None,
             where: Optional[str] = None,
             order: Optional[str] = None,
             format: str = 'csv',
             ra: Optional[float] = None,
             dec: Optional[float] = None,
             radius: Optional[str] = None,
             return_dataframe: bool = True) -> Any:
        """
        Executa uma query na API legada do Exoplanet Archive.
        
        Args:
            table: Nome da tabela
            select: Colunas a selecionar
            where: Filtros (cláusula WHERE)
            order: Ordenação
            format: Formato de saída
            ra: Right Ascension (cone search)
            dec: Declination (cone search)
            radius: Raio (cone search)
            return_dataframe: Se True, retorna pandas DataFrame (apenas para CSV)
        
        Returns:
            Dados da query (DataFrame, dict ou texto dependendo do formato)
        """
        url = self.build_query_url(
            table=table,
            select=select,
            where=where,
            order=order,
            format=format,
            ra=ra,
            dec=dec,
            radius=radius
        )
        
        try:
            response = self.session.get(url, timeout=60)
            response.raise_for_status()
            
            if format == 'csv' and return_dataframe:
                from io import StringIO
                return pd.read_csv(StringIO(response.text))
            elif format == 'json':
                return response.json()
            else:
                return response.text
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro na requisição: {e}")
    
    def tap_query(self,
                 query: str,
                 format: str = 'csv',
                 return_dataframe: bool = True) -> Any:
        """
        Executa uma query ADQL no serviço TAP (Table Access Protocol).
        
        O TAP service usa queries ADQL (Astronomical Data Query Language), similar a SQL.
        
        Args:
            query: Query ADQL completa
            format: Formato de saída (csv, json, xml, votable, ipac, tsv)
            return_dataframe: Se True, retorna pandas DataFrame (para CSV/TSV)
        
        Returns:
            Dados da query
        """
        params = {
            'query': query,
            'format': format
        }
        
        try:
            response = self.session.post(self.TAP_URL, data=params, timeout=120)
            response.raise_for_status()
            
            if format in ['csv', 'tsv'] and return_dataframe:
                from io import StringIO
                sep = '\t' if format == 'tsv' else ','
                return pd.read_csv(StringIO(response.text), sep=sep)
            elif format == 'json':
                return response.json()
            else:
                return response.text
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro na requisição TAP: {e}")
    
    def get_confirmed_planets(self,
                             columns: Optional[List[str]] = None,
                             where: Optional[str] = None,
                             limit: int = 100) -> pd.DataFrame:
        """
        Obtém planetas confirmados usando TAP service (tabela ps).
        
        Args:
            columns: Lista de colunas a retornar
            where: Cláusula WHERE para filtrar
            limit: Número máximo de resultados
        
        Returns:
            DataFrame com os planetas
        """
        if columns is None:
            columns = ['pl_name', 'hostname', 'discoverymethod', 'disc_year', 
                      'pl_orbper', 'pl_rade', 'pl_masse', 'sy_dist']
        
        cols_str = ', '.join(columns)
        query = f"SELECT TOP {limit} {cols_str} FROM ps"
        
        if where:
            query += f" WHERE {where}"
        
        return self.tap_query(query)
    
    def get_koi_candidates(self,
                          disposition: str = 'CANDIDATE',
                          period_min: Optional[float] = None,
                          period_max: Optional[float] = None,
                          radius_max: Optional[float] = None,
                          limit: int = 100) -> pd.DataFrame:
        """
        Obtém objetos de interesse do Kepler (KOIs) da tabela cumulative.
        
        Args:
            disposition: CANDIDATE, FALSE POSITIVE, ou CONFIRMED
            period_min: Período orbital mínimo (dias)
            period_max: Período orbital máximo (dias)
            radius_max: Raio máximo do planeta (raios terrestres)
            limit: Número máximo de resultados
        
        Returns:
            DataFrame com os KOIs
        """
        query = f"SELECT TOP {limit} kepoi_name, koi_disposition, koi_period, koi_prad, koi_teq FROM cumulative"
        
        conditions = [f"koi_disposition = '{disposition}'"]
        
        if period_min is not None:
            conditions.append(f"koi_period > {period_min}")
        if period_max is not None:
            conditions.append(f"koi_period < {period_max}")
        if radius_max is not None:
            conditions.append(f"koi_prad < {radius_max}")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY koi_period"
        
        return self.tap_query(query)
    
    def cone_search(self,
                   table: str,
                   ra: float,
                   dec: float,
                   radius: float = 1.0,
                   radius_unit: str = 'degree',
                   columns: Optional[str] = None) -> pd.DataFrame:
        """
        Realiza uma busca cone (cone search) em uma região do céu.
        
        Args:
            table: Nome da tabela
            ra: Right Ascension em graus
            dec: Declination em graus
            radius: Raio da busca
            radius_unit: Unidade do raio (degree, arcmin, arcsec)
            columns: Colunas a retornar (string separada por vírgulas)
        
        Returns:
            DataFrame com os objetos na região
        """
        radius_str = f"{radius} {radius_unit}"
        
        return self.query(
            table=table,
            select=columns,
            ra=ra,
            dec=dec,
            radius=radius_str,
            format='csv',
            return_dataframe=True
        )
    
    def get_column_names(self, table: str, all_columns: bool = True) -> List[str]:
        """
        Obtém nomes das colunas de uma tabela (API legada).
        
        Args:
            table: Nome da tabela
            all_columns: Se True, retorna todas as colunas; se False, apenas as padrão
        
        Returns:
            Lista de nomes das colunas
        """
        column_type = 'getAllColumns' if all_columns else 'getDefaultColumns'
        url = f"{self.BASE_URL}?table={table}&{column_type}&format=json"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list):
                return [col.get('name', '') for col in data]
            
            return []
            
        except Exception as e:
            raise Exception(f"Erro ao obter colunas: {e}")
    
    def count_rows(self, table: str, where: Optional[str] = None) -> int:
        """
        Conta o número de linhas em uma tabela (API legada).
        
        Args:
            table: Nome da tabela
            where: Cláusula WHERE opcional
        
        Returns:
            Número de linhas
        """
        result = self.query(
            table=table,
            select='count(*)',
            where=where,
            format='csv',
            return_dataframe=True
        )
        
        if result is not None and not result.empty:
            return int(result.iloc[0, 0])
        return 0
    
    def search_by_name(self, 
                       planet_name: str,
                       table: str = 'ps') -> pd.DataFrame:
        """
        Busca um planeta pelo nome usando TAP.
        
        Args:
            planet_name: Nome do planeta
            table: Tabela a consultar (padrão: ps)
        
        Returns:
            DataFrame com os dados do planeta
        """
        query = f"SELECT * FROM {table} WHERE pl_name = '{planet_name}'"
        return self.tap_query(query)
    
    def get_planets_by_method(self,
                             method: str,
                             limit: int = 100) -> pd.DataFrame:
        """
        Obtém planetas descobertos por um método específico.
        
        Args:
            method: Método de descoberta (Transit, Radial Velocity, Microlensing, etc.)
            limit: Número máximo de resultados
        
        Returns:
            DataFrame com os planetas
        """
        query = f"""
        SELECT TOP {limit} 
            pl_name, hostname, discoverymethod, disc_year, 
            pl_orbper, pl_rade, pl_masse, sy_dist
        FROM ps 
        WHERE discoverymethod = '{method}'
        ORDER BY disc_year DESC
        """
        return self.tap_query(query)
    
    def get_habitable_zone_candidates(self,
                                     temp_min: float = 180,
                                     temp_max: float = 310,
                                     radius_min: float = 0.5,
                                     radius_max: float = 2.0,
                                     limit: int = 50) -> pd.DataFrame:
        """
        Busca candidatos na zona habitável.
        
        Args:
            temp_min: Temperatura de equilíbrio mínima (K)
            temp_max: Temperatura de equilíbrio máxima (K)
            radius_min: Raio mínimo (raios terrestres)
            radius_max: Raio máximo (raios terrestres)
            limit: Número máximo de resultados
        
        Returns:
            DataFrame com candidatos
        """
        query = f"""
        SELECT TOP {limit}
            pl_name, hostname, pl_rade, pl_eqt, sy_dist, disc_year
        FROM ps
        WHERE pl_eqt BETWEEN {temp_min} AND {temp_max}
        AND pl_rade BETWEEN {radius_min} AND {radius_max}
        ORDER BY sy_dist
        """
        return self.tap_query(query)
    
    def get_pre_generated_query(self, query_type: str) -> str:
        """
        Retorna URLs pré-geradas para queries comuns.
        
        Args:
            query_type: Tipo de query desejada
        
        Returns:
            URL da query
        """
        queries = {
            'all_confirmed_planets_csv': 
                'https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+*+from+ps&format=csv',
            
            'all_confirmed_planets_json': 
                'https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+*+from+pscomppars&format=json',
            
            'stars_hosting_exoplanets': 
                'https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+distinct+hostname+from+ps+order+by+hostname+asc&format=ipac',
            
            'kepler_confirmed_planets': 
                'https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+*+from+ps+where+default_flag+=+1+and+disc_facility+LIKE+\'Kepler\'+order+by+pl_name+asc+&format=votable',
            
            'transiting_planets': 
                'https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+*+from+ps+where+tran_flag=1+and+default_flag=1+order+by+pl_name&format=tsv',
            
            'koi_candidates': 
                'https://exoplanetarchive.ipac.caltech.edu/cgi-bin/nstedAPI/nph-nstedAPI?&table=cumulative&format=ipac&where=koi_disposition+like+\'CANDIDATE\'',
            
            'microlensing_with_photometry': 
                'https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+pl_name,st_nphot+from+pscomppars+where+discoverymethod+like+%27%25Micro%25%27+and+st_nphot%3E0&format=tsv',
            
            'habitable_zone_koi': 
                'https://exoplanetarchive.ipac.caltech.edu/cgi-bin/nstedAPI/nph-nstedAPI?table=cumulative&where=koi_prad<2+and+koi_teq>180+and+koi_teq<303+and+koi_disposition+like+\'CANDIDATE\'',
            
            'tess_planets': 
                'https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+*+from+pscomppars+where+disc_facility+like+%27%25TESS%25%27+order+by+pl_orbper+desc&format=json',
        }
        
        return queries.get(query_type, '')


def quick_planet_search(name: str) -> pd.DataFrame:
    """Busca rápida de planeta por nome."""
    api = ExoplanetAPI()
    return api.search_by_name(name)


def quick_koi_candidates(period_min: float = 300, radius_max: float = 2) -> pd.DataFrame:
    """Busca rápida de KOI candidatos."""
    api = ExoplanetAPI()
    return api.get_koi_candidates(
        disposition='CANDIDATE',
        period_min=period_min,
        radius_max=radius_max
    )


def quick_confirmed_planets(limit: int = 100) -> pd.DataFrame:
    """Busca rápida de planetas confirmados."""
    api = ExoplanetAPI()
    return api.get_confirmed_planets(limit=limit)


def quick_habitable_candidates() -> pd.DataFrame:
    """Busca rápida de candidatos habitáveis."""
    api = ExoplanetAPI()
    return api.get_habitable_zone_candidates()


if __name__ == "__main__":
    print("=" * 80)
    print("TESTANDO EXOPLANET ARCHIVE API")
    print("=" * 80)
    
    api = ExoplanetAPI()
    
    # Teste 1: Buscar 5 planetas confirmados recentes
    print("\n[1/5] Buscando planetas confirmados descobertos após 2020...")
    try:
        planets = api.get_confirmed_planets(where="disc_year > 2020", limit=5)
        print(f"✓ Encontrados {len(planets)} planetas")
        print(planets[['pl_name', 'hostname', 'disc_year', 'discoverymethod']].to_string())
    except Exception as e:
        print(f"✗ Erro: {e}")
    
    # Teste 2: Buscar KOI candidatos
    print("\n[2/5] Buscando KOI candidatos (período > 300 dias, raio < 2 Re)...")
    try:
        kois = api.get_koi_candidates(period_min=300, radius_max=2, limit=5)
        print(f"✓ Encontrados {len(kois)} candidatos")
        print(kois[['kepoi_name', 'koi_period', 'koi_prad', 'koi_teq']].to_string())
    except Exception as e:
        print(f"✗ Erro: {e}")
    
    # Teste 3: Planetas descobertos por trânsito
    print("\n[3/5] Buscando planetas descobertos por Transit...")
    try:
        transit = api.get_planets_by_method('Transit', limit=5)
        print(f"✓ Encontrados {len(transit)} planetas")
        print(transit[['pl_name', 'disc_year', 'pl_orbper']].to_string())
    except Exception as e:
        print(f"✗ Erro: {e}")
    
    # Teste 4: Candidatos na zona habitável
    print("\n[4/5] Buscando candidatos na zona habitável...")
    try:
        habitable = api.get_habitable_zone_candidates(limit=5)
        print(f"✓ Encontrados {len(habitable)} candidatos")
        print(habitable[['pl_name', 'pl_rade', 'pl_eqt', 'sy_dist']].to_string())
    except Exception as e:
        print(f"✗ Erro: {e}")
    
    # Teste 5: Query TAP personalizada
    print("\n[5/5] Query TAP personalizada - Planetas super-Júpiter...")
    try:
        query = """
        SELECT TOP 5 
            pl_name, pl_rade, pl_masse, hostname
        FROM ps 
        WHERE pl_rade > 11
        ORDER BY pl_rade DESC
        """
        large = api.tap_query(query)
        print(f"✓ Encontrados {len(large)} planetas")
        print(large.to_string())
    except Exception as e:
        print(f"✗ Erro: {e}")
    
    print("\n" + "=" * 80)
    print("TESTE CONCLUÍDO")
    print("=" * 80)
    print("\nPara mais informações:")
    print("https://exoplanetarchive.ipac.caltech.edu/docs/program_interfaces.html")

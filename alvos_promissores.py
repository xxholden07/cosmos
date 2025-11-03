"""
Gerador de Alvos Promissores para Descobertas
Identifica estrelas pouco estudadas com maior potencial de novas descobertas
"""

import numpy as np
from astroquery.simbad import Simbad
from astroquery.mast import Catalogs
from astropy.coordinates import SkyCoord
from astropy import units as u
import random

class GeradorAlvosPromissores:
    """Identifica alvos astronômicos promissores para descobertas"""
    
    def __init__(self):
        self.simbad = Simbad()
        self.simbad.add_votable_fields('otype', 'ids')
    
    def gerar_alvos_kepler(self, n_alvos=10):
        """
        Gera lista de alvos promissores do Kepler
        Critérios: Poucos estudos, sem planetas conhecidos, variabilidade potencial
        
        Args:
            n_alvos: Número de alvos a gerar
            
        Returns:
            list: Lista de dicts com informações dos alvos
        """
        alvos = []
        
        # KIC IDs promissores (seleção aleatória de ranges menos estudados)
        # Evitar KICs muito conhecidos (< 1000000)
        kic_ranges = [
            (3000000, 5000000),   # Range médio
            (7000000, 9000000),   # Range alto
            (10000000, 12000000), # Range muito alto (menos estudados)
        ]
        
        for _ in range(n_alvos):
            # Escolher range aleatório
            kic_min, kic_max = random.choice(kic_ranges)
            kic_id = random.randint(kic_min, kic_max)
            
            alvo = {
                'nome': f'KIC {kic_id}',
                'missao': 'Kepler',
                'razao': 'KIC de alto número - estatisticamente menos estudado',
                'prioridade': random.randint(3, 5),
                'dica': 'Use cadência "long" primeiro, depois "short" se detectar algo'
            }
            alvos.append(alvo)
        
        return alvos
    
    def gerar_alvos_tess(self, n_alvos=10):
        """
        Gera lista de alvos promissores do TESS
        
        Args:
            n_alvos: Número de alvos a gerar
            
        Returns:
            list: Lista de alvos TESS
        """
        alvos = []
        
        # TIC IDs promissores
        tic_ranges = [
            (100000000, 300000000),  # Range médio
            (400000000, 600000000),  # Range alto
        ]
        
        for _ in range(n_alvos):
            tic_min, tic_max = random.choice(tic_ranges)
            tic_id = random.randint(tic_min, tic_max)
            
            alvo = {
                'nome': f'TIC {tic_id}',
                'missao': 'TESS',
                'razao': 'TIC de alto número - potencialmente pouco estudado',
                'prioridade': random.randint(3, 5),
                'dica': 'TESS tem dados mais recentes - maior chance de descobertas não publicadas ainda'
            }
            alvos.append(alvo)
        
        return alvos
    
    def gerar_alvos_variaveis_suspeitas(self):
        """
        Gera alvos baseados em estrelas com suspeita de variabilidade
        mas poucas confirmações
        
        Returns:
            list: Alvos promissores
        """
        alvos = [
            {
                'nome': 'KIC 8462852',
                'missao': 'Kepler',
                'razao': 'Estrela de Tabby - variabilidade extrema e misteriosa',
                'prioridade': 5,
                'dica': 'Uma das estrelas mais estranhas conhecidas. Continue monitorando!'
            },
            {
                'nome': 'KIC 9832227',
                'missao': 'Kepler',
                'razao': 'Candidata a fusão estelar - sistema binário eclipsante',
                'prioridade': 5,
                'dica': 'Período orbital diminuindo. Pode ser evento único!'
            },
            {
                'nome': 'KIC 12557548',
                'missao': 'Kepler',
                'razao': 'Planeta evaporando - trânsitos variáveis',
                'prioridade': 4,
                'dica': 'Planeta em desintegração. Padrões de trânsito únicos.'
            },
        ]
        
        return alvos
    
    def gerar_alvos_por_tipo_estelar(self, tipo='M', n_alvos=5):
        """
        Gera alvos de um tipo estelar específico
        
        Args:
            tipo: Tipo estelar ('M', 'K', 'G', etc.)
            n_alvos: Número de alvos
            
        Returns:
            list: Alvos do tipo especificado
        """
        razoes_por_tipo = {
            'M': 'Anãs M são mais comuns e têm muitos planetas terrestres',
            'K': 'Anãs K são ideais - zona habitável maior, mais estáveis que M',
            'G': 'Tipo solar - importante para comparação com nosso sistema',
            'F': 'Estrelas F evoluem mais rápido - podem ter fenômenos únicos',
            'A': 'Estrelas A têm debris disks - possíveis sistemas planetários jovens'
        }
        
        alvos = []
        
        # Gerar alvos aleatórios deste tipo
        for i in range(n_alvos):
            kic_id = random.randint(5000000, 12000000)
            
            alvo = {
                'nome': f'KIC {kic_id}',
                'missao': 'Kepler',
                'tipo_esperado': f'{tipo}V',
                'razao': razoes_por_tipo.get(tipo, 'Tipo estelar interessante'),
                'prioridade': 3,
                'dica': f'Busque por estrelas tipo {tipo} - {razoes_por_tipo.get(tipo, "")}'
            }
            alvos.append(alvo)
        
        return alvos
    
    def gerar_coordenadas_aleatorias_kepler(self, n_alvos=5):
        """
        Gera coordenadas aleatórias dentro do campo do Kepler
        Para exploração de regiões menos estudadas
        
        Returns:
            list: Alvos com coordenadas
        """
        # Campo do Kepler: RA ~290-297°, Dec ~40-50°
        alvos = []
        
        for i in range(n_alvos):
            ra = random.uniform(290, 297)
            dec = random.uniform(40, 50)
            
            # Converter para sexagesimal
            coord = SkyCoord(ra=ra*u.degree, dec=dec*u.degree, frame='icrs')
            ra_str = coord.ra.to_string(unit=u.hour, sep=':', precision=2)
            dec_str = coord.dec.to_string(unit=u.degree, sep=':', precision=2)
            
            alvo = {
                'nome': f'Coord_{i+1}',
                'coordenadas': f'{ra_str} {dec_str}',
                'ra': ra,
                'dec': dec,
                'missao': 'Kepler',
                'razao': 'Coordenadas aleatórias no campo Kepler - região pouco explorada',
                'prioridade': 4,
                'dica': 'Use estas coordenadas diretamente na busca'
            }
            alvos.append(alvo)
        
        return alvos
    
    def gerar_lista_completa(self, incluir_tess=True):
        """
        Gera lista completa e diversificada de alvos promissores
        
        Args:
            incluir_tess: Se True, inclui alvos TESS
            
        Returns:
            dict: Alvos categorizados
        """
        alvos_completos = {
            'alta_prioridade': [],
            'variaveis_suspeitas': [],
            'kepler_aleatorios': [],
            'tess_aleatorios': [],
            'por_tipo_estelar': {},
            'coordenadas': []
        }
        
        # Alta prioridade
        alvos_completos['alta_prioridade'] = [
            {
                'nome': 'KIC 8462852',
                'missao': 'Kepler',
                'razao': '🌟 Estrela de Tabby - A mais misteriosa conhecida',
                'prioridade': 5,
                'dica': 'Variações de até 22% no brilho!'
            },
            {
                'nome': 'TIC 400799224',
                'missao': 'TESS',
                'razao': '🪐 Candidata a planeta em desintegração',
                'prioridade': 5,
                'dica': 'Trânsitos irregulares - possível descoberta única'
            },
        ]
        
        # Variáveis suspeitas
        alvos_completos['variaveis_suspeitas'] = self.gerar_alvos_variaveis_suspeitas()
        
        # Kepler aleatórios
        alvos_completos['kepler_aleatorios'] = self.gerar_alvos_kepler(15)
        
        # TESS aleatórios
        if incluir_tess:
            alvos_completos['tess_aleatorios'] = self.gerar_alvos_tess(15)
        
        # Por tipo estelar
        for tipo in ['M', 'K', 'G']:
            alvos_completos['por_tipo_estelar'][tipo] = self.gerar_alvos_por_tipo_estelar(tipo, 5)
        
        # Coordenadas aleatórias
        alvos_completos['coordenadas'] = self.gerar_coordenadas_aleatorias_kepler(10)
        
        return alvos_completos


# Função auxiliar
def obter_alvos_recomendados(categoria='todos', missao='Kepler'):
    """
    Obtém alvos recomendados para análise
    
    Args:
        categoria: 'alta_prioridade', 'aleatorios', 'variaveis', 'todos'
        missao: 'Kepler', 'TESS', 'ambos'
        
    Returns:
        list: Lista de alvos recomendados
    """
    gerador = GeradorAlvosPromissores()
    
    if categoria == 'alta_prioridade':
        return gerador.gerar_alvos_variaveis_suspeitas()
    elif categoria == 'aleatorios':
        if missao == 'Kepler':
            return gerador.gerar_alvos_kepler(20)
        elif missao == 'TESS':
            return gerador.gerar_alvos_tess(20)
        else:
            return gerador.gerar_alvos_kepler(10) + gerador.gerar_alvos_tess(10)
    elif categoria == 'todos':
        return gerador.gerar_lista_completa(incluir_tess=(missao != 'Kepler'))
    else:
        return gerador.gerar_alvos_kepler(10)

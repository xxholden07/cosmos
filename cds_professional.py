"""
Integração Profissional com CDS (Centre de Données astronomiques de Strasbourg)
Usa bibliotecas oficiais: astroquery.simbad, astroquery.vizier
"""

from astroquery.simbad import Simbad
from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
from astropy import units as u
import numpy as np

class CDSProfessionalChecker:
    """Verificador profissional usando APIs oficiais da CDS"""
    
    def __init__(self, radius_arcsec=120):  # 2 arcmin = 120 arcsec
        """
        Inicializa verificador CDS profissional
        
        Args:
            radius_arcsec: Raio de busca em arcsegundos (padrão: 120 = 2 arcmin)
        """
        self.radius = radius_arcsec * u.arcsec
        
        # Configurar SIMBAD com campos adicionais
        self.simbad = Simbad()
        self.simbad.add_votable_fields('otype', 'flux(V)', 'sp', 'ids')
        
        # Configurar VizieR
        self.vizier = Vizier(columns=['*', '+_r'], row_limit=50)
    
    def verificar_simbad_completo(self, ra, dec):
        """
        Verificação completa no SIMBAD usando astroquery oficial
        
        Args:
            ra: Ascensão Reta em graus
            dec: Declinação em graus
            
        Returns:
            dict com resultados detalhados
        """
        try:
            coord = SkyCoord(ra=ra*u.degree, dec=dec*u.degree, frame='icrs')
            result_table = self.simbad.query_region(coord, radius=self.radius)
            
            if result_table is None or len(result_table) == 0:
                return {
                    'encontrado': False,
                    'total_objetos': 0,
                    'objetos': [],
                    'status': 'POTENCIAL_NOVA',
                    'coord_busca': f"{ra:.6f}, {dec:.6f}"
                }
            
            objetos = []
            for row in result_table:
                obj_coord = SkyCoord(ra=row['RA'], dec=row['DEC'], unit=(u.hourangle, u.deg))
                separacao = coord.separation(obj_coord)
                
                try:
                    bibcodes = self.simbad.query_bibobj(row['MAIN_ID'])
                    n_refs = len(bibcodes) if bibcodes is not None else 0
                except:
                    n_refs = 0
                
                objeto = {
                    'nome': str(row['MAIN_ID']),
                    'tipo': str(row['OTYPE']) if 'OTYPE' in row.colnames else 'Unknown',
                    'ra': obj_coord.ra.deg,
                    'dec': obj_coord.dec.deg,
                    'separacao_arcsec': separacao.arcsec,
                    'mag_v': float(row['FLUX_V']) if row['FLUX_V'] and not np.ma.is_masked(row['FLUX_V']) else None,
                    'tipo_espectral': str(row['SP_TYPE']) if 'SP_TYPE' in row.colnames and row['SP_TYPE'] else None,
                    'referencias': n_refs,
                    'identificadores': str(row['IDS']) if 'IDS' in row.colnames else row['MAIN_ID']
                }
                objetos.append(objeto)
            
            objetos.sort(key=lambda x: x['separacao_arcsec'])
            
            if len(objetos) > 0:
                obj_mais_proximo = objetos[0]
                if obj_mais_proximo['separacao_arcsec'] < 5:
                    status = 'CONHECIDA'
                elif obj_mais_proximo['separacao_arcsec'] < 30:
                    status = 'CANDIDATA'
                else:
                    status = 'CAMPO_ESTELAR'
            else:
                status = 'POTENCIAL_NOVA'
            
            return {
                'encontrado': True,
                'total_objetos': len(objetos),
                'objetos': objetos,
                'objeto_principal': objetos[0] if objetos else None,
                'status': status,
                'coord_busca': f"{ra:.6f}, {dec:.6f}"
            }
            
        except Exception as e:
            return {
                'encontrado': False,
                'total_objetos': 0,
                'objetos': [],
                'status': 'ERRO',
                'erro': str(e),
                'coord_busca': f"{ra:.6f}, {dec:.6f}"
            }
    
    def verificar_exoplanetas(self, ra, dec):
        """Verifica se há exoplanetas conhecidos nas coordenadas"""
        try:
            coord = SkyCoord(ra=ra*u.degree, dec=dec*u.degree, frame='icrs')
            catalogos_exoplanetas = ['B/exopl', 'V/150', 'J/ApJS/197/8']
            planetas_encontrados = []
            
            for catalogo in catalogos_exoplanetas:
                try:
                    result = self.vizier.query_region(coord, radius=self.radius, catalog=catalogo)
                    if result and len(result) > 0:
                        for table in result:
                            for row in table:
                                planetas_encontrados.append({'catalogo': catalogo, 'dados': dict(row)})
                except:
                    continue
            
            return {
                'encontrado': len(planetas_encontrados) > 0,
                'total_planetas': len(planetas_encontrados),
                'planetas': planetas_encontrados
            }
        except Exception as e:
            return {'encontrado': False, 'total_planetas': 0, 'planetas': [], 'erro': str(e)}
    
    def verificar_variaveis(self, ra, dec):
        """Verifica se há estrelas variáveis conhecidas"""
        try:
            coord = SkyCoord(ra=ra*u.degree, dec=dec*u.degree, frame='icrs')
            result = self.vizier.query_region(coord, radius=self.radius, catalog='B/vsx')
            
            if not result or len(result) == 0:
                return {'encontrado': False, 'total_variaveis': 0, 'variaveis': []}
            
            variaveis = []
            for table in result:
                for row in table:
                    variavel = {
                        'nome': str(row['Name']) if 'Name' in row.colnames else 'Unknown',
                        'tipo': str(row['Type']) if 'Type' in row.colnames else 'Unknown',
                        'periodo': float(row['Period']) if 'Period' in row.colnames and not np.ma.is_masked(row['Period']) else None,
                        'max_mag': float(row['max']) if 'max' in row.colnames and not np.ma.is_masked(row['max']) else None,
                        'min_mag': float(row['min']) if 'min' in row.colnames and not np.ma.is_masked(row['min']) else None,
                    }
                    variaveis.append(variavel)
            
            return {'encontrado': True, 'total_variaveis': len(variaveis), 'variaveis': variaveis}
        except Exception as e:
            return {'encontrado': False, 'total_variaveis': 0, 'variaveis': [], 'erro': str(e)}
    
    def verificar_transientes(self, ra, dec):
        """Verifica transientes conhecidos"""
        try:
            coord = SkyCoord(ra=ra*u.degree, dec=dec*u.degree, frame='icrs')
            catalogos = ['VII/282', 'B/sn']
            transientes = []
            
            for catalogo in catalogos:
                try:
                    result = self.vizier.query_region(coord, radius=self.radius, catalog=catalogo)
                    if result and len(result) > 0:
                        for table in result:
                            for row in table:
                                transientes.append({'catalogo': catalogo, 'dados': dict(row)})
                except:
                    continue
            
            return {
                'encontrado': len(transientes) > 0,
                'total_transientes': len(transientes),
                'transientes': transientes
            }
        except Exception as e:
            return {'encontrado': False, 'total_transientes': 0, 'transientes': [], 'erro': str(e)}
    
    def verificacao_completa(self, ra, dec, tipo_deteccao='all'):
        """Verificação completa em múltiplos catálogos"""
        resultado = {
            'coordenadas': {'ra': ra, 'dec': dec},
            'simbad': None,
            'exoplanetas': None,
            'variaveis': None,
            'transientes': None,
            'classificacao_final': None
        }
        
        print("Verificando SIMBAD...")
        resultado['simbad'] = self.verificar_simbad_completo(ra, dec)
        
        if tipo_deteccao in ['planeta', 'all']:
            print("Verificando catálogos de exoplanetas...")
            resultado['exoplanetas'] = self.verificar_exoplanetas(ra, dec)
        
        if tipo_deteccao in ['variavel', 'cometa', 'all']:
            print("Verificando catálogo de estrelas variáveis...")
            resultado['variaveis'] = self.verificar_variaveis(ra, dec)
        
        if tipo_deteccao in ['transiente', 'supernova', 'all']:
            print("Verificando catálogos de transientes...")
            resultado['transientes'] = self.verificar_transientes(ra, dec)
        
        resultado['classificacao_final'] = self._classificar_resultado(resultado)
        
        return resultado
    
    def _classificar_resultado(self, resultado):
        """Classificação final baseada em todos os resultados - RIGOROSA"""
        
        status_simbad = resultado['simbad']['status']
        total_objetos_simbad = resultado['simbad']['total_objetos']
        obj_principal = resultado['simbad'].get('objeto_principal')
        
        # Verificar se há planetas conhecidos
        tem_planetas_conhecidos = (resultado['exoplanetas'] and 
                                   resultado['exoplanetas']['encontrado'] and 
                                   resultado['exoplanetas']['total_planetas'] > 0)
        
        # Verificar se há variáveis conhecidas
        tem_variaveis_conhecidas = (resultado['variaveis'] and 
                                     resultado['variaveis']['encontrado'] and 
                                     resultado['variaveis']['total_variaveis'] > 0)
        
        # Verificar se há transientes conhecidos
        tem_transientes_conhecidos = (resultado['transientes'] and 
                                       resultado['transientes']['encontrado'] and 
                                       resultado['transientes']['total_transientes'] > 0)
        
        # CASO 1: Nenhum objeto encontrado em NENHUM catálogo (DESCOBERTA REAL!)
        if (total_objetos_simbad == 0 and 
            not tem_planetas_conhecidos and 
            not tem_variaveis_conhecidas and 
            not tem_transientes_conhecidos):
            
            return {
                'status': 'DESCOBERTA_POTENCIAL',
                'prioridade': 5,
                'mensagem': '🚨 DESCOBERTA POTENCIAL! Nenhum objeto encontrado em SIMBAD, VizieR, catálogos de exoplanetas, variáveis ou transientes.',
                'recomendacao': 'AÇÃO IMEDIATA: (1) Verifique manualmente no SIMBAD, (2) Faça mais 2-3 observações, (3) Considere reportar se confirmar.'
            }
        
        # CASO 2: Objeto MUITO próximo no SIMBAD (< 5 arcsec) = Mesmo objeto
        if obj_principal and obj_principal['separacao_arcsec'] < 5:
            obj_nome = obj_principal['nome']
            obj_tipo = obj_principal['tipo']
            obj_refs = obj_principal['referencias']
            
            # Sub-caso 2.1: É um planeta conhecido
            if tem_planetas_conhecidos:
                return {
                    'status': 'PLANETA_CONHECIDO',
                    'prioridade': 1,
                    'mensagem': f"✅ Sistema planetário CONHECIDO: {obj_nome} ({obj_refs} referências científicas)",
                    'recomendacao': f'Este planeta já foi descoberto e estudado. Sua detecção VALIDA que o sistema está funcionando corretamente!'
                }
            
            # Sub-caso 2.2: É uma variável conhecida
            if tem_variaveis_conhecidas:
                tipo_variavel = resultado['variaveis']['variaveis'][0]['tipo'] if resultado['variaveis']['variaveis'] else 'desconhecido'
                return {
                    'status': 'VARIAVEL_CONHECIDA',
                    'prioridade': 1,
                    'mensagem': f"✅ Estrela VARIÁVEL CONHECIDA: {obj_nome} (Tipo: {tipo_variavel}, {obj_refs} refs)",
                    'recomendacao': 'Variabilidade já catalogada. Sua detecção confirma os dados publicados.'
                }
            
            # Sub-caso 2.3: Objeto conhecido mas SEM planeta/variável catalogado
            if obj_refs > 50:
                return {
                    'status': 'OBJETO_BEM_ESTUDADO',
                    'prioridade': 2,
                    'mensagem': f"⚪ Objeto BEM ESTUDADO: {obj_nome} ({obj_tipo}, {obj_refs} papers publicados)",
                    'recomendacao': 'Objeto muito estudado. Se detectou algo novo (planeta/variabilidade), pode ser descoberta SECUNDÁRIA interessante!'
                }
            elif obj_refs > 10:
                return {
                    'status': 'OBJETO_CONHECIDO',
                    'prioridade': 2,
                    'mensagem': f"⚪ Objeto CONHECIDO: {obj_nome} ({obj_tipo}, {obj_refs} referências)",
                    'recomendacao': 'Objeto catalogado mas moderadamente estudado. Características detectadas podem ser novas!'
                }
            else:
                return {
                    'status': 'CANDIDATA_FORTE',
                    'prioridade': 4,
                    'mensagem': f"🟡 Objeto POUCO ESTUDADO: {obj_nome} ({obj_refs} referências apenas)",
                    'recomendacao': 'Objeto existe mas com poucos estudos. Alta chance de descobrir características novas!'
                }
        
        # CASO 3: Objeto moderadamente próximo (5-30 arcsec) = Pode ser mesmo objeto ou campo
        if obj_principal and 5 <= obj_principal['separacao_arcsec'] < 30:
            return {
                'status': 'CANDIDATA',
                'prioridade': 3,
                'mensagem': f"🟡 Objeto a {obj_principal['separacao_arcsec']:.1f} arcsec - Pode ser o mesmo ou campo estelar",
                'recomendacao': 'Distância moderada. Verifique astrometria. Pode ser companheira ou objeto novo no campo.'
            }
        
        # CASO 4: Objeto distante (30-120 arcsec) = Campo estelar
        if obj_principal and 30 <= obj_principal['separacao_arcsec'] < 120:
            return {
                'status': 'CAMPO_ESTELAR',
                'prioridade': 4,
                'mensagem': f"🟢 Objeto mais próximo a {obj_principal['separacao_arcsec']:.1f} arcsec - Distante do alvo",
                'recomendacao': 'Objeto no campo estelar mas distante. Sua detecção pode ser algo NOVO! Continue monitorando.'
            }
        
        # CASO 5: Apenas objetos muito distantes encontrados
        if total_objetos_simbad > 0 and (not obj_principal or obj_principal['separacao_arcsec'] >= 120):
            return {
                'status': 'CANDIDATA_FORTE',
                'prioridade': 4,
                'mensagem': f"🟢 {total_objetos_simbad} objetos no campo mas TODOS muito distantes (>120 arcsec)",
                'recomendacao': 'Nenhum objeto próximo conhecido. Alta probabilidade de descoberta nova!'
            }
        
        # CASO PADRÃO: Situação ambígua
        return {
            'status': 'ANALISAR_MANUALMENTE',
            'prioridade': 3,
            'mensagem': 'Situação ambígua - análise manual recomendada',
            'recomendacao': 'Verifique manualmente os resultados. Consulte especialista se necessário.'
        }
    
    def gerar_relatorio_profissional(self, resultado):
        """Gera relatório profissional completo"""
        relatorio = "## 📊 Relatório de Verificação Profissional CDS\n\n"
        
        coord = resultado['coordenadas']
        relatorio += f"**Coordenadas:** RA={coord['ra']:.6f}°, Dec={coord['dec']:.6f}°\n\n"
        
        classificacao = resultado['classificacao_final']
        relatorio += f"### Status: {classificacao['status']}\n"
        relatorio += f"**Prioridade:** {classificacao['prioridade']}/5\n\n"
        relatorio += f"**{classificacao['mensagem']}**\n\n"
        relatorio += f"*Recomendação:* {classificacao['recomendacao']}\n\n"
        
        simbad = resultado['simbad']
        relatorio += "---\n### 🔍 SIMBAD\n"
        relatorio += f"**Objetos encontrados:** {simbad['total_objetos']}\n\n"
        
        if simbad['total_objetos'] > 0:
            obj = simbad['objeto_principal']
            relatorio += "**Objeto mais próximo:**\n"
            relatorio += f"- Nome: {obj['nome']}\n"
            relatorio += f"- Tipo: {obj['tipo']}\n"
            relatorio += f"- Separação: {obj['separacao_arcsec']:.2f} arcsec\n"
            relatorio += f"- Mag V: {obj['mag_v'] if obj['mag_v'] else 'N/A'}\n"
            relatorio += f"- Tipo Espectral: {obj['tipo_espectral'] if obj['tipo_espectral'] else 'N/A'}\n"
            relatorio += f"- Referências: {obj['referencias']}\n\n"
        
        if resultado['exoplanetas']:
            exo = resultado['exoplanetas']
            relatorio += "---\n### 🪐 Exoplanetas\n"
            relatorio += f"**Planetas conhecidos:** {exo['total_planetas']}\n\n"
            if exo['total_planetas'] > 0:
                relatorio += "Este sistema planetário já é conhecido.\n\n"
        
        if resultado['variaveis']:
            var = resultado['variaveis']
            relatorio += "---\n### ⭐ Estrelas Variáveis\n"
            relatorio += f"**Variáveis conhecidas:** {var['total_variaveis']}\n\n"
            if var['total_variaveis'] > 0:
                for v in var['variaveis'][:3]:
                    relatorio += f"- {v['nome']}: Tipo {v['tipo']}"
                    if v['periodo']:
                        relatorio += f", Período={v['periodo']:.2f}d"
                    relatorio += "\n"
                relatorio += "\n"
        
        if resultado['transientes']:
            trans = resultado['transientes']
            relatorio += "---\n### 💥 Transientes\n"
            relatorio += f"**Transientes conhecidos:** {trans['total_transientes']}\n\n"
        
        return relatorio

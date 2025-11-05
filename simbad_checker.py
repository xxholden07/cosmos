"""
Módulo para verificação automática de objetos no SIMBAD
Identifica se detecções são conhecidas ou potencialmente novas
"""

import requests
from urllib.parse import quote
import time

class SimbadChecker:
    """Verifica objetos astronômicos no banco de dados SIMBAD"""
    
    def __init__(self, radius_arcmin=2.0):
        """
        Inicializa verificador SIMBAD
        
        Args:
            radius_arcmin: Raio de busca em arcminutos (padrão: 2.0)
        """
        self.base_url = "https://simbad.u-strasbg.fr/simbad/sim-coo"
        self.radius = radius_arcmin
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Cosmic-Analyzer/1.0 (Educational Research)'
        })
    
    def verificar_coordenadas(self, ra, dec, timeout=10):
        """
        Verifica se há objetos conhecidos nas coordenadas especificadas
        
        Args:
            ra: Ascensão Reta em graus decimais
            dec: Declinação em graus decimais
            timeout: Timeout da requisição em segundos
            
        Returns:
            dict com informações sobre objetos encontrados:
            {
                'encontrado': bool,
                'total_objetos': int,
                'objeto_principal': dict ou None,
                'todos_objetos': list,
                'url_busca': str,
                'status': str  # 'CONHECIDA', 'POTENCIAL_NOVA', 'ERRO'
            }
        """
        try:
            # Construir URL de busca
            params = {
                'Coord': f"{ra:.6f} {dec:.6f}",
                'Radius': str(self.radius),
                'output.format': 'ASCII',
                'frame': 'ICRS',
                'epoch': 'J2000'
            }
            
            # URL para visualização humana
            url_visual = f"{self.base_url}?Coord={ra}+{dec}&Radius={self.radius}"
            
            # Fazer requisição
            response = self.session.get(
                self.base_url,
                params=params,
                timeout=timeout
            )
            
            if response.status_code != 200:
                return {
                    'encontrado': False,
                    'total_objetos': 0,
                    'objeto_principal': None,
                    'todos_objetos': [],
                    'url_busca': url_visual,
                    'status': 'ERRO',
                    'erro': f'HTTP {response.status_code}'
                }
            
            # Parsear resposta
            texto = response.text
            
            # Verificar se encontrou objetos
            if 'Number of rows : 0' in texto or 'No astronomical object found' in texto:
                return {
                    'encontrado': False,
                    'total_objetos': 0,
                    'objeto_principal': None,
                    'todos_objetos': [],
                    'url_busca': url_visual,
                    'status': 'POTENCIAL_NOVA'
                }
            
            # Extrair número de objetos
            total = self._extrair_total_objetos(texto)
            
            # Extrair objetos
            objetos = self._parsear_objetos(texto)
            
            # Determinar status
            if total == 0:
                status = 'POTENCIAL_NOVA'
            else:
                # Verificar se há objeto muito próximo (< 5 arcsec)
                objeto_proximo = any(obj.get('distancia_arcsec', 999) < 5 for obj in objetos)
                
                if objeto_proximo:
                    status = 'CONHECIDA'
                else:
                    # Objetos distantes podem ser campo, não o alvo
                    status = 'CANDIDATA'  # Precisa verificação manual
            
            return {
                'encontrado': total > 0,
                'total_objetos': total,
                'objeto_principal': objetos[0] if objetos else None,
                'todos_objetos': objetos,
                'url_busca': url_visual,
                'status': status
            }
            
        except requests.Timeout:
            return {
                'encontrado': False,
                'total_objetos': 0,
                'objeto_principal': None,
                'todos_objetos': [],
                'url_busca': url_visual if 'url_visual' in locals() else '',
                'status': 'ERRO',
                'erro': 'Timeout na conexão com SIMBAD'
            }
        except Exception as e:
            return {
                'encontrado': False,
                'total_objetos': 0,
                'objeto_principal': None,
                'todos_objetos': [],
                'url_busca': url_visual if 'url_visual' in locals() else '',
                'status': 'ERRO',
                'erro': str(e)
            }
    
    def _extrair_total_objetos(self, texto):
        """Extrai número total de objetos da resposta"""
        try:
            if 'Number of rows :' in texto:
                linha = [l for l in texto.split('\n') if 'Number of rows :' in l][0]
                # Extrair número entre ':' e próximo espaço/tab
                num_str = linha.split(':')[1].strip().split()[0]
                return int(num_str)
        except:
            pass
        return 0
    
    def _parsear_objetos(self, texto):
        """
        Parseia objetos da resposta ASCII do SIMBAD
        
        Formato esperado:
        N  Identifier  dist(asec)  Otype  RA  DEC  ...
        """
        objetos = []
        
        try:
            linhas = texto.split('\n')
            
            # Encontrar linha de cabeçalho
            idx_cabecalho = -1
            for i, linha in enumerate(linhas):
                if 'Identifier' in linha and 'dist' in linha:
                    idx_cabecalho = i
                    break
            
            if idx_cabecalho == -1:
                return objetos
            
            # Processar linhas de dados
            for linha in linhas[idx_cabecalho + 1:]:
                linha = linha.strip()
                
                # Pular linhas vazias ou não numéricas no início
                if not linha or not linha[0].isdigit():
                    continue
                
                # Tentar parsear linha
                try:
                    partes = linha.split('\t')
                    if len(partes) < 4:
                        continue
                    
                    # Extrair campos principais
                    numero = partes[0].strip()
                    identificador = partes[1].strip() if len(partes) > 1 else ''
                    distancia = partes[2].strip() if len(partes) > 2 else ''
                    tipo = partes[3].strip() if len(partes) > 3 else ''
                    
                    # Converter distância para float
                    try:
                        dist_arcsec = float(distancia)
                    except:
                        dist_arcsec = 999.0
                    
                    # Extrair referências (#ref)
                    referencias = 0
                    for parte in partes:
                        if parte.strip().isdigit() and len(parte.strip()) < 5:
                            try:
                                referencias = int(parte.strip())
                            except:
                                pass
                    
                    objeto = {
                        'numero': numero,
                        'identificador': identificador,
                        'distancia_arcsec': dist_arcsec,
                        'tipo': tipo,
                        'referencias': referencias
                    }
                    
                    objetos.append(objeto)
                    
                except Exception as e:
                    continue
            
        except Exception as e:
            pass
        
        return objetos
    
    def verificar_nome(self, nome_objeto, timeout=10):
        """
        Verifica se objeto existe no SIMBAD por nome
        
        Args:
            nome_objeto: Nome do objeto (ex: "Kepler-10")
            timeout: Timeout da requisição
            
        Returns:
            dict com informações do objeto
        """
        try:
            url = "https://simbad.u-strasbg.fr/simbad/sim-id"
            params = {
                'Ident': nome_objeto,
                'output.format': 'ASCII'
            }
            
            response = self.session.get(url, params=params, timeout=timeout)
            
            if response.status_code != 200:
                return {'encontrado': False, 'erro': f'HTTP {response.status_code}'}
            
            texto = response.text
            
            if 'not found' in texto.lower() or 'no astronomical object' in texto.lower():
                return {'encontrado': False, 'status': 'NAO_ENCONTRADO'}
            
            return {'encontrado': True, 'status': 'ENCONTRADO', 'dados': texto}
            
        except Exception as e:
            return {'encontrado': False, 'erro': str(e)}
    
    def classificar_descoberta(self, resultado_simbad, confianca_deteccao):
        """
        Classifica uma detecção baseado nos resultados do SIMBAD
        
        Args:
            resultado_simbad: Resultado da verificação SIMBAD
            confianca_deteccao: Confiança da detecção (0-100)
            
        Returns:
            dict com classificação final:
            {
                'status': str,  # NOVA, CONHECIDA, CANDIDATA, ANALISAR
                'prioridade': int,  # 1-5 (5 = máxima)
                'recomendacao': str
            }
        """
        status_simbad = resultado_simbad.get('status', 'ERRO')
        total_objetos = resultado_simbad.get('total_objetos', 0)
        objeto_principal = resultado_simbad.get('objeto_principal')
        
        # Caso 1: ERRO na verificação
        if status_simbad == 'ERRO':
            return {
                'status': 'ANALISAR',
                'prioridade': 2,
                'recomendacao': 'Erro ao verificar SIMBAD. Verifique manualmente ou tente novamente.'
            }
        
        # Caso 2: Nenhum objeto encontrado - DESCOBERTA POTENCIAL!
        if status_simbad == 'POTENCIAL_NOVA' or total_objetos == 0:
            if confianca_deteccao > 85:
                return {
                    'status': 'NOVA',
                    'prioridade': 5,
                    'recomendacao': '🚨 DESCOBERTA POTENCIAL! Nenhum objeto no SIMBAD. (1) Verifique com modo Profissional, (2) Faça 2+ observações, (3) Considere reportar.'
                }
            elif confianca_deteccao > 70:
                return {
                    'status': 'CANDIDATA',
                    'prioridade': 4,
                    'recomendacao': 'Nenhum objeto conhecido. Aumente confiança com mais observações antes de declarar descoberta.'
                }
            else:
                return {
                    'status': 'ANALISAR',
                    'prioridade': 3,
                    'recomendacao': 'Detecção com baixa confiança. Observe novamente antes de confirmar.'
                }
        
        # Caso 3: Objeto conhecido MUITO próximo (< 5 arcsec) = Mesmo objeto
        if status_simbad == 'CONHECIDA':
            if objeto_principal:
                nome = objeto_principal.get('identificador', 'desconhecido')
                tipo = objeto_principal.get('tipo', 'desconhecido')
                refs = objeto_principal.get('referencias', 0)
                dist = objeto_principal.get('distancia_arcsec', 0)
                
                # Muito próximo = definitivamente o mesmo objeto
                if dist < 5:
                    if refs > 50:
                        return {
                            'status': 'CONHECIDA',
                            'prioridade': 1,
                            'recomendacao': f'✅ Objeto BEM ESTUDADO: {nome} ({refs} refs). Detecção valida sistema, mas não é descoberta nova.'
                        }
                    elif refs > 10:
                        return {
                            'status': 'CONHECIDA',
                            'prioridade': 2,
                            'recomendacao': f'✅ Objeto CONHECIDO: {nome} ({refs} refs). Se detectou característica nova, pode ser interessante!'
                        }
                    else:
                        return {
                            'status': 'CANDIDATA',
                            'prioridade': 3,
                            'recomendacao': f'🟡 Objeto POUCO ESTUDADO: {nome} ({refs} refs). Características detectadas podem ser novas!'
                        }
                # Moderadamente próximo (5-30 arcsec) = Incerto
                elif 5 <= dist < 30:
                    return {
                        'status': 'CANDIDATA',
                        'prioridade': 3,
                        'recomendacao': f'🟡 Objeto a {dist:.1f}" - Pode ser mesmo objeto ou campo. Verifique astrometria.'
                    }
                # Distante (>30 arcsec) = Provavelmente campo
                else:
                    return {
                        'status': 'CANDIDATA',
                        'prioridade': 4,
                        'recomendacao': f'🟢 Objeto mais próximo a {dist:.1f}" (distante). Sua detecção pode ser nova!'
                    }
        
        # Caso 4: Objetos no campo mas não muito próximos
        if status_simbad == 'CANDIDATA':
            return {
                'status': 'CANDIDATA',
                'prioridade': 4,
                'recomendacao': f'🟡 {total_objetos} objetos no campo mas não muito próximos. Pode ser companheira ou evento novo.'
            }
        
        # Caso padrão
        return {
            'status': 'ANALISAR',
            'prioridade': 2,
            'recomendacao': 'Verificação manual necessária.'
        }
    
    def gerar_relatorio(self, resultado_simbad):
        """
        Gera relatório formatado dos resultados SIMBAD
        
        Args:
            resultado_simbad: Resultado da verificação
            
        Returns:
            str: Relatório formatado em markdown
        """
        status = resultado_simbad.get('status', 'DESCONHECIDO')
        total = resultado_simbad.get('total_objetos', 0)
        url = resultado_simbad.get('url_busca', '')
        
        relatorio = f"### Verificação SIMBAD\n\n"
        relatorio += f"**Status:** {status}\n\n"
        relatorio += f"**Objetos encontrados:** {total}\n\n"
        
        if total > 0:
            obj_principal = resultado_simbad.get('objeto_principal')
            if obj_principal:
                relatorio += f"**Objeto mais próximo:**\n"
                relatorio += f"- Nome: {obj_principal.get('identificador', 'N/A')}\n"
                relatorio += f"- Tipo: {obj_principal.get('tipo', 'N/A')}\n"
                relatorio += f"- Distância: {obj_principal.get('distancia_arcsec', 0):.2f} arcsec\n"
                relatorio += f"- Referências: {obj_principal.get('referencias', 0)}\n\n"
            
            if total > 1:
                relatorio += f"**Outros {total - 1} objetos encontrados no campo**\n\n"
        
        relatorio += f"[🔗 Ver detalhes completos no SIMBAD]({url})\n"
        
        return relatorio


# Função auxiliar para uso rápido
def verificar_descoberta_rapido(ra, dec, confianca, radius_arcmin=2.0):
    """
    Verificação rápida de uma descoberta
    
    Args:
        ra: Ascensão Reta em graus
        dec: Declinação em graus
        confianca: Confiança da detecção (0-100)
        radius_arcmin: Raio de busca
        
    Returns:
        dict: Resultado completo da verificação
    """
    checker = SimbadChecker(radius_arcmin=radius_arcmin)
    resultado_simbad = checker.verificar_coordenadas(ra, dec)
    classificacao = checker.classificar_descoberta(resultado_simbad, confianca)
    relatorio = checker.gerar_relatorio(resultado_simbad)
    
    return {
        'simbad': resultado_simbad,
        'classificacao': classificacao,
        'relatorio': relatorio
    }

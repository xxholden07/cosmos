"""
Sistema de Banco de Dados para Monitoramento de Objetos Celestes
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import os

class CelestialDatabase:
    """Gerencia banco de dados de objetos celestes detectados"""
    
    def __init__(self, db_path: str = "celestial_objects.db"):
        self.db_path = db_path
        self._criar_tabelas()
    
    def _criar_tabelas(self):
        """Cria estrutura do banco de dados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de objetos (estrelas observadas)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS objetos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                ra REAL,
                dec REAL,
                missao TEXT,
                primeira_observacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultima_observacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_observacoes INTEGER DEFAULT 0
            )
        """)
        
        # Tabela de observações
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS observacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                objeto_id INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cadencia TEXT,
                pontos_dados INTEGER,
                periodo_dias REAL,
                FOREIGN KEY (objeto_id) REFERENCES objetos(id)
            )
        """)
        
        # Tabela de planetas detectados
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS planetas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                observacao_id INTEGER NOT NULL,
                periodo_dias REAL NOT NULL,
                profundidade_transito REAL NOT NULL,
                duracao_horas REAL,
                raio_terrestre REAL,
                confianca REAL,
                status TEXT,
                descoberta_nova BOOLEAN DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (observacao_id) REFERENCES observacoes(id)
            )
        """)
        
        # Tabela de cometas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cometas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                observacao_id INTEGER NOT NULL,
                tempo_deteccao REAL NOT NULL,
                aumento_brilho REAL,
                tipo_atividade TEXT,
                velocidade REAL,
                confianca REAL,
                descoberta_nova BOOLEAN DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (observacao_id) REFERENCES observacoes(id)
            )
        """)
        
        # Tabela de meteoros/eventos rápidos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meteoros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                observacao_id INTEGER NOT NULL,
                tempo_deteccao REAL NOT NULL,
                duracao_horas REAL,
                amplitude REAL,
                tipo_evento TEXT,
                confianca REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (observacao_id) REFERENCES observacoes(id)
            )
        """)
        
        # Tabela de eventos transientes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                observacao_id INTEGER NOT NULL,
                tipo TEXT,
                tempo_inicio REAL,
                tempo_pico REAL,
                tempo_fim REAL,
                duracao_dias REAL,
                amplitude_mag REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (observacao_id) REFERENCES observacoes(id)
            )
        """)
        
        # Tabela de descobertas potenciais
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS descobertas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                observacao_id INTEGER NOT NULL,
                tipo TEXT NOT NULL,
                status TEXT NOT NULL,
                confianca REAL,
                parametros TEXT,
                verificado BOOLEAN DEFAULT 0,
                notas TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (observacao_id) REFERENCES observacoes(id)
            )
        """)
        
        # Índices para busca rápida
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_objetos_nome ON objetos(nome)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_planetas_confianca ON planetas(confianca)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_descobertas_status ON descobertas(status)")
        
        conn.commit()
        conn.close()
    
    def salvar_objeto(self, nome: str, ra: float, dec: float, missao: str) -> int:
        """Salva ou atualiza objeto e retorna ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar se objeto já existe
        cursor.execute("SELECT id, total_observacoes FROM objetos WHERE nome = ?", (nome,))
        resultado = cursor.fetchone()
        
        if resultado:
            objeto_id, total_obs = resultado
            # Atualizar
            cursor.execute("""
                UPDATE objetos 
                SET ultima_observacao = CURRENT_TIMESTAMP,
                    total_observacoes = ?,
                    ra = ?,
                    dec = ?,
                    missao = ?
                WHERE id = ?
            """, (total_obs + 1, ra, dec, missao, objeto_id))
        else:
            # Inserir novo
            cursor.execute("""
                INSERT INTO objetos (nome, ra, dec, missao, total_observacoes)
                VALUES (?, ?, ?, ?, 1)
            """, (nome, ra, dec, missao))
            objeto_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return objeto_id
    
    def salvar_observacao(self, objeto_id: int, cadencia: str, pontos_dados: int, periodo_dias: float) -> int:
        """Salva observação e retorna ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO observacoes (objeto_id, cadencia, pontos_dados, periodo_dias)
            VALUES (?, ?, ?, ?)
        """, (objeto_id, cadencia, pontos_dados, periodo_dias))
        
        observacao_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return observacao_id
    
    def salvar_planetas(self, observacao_id: int, planetas: List[Dict]):
        """Salva planetas detectados"""
        if not planetas:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for planeta in planetas:
            # Determinar se é descoberta nova (confiança > 85%)
            descoberta_nova = planeta.get('confidence', 0) > 85
            status = 'NOVO' if descoberta_nova else 'CANDIDATO' if planeta.get('confidence', 0) > 70 else 'DETECTADO'
            
            raio = planeta.get('transit_depth', 0) ** 0.5 * 109
            
            cursor.execute("""
                INSERT INTO planetas (
                    observacao_id, periodo_dias, profundidade_transito, duracao_horas,
                    raio_terrestre, confianca, status, descoberta_nova
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                observacao_id,
                planeta.get('period_days'),
                planeta.get('transit_depth'),
                planeta.get('transit_duration_hours'),
                raio,
                planeta.get('confidence'),
                status,
                descoberta_nova
            ))
        
        conn.commit()
        conn.close()
    
    def salvar_cometas(self, observacao_id: int, cometas: List[Dict]):
        """Salva cometas detectados"""
        if not cometas:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for cometa in cometas:
            descoberta_nova = cometa.get('confidence', 0) > 0.8
            
            cursor.execute("""
                INSERT INTO cometas (
                    observacao_id, tempo_deteccao, aumento_brilho, tipo_atividade,
                    velocidade, confianca, descoberta_nova
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                observacao_id,
                cometa.get('detection_time'),
                cometa.get('brightness_increase'),
                cometa.get('activity_type'),
                cometa.get('velocity_deg_day'),
                cometa.get('confidence'),
                descoberta_nova
            ))
        
        conn.commit()
        conn.close()
    
    def salvar_meteoros(self, observacao_id: int, meteoros: List[Dict]):
        """Salva meteoros/eventos rápidos"""
        if not meteoros:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for meteoro in meteoros:
            cursor.execute("""
                INSERT INTO meteoros (
                    observacao_id, tempo_deteccao, duracao_horas, amplitude,
                    tipo_evento, confianca
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                observacao_id,
                meteoro.get('detection_time'),
                meteoro.get('duration_hours'),
                meteoro.get('amplitude'),
                meteoro.get('event_type'),
                meteoro.get('confidence')
            ))
        
        conn.commit()
        conn.close()
    
    def salvar_transientes(self, observacao_id: int, transientes: List[Dict]):
        """Salva eventos transientes"""
        if not transientes:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for evento in transientes:
            cursor.execute("""
                INSERT INTO transientes (
                    observacao_id, tipo, tempo_inicio, tempo_pico, tempo_fim,
                    duracao_dias, amplitude_mag
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                observacao_id,
                evento.get('type'),
                evento.get('start_time'),
                evento.get('peak_time'),
                evento.get('end_time'),
                evento.get('duration_days'),
                evento.get('amplitude')
            ))
        
        conn.commit()
        conn.close()
    
    def salvar_descobertas(self, observacao_id: int, descobertas: List[Dict]):
        """Salva descobertas potenciais"""
        if not descobertas:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for desc in descobertas:
            cursor.execute("""
                INSERT INTO descobertas (
                    observacao_id, tipo, status, confianca, parametros
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                observacao_id,
                desc.get('tipo'),
                desc.get('status'),
                desc.get('confianca'),
                desc.get('parametros')
            ))
        
        conn.commit()
        conn.close()
    
    def obter_historico_objeto(self, nome: str) -> Dict:
        """Obtém histórico completo de um objeto"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Buscar objeto
        cursor.execute("SELECT * FROM objetos WHERE nome = ?", (nome,))
        objeto = cursor.fetchone()
        
        if not objeto:
            conn.close()
            return None
        
        resultado = {
            'objeto': dict(objeto),
            'observacoes': [],
            'planetas': [],
            'cometas': [],
            'meteoros': [],
            'transientes': [],
            'descobertas': []
        }
        
        # Buscar observações
        cursor.execute("SELECT * FROM observacoes WHERE objeto_id = ? ORDER BY timestamp DESC", (objeto['id'],))
        resultado['observacoes'] = [dict(row) for row in cursor.fetchall()]
        
        # Buscar planetas
        cursor.execute("""
            SELECT p.* FROM planetas p
            JOIN observacoes o ON p.observacao_id = o.id
            WHERE o.objeto_id = ?
            ORDER BY p.confianca DESC
        """, (objeto['id'],))
        resultado['planetas'] = [dict(row) for row in cursor.fetchall()]
        
        # Buscar cometas
        cursor.execute("""
            SELECT c.* FROM cometas c
            JOIN observacoes o ON c.observacao_id = o.id
            WHERE o.objeto_id = ?
            ORDER BY c.timestamp DESC
        """, (objeto['id'],))
        resultado['cometas'] = [dict(row) for row in cursor.fetchall()]
        
        # Buscar descobertas
        cursor.execute("""
            SELECT d.* FROM descobertas d
            JOIN observacoes o ON d.observacao_id = o.id
            WHERE o.objeto_id = ?
            ORDER BY d.confianca DESC
        """, (objeto['id'],))
        resultado['descobertas'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return resultado
    
    def listar_descobertas_novas(self, limit: int = 50) -> List[Dict]:
        """Lista todas as descobertas potenciais"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT d.*, o.nome, o.ra, o.dec, obs.timestamp as observacao_timestamp
            FROM descobertas d
            JOIN observacoes obs ON d.observacao_id = obs.id
            JOIN objetos o ON obs.objeto_id = o.id
            WHERE d.status IN ('NOVO', 'CANDIDATO')
            ORDER BY d.confianca DESC, d.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        descobertas = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return descobertas
    
    def estatisticas_gerais(self) -> Dict:
        """Retorna estatísticas gerais do banco de dados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute("SELECT COUNT(*) FROM objetos")
        stats['total_objetos'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM observacoes")
        stats['total_observacoes'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM planetas")
        stats['total_planetas'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM planetas WHERE descoberta_nova = 1")
        stats['planetas_novos'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM cometas")
        stats['total_cometas'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM meteoros")
        stats['total_meteoros'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM descobertas WHERE status = 'NOVO'")
        stats['descobertas_novas'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM descobertas WHERE status = 'CANDIDATO'")
        stats['candidatos'] = cursor.fetchone()[0]
        
        conn.close()
        return stats

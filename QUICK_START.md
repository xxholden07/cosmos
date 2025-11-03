# Guia de Uso Rápido - Sistema de Análise de Dados Cósmicos

## 🚀 Instalação

```bash
cd ~/Documentos/cosmos
pip install -r requirements.txt
```

## 📖 Uso Básico

### 1. Via Jupyter Notebook (Recomendado para iniciantes)

```bash
jupyter notebook analise_cosmica.ipynb
```

Execute as células sequencialmente para ver exemplos completos de:
- Detecção de planetas
- Análise de vibrações estelares
- Busca por padrões/mensagens

### 2. Via Python Script

```python
from cosmic_analyzer import CosmicAnalyzer
import numpy as np

# Inicializar
analyzer = CosmicAnalyzer(sensitivity=3.0)

# Analisar curva de luz
time = np.linspace(0, 30, 5000)
flux = np.ones(5000) + np.random.normal(0, 0.001, 5000)

results = analyzer.analyze_lightcurve(
    time, flux,
    detect_planets=True,
    detect_transients=True,
    analyze_vibrations=True
)

# Ver resultados
print(f"Planetas encontrados: {len(results['planets'])}")
```

### 3. Módulos Individuais

#### Detector de Corpos Celestes

```python
from celestial_detector import CelestialBodyDetector

detector = CelestialBodyDetector()
planets = detector.detect_transiting_planets(time, flux)
transients = detector.detect_transient_events(time, magnitude)
```

#### Asterosismologia

```python
from stellar_seismology import StellarSeismologyAnalyzer

seismo = StellarSeismologyAnalyzer()
analysis = seismo.analyze_stellar_vibrations(time, flux)

# Ver parâmetros estelares
params = analysis['stellar_parameters']
print(f"Massa: {params['mass_solar']:.2f} M☉")
print(f"Raio: {params['radius_solar']:.2f} R☉")
```

#### Detector de Padrões (SETI)

```python
from pattern_detector import PatternDetector

detector = PatternDetector()
analysis = detector.analyze_signal(signal_data, sample_rate=1.0)

score = analysis['artificiality_score']['score']
print(f"Score de artificialidade: {score}/100")
```

## 📊 Visualizações

```python
from visualizer import CosmicVisualizer

viz = CosmicVisualizer()

# Visualizar detecções
viz.plot_celestial_detections(time, flux, planets, transients)

# Visualizar asterosismologia
viz.plot_stellar_seismology(seismo_analysis)

# Visualizar análise de padrões
viz.plot_pattern_analysis(signal_data, pattern_analysis)

# Dashboard consolidado
viz.plot_summary_dashboard(
    celestial_results={'planets': planets, 'transients': transients},
    seismology_results=seismo_analysis,
    pattern_results=pattern_analysis
)
```

## 🔬 Usando Dados Reais

### Integração com Kepler/TESS (via lightkurve)

```bash
pip install lightkurve
```

```python
import lightkurve as lk
from cosmic_analyzer import CosmicAnalyzer

# Baixar dados do Kepler
search = lk.search_lightcurve('KIC 11904151', author='Kepler')
lc = search.download()

# Analisar
analyzer = CosmicAnalyzer()
results = analyzer.analyze_lightcurve(
    lc.time.value,
    lc.flux.value,
    analyze_vibrations=True
)
```

## 📁 Estrutura dos Arquivos

```
cosmos/
├── README.md                    # Documentação principal
├── QUICK_START.md              # Este arquivo
├── requirements.txt            # Dependências
│
├── cosmic_analyzer.py          # Módulo principal integrado
├── celestial_detector.py       # Detecção de corpos celestes
├── stellar_seismology.py       # Análise de vibrações estelares
├── pattern_detector.py         # Detecção de padrões/mensagens
├── visualizer.py               # Visualizações
│
└── analise_cosmica.ipynb       # Notebook tutorial completo
```

## 💡 Dicas

1. **Para detecção de planetas**: Use dados com pelo menos 3 períodos orbitais
2. **Para asterosismologia**: São necessários dados de alta cadência (≤1 minuto)
3. **Para análise SETI**: Sinais mais longos (>10000 pontos) dão melhores resultados
4. **Sensibilidade**: Aumente para detecções mais rigorosas, diminua para mais candidatos

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError"
```bash
# Certifique-se de estar no diretório correto
cd ~/Documentos/cosmos
# Reinstale as dependências
pip install -r requirements.txt
```

### Gráficos não aparecem
```python
# No Jupyter, adicione no início:
%matplotlib inline
```

### Muitos falsos positivos
```python
# Aumente a sensibilidade
analyzer = CosmicAnalyzer(sensitivity=5.0)  # padrão é 3.0
```

## 📚 Recursos Adicionais

- **Kepler Data**: https://archive.stsci.edu/kepler/
- **TESS Data**: https://archive.stsci.edu/tess/
- **Asterosismologia**: https://www.nature.com/subjects/asteroseismology
- **SETI**: https://www.seti.org/

## 🤝 Contribuindo

Sinta-se livre para modificar e expandir este sistema!

Ideias para melhorias:
- Adicionar machine learning para classificação
- Implementar análise espectroscópica
- Criar interface web interativa
- Adicionar mais tipos de detecções

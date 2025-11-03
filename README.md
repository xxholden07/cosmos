# Sistema de Análise de Dados Cósmicos

Sistema para análise de dados astronômicos reais usando dados do Kepler e TESS.

## Funcionalidades

- Detecção de exoplanetas por trânsito
- Análise de vibrações estelares (Asterosismologia)
- Busca por padrões em sinais cósmicos (SETI)
- Detecção de eventos transientes (supernovas, etc)

## Instalação

```bash
pip install -r requirements.txt
```

## Interface Web

Execute a aplicação Streamlit:

```bash
streamlit run app.py
```

Ou use o script de inicialização:

```bash
python run_app.py
```

A interface estará disponível em: http://localhost:8501

## Uso via Python

```python
from cosmic_analyzer import CosmicAnalyzer
import lightkurve as lk

# Baixar dados reais
lc = lk.search_lightcurve('Kepler-10').download()

# Analisar
analyzer = CosmicAnalyzer()
results = analyzer.analyze_lightcurve(lc.time.value, lc.flux.value)
```

## Estrutura

- `app.py` - Interface web Streamlit
- `cosmic_analyzer.py` - Motor de análise principal
- `celestial_detector.py` - Detecção de corpos celestes
- `stellar_seismology.py` - Asterosismologia
- `pattern_detector.py` - Análise de padrões SETI
- `visualizer.py` - Visualizações

## Fontes de Dados

O sistema usa dados reais de:
- Missão Kepler (NASA)
- Missão TESS (NASA)
- Arquivos FITS/CSV locais

Biblioteca: `lightkurve`

## Exemplos

### Interface Web
Mais fácil - use `streamlit run app.py`

### Python Script
```python
import lightkurve as lk
from cosmic_analyzer import CosmicAnalyzer

# Buscar e baixar dados
search = lk.search_lightcurve('Kepler-90', author='Kepler')
lc = search.download()

# Analisar
analyzer = CosmicAnalyzer()
results = analyzer.analyze_lightcurve(
    lc.time.value,
    lc.flux.value,
    detect_planets=True,
    analyze_vibrations=True
)

print(f"Planetas detectados: {len(results['planets'])}")
```

## Requisitos

- Python 3.8+
- NumPy, SciPy, Pandas
- Matplotlib, Seaborn
- Astropy, Lightkurve
- Streamlit (para interface web)

## Licença

MIT

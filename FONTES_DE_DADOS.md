# 📊 Fontes de Dados - Sistema de Análise Cósmica

## 🎯 Resumo

O sistema funciona com **3 tipos de fontes de dados**:

### 1. 🧪 **Dados Sintéticos (Gerados)** - PADRÃO ATUAL
### 2. 📁 **Arquivos Locais** (CSV, FITS, etc)
### 3. 🛰️ **Dados Reais de Missões Espaciais** (Kepler, TESS)

---

## 1️⃣ Dados Sintéticos (Atualmente em Uso)

### O que são?
Dados **simulados matematicamente** que imitam fenômenos astronômicos reais. São gerados por funções Python no notebook.

### Onde estão?
No arquivo `analise_cosmica.ipynb`, seção "2. Gerar Dados de Exemplo":

```python
# Funções que GERAM os dados:
def generate_planet_transit_data(...)     # Simula trânsito planetário
def generate_stellar_vibration_data(...)  # Simula oscilações estelares
def generate_seti_signal(...)             # Simula sinal de rádio
```

### Como funcionam?

#### A) **Trânsito Planetário**
```python
def generate_planet_transit_data(n_points=5000, period=3.5, depth=0.01):
    time = np.linspace(0, 30, n_points)  # 30 dias de observação
    flux = np.ones(n_points)              # Fluxo base = 1
    
    # Simula o planeta passando na frente da estrela
    for cycle_start in np.arange(0, 30, period):  # A cada 3.5 dias
        mask = (time >= cycle_start) & (time < cycle_start + 0.1)
        flux[mask] *= (1 - depth)  # Reduz brilho em 1%
    
    # Adiciona ruído realista
    flux += np.random.normal(0, 0.001, n_points)
    return time, flux
```
**Simula**: Um planeta com órbita de 3.5 dias que bloqueia 1% da luz estelar

#### B) **Vibrações Estelares**
```python
def generate_stellar_vibration_data(n_points=10000, nu_max=3000, delta_nu=135):
    time = np.linspace(0, 100, n_points)
    flux = np.zeros(n_points)
    
    # Adiciona 20 modos de oscilação diferentes
    for i in range(20):
        freq = (nu_max + (i - 10) * delta_nu) * 1e-6  # Hz
        amplitude = 0.001 * np.exp(-(i - 10)**2 / 50)
        flux += amplitude * np.sin(2 * np.pi * freq * time * 86400)
    
    return time, flux
```
**Simula**: Estrela similar ao Sol com múltiplas frequências de oscilação

#### C) **Sinal SETI**
```python
def generate_seti_signal(n_points=10000, has_pattern=True):
    signal_data = np.random.normal(0, 1, n_points)  # Ruído base
    
    if has_pattern:
        # Adiciona pulsos regulares (artificial!)
        for i in range(0, n_points, 100):
            signal_data[i:i+10] += 5
        
        # Adiciona frequência portadora
        signal_data += 2 * np.sin(2 * np.pi * 0.05 * time)
    
    return signal_data
```
**Simula**: Sinal de rádio com padrão repetitivo (como uma transmissão)

### ✅ Vantagens dos Dados Sintéticos
- ✅ Rápido para testar
- ✅ Não precisa download
- ✅ Controle total dos parâmetros
- ✅ Ideal para aprendizado e demonstração

### ❌ Limitações
- ❌ Não são dados reais do universo
- ❌ Mais simples que fenômenos reais
- ❌ Não têm anomalias/complexidades reais

---

## 2️⃣ Arquivos Locais (Seus Próprios Dados)

### Como usar arquivos CSV?

```python
import pandas as pd

# Ler arquivo CSV
data = pd.read_csv('meus_dados.csv')
time = data['time'].values
flux = data['flux'].values

# Analisar
analyzer = CosmicAnalyzer()
results = analyzer.analyze_lightcurve(time, flux)
```

### Como usar arquivos FITS? (formato astronômico)

```python
from astropy.io import fits

# Ler arquivo FITS
hdu = fits.open('lightcurve.fits')
time = hdu[1].data['TIME']
flux = hdu[1].data['FLUX']

# Analisar
analyzer = CosmicAnalyzer()
results = analyzer.analyze_lightcurve(time, flux)
```

### Formato esperado dos dados

**Curva de Luz:**
- `time`: Array de tempos (em dias, geralmente)
- `flux`: Array de fluxo normalizado (valores ~1.0)

**Sinal de Rádio:**
- `signal`: Array de amplitudes
- `sample_rate`: Taxa de amostragem (Hz)

---

## 3️⃣ Dados Reais de Missões Espaciais

### 🛰️ Usando dados do Kepler/TESS

O **Kepler** e **TESS** são telescópios espaciais que coletam dados reais de estrelas!

#### Instalação necessária:
```bash
pip install lightkurve
```

#### Exemplo completo:

```python
import lightkurve as lk
from cosmic_analyzer import CosmicAnalyzer

# 1. BUSCAR dados de uma estrela específica
print("Buscando dados da estrela KIC 11904151...")
search_result = lk.search_lightcurve('KIC 11904151', 
                                      author='Kepler', 
                                      cadence='short')

print(f"Encontrados: {len(search_result)} conjuntos de dados")

# 2. BAIXAR os dados
print("Baixando dados...")
lc_collection = search_result.download_all()
lc = lc_collection.stitch()  # Juntar todos os trimestres

# 3. EXTRAIR arrays
time = lc.time.value      # Tempo em dias
flux = lc.flux.value      # Fluxo

# 4. ANALISAR com nosso sistema
print("Analisando...")
analyzer = CosmicAnalyzer()
results = analyzer.analyze_lightcurve(
    time, flux,
    detect_planets=True,
    analyze_vibrations=True
)

print(f"Planetas encontrados: {len(results['planets'])}")
```

### 🌟 Estrelas Interessantes para Testar

```python
# Estrela com planetas conhecidos
'Kepler-90'        # Sistema com 8 planetas!
'TRAPPIST-1'       # 7 planetas do tamanho da Terra

# Estrela pulsante (para asterosismologia)
'KIC 11904151'     # Estrela oscilante tipo solar
'KIC 8006161'      # Outra ótima para asterosismologia

# Pesquisa geral
search = lk.search_lightcurve('Kepler-186', author='Kepler')
```

### 📡 Onde os dados estão armazenados?

```
Internet → Servidores NASA/STScI
              ↓ (lightkurve baixa)
          Cache Local
         ~/.lightkurve-cache/
              ↓
       Seu script Python
```

---

## 🔄 Fluxo Completo de Dados

### Cenário Atual (Sintético):
```
Funções Python → Dados gerados → Sistema de Análise → Resultados
```

### Com Arquivos Locais:
```
Arquivo CSV/FITS → Pandas/Astropy → Sistema de Análise → Resultados
```

### Com Dados Reais:
```
NASA/STScI → lightkurve → Sistema de Análise → Resultados
```

---

## 📝 Exemplo Prático Completo

### Criar arquivo de dados próprio:

```python
import numpy as np
import pandas as pd

# Gerar dados sintéticos
time = np.linspace(0, 30, 5000)
flux = np.ones(5000) + np.random.normal(0, 0.001, 5000)

# Salvar em CSV
df = pd.DataFrame({'time': time, 'flux': flux})
df.to_csv('meus_dados.csv', index=False)

# Depois, carregar e usar:
data = pd.read_csv('meus_dados.csv')
time = data['time'].values
flux = data['flux'].values

# Analisar
from cosmic_analyzer import CosmicAnalyzer
analyzer = CosmicAnalyzer()
results = analyzer.analyze_lightcurve(time, flux)
```

---

## 🎓 Para Usar Dados Reais AGORA

### Opção 1: Lightkurve (Mais Fácil)

```python
# Adicione esta célula no notebook:
import lightkurve as lk

# Buscar estrela
search = lk.search_lightcurve('Kepler-10', author='Kepler')
lc = search.download()

# Usar com nosso sistema
time = lc.time.value
flux = lc.flux.value

detector = CelestialBodyDetector()
planets = detector.detect_transiting_planets(time, flux)
```

### Opção 2: Arquivo CSV Manual

Crie um arquivo `dados.csv`:
```csv
time,flux
0.0,1.0001
0.1,0.9999
0.2,1.0002
...
```

Depois carregue:
```python
import pandas as pd
data = pd.read_csv('dados.csv')
```

---

## 📊 Resumo Visual

```
DADOS DE INPUT
│
├─ 1. SINTÉTICOS (Atual) ⭐
│  │
│  ├─ generate_planet_transit_data()
│  ├─ generate_stellar_vibration_data()
│  └─ generate_seti_signal()
│
├─ 2. ARQUIVOS LOCAIS
│  │
│  ├─ CSV: pandas.read_csv()
│  └─ FITS: astropy.io.fits.open()
│
└─ 3. DADOS REAIS
   │
   ├─ Kepler: lightkurve.search_lightcurve()
   └─ TESS: lightkurve.search_lightcurve()
```

---

## ❓ FAQ

**P: Os dados atuais são reais?**
R: Não, são simulações matemáticas que imitam dados reais.

**P: Como usar dados reais?**
R: Instale `lightkurve` e use o código da seção 3.

**P: Posso usar meus próprios dados?**
R: Sim! Basta ter arrays de `time` e `flux` (ver seção 2).

**P: Onde o sistema "busca" os dados?**
R: Atualmente ele **gera** (não busca). Para buscar dados reais, use lightkurve.

**P: Os dados sintéticos são úteis?**
R: Sim! Ótimos para aprender, testar e validar algoritmos.

---

## 🚀 Próximos Passos

1. **Testar com dados sintéticos** (atual) ✅
2. **Salvar/carregar arquivos CSV**
3. **Instalar lightkurve e baixar dados reais**
4. **Analisar estrelas famosas do Kepler**

---

**Atualmente: GERANDO dados sintéticos** 🧪  
**Próximo nível: BAIXAR dados reais** 🛰️

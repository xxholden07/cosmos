# 🌌 Sistema de Análise de Dados Cósmicos

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

## 📖 Sobre

Sistema completo e avançado para análise de dados astronômicos, desenvolvido para:

- 🔭 **Detectar corpos celestes** (exoplanetas, asteroides, cometas)
- ⭐ **Analisar vibrações estelares** (Asterosismologia)
- 📡 **Buscar padrões e mensagens** em sinais cósmicos (SETI)
- 💥 **Identificar eventos transientes** (supernovas, flares)

## ✨ Características

### Detecção de Corpos Celestes
- ✅ Identificação de exoplanetas por método de trânsito
- ✅ Cálculo de período orbital e tamanho planetário
- ✅ Detecção de asteroides por movimento aparente
- ✅ Classificação de eventos transientes

### Asterosismologia
- ✅ Análise de frequências de oscilação estelar
- ✅ Determinação de massa, raio e idade
- ✅ Identificação de modos de pulsação
- ✅ Detecção de rotação estelar

### SETI - Busca por Inteligência
- ✅ Testes de aleatoriedade estatística
- ✅ Detecção de periodicidades e pulsos
- ✅ Busca por padrões matemáticos
- ✅ Análise de entropia e modulação
- ✅ Score de "artificialidade" do sinal

### Visualizações
- ✅ Gráficos interativos e informativos
- ✅ Espectrogramas e análise espectral
- ✅ Diagramas Echelle para asterosismologia
- ✅ Dashboard consolidado

## 🚀 Início Rápido

### Instalação

```bash
cd ~/Documentos/cosmos
pip install -r requirements.txt
```

### Uso Básico

**Opção 1: Jupyter Notebook (Recomendado)**
```bash
jupyter notebook analise_cosmica.ipynb
```

**Opção 2: Script Python**
```bash
python exemplo_simples.py
```

**Opção 3: API Python**
```python
from cosmic_analyzer import CosmicAnalyzer
import numpy as np

# Inicializar
analyzer = CosmicAnalyzer()

# Analisar dados
results = analyzer.analyze_lightcurve(time, flux)

print(f"Planetas encontrados: {len(results['planets'])}")
```

## 📚 Documentação

- **[QUICK_START.md](QUICK_START.md)** - Guia de início rápido
- **[analise_cosmica.ipynb](analise_cosmica.ipynb)** - Tutorial completo com exemplos

## 🔬 Exemplos de Uso

### Detectar Planetas

```python
from celestial_detector import CelestialBodyDetector

detector = CelestialBodyDetector()
planets = detector.detect_transiting_planets(time, flux)

for planet in planets:
    print(f"Período: {planet['period_days']:.2f} dias")
    print(f"Raio: ~{np.sqrt(planet['transit_depth']) * 109:.1f} R⊕")
```

### Analisar Vibrações Estelares

```python
from stellar_seismology import StellarSeismologyAnalyzer

seismo = StellarSeismologyAnalyzer()
analysis = seismo.analyze_stellar_vibrations(time, flux)

params = analysis['stellar_parameters']
print(f"Massa: {params['mass_solar']:.2f} M☉")
print(f"Raio: {params['radius_solar']:.2f} R☉")
print(f"Idade: {params['age_gyr']:.1f} bilhões de anos")
```

### Buscar Padrões (SETI)

```python
from pattern_detector import PatternDetector

detector = PatternDetector()
analysis = detector.analyze_signal(signal_data)

score = analysis['artificiality_score']['score']
print(f"Score de Artificialidade: {score}/100")
print(f"Classificação: {analysis['artificiality_score']['classification']}")
```

## 📊 Estrutura do Projeto

```
cosmos/
├── README.md                    # Este arquivo
├── QUICK_START.md              # Guia rápido
├── requirements.txt            # Dependências
├── .gitignore                  # Arquivos ignorados pelo git
│
├── cosmic_analyzer.py          # 🎯 Módulo principal
├── celestial_detector.py       # 🔭 Detecção de corpos celestes
├── stellar_seismology.py       # ⭐ Asterosismologia
├── pattern_detector.py         # 📡 Detecção de padrões SETI
├── visualizer.py               # 📊 Visualizações
│
├── analise_cosmica.ipynb       # 📓 Notebook tutorial
└── exemplo_simples.py          # 🐍 Script de exemplo
```

## 🛠️ Tecnologias

- **Python 3.8+**
- **NumPy** - Computação numérica
- **SciPy** - Análise científica
- **Matplotlib/Seaborn** - Visualizações
- **Pandas** - Manipulação de dados
- **Astropy** - Ferramentas astronômicas
- **Scikit-learn** - Machine learning

## 📈 Aplicações

### Pesquisa Científica
- Descoberta de novos exoplanetas
- Caracterização de propriedades estelares
- Monitoramento de eventos transientes
- Estudos de asterosismologia

### SETI e Astrobiologia
- Busca por sinais de inteligência extraterrestre
- Análise de padrões não-naturais
- Detecção de anomalias

### Educação
- Demonstração de técnicas de análise astronômica
- Visualização de fenômenos cósmicos
- Aprendizado de processamento de sinais

## 🔮 Roadmap

- [ ] Integração com banco de dados astronômicos (Kepler, TESS)
- [ ] Machine learning para classificação automática
- [ ] Análise espectroscópica
- [ ] Interface web interativa
- [ ] API REST para acesso remoto
- [ ] Processamento em tempo real de streams de dados
- [ ] Integração com observatórios

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se livre para:

1. Fazer fork do projeto
2. Criar uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abrir um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 🙏 Agradecimentos

- Missões espaciais Kepler e TESS pelos dados
- Comunidade científica de asterosismologia
- SETI Institute pelas metodologias de busca
- Comunidade Python científico

## 📞 Contato

Para questões, sugestões ou colaborações, abra uma issue no repositório.

## 🌟 Créditos

Desenvolvido com ❤️ para a comunidade de astronomia e ciência de dados.

---

**"O universo está cheio de segredos esperando para serem descobertos."** 🌌


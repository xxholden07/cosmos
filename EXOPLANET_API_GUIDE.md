# Exoplanet Archive API - Guia de Uso

Interface Python para o NASA Exoplanet Archive API e TAP Service.

## Instalação de Dependências

```bash
pip install requests pandas
```

## Uso Básico

### Inicializar API

```python
from exoplanet_api import ExoplanetAPI

api = ExoplanetAPI()
```

### Query TAP (Recomendado)

```python
# Query ADQL personalizada
query = "SELECT TOP 10 pl_name, hostname, sy_dist FROM ps WHERE disc_year > 2020"
planets = api.tap_query(query)
```

### Métodos Prontos

```python
# Buscar planetas confirmados
planets = api.get_confirmed_planets(limit=100, where="disc_year > 2020")

# Buscar KOI candidatos
kois = api.get_koi_candidates(period_min=300, radius_max=2)

# Buscar por método de descoberta
transit = api.get_planets_by_method('Transit', limit=50)

# Buscar zona habitável
habitable = api.get_habitable_zone_candidates()

# Buscar por nome
planet = api.search_by_name('Kepler-452 b')
```

### Cone Search

```python
# Buscar objetos em região do céu
results = api.cone_search(
    table='missionstars',
    ra=291.0,
    dec=48.0,
    radius=1.0,
    radius_unit='degree'
)
```

### Queries Pré-Geradas

```python
# Obter URL de query comum
url = api.get_pre_generated_query('all_confirmed_planets_csv')
```

## Tabelas Disponíveis

### TAP Service (Recomendado)
- `ps` - Planetary Systems
- `pscomppars` - Planetary Systems Composite Parameters
- `cumulative` - KOI Cumulative
- `keplerstellar` - Kepler Stellar
- `k2targets` - K2 Targets
- `k2pandc` - K2 Planets and Candidates

### API Legada
- `missionstars` - Mission Star List
- `mission_exocat` - Mission and ExoCat Star List

## Formatos de Saída

Suportados: `csv`, `json`, `xml`, `votable`, `ipac`, `tsv`, `pipe`

```python
# Retornar JSON
data = api.tap_query(query, format='json')

# Retornar CSV como DataFrame
data = api.tap_query(query, format='csv', return_dataframe=True)
```

## Funções Rápidas

```python
from exoplanet_api import quick_planet_search, quick_confirmed_planets

# Busca rápida
planet = quick_planet_search('Earth')
planets = quick_confirmed_planets(limit=100)
```

## Queries Pré-Geradas Disponíveis

- `all_confirmed_planets_csv` - Todos os planetas confirmados (CSV)
- `all_confirmed_planets_json` - Todos os planetas confirmados (JSON)
- `stars_hosting_exoplanets` - Estrelas com exoplanetas
- `kepler_confirmed_planets` - Planetas confirmados do Kepler
- `transiting_planets` - Planetas em trânsito
- `koi_candidates` - Candidatos KOI
- `microlensing_with_photometry` - Microlensing com fotometria
- `habitable_zone_koi` - KOI na zona habitável
- `tess_planets` - Planetas do TESS

## Referências

- [Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/)
- [TAP Service](https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html)
- [API User Guide](https://exoplanetarchive.ipac.caltech.edu/docs/program_interfaces.html)

# 📊 Análise Temporal de Crimes Encadeados com Grafos

Repositório do projeto final da disciplina **CMAC03 - Algoritmos em Grafos**, ministrada pelo **Prof. Rafael Frinhani**, no curso de Ciência da Computação da **Universidade Federal de Itajubá (UNIFEI)**.

## 🧠 Sobre o Projeto

O objetivo principal deste trabalho é utilizar a **teoria dos grafos** para modelar, analisar e interpretar padrões espaço-temporais de crimes ocorridos na cidade de **Los Angeles (LAPD)** entre os anos de **2020 a 2024**, com foco em:

- Detecção de comunidades criminosas;
- Análise de transições temporais e espaciais de ocorrências;
- Proposição de rotas de patrulhamento eficientes com base em grafos ponderados.

O projeto integra algoritmos clássicos como **Dijkstra** e **Louvain** com modelagens personalizadas de **subgrafos temporais (A)** e **espaciais (B)**, além de um **grafo integrado** que unifica ambas as dimensões.

## 🗂️ Estrutura do Repositório

O repositório está organizado nos seguintes diretórios e arquivos:

### 📁 `dataset/`
Contém os **arquivos originais de registros criminais** fornecidos pelo LAPD, utilizados como base para todo o projeto.

### 📁 `filtragem/`
Scripts responsáveis pelo **pré-processamento e filtragem** dos dados:
- Remoção de colunas irrelevantes;
- Seleção das 5 subáreas mais críticas;
- Conversão de horários em turnos.

### 📁 `comunidades/`
Código para construção do **grafo de similaridade entre crimes** e aplicação do **algoritmo de Louvain** para detecção de comunidades:
- Análise de modularidade;
- Agrupamento por tipo de crime, área, vítima e local.

### 📁 `subgrafos/`
Scripts responsáveis pela construção dos subgrafos:
- **Subgrafo A:** representa encadeamentos temporais de crimes.
- **Subgrafo B:** modela transições entre turnos do dia nas subáreas.

### 📁 `resultados/`
Contém os **arquivos de saída**, como:
- Visualizações dos grafos;
- Mapas interativos com a biblioteca `folium`;

## 🧪 Tecnologias e Ferramentas Utilizadas

- **Python 3.9**
- `pandas`, `numpy`
- `networkx`, `matplotlib`, `seaborn`
- `community` (python-louvain)
- `folium` (visualização geográfica)

## 🧑‍💻 Integrantes

- Eduardo Brandão Rocha  
- Jorge Alexandre Teixeira Henriques Luís  
- Rafael Santos Pinto Batista Leite  
- Thomas Sá Capucho

---

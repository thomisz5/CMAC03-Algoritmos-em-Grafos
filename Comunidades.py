import pandas as pd
import networkx as nx
import community as community_louvain
import folium
import matplotlib.pyplot as plt
import numpy as np
from itertools import combinations
from matplotlib import cm

# Configurações globais
TOP_AREAS = ['Central', '77th Street', 'Pacific', 'Southwest', 'Southeast']
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)


# Funções de pré-processamento
def convert_coordinate(coord):
    """Converte coordenadas para     float com tratamento de erros"""
    if pd.isna(coord) or coord in ['missing', 'N/A']:
        return None
    try:
        coord_str = str(coord).strip()
        if coord_str.count('.') > 1:
            parts = coord_str.split('.')
            coord_str = f"{parts[0]}.{''.join(parts[1:])}"
        return float(coord_str)
    except (ValueError, AttributeError):
        return None


def clean_coordinates(df):
    """Limpa e valida as colunas de coordenadas"""
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input deve ser um DataFrame")

    if not all(col in df.columns for col in ['LAT', 'LON']):
        print("Aviso: Colunas LAT/LON não encontradas")
        return df

    df = df.copy()
    df['LAT'] = df['LAT'].apply(convert_coordinate)
    df['LON'] = df['LON'].apply(convert_coordinate)
    df = df.dropna(subset=['LAT', 'LON'])
    valid_coords = (df['LAT'].between(-90, 90) & df['LON'].between(-180, 180))
    return df[valid_coords].copy()


def preparar_dados(df):
    """Pré-processa os dados para análise"""
    cols_relevantes = [
        'DR_NO', 'Crm Cd Desc', 'AREA NAME', 'Weapon Desc',
        'Vict Sex', 'Vict Descent', 'Premis Desc', 'LAT', 'LON'
    ]

    df = df[cols_relevantes].copy()

    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].fillna('missing').str.strip()
        elif col != 'DR_NO':
            df[col] = df[col].fillna(0)

    return df


# Funções de análise de grafos
def construir_grafo(df):
    """Constroi grafo de similaridade entre crimes"""
    G = nx.Graph()

    # Adiciona nós com atributos
    for _, row in df.iterrows():
        attrs = {col: row[col] for col in df.columns if col != 'DR_NO'}
        G.add_node(row['DR_NO'], **attrs)

    # Conecta crimes similares
    for (n1, d1), (n2, d2) in combinations(G.nodes(data=True), 2):
        similarity = 0

        # Peso maior para tipo de crime e localização
        if d1['Crm Cd Desc'] == d2['Crm Cd Desc'] and d1['Crm Cd Desc'] != 'missing':
            similarity += 3

        if d1['AREA NAME'] == d2['AREA NAME'] and d1['AREA NAME'] != 'missing':
            similarity += 2

        # Outros atributos
        for attr in ['Weapon Desc', 'Premis Desc', 'Vict Sex', 'Vict Descent']:
            if d1[attr] == d2[attr] and d1[attr] != 'missing':
                similarity += 1

        if similarity >= 3:  # Limiar para considerar conexão
            G.add_edge(n1, n2, weight=similarity)

    return G


def analisar_comunidades(G, partition, periodo):
    """Analisa padrões nas comunidades detectadas"""
    print(f"\n=== ANÁLISE DETALHADA - {periodo} ===")
    print(f"Número de comunidades: {len(set(partition.values()))}")
    print(f"Modularidade: {community_louvain.modularity(partition, G):.3f}")

    for com_id in set(partition.values()):
        nodes = [n for n in G.nodes if partition[n] == com_id]
        subgraph = G.subgraph(nodes)

        print(f"\n--- Comunidade {com_id} ({len(nodes)} crimes) ---")

        atributos = {
            'Tipo de Crime': 'Crm Cd Desc',
            'Área': 'AREA NAME',
            'Arma': 'Weapon Desc',
            'Local': 'Premis Desc',
            'Vítima (Sexo)': 'Vict Sex',
            'Vítima (Etnia)': 'Vict Descent',
        }

        for nome, attr in atributos.items():
            valores = [data[attr] for _, data in subgraph.nodes(data=True) if data.get(attr, 'missing') != 'missing']
            if valores:
                contagem = pd.Series(valores).value_counts().head(3)
                print(f"\n🔍 {nome}:")
                for valor, count in contagem.items():
                    print(f"  - {valor}: {count} ({count / len(nodes):.1%})")
            else:
                print(f"\n🔍 {nome}: Sem dados válidos")


# Funções de visualização
def plotar_mapa(G, partition, periodo):
    """Cria mapa interativo com arestas coloridas por comunidade e legenda de pesos"""
    # Limites de Los Angeles
    LA_LAT_MIN, LA_LAT_MAX = 33.5, 34.5
    LA_LON_MIN, LA_LON_MAX = -118.7, -118.1

    # Filtra nós válidos dentro de LA
    valid_nodes = [
        (node, data) for node, data in G.nodes(data=True)
        if (data.get('LAT') and data.get('LON') and
            LA_LAT_MIN <= data['LAT'] <= LA_LAT_MAX and
            LA_LON_MIN <= data['LON'] <= LA_LON_MAX)
    ]

    if not valid_nodes:
        print(f"Nenhuma coordenada válida para {periodo} dentro de LA")
        return

    # Configura mapa
    avg_lat = np.mean([data['LAT'] for _, data in valid_nodes])
    avg_lon = np.mean([data['LON'] for _, data in valid_nodes])
    mapa = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)

    # Cores por comunidade
    communities = sorted(set(partition.values()))
    colors = cm.rainbow(np.linspace(0, 1, len(communities)))
    color_map = {c: '#%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255))
                 for c, (r, g, b, _) in zip(communities, colors)}

    # Adiciona nós
    node_coords = {}
    for node, data in valid_nodes:
        lat, lon = data['LAT'], data['LON']
        node_coords[node] = (lat, lon)

        folium.CircleMarker(
            location=[lat, lon],
            radius=5,
            color=color_map[partition[node]],
            fill=True,
            popup=f"""<b>Crime:</b> {data.get('Crm Cd Desc', 'N/A')}<br>
                      <b>Área:</b> {data.get('AREA NAME', 'N/A')}<br>
                      <b>Comunidade:</b> {partition[node]}"""
        ).add_to(mapa)

    # Adiciona arestas com tooltip de peso
    for u, v, data in G.edges(data=True):
        if u in node_coords and v in node_coords:
            weight = data.get('weight', 1)
            same_comm = partition[u] == partition[v]

            folium.PolyLine(
                locations=[node_coords[u], node_coords[v]],
                color=color_map[partition[u]] if same_comm else '#aaaaaa',
                weight=min(5, max(1, weight)),
                opacity=0.7 if same_comm else 0.3,
                tooltip=f"Peso: {weight} | {'Mesma comunidade' if same_comm else 'Entre comunidades'}"
            ).add_to(mapa)

    # Adiciona legenda de comunidades
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 180px; height: auto;
                border:2px solid grey; z-index:9999; font-size:14px;
                background-color:white; padding:10px;">
        <b>Legenda</b><br>
        <i style="background:{}; width:20px; height:20px; 
                 display:inline-block; vertical-align:middle;"></i> Comunidades<br>
        <i style="background:#aaaaaa; width:20px; height:20px; 
                 display:inline-block; vertical-align:middle;"></i> Conexões entre comunidades<br>
        <b>Largura da linha:</b> Peso da conexão (1-5)
    </div>
    '''.format(list(color_map.values())[0])

    mapa.get_root().html.add_child(folium.Element(legend_html))

    mapa.save(f'mapa_crimes_{periodo}.html')
    print(f"Mapa salvo como mapa_crimes_{periodo}.html")

def plotar_grafo(G, partition, title, filename):
    """Visualização do grafo com comunidades"""
    plt.figure(figsize=(15, 12))
    pos = nx.spring_layout(G, seed=RANDOM_SEED)

    communities = set(partition.values())
    colors = cm.rainbow(np.linspace(0, 1, len(communities)))
    node_colors = [colors[partition[n]] for n in G.nodes()]

    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=30, alpha=0.8)
    nx.draw_networkx_edges(G, pos, alpha=0.05, edge_color='gray')
    plt.title(title)
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()


# Função principal
def main():
    # Carrega e prepara os dados
    caminhos = {
        '2020-2022': '/home/thomas/PycharmProjects/CMAC03/ProjetoParcial - Analise Criminal/Cenário 6 - Análise Criminal/ProjetoFinal/comunidades_2020_2022.csv',
        '2023-2024': '/home/thomas/PycharmProjects/CMAC03/ProjetoParcial - Analise Criminal/Cenário 6 - Análise Criminal/ProjetoFinal/comunidades_2023_2024.csv'
    }

    grafos = {}
    particoes = {}

    for periodo, caminho in caminhos.items():
        print(f"\n=== PROCESSANDO {periodo} ===")

        try:
            # Carrega e prepara os dados
            df = pd.read_csv(caminho, delimiter=';', encoding='utf-8')
            df = df[df['AREA NAME'].isin(TOP_AREAS)].copy()
            df = clean_coordinates(df)
            df = preparar_dados(df)

            # Amostra representativa (aumente conforme recursos disponíveis)
            sample_size = min(1000, len(df))  # Tamanho da amostra ajustável
            df_sample = df.sample(sample_size, random_state=RANDOM_SEED)

            # Constroi e analisa o grafo
            G = construir_grafo(df_sample)
            partition = community_louvain.best_partition(G, weight='weight', random_state=RANDOM_SEED)

            # Armazena resultados
            grafos[periodo] = G
            particoes[periodo] = partition

            # Visualizações e análises
            plotar_grafo(G, partition, f'Grafo de Crimes - {periodo}', f'grafo_{periodo}.png')
            plotar_mapa(G, partition, periodo)
            analisar_comunidades(G, partition, periodo)

        except Exception as e:
            print(f"Erro ao processar {periodo}: {str(e)}")
            continue

    # Comparação entre períodos
    if grafos and particoes:
        print("\n=== COMPARAÇÃO ENTRE PERÍODOS ===")
        print(pd.DataFrame({
            'Período': list(grafos.keys()),
            'Nós': [G.number_of_nodes() for G in grafos.values()],
            'Arestas': [G.number_of_edges() for G in grafos.values()],
            'Densidade': [nx.density(G) for G in grafos.values()],
            'Modularidade': [community_louvain.modularity(p, grafos[k])
                             for k, p in particoes.items()]
        }).set_index('Período'))


if __name__ == "__main__":
    main()
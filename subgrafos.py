import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from datetime import timedelta
from math import radians, sin, cos, sqrt, atan2
import numpy as np

# Detecta o turno com base na hora
def classificar_turno(hora_str):
    try:
        hora = int(str(hora_str).zfill(4))
        if 600 <= hora < 1200:
            return 'Manhã'
        elif 1200 <= hora < 1800:
            return 'Tarde'
        return 'Noite'
    except:
        return 'Noite'

# Cálculo de distância geográfica para as coordenadas
def calcular_distancia(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat/2)*2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)*2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))

# Subgrafo A padrão temporal entre crimes comuns
def montar_subgrafo_a(df, limite=10):
    G = nx.DiGraph()
    principais = df['Crm Cd Desc'].value_counts().nlargest(limite).index
    dados = df[df['Crm Cd Desc'].isin(principais)].sort_values(['Rpt Dist No', 'DATE OCC'])

    for crime in principais:
        G.add_node(crime)

    for _, grupo in dados.groupby('Rpt Dist No'):
        eventos = grupo[['Crm Cd Desc', 'DATE OCC']].reset_index(drop=True)
        for i in range(len(eventos) - 1):
            c1, d1 = eventos.loc[i]
            for j in range(i + 1, len(eventos)):
                c2, d2 = eventos.loc[j]
                if timedelta(0) < d2 - d1 <= timedelta(hours=24):
                    atual = G.get_edge_data(c1, c2, default={'weight': 0})['weight']
                    G.add_edge(c1, c2, weight=atual + 1)
                elif d2 - d1 > timedelta(hours=24):
                    break
    return G

# Subgrafo B transição turno-espacial entre crimes
def montar_subgrafo_b(df, coords, ref):
    G, pos = nx.DiGraph(), {}
    turnos = ['Manhã', 'Tarde', 'Noite']
    desloca_lat, desloca_lon = {'Manhã': 30, 'Tarde': 15, 'Noite': 0}, 1.5

    for idx, sub in enumerate(sorted(coords.index)):
        lat, lon = coords.loc[sub]
        for t in turnos:
            nodo = f"{sub}|{t}"
            pos[nodo] = (lon + desloca_lon * idx, lat + desloca_lat[t])
            G.add_node(nodo)

    for data_ref, sub_df in df.groupby(df['DATE OCC'].dt.date):
        for t1, t2 in zip(turnos[:-1], turnos[1:]):
            bloco1, bloco2 = sub_df[sub_df['Turno'] == t1], sub_df[sub_df['Turno'] == t2]
            for _, r1 in bloco1.iterrows():
                for _, r2 in bloco2.iterrows():
                    s1, s2, c1, c2 = r1['Rpt Dist No'], r2['Rpt Dist No'], r1['Crm Cd Desc'], r2['Crm Cd Desc']
                    if s1 in coords.index and s2 in coords.index:
                        if calcular_distancia(*coords.loc[s1], *coords.loc[s2]) <= 50:
                            n1, n2 = f"{s1}|{t1}", f"{s2}|{t2}"
                            peso = ref[c1][c2]['weight'] if ref.has_edge(c1, c2) else 1
                            atual = G.get_edge_data(n1, n2, default={'weight': 0})['weight']
                            G.add_edge(n1, n2, weight=atual + peso)
    return G, pos

# Implementação do Dijkstra
def dijkstra(G, origem):
    custo = {v: float('inf') for v in G.nodes}
    rota = {v: None for v in G.nodes}
    custo[origem] = 0
    visitados = set()

    while len(visitados) < len(G):
        nao_visitados = {v: custo[v] for v in G if v not in visitados}
        if not nao_visitados:
            break
        atual = min(nao_visitados, key=nao_visitados.get)
        visitados.add(atual)
        for vizinho in G.successors(atual):
            peso = G[atual][vizinho]['weight']
            custo_novo = custo[atual] + (1 / peso)
            if custo_novo < custo[vizinho]:
                custo[vizinho] = custo_novo
                rota[vizinho] = atual

    return custo, rota

def reconstruir_caminho(rota, origem, destino):
    caminho = [destino]
    atual = destino
    while atual != origem and atual is not None:
        atual = rota[atual]
        caminho.append(atual)
    caminho.reverse()
    return caminho if caminho[0] == origem else []

# Busca o caminho com maior criminalidade entre manhã, tarde e noite
def encontrar_rota(G):
    inicio = [n for n in G.nodes if '|Manhã' in n]
    fim = [n for n in G.nodes if '|Noite' in n]
    melhor, custo_min = None, float('inf')

    for o in inicio:
        custos, rotas = dijkstra(G, o)
        for d in fim:
            if custos[d] < custo_min:
                custo_min = custos[d]
                melhor = reconstruir_caminho(rotas, o, d)

    return melhor, custo_min

# Plotagem dos grafos
def mostrar_grafo_final(G, pos, rota, titulo):
    plt.figure(figsize=(20, 12))
    cores = ['red' if rota and (u, v) in zip(rota, rota[1:]) else 'gray' for u, v in G.edges()]
    nx.draw(G, pos, node_color='#b3d9ff', edge_color=cores, with_labels=True,
            node_size=700, font_size=8, arrows=True, arrowstyle='-|>', arrowsize=12)
    plt.title(titulo + " \U0001F5FA")
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def mostrar_subgrafo_a(G, titulo):
    layout = nx.spring_layout(G, seed=0)
    plt.figure(figsize=(14, 10))
    pesos = np.array([G[u][v]['weight'] for u, v in G.edges()])
    esc = np.clip((pesos / pesos.max()) * 5, 1, 5) if len(pesos) > 0 else []
    nx.draw(G, layout, with_labels=True, node_color='#c6e2ff', node_size=1400,
            edge_color='gray', width=esc.tolist(), arrows=True, arrowstyle='-|>', arrowsize=15)
    plt.title(titulo)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def mostrar_subgrafo_b(G, pos, titulo):
    plt.figure(figsize=(20, 12))
    pesos = [d['weight'] for _, _, d in G.edges(data=True)]
    larg = [max(1, (p / max(pesos)) * 5) for p in pesos] if pesos else []
    nx.draw(G, pos, with_labels=True, node_color='#c6ffc6', node_size=800,
            width=larg, edge_color='gray', font_size=8, arrows=True, arrowstyle='-|>', arrowsize=12)
    plt.title(titulo)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

print("\nÁreas disponíveis:\n 77th Street, Central, Devonshire, Foothill, Harbor, Hollenbeck, Hollywood, Mission, Newton, Northeast, North Hollywood, Olympic, Pacific, Rampart, Southeast, Southwest, Topanga, Van Nuys, West LA, West Valley, Wilshire")

arq = "Cenário 6 - Crimes_2020-2024 Los Angeles.csv"
area = input("\nQual área você quer analisar? ")
ano = int(input("Ano (2020 a 2024): "))

df = pd.read_csv(arq, sep=";", encoding="latin1", on_bad_lines="skip")
df['DATE OCC'] = pd.to_datetime(df['DATE OCC'], errors='coerce')
df['ANO'] = df['DATE OCC'].dt.year
df['MES'] = df['DATE OCC'].dt.month
df['Turno'] = df['TIME OCC'].apply(classificar_turno)
df['LAT'] = pd.to_numeric(df['LAT'], errors='coerce')
df['LON'] = pd.to_numeric(df['LON'], errors='coerce')

df_filtrado = df[(df['AREA NAME'] == area) & (df['ANO'] == ano)].copy()

GA = montar_subgrafo_a(df_filtrado)
mostrar_subgrafo_a(GA, f"Crimes Encadeados – {area} ({ano})")

coordenadas = df_filtrado.groupby("Rpt Dist No")[["LAT", "LON"]].mean().dropna()
GB, pos = montar_subgrafo_b(df_filtrado, coordenadas, GA)
mostrar_subgrafo_b(GB, pos, f"Transições Temporais – {area} ({ano})")

rota, custo = encontrar_rota(GB)
print(f"\nRota crítica: {rota} (Custo: {custo:.2f})")
mostrar_grafo_final(GB, pos, rota, f"Caminho Crítico – {area} ({ano})")
import pandas as pd

# Carrega o dataset completo
df = pd.read_csv("/home/thomas/PycharmProjects/CMAC03/ProjetoParcial - Analise Criminal/Cenário 6 - Análise Criminal/Cenário 6 - Crimes_2020-2024 Los Angeles.csv",
                 encoding="utf-8", sep=";", on_bad_lines='skip')

# Define os crimes considerados (15 mais recorrentes)
crimes_considerados = [
    "VEHICLE - STOLEN",
    "BATTERY - SIMPLE ASSAULT",
    "BURGLARY FROM VEHICLE",
    "THEFT OF IDENTITY",
    "VANDALISM - FELONY ($400 & OVER, ALL CHURCH VANDALISMS)",
    "BURGLARY",
    "ASSAULT WITH DEADLY WEAPON, AGGRAVATED ASSAULT",
    "THEFT PLAIN - PETTY ($950 & UNDER)",
    "INTIMATE PARTNER - SIMPLE ASSAULT",
    "THEFT FROM MOTOR VEHICLE - PETTY ($950 & UNDER)",
    "THEFT FROM MOTOR VEHICLE - GRAND ($950.01 AND OVER)",
    "THEFT-GRAND ($950.01 & OVER)EXCPT,GUNS,FOWL,LIVESTK,PROD",
    "ROBBERY",
    "SHOPLIFTING - PETTY THEFT ($950 & UNDER)",
    "VANDALISM - MISDEAMEANOR ($399 OR UNDER)",
]

# Filtra apenas os crimes considerados
df_filtrado = df[df["Crm Cd Desc"].isin(crimes_considerados)].copy()

# Converte DATA OCC para datetime
df_filtrado["DATE OCC"] = pd.to_datetime(df_filtrado["DATE OCC"], errors="coerce")

# Remove linhas com datas inválidas
df_filtrado = df_filtrado.dropna(subset=["DATE OCC"])

# Extrai o ano da ocorrência
df_filtrado["ANO"] = df_filtrado["DATE OCC"].dt.year

# Função para categorizar o horário em turnos
def categoriza_tempo(turno):
    try:
        time = int(turno)
        if 0 <= time <= 1200:
            return "Manhã"
        elif 1201 <= time <= 1800:
            return "Tarde"
        else:
            return "Noite"
    except:
        return "Desconhecido"

# Aplica a categorização de turnos
df_filtrado["TURNO"] = df_filtrado["TIME OCC"].apply(categoriza_tempo)

# --- INÍCIO DA ALTERAÇÃO: COLUNAS QUE SERÃO MANTIDAS ---
# Adicione as colunas relevantes para similaridade aqui!
colunas_mantidas = [
    "DR_NO", # Essencial como ID único para nós no grafo de similaridade
    "Date Rptd",
    "Rpt Dist No",
    "AREA",
    "AREA NAME",
    "DATE OCC",
    "TURNO", # Será TURNO_OCORRENCIA no main.py
    "Crm Cd", # Pode ser útil para outras análises, mas Crm Cd Desc é mais legível para similaridade
    "Crm Cd Desc",
    "Mocodes", # NOVO: Códigos de Modus Operandi
    "Vict Age", # NOVO: Idade da vítima
    "Vict Sex", # NOVO: Sexo da vítima
    "Vict Descent", # NOVO: Descendência da vítima
    "Premis Desc", # NOVO: Descrição do local
    "Weapon Desc", # NOVO: Descrição da arma
    "Status Desc", # NOVO: Status do caso
    "LAT",
    "LON",
    "ANO"
]

# Filtra o DataFrame final para conter apenas as colunas desejadas
# Lida com colunas que podem não existir no dataset original (se alguma for opcional)
df_final = df_filtrado[[col for col in colunas_mantidas if col in df_filtrado.columns]].copy()
# --- FIM DA ALTERAÇÃO ---

# --- NOVA ETAPA: IDENTIFICAR TOP 5 ÁREAS NO DF_FINAL ANTES DA DIVISÃO ---
num_top_areas = 5
contagem_areas = df_final['AREA NAME'].value_counts()
top_areas_identificadas = contagem_areas.head(num_top_areas).index.tolist()
print(f"As {num_top_areas} áreas com maior incidência de crimes (considerando 2020-2024 e os crimes selecionados) são: {top_areas_identificadas}")

# --- FILTRAR DF_FINAL PELAS TOP_AREAS IDENTIFICADAS ---
df_final_filtrado_top_areas = df_final[df_final['AREA NAME'].isin(top_areas_identificadas)].copy()

# Divide em dois blocos: 2020–2022 e 2023–2024 (agora já filtrados pelas top áreas)
df_2020_2022 = df_final_filtrado_top_areas[df_final_filtrado_top_areas["ANO"].between(2020, 2022)].copy()
df_2023_2024 = df_final_filtrado_top_areas[df_final_filtrado_top_areas["ANO"].between(2023, 2024)].copy()

# Salva os arquivos resultantes
df_2020_2022.to_csv("comunidades_2020_2022.csv", index=False, sep=";", encoding="utf-8")
df_2023_2024.to_csv("comunidades_2023_2024.csv", index=False, sep=";", encoding="utf-8")

print("Filtragem concluída, top áreas identificadas e datasets separados com sucesso!")
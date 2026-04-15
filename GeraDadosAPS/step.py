
from Configuration_data import ConfigurationDataScenario, PathArquivoDados, ExecutionDataType
import os
from create_dat_files import CreatorDatFiles
from step_convert_Cluster_in_SC import ConvertClusterResults

# Diretório base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, "Dados")
MUNCIPIO = "Lagoa Santa"    #["Divinopolis, "#"Montes Claros" #"Lagoa Santa", "Contagem", "Belo Horizonte"]
PASTAS = {
    'todos_municipios': os.path.join(DADOS_DIR, "Dados_todos_municipios"),
    MUNCIPIO: os.path.join(DADOS_DIR, f"{MUNCIPIO}/dados_brutos")
}   

if __name__ == "__main__":
    municipio = MUNCIPIO
    arquivo_setor_censitario = f"dados_setor_censitario_{MUNCIPIO.upper()}.xlsx"
    arquivo_json_distancias = r"C:\Users\marce\OneDrive\Área de Trabalho\aps\GeraDadosAPS\Dados\Contagem\dados_brutos\Contagem_matrix_results_full_matrix.json" #f"{MUNCIPIO}_distance.json"
    dados_setor_censitario_completo = r"dados_setor_censitario_correto_final.xlsx"
    tipo_dos_dados = ExecutionDataType.BY_CLUSTER
    path_resultados = {"Montes Claros":r"C:\aps\resultados_por_cluster_final\report-MC_CLU.xlsx",
                        "Lagoa Santa": r"C:\aps\resultados_por_cluster_final\report-LS_CLU.xlsx",
                        "Contagem": r"C:\aps\resultados_por_cluster_final\report-Cont_CLU.xlsx",
                        "Divinopolis": r"C:\aps\resultados_por_cluster_final\report-Div_CLU.xlsx"
    }

    path_locais_candidatos = {"Montes Claros":r"C:\aps\data\selecao_candidatos_final_montes_claros.xlsx",
                        "Lagoa Santa": r"C:\aps\data\selecao_candidatos_final_lagoa_santa.xlsx",
                        "Contagem": r"C:\aps\data\selecao_candidatos_final_contagem.xlsx",
                        "Divinopolis": r"C:\aps\data\selecao_candidatos_final_divinopolis.xlsx",
                        "Belo Horizonte": r"C:\aps\data\selecao_candidatos_final_bh.xlsx"
    }

    configs = ConfigurationDataScenario(
        municipio = MUNCIPIO,
        budget = 19333029.53,
        I_L1 = 3818078,
        I_L1_exp = 1200000, 
        raios_criticos = {
            "PHC": 5000,
            "SHC": 30000,
            "THC": 35000
        },
        custos_mensais_PHC = {"eSF": 288000, "eSB": 105248, "eMulti": 322625, "ACS": 36280 },
        custos_mensais_SHC = {"EQ2": 0},
        custos_mensais_THC = {"EQ3": 0},
        equipes_saude_primario = ["eSF", "eSB", "eMulti", "ACS"],
        equipes_saude_secundario = ["EQ2"],
        equipes_saude_terciario = ["EQ3"],
        name_output_file = municipio,
        maximo_de_unidades_abertas = {"1": 10, "2": 1, "3": 1},
        encaminhamentos_primeiro_nivel = {"1": 0.71, "2": 0.20, "3": 0.05},
        encaminhamentos_segundo_nivel = {"1": 0.65, "2": 0.20, "3": 0.10},
        encaminhamentos_terceiro_nivel = {"1": 0.8, "2": 0.1, "3": 0.05},
        maximo_atendimentos_telemedicina = {"MAX_TELE_PHC": 0.05, "MAX_TELE_SHC": 0.05,"MAX_TELE_THC": 0.05},
        maximo_deslocamento = {"MAX_HOME_PHC": 1, "MAX_HOME_SHC": 0.15, "MAX_HOME_THC": 0.05,},
        name_output_file_distancias = municipio,
        tipo_rodada=tipo_dos_dados


    )

    paths_arquivos = PathArquivoDados(
        path_arquivo_setores_censitarios=os.path.join(PASTAS["todos_municipios"], dados_setor_censitario_completo),
        path_dados_IVS=os.path.join(PASTAS['todos_municipios'], "dados_IVS.xlsx"),
        path_equipes_PHC=os.path.join(PASTAS[municipio], "v02_Equipe.xlsx"),
        path_setores_com_UBS=os.path.join(PASTAS['todos_municipios'], "setores_com_ubs.xlsx"),
        #path_json_distances = os.path.join(PASTAS[municipio], arquivo_json_distancias),
        path_arquivos_dat_final = os.path.join(PASTAS[municipio]),
        path_cluster_CSV = os.path.join(PASTAS['todos_municipios'], "sector_cluster_by_uf.csv"),
        path_porte_UBS = os.path.join(PASTAS['todos_municipios'], "Porte_UBS.xlsx"),
        path_locais_candidatos = path_locais_candidatos[municipio], #TODO: Parametrizar isso !
        path_dados_custo = os.path.join(PASTAS['todos_municipios'], "Dados_custos_finais_formatados.xlsx"), 
        path_result_optimization = path_resultados[municipio],
        path_nome_relatorio_convertido = fr"C:\aps\Resultado_{municipio}_CLUSTER_convertido_para_SC.xlsx"
    )


    # creator = CreatorDatFiles(configuration_data=configs, path_arquivos_data=paths_arquivos, create_distance_file=True)
    # creator.create_file()

    converter = ConvertClusterResults(configuration_data=configs, path_arquivos_data=paths_arquivos)
    converter.convert_results()

    #Dados de setor censitario de contagem estao errados porque tem menos populacao que o real
    # Dados de ACS tambem está errado.
    
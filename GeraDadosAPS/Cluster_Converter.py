from Configuration_data import ConfigurationDataScenario, PathArquivoDados, ExecutionDataType
from Text_Creator import text_messages_creator_By_SC, text_messages_creator_By_Cluster
from scenario_data_builder import ScenarioDataBuilder
from writer_text_in_file import text_writer
import math
import numpy as np
import re
import pandas as pd

class ClusterConverter():
    def __init__(self, scenario_data, path): #TODO: passar aqui todos os dados para realizar as logicas da conversao
        self.scenario_data = scenario_data
        self.final_path = path

    @staticmethod
    def calculate_distance_between_tuples_coords_long_lat(origem, destino):
            #Separar em método de formatar dados e calcular distancias na classe de distancias totais!
            lon1, lat1 = map(math.radians, origem)
            lon2, lat2 = map(math.radians, destino)
            dlon = lon2 - lon1
            dlat = lat2 - lat1

            a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
            c = 2 * math.asin(math.sqrt(a))

            raio_terra_m = 6371000  # raio médio da Terra em metros
            distancia_m = raio_terra_m * c
            return distancia_m

    def calculate_distance_to_sc_from_cluster(self, df_scs_in_cluster, cl):
        df_demanda = self.scenario_data["df_demanda"]
        lat_cluster = df_demanda[df_demanda.cluster == cl]["LAT"].iloc[0]
        long_cluster = df_demanda[df_demanda.cluster == cl]["LONG"].iloc[0]
        origem = (long_cluster, lat_cluster)
        #transformar numa lista e pegar argmin!
        dist_values = list()
        setores = list()
        for _, row in df_scs_in_cluster.iterrows():
            destino = (row.LONG, row.LAT)
            lon1, lat1 = map(math.radians, origem)
            lon2, lat2 = map(math.radians, destino)
            dlon = lon2 - lon1
            dlat = lat2 - lat1

            a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
            c = 2 * math.asin(math.sqrt(a))

            raio_terra_m = 6371000  # raio médio da Terra em metros
            distancia_m = raio_terra_m * c
            dist_values.append(distancia_m)
            setores.append(row.SETOR)

        return setores[np.argmin(dist_values)]

    # def create_outputs_relatorio_Fluxo_PHC(self):
    #     #13-Fluxo_PHC
    #     df_fluxo_original = self.scenario_data["result_dfs"]["13-Fluxo_PHC"]

    def convert_and_create_output_data_to_fluxo_PHC(self):
        self.convert_candidate_locations()
        #self.create_outputs_relatorio_Fluxo_PHC()

    def create_candidate_locations_relation(self):
        """
        Método que vai verificar os clusters candidatos que tiveram UBS abertas
        Para cada cluster candidato aberto:
            ver quantos setores censitarios candidatos tem no cluster
            se tiver 1 setor:
                defino que ele é o candidato aberto
                continue
            se nao:
                calcular distancia do centro do setor até o centro do cluster
                escolha setor com menor distancia
        """
        qntd_un_open = self.scenario_data['result_dfs']['2-NovasUnidades'][self.scenario_data['result_dfs']['2-NovasUnidades']["New Units:"] == "PHC:"].Qty.iloc[0]
        df_fluxo_PHC = self.scenario_data['result_dfs']["13-Fluxo_PHC"]
        df_fluxo_equipes = self.scenario_data['result_dfs']["3-RealocacaoEquipe_PHC"]
        cl_open_fl = [s[s.index('[')+1 : s.index(']')] for s in df_fluxo_PHC.PHC.unique().tolist() if "CLU_" in s]
        cl_com_equipes = [s[s.index('[')+1 : s.index(']')] for s in df_fluxo_equipes["To"].unique().tolist() if "CLU_" in s]
        cl_open = set(cl_open_fl + cl_com_equipes)
        df_base = self.scenario_data['df_relacao_SC_cluster']
        self.cluster_LC_convert_in_SC = dict()
        for cl in cl_open:
            df_scs_in_cluster = df_base[((df_base.cluster == cl) & (df_base.IS_CL == True))]  #CLU_6326 CLU_6117 CLU_6414
            if df_scs_in_cluster.empty:
                df_scs_in_cluster = df_base[((df_base.cluster == cl))]
            if df_scs_in_cluster.shape[0] == 1:
                result = {"sc": df_scs_in_cluster.SETOR.iloc[0], 
                           "lat": df_scs_in_cluster.LAT.iloc[0],
                           "long": df_scs_in_cluster.LONG.iloc[0]}
                self.cluster_LC_convert_in_SC[cl] = result
            elif df_scs_in_cluster.shape[0] > 1: 
                setor = self.calculate_distance_to_sc_from_cluster(df_scs_in_cluster, cl)
                result = {"sc": setor, 
                           "lat": df_scs_in_cluster[df_scs_in_cluster.SETOR == setor].LAT.iloc[0],
                           "long":df_scs_in_cluster[df_scs_in_cluster.SETOR == setor].LONG.iloc[0]
                           }
                self.cluster_LC_convert_in_SC[cl] = result
            
            else:
                df_scs_in_cluster_to_isolated_clusters = df_base[((df_base.cluster == cl))]
                result = {"sc": df_scs_in_cluster_to_isolated_clusters.SETOR.iloc[0], 
                           "lat": df_scs_in_cluster_to_isolated_clusters.LAT.iloc[0],
                           "long": df_scs_in_cluster_to_isolated_clusters.LONG.iloc[0]}
                self.cluster_LC_convert_in_SC[cl] = result


    def convert_patients_flow_relation(self):        
        df_aux =  self.scenario_data['df_relacao_SC_cluster']
        self.relacao_cluster_sc = dict()
        all_clusters = df_aux.cluster.unique()
        for cluster in all_clusters:
            setores = df_aux[df_aux.cluster == cluster].SETOR.to_list()
            populacao = df_aux[df_aux.cluster == cluster].V01006.to_list()
            latitudes = df_aux[df_aux.cluster == cluster].LAT.to_list()
            longitudes = df_aux[df_aux.cluster == cluster].LONG.to_list()

            dict_aux = {"setores": setores, "populacao" : populacao, "lat" : latitudes, "long": longitudes}
            self.relacao_cluster_sc[cluster] = dict_aux

    def create_new_report_12_Fluxo_RegCensitaria(self):
        df_original = self.scenario_data['result_dfs']["12-Fluxo_RegCensitaria"].copy()
        col_clusters = df_original[df_original.RegiaoCensitaria != ">"].RegiaoCensitaria 
        list_final_data = list()

        for _, row in df_original.iterrows():
            if row.RegiaoCensitaria != ">":
                #Aqui estou iniciando uma regiao censitária!
                cluster = row.RegiaoCensitaria
                total_pop = row.Qde_Pop
                continue
            elif row.RegiaoCensitaria == ">":
                #Aqui vou fazer as proporcoes de cada setor do cluster!
                chave = re.search(r'\[(.+?)\]', cluster).group(1)
                SC_data = self.relacao_cluster_sc.get(chave)
                if SC_data != None:
                    for i in range(len(SC_data["setores"])):
                        setor = SC_data["setores"][i]
                        destino = row.Local_Destino
                        pop_c = SC_data["populacao"][i]
                        pop = int(np.floor((row.Qde_Pop / total_pop) * pop_c)) if not  isinstance(pop_c, float) and math.isnan(pop_c) else 0
                        setor_final = re.sub(r'\[(.+?)\]', f'[{setor}]',  cluster)
                        dist = 0
                        list_final_data.append({"cluster": cluster ,
                                                "RegiaoCensitaria": setor_final, 
                                                "Local_Destino": destino, 
                                                "Qde_Pop": pop, 
                                                "Dist (km)": dist})
                else:
                    list_final_data.append({"cluster":cluster ,
                                            "RegiaoCensitaria": "SEM SETOR, AVALIAR!", 
                                            "Local_Destino": 0, 
                                            "Qde_Pop": 0, 
                                            "Dist (km)": 0})

        df = pd.DataFrame(list_final_data)

        #converter as UBS
        for i, row in df.iterrows():
            lc = re.search(r'\[(.+?)\]', row.Local_Destino).group(1)
            setor = self.cluster_LC_convert_in_SC.get(lc)
            if setor != None:
                valor_fim = re.sub(r'\[(.+?)\]', f'[{setor["sc"]}]',  row.Local_Destino)
                df.at[i, 'Local_Destino'] = valor_fim


        #Converte em distancias!
         
        df_setor = self.scenario_data['df_relacao_SC_cluster'].copy()
        list_setores = df_setor.SETOR.to_list()
        df_UBS = self.scenario_data['df_PHC_exists_and_candidadtes'].copy() 
        for i, row in df.iterrows():
            if "tel" in row.Local_Destino:
                dist = 0
            elif "SHC" in row.Local_Destino:
                dist = 20
            elif "THC" in row.Local_Destino:
                dist = 25

            else:
                setor = int(re.search(r'\[(.+?)\]', row.RegiaoCensitaria).group(1))
                ubs = int(re.search(r'\[(.+?)\]', row.Local_Destino).group(1))
                coords_setor = (df_setor[df_setor.SETOR == setor].LONG.iloc[0], df_setor[df_setor.SETOR == setor].LAT.iloc[0])
                if ubs in list_setores:
                    #UBS é um Setor censitário:
                    coord_ubs = (df_setor[df_setor.SETOR == ubs].LONG.iloc[0], df_setor[df_setor.SETOR == setor].LAT.iloc[0])
                else:
                    #ubs é um CNES!
                    coord_ubs = (df_UBS[df_UBS.CO_UNIDADE == ubs].LONG.iloc[0], df_UBS[df_UBS.CO_UNIDADE == ubs].LAT.iloc[0])
                try:
                    dist = round(self.calculate_distance_between_tuples_coords_long_lat(coords_setor, coord_ubs)/1000, 3)
                except:
                    b=0
            
            df.at[i, 'Dist (km)'] = dist



        self.new_report_12_Fluxo_RegCensitaria = df.copy()


    def create_new_report_13_Fluxo_PHC(self):
        df_original = self.scenario_data['result_dfs']["13-Fluxo_PHC"].copy()
        list_final_data = list()
        df_setor = self.scenario_data['df_relacao_SC_cluster'].copy()
        list_setores = df_setor.SETOR.to_list()
        df_UBS = self.scenario_data['df_PHC_exists_and_candidadtes'].copy() 

        
        for _, row in df_original.iterrows():
            if row.PHC != ">":
                #inicio de uma nova unidade!
                #checando se é local candidato
                can_change = False
                phc_original = row.PHC
                lc = re.search(r'\[(.+?)\]', row.PHC).group(1)
                setor = self.cluster_LC_convert_in_SC.get(lc)
                if setor != None:
                    valor_fim = re.sub(r'\[(.+?)\]', f'[{setor["sc"]}]',  row.PHC)
                    #valor_fim = valor_fim.replace(']', '*]')
                    can_change = True
            
            elif row.PHC == ">":
                chave = re.search(r'\[(.+?)\]', row.Local_Destino).group(1)
                SC_data = self.relacao_cluster_sc.get(chave)
                if SC_data != None:
                    for i in range(len(SC_data["setores"])):
                        setor = SC_data["setores"][i]
                        setor_fim = re.sub(r'\[(.+?)\]', f'[{setor}]',  row.Local_Destino)
                        PHC_value = phc_original if can_change == False else valor_fim
                        pop = SC_data["populacao"][i]
                        dist = 0
                        #calcular distancia entre os pontos:
                        ubs = int(re.search(r'\[(.+?)\]', PHC_value).group(1))
                        coords_setor = (df_setor[df_setor.SETOR == setor].LONG.iloc[0], df_setor[df_setor.SETOR == setor].LAT.iloc[0])
                        if ubs in list_setores:
                            #UBS é um Setor censitário:
                            coords_ubs = (df_setor[df_setor.SETOR == ubs].LONG.iloc[0], df_setor[df_setor.SETOR == setor].LAT.iloc[0])
                        else:
                            #ubs é um CNES!
                            coord_ubs = (df_UBS[df_UBS.CO_UNIDADE == ubs].LONG.iloc[0], df_UBS[df_UBS.CO_UNIDADE == ubs].LAT.iloc[0])
                        dist = round(self.calculate_distance_between_tuples_coords_long_lat(coords_setor, coord_ubs)/1000, 3)


                        if can_change == True:
                            phc_end = PHC_value.replace(']', '*]')
                        else:
                            phc_end = PHC_value

                        list_final_data.append({"PHC": phc_end, "Local_Destino": setor_fim, "Qde_Pop": pop, "Dist (km)": dist})
                else:
                    if can_change == True:
                        phc_end = PHC_value.replace(']', '*]')
                        list_final_data.append({"PHC": phc_end, "Local_Destino": row.Local_Destino, "Qde_Pop":row.Qde_Pop, "Dist (km)": 0})
                    else:
                        list_final_data.append({"PHC": phc_original, "Local_Destino": row.Local_Destino, "Qde_Pop":row.Qde_Pop, "Dist (km)": 0})
        
        df = pd.DataFrame(list_final_data)
        self.new_report_13_Fluxo_PHC = df.copy()

    def create_new_report_3_RealocacaoEquipe_PHC(self):
        df_original = self.scenario_data['result_dfs']["3-RealocacaoEquipe_PHC"]
        df_ubs = self.scenario_data['df_PHC_exists_and_candidadtes']
        df_to_export = df_original.copy()  #  

        for i, row in df_to_export.iterrows():
            chave = re.search(r'\[(.+?)\]', row.To).group(1)
            SC_data = self.cluster_LC_convert_in_SC.get(chave)
            if SC_data != None:
                df_to_export.at[i, 'To'] = re.sub(r'\[(.+?)\]', f'[{SC_data["sc"]}]',  row.To)
                #Preciso pegar o centro do setor censitario e o centro da UBS para recalcular a distancia!
                origem = (SC_data["long"], SC_data["lat"])
                cnes_ubs = re.search(r'\[(.+?)\]', row.From).group(1)
                lat_ubs = df_ubs[df_ubs.CO_UNIDADE == int(cnes_ubs)].LAT.iloc[0]
                long_ubs = df_ubs[df_ubs.CO_UNIDADE == int(cnes_ubs)].LONG.iloc[0]

                destino = (long_ubs, lat_ubs)
                dist = round(self.calculate_distance_between_tuples_coords_long_lat(origem, destino) / 1000,2)
                df_to_export.at[i, 'Dist (km)'] = dist


        self.new_report_3_RealocacaoEquipe_PHC = df_to_export.copy()

    def create_new_report_6_ContratacaoEquipe_PHC(self):
        df_original = self.scenario_data['result_dfs']["6-ContratacaoEquipe_PHC"]
        df_to_export = df_original.copy()

        for i, row in df_to_export.iterrows():
            chave = re.search(r'\[(.+?)\]', row.Location).group(1)
            SC_data = self.cluster_LC_convert_in_SC.get(chave)
            if SC_data != None:
                df_to_export.at[i, 'Location'] = re.sub(r'\[(.+?)\]', f'[{SC_data["sc"]}]',  row.Location)

        self.new_report_6_ContratacaoEquipe_PHC = df_to_export.copy()

    def create_new_report_9_Balanceamento_PHC(self):
        df_original = self.scenario_data['result_dfs']["9-Balanceamento_PHC"]
        df_to_export = df_original.copy()

        for i, row in df_to_export.iterrows():
            chave = re.search(r'\[(.+?)\]', row.Loc).group(1)
            SC_data = self.cluster_LC_convert_in_SC.get(chave)
            if SC_data != None:
                df_to_export.at[i, 'Loc'] = re.sub(r'\[(.+?)\]', f'[{SC_data["sc"]}]',  row.Loc)

        self.new_report_9_Balanceamento_PHC = df_to_export.copy()

    def create_new_report_14_Fluxo_SHC(self):
        df_original = self.scenario_data['result_dfs']["14-Fluxo_SHC"]
        final_data = []
        for _, row in df_original.iterrows():
            if isinstance(row.Local_Destino, str) == False:
                SHC = row.SHC
                continue
            if isinstance(row.Local_Destino, str) == True:   
                cluster = re.search(r'\[(.+?)\]', row.Local_Destino).group(1)
                sc_data = self.relacao_cluster_sc.get(cluster)
                if sc_data != None:
                    for i in range(len(sc_data["setores"])):
                        sc_final = re.sub(r'\[(.+?)\]', f'[{sc_data["setores"][i]}]',  row.Local_Destino)
                        data = { "SHC": SHC, "cluster": cluster , "Local_Destino": sc_final , "Qde_Pop":  sc_data["populacao"][i], "Dist (km)": 20.00}
                        final_data.append(data)
                else:
                    data = { "SHC": SHC, "cluster": "Unidade_Existente" , "Local_Destino":row.Local_Destino, "Qde_Pop":  row.Qde_Pop, "Dist (km)": row["Dist (km)"]}
                    final_data.append(data)
        
        self.new_report_14_Fluxo_SHC = pd.DataFrame(final_data)

    def create_new_report_15_Fluxo_THC(self):
        df_original = self.scenario_data['result_dfs']["15-Fluxo_THC"]
        final_data = []
        for _, row in df_original.iterrows():
            if isinstance(row.Local_Destino, str) == False:
                THC = row.Column1
            elif isinstance(row.Local_Destino, str) == True:
                cluster = re.search(r'\[(.+?)\]', row.Local_Destino).group(1)
                sc_data = self.relacao_cluster_sc.get(cluster)
                if sc_data != None:
                    for i in range(len(sc_data["setores"])):
                        sc_final = re.sub(r'\[(.+?)\]', f'[{sc_data["setores"][i]}]',  row.Local_Destino)
                        data = {"Column1": THC, "Local_Destino": sc_final, "Qde_Pop":  sc_data["populacao"][i], "Dist (km)": 25}
                        final_data.append(data)
                else:
                    data = {"Column1": THC, "Local_Destino":row.Local_Destino, "Qde_Pop":  row.Qde_Pop, "Dist (km)": row["Dist (km)"]}
                    final_data.append(data)

        self.new_report_15_Fluxo_THC = pd.DataFrame(final_data)

    def create_new_report_16_uso_PHC(self):
        df_original = self.scenario_data['result_dfs']["16-Uso_PHC"]
        df_to_export = df_original.copy()

        for i, row in df_to_export.iterrows():
            chave = re.search(r'\[(.+?)\]', row.PHC).group(1)
            SC_data = self.cluster_LC_convert_in_SC.get(chave[:-1])
            if SC_data != None:
                phc_convert = re.sub(r'\[(.+?)\]', f'[{SC_data["sc"]}]',  row.PHC)
                valor_fim = phc_convert.replace(']', '*]')
                df_to_export.at[i, 'PHC'] = valor_fim

        self.new_report_16_uso_PHC = df_to_export.copy()


    def export_datas(self):
        path = self.final_path
        dados_novos = {
            "12-Fluxo_RegCensitaria": self.new_report_12_Fluxo_RegCensitaria,
            "13-Fluxo_PHC": self.new_report_13_Fluxo_PHC,
            "3-RealocacaoEquipe_PHC": self.new_report_3_RealocacaoEquipe_PHC,
            "6-ContratacaoEquipe_PHC": self.new_report_6_ContratacaoEquipe_PHC,
            "9-Balanceamento_PHC": self.new_report_9_Balanceamento_PHC,
            "15-Fluxo_THC": self.new_report_15_Fluxo_THC, 
            "14-Fluxo_SHC": self.new_report_14_Fluxo_SHC,
            "16-Uso_PHC": self.new_report_16_uso_PHC,
        }

        sheets_ja_att = list(self.scenario_data["result_dfs"].keys())

        with pd.ExcelWriter(path, engine='openpyxl') as writer:
            for aba in sheets_ja_att:
                if aba in dados_novos:
                    df = dados_novos[aba]
                else:
                    df = self.scenario_data["result_dfs"][aba]
                
                df.to_excel(writer, sheet_name=aba, index=False)





    def convert(self):
        #um método para cada conversao
        self.create_candidate_locations_relation()
        self.convert_patients_flow_relation()
        self.create_new_report_3_RealocacaoEquipe_PHC()
        self.create_new_report_12_Fluxo_RegCensitaria()
        self.create_new_report_13_Fluxo_PHC()
        self.create_new_report_6_ContratacaoEquipe_PHC()
        self.create_new_report_9_Balanceamento_PHC()
        self.create_new_report_14_Fluxo_SHC()
        self.create_new_report_15_Fluxo_THC()
        self.create_new_report_16_uso_PHC()

        self.export_datas()
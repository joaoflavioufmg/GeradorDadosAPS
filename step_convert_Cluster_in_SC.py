from Configuration_data import ConfigurationDataScenario, PathArquivoDados, ExecutionDataType
from Text_Creator import text_messages_creator_By_SC, text_messages_creator_By_Cluster
from scenario_data_builder import ResultConverterDataBuilder
from writer_text_in_file import text_writer
from Cluster_Converter import ClusterConverter

class ConvertClusterResults():
    def __init__(self, 
                configuration_data:ConfigurationDataScenario,
                path_arquivos_data: PathArquivoDados,
                ) -> None:


        self.configuration_data = configuration_data
        self.path_arquivos_data = path_arquivos_data


    
    def convert_results(self):
        data_formatter = ResultConverterDataBuilder(
            self.configuration_data,
            self.path_arquivos_data,
        )
        scenario_data = data_formatter.build()


        #classe de converter
        final_path = self.path_arquivos_data.path_nome_relatorio_convertido
        cluster_converter = ClusterConverter(scenario_data, final_path)
        cluster_converter.convert()

        #exportar dados!



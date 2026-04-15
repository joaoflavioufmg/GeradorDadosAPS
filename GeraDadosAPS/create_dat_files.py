from Configuration_data import ConfigurationDataScenario, PathArquivoDados, ExecutionDataType
from Text_Creator import text_messages_creator_By_SC, text_messages_creator_By_Cluster
from scenario_data_builder import ScenarioDataBuilder
from writer_text_in_file import text_writer


class CreatorDatFiles():
    def __init__(self, 
                configuration_data:ConfigurationDataScenario,
                path_arquivos_data: PathArquivoDados,
                create_distance_file: bool
                ) -> None:
        
        self.configuration_data = configuration_data
        self.path_arquivos_data = path_arquivos_data
        self.texts_variables = list()
        self.create_distance_file = create_distance_file
    



    def create_file(self):

        data_formatter = ScenarioDataBuilder(
            self.configuration_data,
            self.path_arquivos_data,
            self.create_distance_file
        )
        scenario_data = data_formatter.build()

        name_arch = self.configuration_data.name_output_file

        if  self.configuration_data.tipo_rodada == ExecutionDataType.BY_CLUSTER:
            formatter = text_messages_creator_By_Cluster(scenario_data)
        else: 
            formatter = text_messages_creator_By_SC(scenario_data)
        texts_list, text_list_distance = formatter.create_texts()

        writer = text_writer(texts_list, text_list_distance, name_arch)
        writer.write_mutable_arch()
        if self.create_distance_file:
            writer.write_distance_arch()






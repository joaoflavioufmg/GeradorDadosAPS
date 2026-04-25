class text_writer():
    def __init__(self, text_lists, text_list_distance, path_name):
        self.text_lists = text_lists
        self.text_list_distance = text_list_distance
        self.path_name = path_name
    
    def write(self):
        with open(self.path_name, "w", encoding="utf-8") as f:
        
            for text in self.text_lists:
                f.write(text)

            f.write("end;\n")

    def write_mutable_arch(self):
        with open(self.path_name + ".dat", "w", encoding="utf-8") as f:
        
            for text in self.text_lists:
                f.write(text)

            f.write("end;\n")


    def write_distance_arch(self):
        path = self.path_name + "_" + "distance" + ".dat"
        with open(path, "w", encoding="utf-8") as f:
        
            for text in self.text_list_distance:
                f.write(text)

            f.write("end;\n")
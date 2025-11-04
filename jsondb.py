from pydantic import BaseModel
import json 

class JsonDB(BaseModel):
    filepath: str

    def read_data(self):
        with open(self.filepath, 'r') as file:
            data = json.load(file)
        return data

    def write_data(self, data):
        with open(self.filepath, 'w') as file:
            json.dump(data, file, indent=4)


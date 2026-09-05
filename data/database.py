from pathlib import Path
import pandas as pd

class Database():
    sections = ["flips","gaps","peaks","strikes","mean_reversion", "cash_session", "drawdowns"]

    def __init__(self):
            pass     

    @classmethod
    def import_csv(cls, name):
        try:
            section = cls.getSection(name)
            url = cls.url_database() + section + "/" + name + ".csv"
            df = pd.read_csv(url, index_col=0)
            df.index.name = None
            if not df.empty:
                print("CSV importado: ", url)
                return df
            else:    
                return False      
        except Exception as e:
              return False

    @classmethod
    def save_csv(cls, df, name):
        try:
            section = cls.getSection(name)
            url = cls.url_database() + section + "/" + name + ".csv"
            print("CSV guardado: ", url)
            df.to_csv(url)
        except Exception as e:
            print(e)

    @staticmethod
    def url_database():
        current_dir = Path(__file__).resolve()
        father_dir = current_dir.parent.parent.parent
        url = str(father_dir) + "/Database/"
        return url

    @classmethod
    def getSection(cls, name):
        for section in cls.sections:
            if section in name:
                return section
        return "dataframe"

    @classmethod
    def symbol_url(cls):
        return cls.url_database() + "dataframe/"

         
         
        
         
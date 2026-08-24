from analytics.statistics_calculations import *
from analytics.flips_calculation import *

class Database():
    def __init__(self):
            pass     

    @staticmethod
    def import_csv(name):
        try:
            df = pd.read_csv("excels/" + name + ".csv", index_col=0)
            df.index.name = None
            print("Importando", name)
            if not df.empty:
                return df
            else:    
                return False      
        except Exception as e:
              print(e)

    @staticmethod
    def save_csv(df, name, type):
        if type == "symbol":
            dir = "excels/dataframe/" + name + "csv"
        elif type == "statistics":
            dir = "excels/statistics/" + name + "csv"
        df.to_csv(dir)
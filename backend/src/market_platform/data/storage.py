from pathlib import Path
import pandas as pd

def import_csv(name, data_section):
    try:
        url = url_database() + data_section + name + ".csv"
        df = pd.read_csv(url, index_col=0)
        df.index.name = None
        if not df.empty:
            print("CSV importado: ", url)
            return df
        else:    
            return False      
    except Exception as e:
          return False


def save_csv(df, name, data_section):
    try:
        url = url_database() + data_section + name + ".csv"
        print("CSV guardado: ", url)
        df.to_csv(url)
    except Exception as e:
        print(e)


def url_database():
    current_dir = Path(__file__).resolve()
    father_dir = current_dir.parent.parent.parent.parent
    url = str(father_dir) + "/data/"
    return url

     
     
    
     
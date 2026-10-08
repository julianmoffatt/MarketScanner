from abc import ABC, abstractmethod

class Strategy(ABC):
    @abstractmethod
    def compute(self, df, coef) -> float:
        return coef

    def prepare_features(self, df):
        return df

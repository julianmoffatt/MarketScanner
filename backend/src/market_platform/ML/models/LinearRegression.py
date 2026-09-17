from sklearn.model_selection import train_test_split
from sklearn import linear_model
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib as plt
import numpy as np
import pandas as pd
from backend.src.market_platform.ML.base import BaseModel
from registry import ModelRegistry
from sklearn.ensemble import RandomForestClassifier


@ModelRegistry.register("LinearRegression")
class LinearRegression(BaseModel):
    def __init__(self, **hyperparams):
        super().__init__(**hyperparams)
        self.model_ = linear_model.LinearRegression(**hyperparams)
 
    def fit(self, X: pd.DataFrame, y: pd.Series) -> "RandomForestModel":
        self.model_.fit(X, y)          # sklearn ya recibe DataFrame/Series tal cual
        self.is_fitted = True
        return self
 
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.model_.predict(X)

cdf = df[['ENGINESIZE','CYLINDERS','FUELCONSUMPTION_COMB','CO2EMISSIONS']]
X = cdf.ENGINESIZE.to_numpy()
y = cdf.CO2EMISSIONS.to_numpy()

X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.2,random_state=42)
# create a model object
regressor = linear_model.LinearRegression()
# train the model on the training data
# X_train is a 1-D array but sklearn models expect a 2D array as input for the training data, with shape (n_observations, n_features).
# So we need to reshape it. We can let it infer the number of observations using '-1'.
regressor.fit(X_train.reshape(-1, 1), y_train)
# Print the coefficients
print ('Coefficients: ', regressor.coef_[0]) # with simple linear regression there is only one coefficient, here we extract it from the 1 by 1 array.
print ('Intercept: ',regressor.intercept_)
plt.scatter(X_train, y_train,  color='blue')
plt.plot(X_train, regressor.coef_ * X_train + regressor.intercept_, '-r')
plt.xlabel("Engine size")
plt.ylabel("Emission")
# Use the predict method to make test predictions
y_pred = regressor.predict(X_test.reshape(-1,1))
# Evaluation
print("Mean absolute error: %.2f" % mean_absolute_error(y_test, y_pred))
print("Mean squared error: %.2f" % mean_squared_error(y_test, y_pred))
print("Root mean squared error: %.2f" % np.sqrt(mean_squared_error(y_test, y_pred)))
print("R2-score: %.2f" % r2_score(y_test, y_pred))
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

# rf_price_v2.0.0은 rf_price_v1.1.1 을 동적으로 변환시킨 모델

# 1. data load
data = pd.read_csv('../data/preprocessed/weather_with_lag.csv')
label = pd.read_csv('../data/preprocessed/coffee_label.csv')
print(f"1. 데이터 로드: {data.shape}\n")

# 2. 컬럼 분류
categorical_cols = data.select_dtypes(include=['object']).columns.tolist()
categorical_cols = [col for col in categorical_cols if col != 'Date']
numerical_cols = data.select_dtypes(include=['float64', 'int64']).columns.tolist()

# 3. train, valid, test 분류
# today를 기준으로 test, valid, train 기간을 자동으로 설정
data['Date'] = pd.to_datetime(data['Date'])
last_date = pd.to_datetime('today')  # 오늘 날짜를 기준으로 설정

# 3-1. test_data: 오늘 날짜부터 4주 후까지를 test 데이터로 설정
test_end_date = last_date
test_start_date = test_end_date + pd.Timedelta(weeks=4)  # 4주 후로 수정

# 3-2. valid_data: test_data의 첫날 전날부터 1년 전까지를 valid 데이터로 설정
valid_end_date = test_start_date - pd.Timedelta(days=1)
valid_start_date = valid_end_date - pd.Timedelta(weeks=52)

# 3-3. train_data: valid_data의 시작일보다 이전 데이터를 train 데이터로 설정
train_start_date = pd.to_datetime('2020-01-01')
train_data = data[(data['Date'] >= train_start_date) & (data['Date'] < valid_start_date)].copy()
valid_data = data[(data['Date'] >= valid_start_date) & (data['Date'] <= valid_end_date)].copy()
test_data = data[(data['Date'] >= test_start_date) & (data['Date'] <= test_end_date)].copy()

print(f"Train Data: {train_data.shape}")
print(f"Valid Data: {valid_data.shape}")
print(f"Test Data: {test_data.shape}")





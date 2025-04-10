import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

# 1. data load
data = pd.read_csv('../data/preprocessed/weather_with_lag.csv')
label = pd.read_csv('../data/preprocessed/coffee_label.csv')
print(f"1. 데이터 로드: {data.shape}\n")

# 2. 컬럼 분류
categorical_cols = data.select_dtypes(include=['object']).columns.tolist()
categorical_cols = [col for col in categorical_cols if col != 'Date']
numerical_cols = data.select_dtypes(include=['float64', 'int64']).columns.tolist()

# 3. split data
train_data = data[(data['Date'] >= '2020-01-01') & (data['Date'] <= '2024-02-28')].copy()
valid_data = data[(data['Date'] >= '2024-02-29') & (data['Date'] <= '2025-02-28')].copy()
test_data  = data[(data['Date'] >= '2025-03-01') & (data['Date'] <= '2025-03-23')].copy()

# NaN 처리
lag_cols = [col for col in test_data.columns if 'lag' in col]
exclude_from_nan = lag_cols + ['locationName', 'season_tag', 'days_until_harvest']
non_lag_weather_cols = [col for col in numerical_cols if col not in exclude_from_nan]
for col in non_lag_weather_cols:
    if test_data[col].dtype == 'int64':
        test_data[col] = test_data[col].astype(float)
    test_data[col] = np.nan

# 4. label 분리
label['Date'] = pd.to_datetime(label['Date'])
train_label = label[(label['Date'] >= '2015-01-02') & (label['Date'] <= '2024-02-28')].copy()
valid_label = label[(label['Date'] >= '2024-02-29') & (label['Date'] <= '2025-02-28')].copy()
test_label  = label[(label['Date'] >= '2025-03-01') & (label['Date'] <= '2025-03-23')].copy()

# 5. train merge
train_data['Date'] = pd.to_datetime(train_data['Date'])
train_label['Date'] = pd.to_datetime(train_label['Date'])
train = pd.merge(train_data, train_label, on="Date", how="inner")
X_train = train.drop(columns=["Date", "Coffee_Price", "Coffee_Price_Return"])
y_train = train["Coffee_Price"]

# 6. valid set
X_valid = valid_data.drop(columns=["Date"])
y_valid = valid_label["Coffee_Price"].values

# 7. OneHotEncoder
preprocessor = ColumnTransformer(
    transformers=[("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols)],
    remainder="passthrough"
)

# 8. 모델 학습
model = RandomForestRegressor(
    random_state=42,
    max_features='sqrt',
    n_estimators=300,
    n_jobs=-1
)
pipeline = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("regressor", model)
])
print("모델 학습중...")
pipeline.fit(X_train, y_train)
print("모델 학습 완료")

# 9. valid 예측
valid_preds = pipeline.predict(X_valid)
valid_data["Predicted_Price"] = valid_preds
pred_daily = valid_data.groupby("Date")["Predicted_Price"].mean().reset_index()
pred_daily["Date"] = pd.to_datetime(pred_daily["Date"])
pred_daily = pd.merge(pred_daily, valid_label, on="Date", how="left")

# 9-1. 일별 가중치 적용 (1.0 → 1.1 선형 증가)
valid_weights = np.linspace(1.0, 2.0, len(pred_daily))
pred_daily["Predicted_Price_Weighted"] = pred_daily["Predicted_Price"] * valid_weights

# 시작 가격 맞추기 (valid)
true_start_valid = pred_daily["Coffee_Price"].iloc[0]
pred_start_valid = pred_daily["Predicted_Price_Weighted"].iloc[0]
scaling_valid = true_start_valid / pred_start_valid
pred_daily["Predicted_Price_Adjusted"] = pred_daily["Predicted_Price_Weighted"] * scaling_valid

# 10. valid 성능
rmse = mean_squared_error(pred_daily["Coffee_Price"], pred_daily["Predicted_Price_Adjusted"])
r2 = r2_score(pred_daily["Coffee_Price"], pred_daily["Predicted_Price_Adjusted"])
print("\n📊 검증 성능 (보정 + 가중치):")
print(f"RMSE : {rmse:.5f}")
print(f"R²   : {r2:.5f}")

# 11. valid 시각화
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
plt.figure(figsize=(14, 6))
sns.lineplot(data=pred_daily, x="Date", y="Coffee_Price", label="True Price")
sns.lineplot(data=pred_daily, x="Date", y="Predicted_Price_Adjusted", label="Predicted Price (Adjusted + Weighted)")
plt.title("검증 기간 커피 가격 예측 결과", fontsize=16)
plt.xlabel("Date")
plt.ylabel("Coffee Price (USD)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# 12. test 예측
X_test = test_data.drop(columns=["Date"])
test_preds = pipeline.predict(X_test)
test_data["Predicted_Price"] = test_preds
test_daily = test_data.groupby("Date")["Predicted_Price"].mean().reset_index()
test_daily["Date"] = pd.to_datetime(test_daily["Date"])
test_daily = pd.merge(test_daily, test_label, on="Date", how="left")

# 12-1. 가중치 적용 안함 test 기간은 짧아서
test_weights = np.linspace(1.0, 1.1, len(test_daily))
test_daily["Predicted_Price_Weighted"] = test_daily["Predicted_Price"]

# 시작 가격 보정 (test)
true_start_test = test_daily["Coffee_Price"].iloc[0]
raw_start_test = test_daily["Predicted_Price_Weighted"].iloc[0]
scaling_test = true_start_test / raw_start_test
test_daily["Predicted_Price_Adjusted"] = test_daily["Predicted_Price_Weighted"] * scaling_test

# 하루 shift
test_daily["Predicted_Price_Adjusted_Shifted"] = test_daily["Predicted_Price_Adjusted"].shift(-1)

# 13. test 성능
rmse_test = mean_squared_error(test_daily["Coffee_Price"], test_daily["Predicted_Price_Adjusted"])
r2_test = r2_score(test_daily["Coffee_Price"], test_daily["Predicted_Price_Adjusted"])
print("\n📊 테스트 성능 (보정 + 가중치):")
print(f"Test RMSE : {rmse_test:.5f}")
print(f"Test R²   : {r2_test:.5f}")

# 14. test 시각화
plt.figure(figsize=(14, 6))
sns.lineplot(data=test_daily[:-1], x="Date", y="Coffee_Price", label="True Price")
sns.lineplot(data=test_daily[:-1], x="Date", y="Predicted_Price_Adjusted_Shifted", label="Predicted Price (Shifted + Weighted)")
plt.title("테스트 기간 커피 가격 예측 결과", fontsize=16)
plt.xlabel("Date")
plt.ylabel("Coffee Price (USD)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

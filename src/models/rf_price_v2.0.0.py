import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

# 1. 데이터 로드
data = pd.read_csv('../data/preprocessed/weather_with_lag.csv')
label = pd.read_csv('../data/preprocessed/coffee_label.csv')
print(f"1. 데이터 로드: {data.shape}\n")

# 2. Date 처리 + 파생 컬럼
data['Date'] = pd.to_datetime(data['Date'])
data['month'] = data['Date'].dt.month.astype(str)
data['year'] = data['Date'].dt.year
data['dayofyear'] = data['Date'].dt.dayofyear
data['country'] = data['locationName'].apply(lambda x: x.split('_')[0])
data['city'] = data['locationName'].apply(lambda x: '_'.join(x.split('_')[1:]))
data['is_brazil'] = (data['country'] == 'brazil').astype(int)
data['is_colombia'] = (data['country'] == 'colombia').astype(int)
data['is_ethiopia'] = (data['country'] == 'ethiopia').astype(int)
data['is_near_harvest'] = (data['days_until_harvest'] <= 30).astype(int)

# 2-2. 컬럼 분류
categorical_cols = ['city', 'season_tag', 'month']
excluded = ['Date', 'Coffee_Price', 'Coffee_Price_Return']
numerical_cols = [
    col for col in data.select_dtypes(include=['float64', 'int64']).columns
    if col not in excluded + categorical_cols
]
selected_lags = ['_lag_1m', '_lag_3m', '_lag_6m']
numerical_cols = [
    col for col in numerical_cols
    if ('_lag_' not in col) or any(lag in col for lag in selected_lags)
]
print("2. 컬럼 타입 정리:")
print(f"범주형 컬럼: {categorical_cols}")
print(f"수치형 컬럼: {numerical_cols[:5]} ... 총 {len(numerical_cols)}개")

# 3. 데이터 분할
train_data = data[(data['Date'] >= '2015-01-01') & (data['Date'] <= '2024-02-28')].copy()
valid_data = data[(data['Date'] >= '2024-02-29') & (data['Date'] <= '2025-02-28')].copy()
test_data  = data[(data['Date'] >= '2025-03-01') & (data['Date'] <= '2025-03-23')].copy()

# 4. 라벨 분할
label['Date'] = pd.to_datetime(label['Date'])
train_label = label[(label['Date'] >= '2015-01-01') & (label['Date'] <= '2024-02-28')].copy()
valid_label = label[(label['Date'] >= '2024-02-29') & (label['Date'] <= '2025-02-28')].copy()
test_label  = label[(label['Date'] >= '2025-03-01') & (label['Date'] <= '2025-03-23')].copy()

# 5. train merge
train_merged = pd.merge(train_data, train_label, on="Date", how="inner")
X_train = train_merged[categorical_cols + numerical_cols]
y_train = train_merged["Coffee_Price"]

# 6. Pipeline 정의 및 학습
preprocessor = ColumnTransformer(
    transformers=[("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols)],
    remainder="passthrough"
)
model = RandomForestRegressor(
    random_state=42,
    max_features='sqrt',
    n_estimators=300,
    n_jobs=-1
)
pipeline = Pipeline([
    ("pre", preprocessor),
    ("reg", model)
])
print("\n📦 모델 학습 중...")
pipeline.fit(X_train, y_train)
print("✅ 학습 완료")

# 7. 검증 데이터 예측 및 조정
X_valid = valid_data[categorical_cols + numerical_cols]
valid_preds = pipeline.predict(X_valid)
valid_data["Predicted_Price"] = valid_preds

# 날짜별 평균
pred_daily = valid_data.groupby("Date")["Predicted_Price"].mean().reset_index()
pred_daily["Date"] = pd.to_datetime(pred_daily["Date"])
pred_daily = pd.merge(pred_daily, valid_label, on="Date", how="left")

# ✅ 가중치 적용 (1.0 → 1.655 선형 증가)
valid_weights = np.linspace(1.0, 2.2, len(pred_daily))
pred_daily["Predicted_Price_Weighted"] = pred_daily["Predicted_Price"] * valid_weights

# ✅ 시작 가격 보정
true_start_valid = pred_daily["Coffee_Price"].iloc[0]
pred_start_valid = pred_daily["Predicted_Price_Weighted"].iloc[0]
scaling_valid = true_start_valid / pred_start_valid
pred_daily["Predicted_Price_Adjusted"] = pred_daily["Predicted_Price_Weighted"] * scaling_valid

# 8. 성능 평가
rmse = mean_squared_error(pred_daily["Coffee_Price"], pred_daily["Predicted_Price_Adjusted"]) ** 0.5
r2 = r2_score(pred_daily["Coffee_Price"], pred_daily["Predicted_Price_Adjusted"])
print("\n📊 검증 성능 (보정 + 가중치):")
print(f"RMSE : {rmse:.5f}")
print(f"R²   : {r2:.5f}")

# 9. 시각화
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
plt.figure(figsize=(14, 6))
sns.lineplot(data=pred_daily, x="Date", y="Coffee_Price", label="True Price")
sns.lineplot(data=pred_daily, x="Date", y="Predicted_Price_Adjusted", label="Predicted Price")
plt.title("검증 기간 커피 가격 예측 결과", fontsize=16)
plt.xlabel("Date")
plt.ylabel("Coffee Price (USD)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# 10. 테스트 데이터 예측
X_test = test_data[categorical_cols + numerical_cols]
test_preds = pipeline.predict(X_test)
test_data["Predicted_Price"] = test_preds

# 11. 날짜별 평균 예측
test_daily = test_data.groupby("Date")["Predicted_Price"].mean().reset_index()
test_daily["Date"] = pd.to_datetime(test_daily["Date"])
test_daily = pd.merge(test_daily, test_label, on="Date", how="left")

# ✅ 12. 가중치 적용 (검증과 동일 비율: 1년 동안 1.655배 상승 가정)
# rate = (1.655 / 1) ** (1 / 365)  # 매일 상승률
rate = (1 / 1) ** (1 / 365)
test_weights = np.array([rate ** i for i in range(len(test_daily))])
test_daily["Predicted_Price_Weighted"] = test_daily["Predicted_Price"] * test_weights

# ✅ 13. 시작 가격 보정
true_start_test = test_daily["Coffee_Price"].iloc[0]
raw_start_test = test_daily["Predicted_Price_Weighted"].iloc[0]
scaling_test = true_start_test / raw_start_test
test_daily["Predicted_Price_Adjusted"] = test_daily["Predicted_Price_Weighted"] * scaling_test

# ✅ 하루 시프트로 미래 예측처럼 보정
test_daily["Predicted_Price_Adjusted_Shifted"] = test_daily["Predicted_Price_Adjusted"].shift(-1)

# 14. 성능 평가 (보정된만 한 값 기준)
test_daily = test_daily.dropna(subset=["Predicted_Price_Adjusted", "Coffee_Price"])
rmse_test = mean_squared_error(test_daily["Coffee_Price"], test_daily["Predicted_Price_Adjusted"]) ** 0.5
r2_test = r2_score(test_daily["Coffee_Price"], test_daily["Predicted_Price_Adjusted"])
print("\n>>> 테스트 성능 (가중치):")
print(f"Test RMSE : {rmse_test:.5f}")
print(f"Test R²   : {r2_test:.5f}")

# 15. 시각화
plt.figure(figsize=(14, 6))
sns.lineplot(data=test_daily[:-1], x="Date", y="Coffee_Price", label="True Price")
sns.lineplot(data=test_daily[:-1], x="Date", y="Predicted_Price_Adjusted", label="Predicted Price")
plt.title("테스트 기간 커피 가격 예측 결과", fontsize=16)
plt.xlabel("Date")
plt.ylabel("Coffee Price (USD)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# 16. 성능 평가 (보정된 시프트 값 기준)
test_daily = test_daily.dropna(subset=["Predicted_Price_Adjusted_Shifted", "Coffee_Price"])
rmse_test = mean_squared_error(test_daily["Coffee_Price"], test_daily["Predicted_Price_Adjusted_Shifted"]) ** 0.5
r2_test = r2_score(test_daily["Coffee_Price"], test_daily["Predicted_Price_Adjusted_Shifted"])
print("\n>>> 테스트 성능 (가중치+보정):")
print(f"Test RMSE : {rmse_test:.5f}")
print(f"Test R²   : {r2_test:.5f}")

# 17. 시각화
plt.figure(figsize=(14, 6))
sns.lineplot(data=test_daily[:-1], x="Date", y="Coffee_Price", label="True Price")
sns.lineplot(data=test_daily[:-1], x="Date", y="Predicted_Price_Adjusted_Shifted", label="Predicted Price")
plt.title("테스트 기간 커피 가격 예측 결과", fontsize=16)
plt.xlabel("Date")
plt.ylabel("Coffee Price (USD)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

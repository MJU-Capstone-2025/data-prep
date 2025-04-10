import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import root_mean_squared_error, r2_score

# 1. data load
data = pd.read_csv('../data/preprocessed/weather_with_lag.csv')
label = pd.read_csv('../data/preprocessed/coffee_label.csv')
print(f"1. 데이터 로드: {data.shape}\n")

# 2. 범주형, 수치형 컬럼 분할
## 2-1. Date에서 month 파생
data['Date'] = pd.to_datetime(data['Date'])
data['month'] = data['Date'].dt.month.astype(str)

## 2-2 컬럼 분류
categorical_cols = data.select_dtypes(include=['object']).columns.tolist()
numerical_cols = data.select_dtypes(include=['float64', 'int64']).columns.tolist()
date_col = ['Date'] if 'Date' in data.columns else []

print("2. 컬럼 타입 분류:")
print(f"범주형 컬럼: {categorical_cols}")
print(f"수치형 컬럼: {numerical_cols[:5]} : 너무 많아서 5개만 출력, 총 {len(numerical_cols)}개")
print(f"날짜 컬럼: {date_col}\n")

# 3. split data
# train_data: 2015/01/02 - 2024/02/28
# valid_data: 2024/02/29 - 2025/02/28
# test_data:  2025/03/01 - 2025/03/23 
# test data는미래라고 가정. 즉, lag feature, locationName,season_tag,days_until_harvest 을 제외한 모든 기후 데이터는 nan처리

# 3-1. 데이터셋 분할
train_data = data[(data['Date'] >= '2015-01-02') & (data['Date'] <= '2024-02-28')].copy()
valid_data = data[(data['Date'] >= '2024-02-29') & (data['Date'] <= '2025-02-28')].copy()
test_data  = data[(data['Date'] >= '2025-03-01') & (data['Date'] <= '2025-03-23')].copy()
print("3. 데이터셋 분할:")
print(f"train_data: {train_data.shape}")
print(f"valid_data: {valid_data.shape}")
print(f"test_data: {test_data.shape}")

# 3-2. test_data의 원래 컬럼 리스트
lag_cols = [col for col in test_data.columns if 'lag' in col]

# NaN 처리 예외 컬럼 목록
exclude_from_nan = lag_cols + ['locationName', 'season_tag', 'days_until_harvest', 'month']

# 나머지 수치형 중에서 NaN 처리할 컬럼만 추출
non_lag_weather_cols = [col for col in numerical_cols if col not in exclude_from_nan]

# 3-3. NaN 처리 (형 변환 포함)
for col in non_lag_weather_cols:
    if test_data[col].dtype == 'int64':
        test_data[col] = test_data[col].astype(float)
    test_data[col] = np.nan

print(f"nan이 적용된 컬럼만 출력:\n{test_data[non_lag_weather_cols].head(3)}\n")

# 4. label을 train, valid, test 용으로 분리
label['Date'] = pd.to_datetime(label['Date'])

train_label = label[(label['Date'] >= '2015-01-02') & (label['Date'] <= '2024-02-28')].copy()
valid_label = label[(label['Date'] >= '2024-02-29') & (label['Date'] <= '2025-02-28')].copy()
test_label  = label[(label['Date'] >= '2025-03-01') & (label['Date'] <= '2025-03-23')].copy()

print("4. 라벨 분할 완료:")
print(f"train_label: {train_label.shape}")
print(f"valid_label: {valid_label.shape}")
print(f"test_label : {test_label.shape}\n")

# 5. label과 X를 날짜 기준으로 병합: 학습을 위해 train만 병합
# 지역별 데이터가 다수 존재하지만 y(label)는 날짜별 하나라서,
# 각 지역의 X에 동일한 y를 “복제”해서 학습할 수 있게 만들기 위함이다.
# valid는 병합 안 하는 이유: 
# 예측 후, 날짜별로 여러 개의 예측값을 평균 내서 하나의 최종 예측을 만들 계획이기 때문
train = pd.merge(train_data, train_label, on="Date", how="inner")
X_train = train.drop(columns=["Date", "Coffee_Price", "Coffee_Price_Return"])
y_train = train["Coffee_Price_Return"]
print(f"5. train 병합 완료:")
print(f"X_train 행의 수: {X_train.shape[0]}")
print(f"y_train 행의 수: {y_train.shape[0]}")
print(f"X_train 컬럼 개수: {X_train.shape[1]}\n")

# 6. 검증용 데이터 준비
exclude_cols = ['Date']
X_valid = valid_data[[col for col in valid_data.columns if col not in exclude_cols]]
y_valid = valid_label["Coffee_Price_Return"].values
print(f"6. 검증용 데이터 준비 완료:")
print(f"X_valid 컬럼 개수: {X_valid.shape[1]}\n")

# 7. OneHotEncoder 설정
preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols)
    ],
    remainder="passthrough"  # 나머지 수치형 컬럼은 그대로 유지
)


# 8. 모델 학습
model = RandomForestRegressor(
                random_state=42,
                max_features='sqrt',
                n_estimators=300,
                n_jobs=-1)

pipeline = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("regressor", model)
])

print("RandomForestRegressor 모델 학습중...")
pipeline.fit(X_train, y_train)
print("RandomForestRegressor 모델 학습 완료")

# 9. 검증 데이터 예측
valid_preds = pipeline.predict(X_valid)

# 10. 예측 결과에 날짜 붙이기고 날짜별 평균 수익률 계산
valid_data["Predicted_Return"] = valid_preds
pred_daily = valid_data.groupby("Date")["Predicted_Return"].mean().reset_index()
pred_daily = pd.merge(pred_daily, valid_label, on="Date", how="left")

# 11. 예측 가격 복원 (누적 곱 방식)
pred_daily = pred_daily.sort_values("Date").reset_index(drop=True)
pred_prices = [pred_daily['Coffee_Price'].iloc[0]]  # 시작 가격

# 12. 모델 평가
for i in range(1, len(pred_daily)):
    prev_price = pred_prices[-1]
    pred_return = pred_daily.loc[i, 'Predicted_Return']
    pred_prices.append(prev_price * (1 + pred_return))

pred_daily["Predicted_Price"] = pred_prices

rmse = root_mean_squared_error(pred_daily["Coffee_Price_Return"], pred_daily["Predicted_Return"])
r2 = r2_score(pred_daily["Coffee_Price_Return"], pred_daily["Predicted_Return"])

print("\n검증 성능 평가 결과:")
print(f"RMSE : {rmse:.5f}")
print(f"R²   : {r2:.5f}")

# 13. 결과 시각화
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

plt.figure(figsize=(14, 6))
sns.lineplot(data=pred_daily, x="Date", y="Coffee_Price", label="True Price")
sns.lineplot(data=pred_daily, x="Date", y="Predicted_Price", label="Predicted Price")

plt.title("검증 기간 커피 가격 예측 결과", fontsize=16)
plt.xlabel("Date")
plt.ylabel("Coffee Price (USD)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
## 1. 차원 축소

### 1-1. 차원 축소 가능성

| 변수 그룹                                                                  | 내부 상관   | 처리 제안              |
| -------------------------------------------------------------------------- | ----------- | ---------------------- |
| 기온 그룹 (`T2M`, `T2M_MAX`, `T2M_MIN`, `TS`)                              | 매우 높음   | 대표 변수 1~2개만 사용 |
| 풍속 그룹 (`WS10M`, `WS10M_MIN/MAX`, `WS2M`)                               | 매우 높음   | `WS10M` 1개만 선택     |
| 복사/광 그룹 (`ALLSKY_SFC_SW_DWN`, `CLRSKY_SFC_SW_DWN`, `PAR`, `UV_INDEX`) | 높음        | 핵심 지표만 남기기     |
| 기압 (`PS`)                                                                | 독립성 높음 | 반드시 포함 추천       |
| 습도 + 강수량 (`RH2M`, `PRECTOTCORR`)                                      | 상식적 상관 | 둘 다 남길 수 있음     |

### 1-2. 남긴 피쳐

-   `Date`: 날짜 (기상 관측 및 커피 시장 가격 기준 날짜)
-   `T2M` (Temperature at 2 meters): 지면 위 2m 높이에서 측정한 평균 기온 (°C)
-   `WS2M` (Wind Speed at 2 meters): 지면 위 2m 높이에서 측정한 평균 풍속 (m/s)
-   `ALLSKY_SFC_SW_DWN` (All Sky Surface Shortwave Downward Radiation): 구름 포함 전체 하늘에서 지표면으로 내려오는 단파 복사 에너지 (MJ/m²/day)
-   `ALLSKY_SFC_UV_INDEX` (UV Index):자외선 지수 – 피부에 해로운 자외선 복사량의 강도 지수
-   `PRECTOTCORR` (Corrected Total Precipitation):하루 동안의 누적 강수량 (mm/day)
-   `RH2M` (Relative Humidity at 2 meters):지면 위 2m 높이에서 측정된 상대 습도 (%)
-   `PS` (Surface Pressure):지표면에서의 기압 (kPa 또는 hPa)
-   `Coffee_Price`: 뉴욕 ICE 거래소 기준 Arabica 커피 선물 종가 (센트/파운드)
-   `Coffee_Return`: 커피 가격의 일별 수익률 변화율 (전일 대비 비율, % 단위 아님)

## 2. 파생 컬럼

-   `season_tag`: 해당 날짜가 수확기(`harvest`), 수확 전(`pre-harvest`), 부수적 수확기(`sub_harvest`), 비수확기(`off-season`) 중 어느 시기에 해당하는지 나타냄
-   `days_until_harvest`: 해당 날짜로부터 주요 수확기(월 기준)의 시작일까지 남은 날짜 (단위: 일수)
-   `T2M_lag_1m ~ T2M_lag_6m`: 평균 기온의 1~6개월 전 시점 값을 lag feature로 생성
-   `WS2M_lag_1m ~ WS2M_lag_6m`: 2m 풍속의 1~6개월 전 시점 값을 lag feature로 생성
-   `ALLSKY_SFC_SW_DWN_lag_1m ~ _6m`: 단파 복사량의 1~6개월 전 시점 값을 lag feature로 생성
-   `PRECTOTCORR_lag_1m ~ _6m`: 강수량의 1~6개월 전 시점 값을 lag feature로 생성

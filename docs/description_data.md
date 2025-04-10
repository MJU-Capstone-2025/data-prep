# Data Description

## 1. 컬럼 설명

> 줄이 그어져 있는 컬럼은 전처리 과정에서 삭제된 컬럼

### 1-1. 기후 데이터

| 컬럼명                 | 설명                                                 |
| ---------------------- | ---------------------------------------------------- |
| ~~YEAR~~               | ~~연도 정보~~                                        |
| ~~MO~~                 | ~~월 정보~~                                          |
| ~~DY~~                 | ~~일 정보~~                                          |
| Date                   | 날짜 (YYYY-MM-DD 형식)                               |
| ALLSKY_SFC_UV_INDEX    | 전체 하늘 자외선 지수                                |
| ALLSKY_SFC_SW_DWN      | 전체 하늘 지표면 단파 복사량 (W/m²)                  |
| WS2M                   | 지표면(2m) 풍속 (m/s)                                |
| ~~CLRSKY_SFC_SW_DWN~~  | ~~맑은 하늘 지표면 단파 복사량 (W/m²)~~              |
| T2M                    | 2m 기온 (°C)                                         |
| ~~T2M_MAX~~            | ~~최고 기온 (°C)~~                                   |
| ~~T2M_MIN~~            | ~~최저 기온 (°C)~~                                   |
| RH2M                   | 상대 습도 (%)                                        |
| PRECTOTCORR            | 강수량 (mm)                                          |
| PS                     | 기압 (Pa)                                            |
| ~~CLRSKY_SFC_PAR_TOT~~ | ~~맑은 하늘 지표면 광합성 유효복사 (mol/m²/day)~~    |
| ~~WS10M_MAX~~          | ~~10m 최대 풍속 (m/s)~~                              |
| ~~WS10M_MIN~~          | ~~10m 최소 풍속 (m/s)~~                              |
| ~~ALLSKY_KT~~          | ~~전체 하늘 투과율 지수~~                            |
| ~~T2M_RANGE~~          | ~~일교차 (T2M_MAX - T2M_MIN)~~                       |
| ~~WS10M~~              | ~~10m 평균 풍속 (m/s)~~                              |
| ~~TS~~                 | ~~지면 온도 (°C)~~                                   |
| ~~WSC~~                | ~~풍향 코드 혹은 기타 기상 요소~~                    |
| locationName           | 지역 정보 (예: brazil_varginha)                      |
| season_tag             | 수확 시기 구분 (harvest, pre-harvest, off-season 등) |
| days_until_harvest     | 해당 날짜로부터 다음 수확까지 남은 일수              |

#### Lag Features

| 컬럼명                          | 설명                                 |
| ------------------------------- | ------------------------------------ |
| T2M_lag_1m ~ T2M_lag_6m         | 2m 기온의 이전 1~6개월 값            |
| WS2M_lag_1m ~ WS2M_lag_6m       | 지표면 풍속의 이전 1~6개월 값        |
| ALLSKY_SFC_SW_DWN_lag_1m ~ \_6m | 지표면 단파 복사량의 이전 1~6개월 값 |
| ALLSKY_SFC_UV_INDEX_lag_1m~\_6m | 자외선 지수의 이전 1~6개월 값        |
| PRECTOTCORR_lag_1m ~ \_6m       | 강수량의 이전 1~6개월 값             |
| RH2M_lag_1m ~ RH2M_lag_6m       | 상대 습도의 이전 1~6개월 값          |
| PS_lag_1m ~ PS_lag_6m           | 기압의 이전 1~6개월 값               |

### 1-2. 시장 데이터

| 컬럼명                                | 설명                                     |
| ------------------------------------- | ---------------------------------------- |
| ~~Date(조인 기준, 기후 Date를 살림)~~ | ~~날짜 (YYYY-MM-DD 형식)~~               |
| Coffee_Price                          | 커피 가격 (국제 시세 기준)               |
| Crude_Oil_Price                       | 원유 가격 (배럴당 가격, 보통 Brent 기준) |
| USD_KRW                               | 미국 달러 대비 원화 환율                 |
| USD_BRL                               | 미국 달러 대비 브라질 헤알 환율          |
| USD_COP                               | 미국 달러 대비 콜롬비아 페소 환율        |
| USD_ETB                               | 미국 달러 대비 에티오피아 비르 환율      |
| Coffee_Price_Return                   | 커피 가격의 전일 대비 수익률 (%)         |
| Crude_Oil_Price_Return                | 원유 가격의 전일 대비 수익률 (%)         |
| USD_KRW_Return                        | 원-달러 환율의 전일 대비 수익률 (%)      |
| USD_BRL_Return                        | 브라질 환율 수익률                       |
| USD_COP_Return                        | 콜롬비아 환율 수익률                     |
| USD_ETB_Return                        | 에티오피아 환율 수익률                   |
| ~~month~~                             | ~~월 단위 기준일 (YYYY-MM-01 형식)~~     |
| Urea_price                            | 요소비료 가격 (단위: USD/톤 등)          |
| Dap_price                             | 인산디암모늄(DAP) 비료 가격 (USD/톤 등)  |

### 1-3. 거시경제지표 데이터

| 컬럼명                                                        | 설명                                                          |
| ------------------------------------------------------------- | ------------------------------------------------------------- |
| ~~Area(조인 기준, 기후 locationName을 살림)~~                 | ~~국가명 (거시경제 데이터 기준)~~                             |
| ~~Year(조인 기준, 기후 Date을 살림)~~                         | ~~연도 (거시경제 데이터 기준)~~                               |
| Production                                                    | 농업 생산지표 (단위에 따라 다름)                              |
| ~~index~~                                                     | ~~인덱스 구분자 또는 레코드 식별자~~                          |
| Agricultural raw materials exports (% of merchandise exports) | 농업 원자재 수출 비율 (% 기준)                                |
| Merchandise trade (% of GDP)                                  | 상품 무역 비율 (GDP 대비 %)                                   |
| Unemployment, male (% of male labor force)                    | 남성 실업률 (ILO 추정 기준)                                   |
| GDP per capita (current US$)                                  | 1인당 GDP (현재 미국 달러 기준)                               |
| IMF repurchases and charges (TDS, current US$)                | IMF 차입 상환 및 수수료 (달러 기준)                           |
| Food production index (2014-2016 = 100)                       | 식량 생산 지수 (기준 연도: 2014–2016 = 100)                   |
| Political Stability and Absence of Violence/Terrorism...      | 정치 안정성 및 폭력/테러 부재 지표 (상위 90% 신뢰구간 백분위) |
| GDP per capita growth (annual %)                              | 1인당 GDP 연간 성장률 (%)                                     |
| Merchandise exports to low- and middle-income...              | 저/중소득 국가로의 상품 수출 비율 (%)                         |
| Export unit value index (2015 = 100)                          | 수출 단가 지수 (2015년 기준 = 100)                            |
| Rural population                                              | 농촌 인구 수                                                  |
| Permanent cropland (% of land area)                           | 영구 농지 비율 (국토 면적 대비 %)                             |
| Cereal yield (kg per hectare)                                 | 곡물 수확량 (헥타르당 킬로그램)                               |

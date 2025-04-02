# data-prep

## 디렉토리 구조

```
DATA-PREP/
├── data/
│ ├── processed1/
│ ├── processed2/
│ ├── raw/
│ └── description_data.md
│
├── docs/
│
├── src/
│ ├── app.py
│ ├── correlation_visualizer.py
│ ├── get_market_data.py
│ ├── merge_data_with_coffee.py
│ ├── missing_data_handler.py
│ ├── preprocessor1.py
│ └── preprocessor2.py
│
├── .gitignore
└── README.md
```

-   `data/raw/` 에 weather, market raw 데이터가 저장되어 있습니다.
-   `data/porcessed1/` 에 1차 가공(전처리 등)한 weather, market 데이터 저장되어 있습니다.
-   `data/porcessed2/` 에 2차 가공(차원 축소, 파생 컬럼 추가 등)한 weather, market 데이터 저장되어 있습니다.
    > raw 및 가공된 데이터 설명은 [이곳]()에서 확인할 수 있습니다.

## 데이터 가공 파이프라인

0. 기후 raw 데이터는 `data/raw` 에 `국가_지역.csv` 형태로 저장되어 있습니다.(nasa 데이터 활용)

1. `cd src`로 `src` 위치로 이동 후 `app.py`를 실행시킵니다.

    - `get_market_data.py`을 자동으로 실행하여 market 데이터(coffee c, 국제 유가, 환율 등)을 수집합니다.
    - `preprocessor1.py`을 자동으로 실행하여 계절 데이터와 market 데이터를 자동으로 전처리 합니다.
    - `merge_data_with_coffee.py`을 자동으로 실행하여 target 컬럼을 자동으로 병합합니다. 이렇게 가공된 데이터는 `data/processed1/`에 저장됩니다.
    - `preprocessor2.py`을 자동으로 실행하여 상관관계가 매우 높은 컬럼을 삭제하여 차원을 축소하고, 여러 파생 컬럼을 추가합니다.
        > 축소된 컬럼과 파생 컬럼의 정보는 [이곳]()에서 확인 할 수 있습니다.

2. `correlation_visualizer.py` 을 실행하여 데이터의 상관관계 정보를 시각화하여 볼 수 있습니다.

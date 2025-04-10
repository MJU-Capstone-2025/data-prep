# data-prep

> 데이터 설명은 [description_data](https://github.com/MJU-Capstone-2025/data-prep/blob/preprocessing/docs/description_data.md) 문서 참고

## 1. 디렉토리 구조

```
data-prep/
├── data/
│ ├── final/
│ ├── raw/
│
├── docs/
│
├── src/
│ ├── models/
│ ├── collect.py           # 시장 데이터 수집
│ ├── preprocessor.ipynb   # 데이터 전처리 및 raw 데이터 가공
│ └── preprocessor.py      # 데이터 전처리 및 raw 데이터 가공
│
├── .gitignore
└── README.md
```

-   `data/raw/`: 가공되지 않은 데이터 저장
    -   재배 지역의 기후 데이터, 시장 데이터(환율, 커피가격(target), 국제 유가, 비료 가격 등), 경제 지표 등
-   `data/preprocessed/`: 가공되지 않은 데이터(`data/raw/`)를 전처리, 가공 및 통합하여 데이터 저장
-   `src`: 코드 저장 폴더
    -   `src/models/`

## 2. 데이터 수집 및 전처리 코드 실행

1. 터미널에 `cd src` 작성하여 `src` 디렉토리로 진입
2. `python collector.py` 실행하여 시장 데이터 일부 수집
3. `python preprocessor.py` 실행하여 raw 데이터 전처리 및 가공 진행

> 데이터 설명은 [description_data](https://github.com/MJU-Capstone-2025/data-prep/blob/preprocessing/docs/description_data.md) 문서 참고

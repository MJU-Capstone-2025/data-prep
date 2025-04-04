from get_market_data import MarketDataFetcher
from preprocessor1 import Preprocessor1
from join_data_with_market import WeatherCoffeeMerger
from preprocessor2 import Preprocessor2
from merge_weather_data import WeatherDataMerger  

if __name__ == "__main__":
    # 1. 시장 데이터 수집
    fetcher = MarketDataFetcher(start="2015-01-01", end="2025-04-01")
    fetcher.run_all()

    # 2. 날씨 및 마켓 데이터 전처리
    processor = Preprocessor1({})
    processor.run_all()

    # 3. 날씨 + 커피 가격 병합
    merger = WeatherCoffeeMerger()
    merger.run_all()

    # 4. 불필요 feature 제거 + 파생 컬럼 생성
    selected_features = [
        'Date',
        'T2M',
        'WS2M',
        'ALLSKY_SFC_SW_DWN',
        'ALLSKY_SFC_UV_INDEX',
        'PRECTOTCORR',
        'RH2M',
        'PS',
        'Coffee_Price',
        'Coffee_Return'
    ]

    processor2 = Preprocessor2(
        selected_features=selected_features,
        input_dir="../data/processed1",
        output_dir="../data/processed2"
    )
    processor2.run_all()

    merger = WeatherDataMerger()
    merger.run_all()

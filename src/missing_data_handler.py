import pandas as pd
import matplotlib.pyplot as plt

class MissingDataHandler:
    def __init__(self, df, date_col='Date'):
        self.df = df.copy()
        self.date_col = date_col

    def plot_missing_pattern(self, column, title_prefix='📉'):
        """특정 컬럼의 결측치 패턴 시각화"""
        plt.figure(figsize=(14, 3))
        plt.plot(
            pd.to_datetime(self.df[self.date_col]),
            self.df[column].isna().astype(int),
            drawstyle='steps-mid',
            color='red'
        )
        plt.title(f"{title_prefix} {column} missing pattern")
        plt.xlabel("Date")
        plt.ylabel(f"{column} NaN (1)")
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.show()

    def fill_by_monthly_avg(self, cols=[]):
        """결측치를 월별 평균으로 대체 (소수점 둘째 자리로 반올림)"""
        df = self.df.copy()
        df['Month'] = pd.to_datetime(df[self.date_col]).dt.month

        for col in cols:
            monthly_avg = df.groupby('Month')[col].mean().round(2)
            df[col] = df.apply(
                lambda row: monthly_avg[row['Month']] if pd.isna(row[col]) else row[col],
                axis=1
            )
            df[col] = df[col].round(2)

        df.drop(columns='Month', inplace=True)
        self.df = df  # 업데이트된 df 저장
        return df

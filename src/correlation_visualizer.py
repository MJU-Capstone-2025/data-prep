import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob
import os

class CorrelationVisualizer:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.data = None
        self.corr_matrix = None

    def load_data(self):
        try:
            self.data = pd.read_csv(self.csv_path)
            print(f"📁 데이터 로드 완료: {self.csv_path}")
        except Exception as e:
            print(f"❌ 데이터 불러오기 실패: {e}")

    def calculate_correlation(self):
        if self.data is not None:
            numeric_cols = self.data.select_dtypes(include='number')
            self.corr_matrix = numeric_cols.corr()
            print("✅ 상관관계 계산 완료")
        else:
            print("⚠ 데이터가 없습니다. 먼저 load_data()를 호출하세요.")

    import os  # 파일명 추출용

    def plot_correlation_heatmap(self, figsize=(10, 8), cmap="coolwarm", annot=True):
        if self.corr_matrix is not None:
            plt.figure(figsize=figsize)

            if annot:
                annot_matrix = self.corr_matrix.copy()
                for row in annot_matrix.index:
                    for col in annot_matrix.columns:
                        val = annot_matrix.loc[row, col]
                        sign = "+" if val > 0 else ("–" if val < 0 else "")
                        annot_matrix.loc[row, col] = f"{sign}{val:.2f}"
            else:
                annot_matrix = False

            sns.heatmap(
                self.corr_matrix.astype(float),
                annot=annot_matrix,
                cmap=cmap,
                fmt="",
                linewidths=0.5
            )
            # 파일 이름을 제목에 추가
            file_name = os.path.basename(self.csv_path)
            plt.title(f"Correlation Heatmap: {file_name}")
            plt.tight_layout()
            plt.show()
        else:
            print("상관관계 행렬이 없습니다. calculate_correlation()을 먼저 호출하세요.")


    def plot_target_correlation_bar(self, target_col='Coffee_Price', figsize=(8, 5), color='skyblue'):
        if self.corr_matrix is None:
            print("상관관계 행렬이 없습니다. calculate_correlation()을 먼저 호출하세요.")
            return
    
        if target_col not in self.corr_matrix.columns:
            print(f"⚠ '{target_col}' 컬럼이 상관관계 행렬에 없습니다.")
            return
    
        target_corr = self.corr_matrix[target_col].drop(labels=[target_col]).sort_values()
    
        plt.figure(figsize=figsize)
        bars = plt.barh(target_corr.index, target_corr.values, color=color)
    
        for bar in bars:
            width = bar.get_width()
            sign = "+" if width > 0 else ("–" if width < 0 else "")
            plt.text(width, bar.get_y() + bar.get_height()/2, f"{sign}{abs(width):.2f}", va='center')
    
        # 파일 이름을 제목에 추가
        file_name = os.path.basename(self.csv_path)
        plt.title(f"{file_name} — '{target_col}' Correlation")
        plt.xlabel("Correlation Coefficient")
        plt.grid(True, axis='x', linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.show()



if __name__ == "__main__":
    data_files = glob.glob("../data/processed2/*.csv")

    for path in data_files:
        print(f"\n파일 분석 시작: {path}")
        viz = CorrelationVisualizer(path)
        viz.load_data()
        viz.calculate_correlation()
        viz.plot_correlation_heatmap()
        viz.plot_target_correlation_bar(target_col="Coffee_Price")
        viz.plot_target_correlation_bar(target_col="Coffee_Return")

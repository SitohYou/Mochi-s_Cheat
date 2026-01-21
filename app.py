import tkinter as tk
from tkinter import scrolledtext
import threading
import mss
from PIL import Image
import time
from ollama_utils import call_ollama_vision

class MultiSolverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Question Solver")
        self.root.geometry("450x600") # 解説が入るため少し大きく
        self.root.attributes("-topmost", True)

        # --- UI設定 ---
        
        # 1. モード切替スイッチ（解説の有無）
        self.show_explanation = tk.BooleanVar(value=False) # デフォルトはOFF（答えのみ）
        self.mode_check = tk.Checkbutton(
            root, 
            text="解説も詳しく表示する", 
            variable=self.show_explanation,
            font=("Meiryo", 10)
        )
        self.mode_check.pack(pady=5)

        # 2. 実行ボタン
        self.solve_btn = tk.Button(
            root, 
            text="📸 画面内の問題をすべて解く", 
            font=("Meiryo", 12, "bold"), 
            bg="#ddddff", 
            command=self.start_solving
        )
        self.solve_btn.pack(pady=5, fill='x', padx=20)

        # 3. 結果表示エリア（スクロール可能）
        self.result_area = scrolledtext.ScrolledText(root, font=("Meiryo", 11), height=25)
        self.result_area.pack(pady=10, padx=10, fill='both', expand=True)

    def capture_screen(self):
        # 邪魔にならないよう隠す
        self.root.withdraw()
        time.sleep(0.3)

        with mss.mss() as sct:
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
        
        self.root.deiconify()
        return img

    def start_solving(self):
        self.solve_btn.config(state='disabled', text="解析中...")
        self.result_area.delete(1.0, tk.END)
        self.result_area.insert(tk.END, "👀 画面全体から問題を検索中...\n")
        
        thread = threading.Thread(target=self.run_ai)
        thread.start()

    def run_ai(self):
        try:
            image = self.capture_screen()
            is_detail_mode = self.show_explanation.get()
            
            # モードに応じたプロンプト作成
            if is_detail_mode:
                # 解説ありモード
                prompt = """
                画像内の【すべての問題】を検出し、それぞれ解いてください。
                以下のフォーマットで見やすく出力してください。

                【第1問】
                正解: [選択肢の記号]
                解説: [なぜその答えになるのか、文法や計算過程を詳しく]

                【第2問】
                ...
                """
            else:
                # 答えのみモード（高速）
                prompt = """
                画像内の【すべての問題】を検出し、正解のみをリストアップしてください。
                解説は不要です。以下の形式で出力してください。

                Q1: [正解の記号]
                Q2: [正解の記号]
                ...
                """
            
            # AI実行
            response_text = call_ollama_vision(prompt, image)
            
            self.root.after(0, self.update_ui, response_text)

        except Exception as e:
            error_msg = f"エラーが発生しました:\n{e}"
            self.root.after(0, self.update_ui, error_msg)

    def update_ui(self, text):
        self.result_area.delete(1.0, tk.END)
        self.result_area.insert(tk.END, text)
        self.solve_btn.config(state='normal', text="📸 画面内の問題をすべて解く")

if __name__ == "__main__":
    root = tk.Tk()
    app = MultiSolverApp(root)
    root.mainloop()
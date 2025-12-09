import tkinter as tk
import threading
import mss
import google.generativeai as genai
from PIL import Image
import time
import pyautogui
import json
import re

# --- 設定エリア ---
API_KEY = "AIzaSyAf6kpnHqSyaVdcQJfI5eYrst_qD1LWc64" # ★ここにAPIキーを入れる★
MODEL_NAME = 'models/gemini-2.5-flash'

# API設定
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

# PyAutoGUI設定
pyautogui.FAILSAFE = True # マウスを画面の四隅に飛ばすと強制停止
pyautogui.PAUSE = 0.3     # 動作の間隔

class AutoLoopSolver:
    def __init__(self, root):
        print("test")
        self.root = root
        self.root.title("Auto Loop Solver (High Precision)")
        self.root.geometry("350x250")
        self.root.attributes("-topmost", True)
        
        self.is_running = False # ループ管理フラグ

        # ステータス表示
        self.status_label = tk.Label(root, text="停止中", font=("Meiryo", 12, "bold"), fg="gray")
        self.status_label.pack(pady=10)

        # 開始ボタン
        self.start_btn = tk.Button(root, text="▶ 自動周回スタート", font=("Meiryo", 14, "bold"), bg="#ccffcc", command=self.start_loop)
        self.start_btn.pack(pady=5, fill='x', padx=20)

        # 停止ボタン
        self.stop_btn = tk.Button(root, text="■ 停止", font=("Meiryo", 12, "bold"), bg="#ffcccc", command=self.stop_loop, state='disabled')
        self.stop_btn.pack(pady=5, fill='x', padx=20)

        self.log_area = tk.Label(root, text="マウスに触れないでください\n緊急時はマウスを画面左上へ", font=("Meiryo", 9), fg="red")
        self.log_area.pack(pady=10)

    def capture_screen(self):
        # スクショ時は一瞬隠れる（チラつき防止のためwaitなしにする手もあるが、安全のため入れる）
        # ループ中は頻繁に隠れると邪魔なので、今回はあえて隠さずに撮るか、高速にやる
        # ここでは安全をとって「隠さずに」撮る（アプリを画面の隅に置いてください）
        
        with mss.mss() as sct:
            monitor = sct.monitors[1] # メインモニター
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
            
        return img, monitor

    def start_loop(self):
        self.is_running = True
        self.start_btn.config(state='disabled', bg="gray")
        self.stop_btn.config(state='normal', bg="#ff5555")
        self.status_label.config(text="🚀 自動周回中...", fg="green")
        
        # 別スレッドでループ開始
        thread = threading.Thread(target=self.run_loop)
        thread.daemon = True
        thread.start()

    def stop_loop(self):
        self.is_running = False
        self.status_label.config(text="🛑 停止処理中...", fg="orange")

    def run_loop(self):
        while self.is_running:
            try:
                # 1. 画面読み取り
                self.update_ui_text("👀 画面解析中...")
                image, monitor = self.capture_screen()
                
                # 2. AI判断
                prompt = """
                あなたはテスト自動回答ボットです。現在の画面を見て、マウス操作JSONを作成してください。

                【優先順位1: ポップアップ画面】
                もし「Directions」や「End」などのポップアップが出ていて「OK」ボタンがある場合:
                Target: "OK Button" (ボタンの中心) -> "NEXT Button"

                【優先順位2: 問題画面】
                問題文を読み、正解の選択肢(A,B,C,D)を特定する。
                Target: "Correct Option Radio Button" -> "NEXT Button"
                重要: 選択肢の文章部分ではなく、左端にある【丸いラジオボタン】または【記号(A)の文字】の正確な中心座標を指定すること。

                出力形式(JSONのみ):
                [
                    {"target": "名前", "box_2d": [ymin, xmin, ymax, xmax]},
                    {"target": "NEXT", "box_2d": [ymin, xmin, ymax, xmax]}
                ]
                box_2dは0-1000の正規化座標。
                """
                print("test2")
                response = model.generate_content([prompt, image])
                print(response)
                # 3. JSON解析と実行
                json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
                if json_match:
                    actions = json.loads(json_match.group())
                    
                    # 操作実行
                    for action in actions:
                        if not self.is_running: break # 中断チェック
                        
                        target_name = action.get("target", "Unknown")
                        box = action.get("box_2d")
                        
                        if box:
                            self.update_ui_text(f"操作: {target_name}")
                            self.precise_click(box, monitor)
                            time.sleep(0.5) # クリック間のウェイト
                    
                    # 4. 次のページ読み込み待ち
                    self.update_ui_text("⏳ ページ遷移待ち(4秒)...")
                    time.sleep(4) 
                    
                else:
                    self.update_ui_text("⚠️ 解析不能 - リトライ")
                    time.sleep(2)

            except Exception as e:
                print(f"Error: {e}")
                self.update_ui_text("エラー発生 - 待機中")
                time.sleep(3)

        # ループ抜け後の処理
        self.root.after(0, self.reset_ui)

    def precise_click(self, box, monitor):
        """
        座標精度を高めたクリック処理
        """
        ymin, xmin, ymax, xmax = box
        
        # 画面解像度（論理）を取得
        screen_w, screen_h = pyautogui.size()
        
        # 正規化座標(0-1000)から論理座標へ変換
        # AIは画像の中心を0-1000で返すため、それを画面サイズに引き延ばす
        center_x = ((xmin + xmax) / 2 / 1000) * screen_w
        center_y = ((ymin + ymax) / 2 / 1000) * screen_h
        
        # マルチモニター等のオフセット補正（mssのmonitor['left']を使う）
        # ※ pyautoguiはメインモニタ基準なので、通常はオフセット不要だが、
        # サブモニタの場合はここに monitor['left'] を足す必要がある。
        # 今回はメインモニタ前提でシンプルにする。

        # 移動してクリック
        pyautogui.moveTo(center_x, center_y, duration=0.4) # 少しゆっくり動かして精度確認
        time.sleep(0.4)
        pyautogui.click()
        time.sleep(1)

    def update_ui_text(self, text):
        self.root.after(0, lambda: self.status_label.config(text=text))

    def reset_ui(self):
        self.start_btn.config(state='normal', bg="#ccffcc")
        self.stop_btn.config(state='disabled', bg="#ffcccc")
        self.status_label.config(text="停止中", fg="gray")

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoLoopSolver(root)
    root.mainloop()
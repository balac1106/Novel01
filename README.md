# 互動小說創作｜銘潔

視覺小說風格的 Streamlit 介面，依「風格基因」與「動作矩陣」組合 Prompt，並可選接 OpenAI 取得 AI 敘事與狀態更新。

## 安裝與執行

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 功能說明

- **主畫面**：顯示最新一段 AI 敘事；下方為依類別分組的動作按鈕。
- **側邊欄**：可填寫 OpenAI API Key、選擇模型；即時顯示「當前位置 / 服裝狀態 / 銘潔狀態 / 標記進度」。
- **按鈕**：點選後會將「故事歷史 + 當前狀態 + 該按鈕的擴展指令」組合成完整 Prompt。
  - 若已填 API Key，會自動呼叫 API 並把回覆加入歷史，並解析文末狀態區塊更新側邊欄。
  - 若未填，可展開「查看／複製生成的 Prompt」手動貼到其他 AI 使用。
- **重置**：側邊欄「重置狀態與歷史」可清空故事與狀態。

## 專案結構

- `app.py`：Streamlit 主程式（UI、狀態、Prompt 組合、可選 API 呼叫）。
- `config/prompts.py`：系統指令、動作矩陣與按鈕分組。
- `requirements.txt`：依賴（streamlit、openai）。

修改風格或按鈕文案請直接編輯 `config/prompts.py`。

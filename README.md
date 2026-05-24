# ⚗️ AI Test Demos

Python / Brython 互動展示專案，所有程式碼直接在瀏覽器中執行，無需安裝任何環境。

## 📁 專案內容

| 檔案 | 說明 |
|------|------|
| [hello.html](hello.html) | Hello World 測試，展示 Brython 基本用法 |
| [multiplication.html](multiplication.html) | 九九乘法表，帶顏色分級的互動表格 |
| [periodic_table.html](periodic_table.html) | 118 種元素週期表，搜尋、篩選、詳細資訊 |
| [hello.py](hello.py) | 原始 Python 程式碼 |

## 🚀 使用方式

直接下載後用瀏覽器開啟任一 `.html` 檔案即可，不需要安裝 Python 或任何套件。

## 🔧 技術

- **[Brython](https://brython.info/)** — 在瀏覽器中執行 Python 3 的直譯器
- 純 HTML + CSS + Python，無其他框架依賴

---

## 📸 功能說明

### ⚗️ 元素週期表（periodic_table.html）

完整 118 種元素的互動式週期表。

**搜尋框**
- 支援元素符號（`Au`）、中文名（`金`）、英文名（`Gold`）或原子序搜尋
- 不符合的元素自動變暗，即時顯示匹配數量

**篩選器**
- 點擊上方圖例可開啟／關閉各元素類別
- 支援多類別同時篩選，與搜尋功能可疊加使用
- 共 10 種類別：鹼金屬、鹼土金屬、過渡金屬、後過渡金屬、類金屬、非金屬、鹵素、惰性氣體、鑭系、錒系

**詳細資訊面板**
- 點擊任一元素顯示完整資訊
- 常溫狀態（固態／液態／氣態／人工合成）
- 電子組態（如 `[Xe] 4f¹⁴ 5d¹⁰ 6s¹`）
- 主要用途說明

---

### ✖️ 九九乘法表（multiplication.html）

- 完整 9×9 表格，共 81 組算式
- 數值顏色分級（綠／藍／紫）
- 對角線橘色粗體標示

---

## 📄 授權

MIT License

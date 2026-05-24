# 🏦 美股全自動交易系統 — 軟體開發計劃書

> **版本**：v1.0.0 | **日期**：2026-05-24  
> **提醒**：本系統所有輸出內容（排名、績效、分析）僅供資訊整理與研究參考，**不構成投資建議**。

---

## 📌 專案概述

本系統透過 Alpaca Markets API 實現美股全自動投資管理，涵蓋自動下單、每日報告、視覺化儀表板與 Email 通知，設計原則為：**簡單白話、可追蹤、可視覺化、可自動通知**。

### 核心設計原則
| 原則 | 說明 |
|------|------|
| 策略即 JSON | 新增策略只需新增 JSON 檔，不需修改 Python 程式碼 |
| 多帳戶支援 | 同一時間每帳戶僅能使用一策略，但可切換 |
| Model-View 分離 | 報告資料（JSON）與顯示（HTML/Email）完全分離 |
| GitHub Actions 驅動 | 每日交易、報告生成全部由 CI/CD 自動執行 |
| 歷史報告儲存 | 所有日報可供客戶回查 |
| 整數股原則 | 只買整數股，避免碎股 |

---

## 🗂 目錄結構

```
alpaca-autotrader/
├── .github/
│   └── workflows/
│       ├── daily_trading.yml       # 每日自動交易（所有帳戶）
│       ├── daily_report.yml        # 每日報告 + Email（06:00 AM）
│       └── monthly_rebalance.yml   # 每月初再平衡
│
├── accounts/
│   ├── account_registry.json       # 帳戶列表與策略指派
│   └── account_template.json       # 新增帳戶範本
│
├── strategies/
│   ├── nasdaq_top10.json           # Nasdaq Top 10 策略
│   ├── sp500_growth.json           # S&P 500 成長策略
│   └── watchlist_custom.json       # 自定義關注清單策略
│
├── reports/
│   ├── model/                      # 每日 JSON 報告資料
│   │   └── YYYY-MM-DD/
│   │       └── {account_id}.json
│   └── views/                      # 渲染後的 HTML 報告
│       └── YYYY-MM-DD/
│           └── {account_id}.html
│
├── src/
│   ├── core/
│   │   ├── alpaca_client.py        # Alpaca API 封裝層
│   │   ├── account_manager.py      # 多帳戶管理
│   │   └── strategy_engine.py      # 策略載入與執行
│   ├── trading/
│   │   ├── executor.py             # 下單執行
│   │   ├── rebalancer.py           # 再平衡邏輯
│   │   └── position_manager.py     # 持倉管理
│   ├── analytics/
│   │   ├── market_data.py          # 市場資料取得
│   │   ├── top10_analyzer.py       # Top 10 Nasdaq 分析
│   │   ├── pe_calculator.py        # 本益比（P/E）計算
│   │   ├── predictor.py            # 隔日預測模型
│   │   └── benchmark.py            # Nasdaq/S&P500 比對
│   ├── reports/
│   │   ├── report_model.py         # 產生 JSON 報告資料
│   │   ├── report_view.py          # 渲染 HTML 視圖
│   │   └── email_sender.py         # Email 發送
│   ├── dashboard/
│   │   ├── app.py                  # Streamlit 主程式
│   │   ├── pages/
│   │   │   ├── overview.py         # 帳戶總覽
│   │   │   ├── positions.py        # 持倉明細
│   │   │   ├── top10.py            # Top 10 分析
│   │   │   └── history.py          # 歷史報告查閱
│   │   └── components/
│   │       ├── nav_chart.py        # NAV 走勢圖元件
│   │       └── watchlist.py        # 關注股票元件
│   └── notifications/
│       └── notifier.py             # 即時交易通知
│
├── tests/
│   ├── phase1/                     # Phase 1 測試
│   ├── phase2/                     # Phase 2 測試
│   ├── phase3/                     # Phase 3 測試
│   ├── phase4/                     # Phase 4 測試
│   ├── phase5/                     # Phase 5 測試
│   ├── phase6/                     # Phase 6 測試
│   └── phase7/                     # Phase 7 測試
│
├── config/
│   ├── settings.json               # 全域設定
│   └── watchlists.json             # 三大關注類別股票
│
├── CLAUDE.md                       # 🔖 專案記憶點（快速上手）
├── PROJECT_PLAN.md                 # 本計劃書
├── requirements.txt
└── README.md
```

---

## 📐 資料模型（JSON 格式定義）

### 1. 帳戶登錄檔 `accounts/account_registry.json`
```json
{
  "accounts": [
    {
      "account_id": "ACC001",
      "name": "主帳戶（Paper Trading）",
      "api_key_env": "ALPACA_KEY_ACC001",
      "api_secret_env": "ALPACA_SECRET_ACC001",
      "base_url": "https://paper-api.alpaca.markets",
      "active_strategy": "nasdaq_top10",
      "email": "user@example.com",
      "timezone": "America/New_York",
      "enabled": true,
      "created_at": "2026-05-24"
    }
  ]
}
```

### 2. 策略定義 `strategies/nasdaq_top10.json`
```json
{
  "strategy_id": "nasdaq_top10",
  "strategy_name": "Nasdaq 市值前十等權重策略",
  "version": "1.0.0",
  "description": "每日追蹤 Nasdaq 市值前 10 大股票，各投入 10%，只買整數股",
  "universe": {
    "source": "nasdaq100",
    "filter": "market_cap",
    "top_n": 10,
    "exclude": []
  },
  "allocation": {
    "method": "equal_weight",
    "per_stock_pct": 10,
    "integer_shares_only": true,
    "cash_buffer_pct": 0
  },
  "rebalance": {
    "monthly_on_first_trading_day": true,
    "on_new_funds": true,
    "drift_threshold_pct": 5
  },
  "risk": {
    "max_single_position_pct": 15,
    "stop_loss_pct": null,
    "take_profit_pct": null
  },
  "execution": {
    "order_type": "market",
    "time_in_force": "day",
    "sell_before_buy": true,
    "delay_between_orders_ms": 300
  },
  "watchlists": {
    "categories": ["tech", "semiconductor", "ai"]
  }
}
```

### 3. 每日報告模型 `reports/model/YYYY-MM-DD/{account_id}.json`
```json
{
  "report_date": "2026-05-24",
  "account_id": "ACC001",
  "account_name": "主帳戶",
  "strategy_id": "nasdaq_top10",
  "generated_at": "2026-05-24T06:00:00",
  "summary": {
    "nav": 105234.50,
    "cash": 5234.50,
    "invested": 100000.00,
    "daily_pnl": 234.50,
    "daily_pnl_pct": 0.0022,
    "weekly_pnl_pct": 0.0185,
    "monthly_pnl_pct": 0.0421,
    "total_return_pct": 0.0523,
    "annual_return_pct": 0.1823,
    "max_drawdown_pct": -0.0312,
    "sharpe_ratio": 1.42
  },
  "positions": [
    {
      "symbol": "NVDA",
      "name": "NVIDIA Corp",
      "qty": 45,
      "avg_entry_price": 125.30,
      "current_price": 131.20,
      "market_value": 5904.00,
      "weight_pct": 10.2,
      "target_weight_pct": 10.0,
      "pnl_amount": 265.50,
      "pnl_pct": 0.0471,
      "pnl_1d_pct": 0.0082,
      "pnl_1w_pct": 0.0231,
      "pnl_1m_pct": 0.0612,
      "pe_ratio": 42.3,
      "market_cap_bn": 3220.5
    }
  ],
  "top10_today": [
    {
      "rank": 1,
      "symbol": "NVDA",
      "reason": "市值最大、動能最強",
      "signal_score": 0.92,
      "predicted_next_day_direction": "up",
      "predicted_confidence": 0.68
    }
  ],
  "trades_today": [
    {
      "time": "2026-05-24T09:35:00",
      "symbol": "NVDA",
      "side": "buy",
      "qty": 5,
      "price": 131.20,
      "amount": 656.00,
      "reason": "再平衡調整"
    }
  ],
  "benchmark": {
    "qqq": {
      "daily_pct": 0.0019,
      "weekly_pct": 0.0162,
      "monthly_pct": 0.0389,
      "nav_normalized": [
        {"date": "2026-01-02", "value": 100000},
        {"date": "2026-05-24", "value": 105123}
      ]
    },
    "spy": {
      "daily_pct": 0.0011,
      "weekly_pct": 0.0098,
      "monthly_pct": 0.0271,
      "nav_normalized": []
    }
  },
  "nav_history": [
    {"date": "2026-01-02", "value": 100000},
    {"date": "2026-05-24", "value": 105234}
  ],
  "watchlist_snapshot": {
    "tech": [
      {"symbol": "AAPL", "price": 198.5, "daily_pct": 0.012, "pe_ratio": 29.1}
    ],
    "semiconductor": [
      {"symbol": "NVDA", "price": 131.2, "daily_pct": 0.008, "pe_ratio": 42.3}
    ],
    "ai": [
      {"symbol": "META", "price": 542.0, "daily_pct": 0.021, "pe_ratio": 24.7}
    ]
  }
}
```

### 4. 全域設定 `config/settings.json`
```json
{
  "app": {
    "name": "Alpaca Auto Trader",
    "version": "1.0.0",
    "timezone": "America/New_York"
  },
  "email": {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_env": "EMAIL_SENDER",
    "password_env": "EMAIL_PASSWORD",
    "send_time_local": "06:00"
  },
  "market": {
    "data_feed": "iex",
    "benchmark_symbols": ["QQQ", "SPY"],
    "trading_days_per_year": 252
  },
  "dashboard": {
    "port": 8501,
    "auto_refresh_seconds": 60
  },
  "notifications": {
    "on_trade_executed": true,
    "on_rebalance": true,
    "on_daily_report": true
  }
}
```

### 5. 關注清單 `config/watchlists.json`
```json
{
  "categories": {
    "tech": {
      "display_name": "科技龍頭",
      "symbols": ["AAPL", "MSFT", "GOOGL", "META", "AMZN"]
    },
    "semiconductor": {
      "display_name": "半導體",
      "symbols": ["NVDA", "AVGO", "AMD", "QCOM", "INTC"]
    },
    "ai": {
      "display_name": "AI 概念",
      "symbols": ["NVDA", "META", "MSFT", "PLTR", "ARM"]
    }
  }
}
```

---

## 🚀 開發階段規劃

> **規則**：每一階段的所有測試案例全數通過後，才能進入下一階段。

---

### Phase 1｜基礎建設與多帳戶連接
**目標**：建立穩定的 API 連接層與多帳戶管理框架

**功能清單**
- [ ] 建立 Git Repo 與目錄結構
- [ ] Alpaca API 封裝（GET/POST/DELETE 通用層）
- [ ] 多帳戶管理：從 `account_registry.json` 載入帳戶
- [ ] 環境變數管理（API Key/Secret 不寫入程式）
- [ ] 連接測試：帳戶狀態、現金餘額、持倉查詢
- [ ] 錯誤處理：超時、Rate Limit、API 錯誤

**測試案例 `tests/phase1/`**
```
TC-1-01  成功載入 account_registry.json，帳戶數量正確
TC-1-02  使用正確 API Key 連接 Alpaca，回傳帳戶狀態 ACTIVE
TC-1-03  使用錯誤 API Key，系統應拋出明確錯誤訊息而非崩潰
TC-1-04  同時初始化 2 個以上帳戶，各自獨立運作
TC-1-05  API 超時（設定 3 秒），自動重試最多 3 次
TC-1-06  查詢現金餘額，回傳數值 >= 0
TC-1-07  查詢持倉清單，空帳戶回傳空陣列 []
TC-1-08  停用帳戶（enabled: false）不被初始化
```

**完成標準**：8 個測試案例全部 PASS，無 Exception 崩潰

---

### Phase 2｜策略引擎（JSON 驅動）
**目標**：實現從 JSON 載入策略並執行買賣邏輯，不需修改 Python 程式碼

**功能清單**
- [ ] 策略 JSON Schema 驗證器
- [ ] 策略載入器：從 `strategies/` 資料夾動態載入
- [ ] 帳戶↔策略對應（每帳戶最多一個啟用策略）
- [ ] 帳戶切換策略功能
- [ ] 取得 Nasdaq Top 10 市值股清單
- [ ] 計算目標股數（10% 等權 × 整數股）
- [ ] 買賣訂單執行（先賣後買）
- [ ] 新資金進入時自動觸發再平衡

**測試案例 `tests/phase2/`**
```
TC-2-01  載入 nasdaq_top10.json，所有欄位驗證通過
TC-2-02  載入格式錯誤的策略 JSON，應回傳明確錯誤而非崩潰
TC-2-03  取得 Nasdaq Top 10 清單，回傳恰好 10 檔股票
TC-2-04  帳戶現金 $100,000、每股 10%，計算出正確整數股數
TC-2-05  股價 $1,000 以上（如 COST），計算整數股數 >= 1
TC-2-06  先賣出超額持倉，再買入不足持倉
TC-2-07  下單後，持倉列表在 30 秒內更新
TC-2-08  帳戶 A 切換策略後，策略 ID 正確更新至 account_registry.json
TC-2-09  新增全新 JSON 策略（不修改 Python），系統正常載入並執行
TC-2-10  同帳戶不允許同時有兩個啟用策略
```

**完成標準**：10 個測試案例全部 PASS

---

### Phase 3｜每日報告系統（Model-View 分離）
**目標**：每日產生 JSON 報告資料（Model），並渲染為 HTML/Email（View），且支援歷史查閱

**功能清單**
- [ ] 報告 Model：產生完整 JSON 報告（含所有欄位）
- [ ] 報告 View：將 JSON 渲染為 HTML 視覺化報告
- [ ] 損益計算：日/週/月報酬率
- [ ] 最大回撤（Drawdown）計算
- [ ] NAV 歷史走勢資料
- [ ] 本益比（P/E Ratio）計算與顯示
- [ ] 歷史報告儲存（日期目錄結構）
- [ ] 客戶查詢歷史報告 API

> 💡 **名詞補充**：本益比（P/E Ratio）= 股價 ÷ 每股盈餘，數字越低代表相對便宜，但需結合成長性判斷

**測試案例 `tests/phase3/`**
```
TC-3-01  產生今日 JSON 報告，所有必要欄位均存在
TC-3-02  報告日期欄位與今日日期一致
TC-3-03  日損益計算正確（與 Alpaca API 帳戶資料一致）
TC-3-04  週報酬率 = 本週首日 NAV 至今日 NAV 的百分比變化
TC-3-05  最大回撤計算：模擬已知 NAV 序列，驗證結果
TC-3-06  P/E Ratio 計算：已知股票 EPS 與股價，驗證計算結果
TC-3-07  JSON Model 渲染為 HTML，HTML 包含所有必要區塊
TC-3-08  報告儲存至 reports/model/YYYY-MM-DD/{account_id}.json
TC-3-09  查詢 2 天前的歷史報告，能正確回傳該日 JSON
TC-3-10  報告 Model 與 View 完全分離，修改 HTML 模板不影響資料層
```

**完成標準**：10 個測試案例全部 PASS

---

### Phase 4｜Streamlit 視覺化儀表板
**目標**：建立可操作的每日儀表板，支援多帳戶切換與歷史查閱

**功能清單**
- [ ] 帳戶選擇器（多帳戶切換）
- [ ] 現金水位顯示卡
- [ ] 持倉股票清單（含 1日/1週/1月 損益%）
- [ ] NAV 走勢折線圖（可勾選 QQQ、SPY 對比）
- [ ] 回撤（Drawdown）曲線圖
- [ ] Nasdaq Top 10 市值分析表
- [ ] 三大關注類別股票區塊（科技龍頭/半導體/AI）
- [ ] 歷史報告查閱頁面（日期選擇器）
- [ ] 每日最強前十（含隔日預測方向）
- [ ] 60 秒自動刷新

**測試案例 `tests/phase4/`**
```
TC-4-01  啟動 Streamlit app，無錯誤，頁面正確載入
TC-4-02  切換帳戶，儀表板所有資料隨之更新
TC-4-03  現金水位卡顯示值與 API 回傳值一致
TC-4-04  持倉清單顯示所有持倉，欄位完整
TC-4-05  1日/1週/1月損益%顯示正確，正值綠色/負值紅色
TC-4-06  NAV 圖勾選 QQQ，QQQ 曲線正確疊加
TC-4-07  NAV 圖取消勾選 SPY，SPY 曲線正確消失
TC-4-08  回撤曲線最低點與 JSON 報告中的 max_drawdown_pct 一致
TC-4-09  歷史頁面選擇過去日期，正確顯示該日報告
TC-4-10  60 秒後頁面自動刷新，資料為最新
```

**完成標準**：10 個測試案例全部 PASS

---

### Phase 5｜Email 通知系統
**目標**：每日 06:00（美東時間）發送日報 Email，交易執行時即時通知

**功能清單**
- [ ] SMTP 連接設定（支援 Gmail、SendGrid）
- [ ] 每日 06:00 日報 Email（HTML 格式）
- [ ] Email 內容：NAV、損益、持倉摘要、Top 10、三大類關注股
- [ ] 即時交易通知（下單成功後 30 秒內）
- [ ] 再平衡通知（含交易明細）
- [ ] 支援多收件人（每帳戶可設定不同 Email）
- [ ] Email 底部固定加入風險提醒

**Email 模板結構**
```
主旨：【帳戶日報】{date} | NAV ${nav} | 今日損益 {pnl}

內容：
1. 帳戶摘要（NAV / 現金 / 今日損益 / 總報酬）
2. 持倉概況（前 5 大持倉）
3. 今日 Top 10 Nasdaq 分析
4. 三大關注類別速報
5. 今日交易紀錄
6. ⚠️ 風險提醒（固定）
```

**測試案例 `tests/phase5/`**
```
TC-5-01  SMTP 連接成功，使用測試信箱收到測試 Email
TC-5-02  Email HTML 格式正確，無破版
TC-5-03  Email NAV 數值與 JSON 報告一致
TC-5-04  模擬帳戶 A 與帳戶 B 各自收到各自的 Email，不混淆
TC-5-05  下單成功後 30 秒內，收到交易通知 Email
TC-5-06  再平衡後，Email 內含完整買賣明細
TC-5-07  SMTP 失敗時，系統記錄錯誤日誌，但不中斷主流程
TC-5-08  Email 底部包含風險提醒文字
TC-5-09  收件人 Email 格式錯誤，系統跳過並繼續處理其他帳戶
```

**完成標準**：9 個測試案例全部 PASS

---

### Phase 6｜GitHub Actions 自動化
**目標**：所有每日作業由 GitHub Actions 自動執行，一條 Workflow 走過所有帳戶

**Workflow 設計**

```yaml
# daily_trading.yml
# 觸發：美東時間 09:31（盤中開盤後 1 分鐘）
# 流程：帳戶 A → 策略執行 → 帳戶 B → 策略執行 → ... → 完成通知

name: Daily Auto Trading
on:
  schedule:
    - cron: '31 13 * * 1-5'   # UTC 13:31 = EST 09:31
  workflow_dispatch:            # 允許手動觸發

jobs:
  trade-all-accounts:
    runs-on: ubuntu-latest
    steps:
      - name: 載入所有帳戶
        # 讀取 account_registry.json
      - name: 依序執行策略
        # for each account → load strategy → execute
      - name: 發送交易通知
```

```yaml
# daily_report.yml
# 觸發：美東時間 06:00
name: Daily Report & Email
on:
  schedule:
    - cron: '0 11 * * 1-5'    # UTC 11:00 = EST 06:00
```

```yaml
# monthly_rebalance.yml
# 觸發：每月第一個交易日 09:35
name: Monthly Rebalance
on:
  schedule:
    - cron: '35 13 1-7 * 1'   # 每月 1-7 日的週一
```

**測試案例 `tests/phase6/`**
```
TC-6-01  手動觸發 daily_trading.yml，所有帳戶依序執行
TC-6-02  帳戶 A 執行失敗（API 錯誤），帳戶 B 仍繼續執行（不中斷）
TC-6-03  daily_report.yml 產生報告 JSON 並提交至 repo
TC-6-04  monthly_rebalance.yml 正確識別每月第一個交易日
TC-6-05  Workflow 執行時間記錄到日誌
TC-6-06  Secrets 中的 API Key 不出現在任何 log 輸出中
TC-6-07  Workflow 完成後，GitHub Actions Summary 顯示各帳戶執行狀態
TC-6-08  週末日期不觸發 Trading Workflow（cron 已限定 1-5）
```

**完成標準**：8 個測試案例全部 PASS

---

### Phase 7｜進階分析功能
**目標**：提供 Top 10 深度分析、隔日預測、本益比追蹤

**功能清單**
- [ ] 每日市值前 10 Nasdaq 股票完整分析
- [ ] 每日最強前 10 股票（動能 + 成交量 + 技術面綜合評分）
- [ ] 隔日漲跌方向預測（機率模型，不保證準確）
- [ ] 本益比（P/E）每日計算與歷史追蹤
- [ ] 三大類別關注股票即時狀態
- [ ] 個股 1日/1週/1月報酬率自動計算

> ⚠️ **重要提醒**：隔日預測為統計模型，準確率有限，僅供參考，不構成投資建議

**測試案例 `tests/phase7/`**
```
TC-7-01  取得 Nasdaq 市值前 10，回傳資料含市值、股價、本益比
TC-7-02  最強前 10 評分計算，分數介於 0~1 之間
TC-7-03  隔日預測回傳方向（up/down/neutral）及信心度（0~1）
TC-7-04  P/E Ratio 計算：AAPL 本益比與 Yahoo Finance 誤差 < 10%
TC-7-05  三大類別股票資料完整（symbol、價格、日損益%）
TC-7-06  個股 1日損益% = (今日收盤 - 昨日收盤) / 昨日收盤
TC-7-07  歷史本益比資料儲存，可查詢過去 30 天任一天的 P/E
```

**完成標準**：7 個測試案例全部 PASS

---

## 🔧 技術棧

| 層次 | 工具 | 用途 |
|------|------|------|
| 語言 | Python 3.12 | 主要開發語言 |
| 交易 API | Alpaca Markets | 帳戶管理、下單、市場資料 |
| 儀表板 | Streamlit | 視覺化 Dashboard |
| 圖表 | Plotly | 互動式走勢圖 |
| Email | smtplib / SendGrid | 日報與即時通知 |
| CI/CD | GitHub Actions | 每日自動交易與報告 |
| 資料格式 | JSON | 策略定義、報告模型 |
| 版本控制 | Git / GitHub | 程式碼管理與觸發 |
| 環境變數 | GitHub Secrets | API Key 安全儲存 |
| 測試 | pytest | 自動化測試 |
| 資料驗證 | jsonschema | JSON 策略格式驗證 |

---

## 📋 GitHub Secrets 設定清單

在 GitHub Repo → Settings → Secrets 新增以下 Secrets：
```
ALPACA_KEY_ACC001         # 帳戶 001 的 API Key
ALPACA_SECRET_ACC001      # 帳戶 001 的 API Secret
ALPACA_KEY_ACC002         # 帳戶 002 的 API Key（多帳戶）
ALPACA_SECRET_ACC002      # 帳戶 002 的 API Secret
EMAIL_SENDER              # 發件人 Email
EMAIL_PASSWORD            # Email 應用程式密碼
```

---

## 📅 開發時程估算

| 階段 | 說明 | 預估時間 |
|------|------|----------|
| Phase 1 | 基礎建設 & 多帳戶連接 | 1 週 |
| Phase 2 | 策略引擎（JSON 驅動） | 1.5 週 |
| Phase 3 | 報告系統（Model-View） | 1.5 週 |
| Phase 4 | Streamlit 儀表板 | 2 週 |
| Phase 5 | Email 通知系統 | 1 週 |
| Phase 6 | GitHub Actions 自動化 | 1 週 |
| Phase 7 | 進階分析功能 | 2 週 |
| **合計** | | **約 10 週** |

---

## 🔖 CLAUDE.md 專案記憶點

> 這個檔案供下次開發或其他開發人員快速上手

```markdown
# CLAUDE.md — 專案快速導覽

## 這個專案是什麼？
Alpaca Markets 美股全自動交易系統，支援多帳戶、JSON 策略、Streamlit Dashboard、GitHub Actions 自動執行。

## 最重要的設計決策
1. **策略 = JSON**：新增策略只改 JSON，不動 Python 程式碼
2. **報告 Model-View 分離**：資料（JSON）與顯示（HTML）完全分開
3. **GitHub Actions 主導**：所有排程作業（交易、報告、再平衡）皆由 GHA 觸發
4. **整數股原則**：只買整數股，不買碎股

## 快速啟動
1. 設定 GitHub Secrets（見 PROJECT_PLAN.md）
2. 設定 accounts/account_registry.json
3. 選擇策略放入 strategies/
4. 推送至 main branch → GHA 自動接管

## 帳戶與策略對應
- 每帳戶同一時間只能有一個 active_strategy
- 切換策略：修改 account_registry.json 中的 active_strategy 欄位
- 切換後下次 GHA 執行時生效

## 關鍵檔案位置
- 帳戶設定：accounts/account_registry.json
- 策略定義：strategies/*.json
- 每日報告：reports/model/YYYY-MM-DD/
- 全域設定：config/settings.json
- 關注清單：config/watchlists.json

## 測試規則
- 每個 Phase 測試全 PASS 才進下一 Phase
- 執行：pytest tests/phase{N}/ -v

## 已完成的 Phase（開發者更新此處）
- [ ] Phase 1
- [ ] Phase 2
...
```

---

## ⚠️ 風險與限制說明

1. **本系統不構成投資建議**，所有分析、排名、預測僅供參考
2. Paper Trading 與真實帳戶行為可能不同（滑價、流動性差異）
3. 隔日預測準確率有限，請勿依賴單一指標做投資決策
4. API 費率限制：Alpaca 免費方案每分鐘有請求上限，大量帳戶需注意
5. 本益比資料來源為第三方，可能有延遲，建議交叉比對
6. GitHub Actions 免費額度每月 2,000 分鐘，多帳戶請評估用量

---

*本計劃書版本 v1.0.0，如有異動請同步更新版本號與日期*

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nasdaq 100 Top 10 自動交易投資組合
Alpaca Paper Trading API
"""

import json, os, sys, time, datetime, threading
import http.server, webbrowser
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# ── 設定 ──────────────────────────────────────────────────────────────
API_KEY    = "PKL6ZHN5BMJWRVHAQPC3N63PJI"
API_SECRET = "BmoeU1bH5HTJs6XJDaLCsUtZDqAH8q8SAmZPisPX9awg"
BASE_URL   = "https://paper-api.alpaca.markets/v2"
DATA_URL   = "https://data.alpaca.markets/v2"
DATA_FILE  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "portfolio_data.json")
PORT       = 8765

# Nasdaq 100 前十大權值股（正規化至 100%）
TARGET_WEIGHTS = {
    "AAPL":  0.20,
    "NVDA":  0.17,
    "MSFT":  0.15,
    "AMZN":  0.11,
    "AVGO":  0.10,
    "META":  0.09,
    "TSLA":  0.08,
    "GOOGL": 0.05,
    "GOOG":  0.03,
    "COST":  0.02,
}
BENCHMARKS = ["QQQ", "SPY"]

HEADERS = {
    "APCA-API-KEY-ID":     API_KEY,
    "APCA-API-SECRET-KEY": API_SECRET,
    "Content-Type":        "application/json",
}

# ── API 工具 ───────────────────────────────────────────────────────────
def api_call(method, endpoint, base=BASE_URL, data=None):
    url  = base + endpoint
    body = json.dumps(data).encode() if data else None
    req  = Request(url, data=body, headers=HEADERS, method=method)
    try:
        with urlopen(req, timeout=15) as r:
            content = r.read()
            return json.loads(content) if content else {}
    except HTTPError as e:
        msg = e.read().decode(errors="replace")
        print(f"  HTTP {e.code}: {msg[:200]}")
        return {"error": str(e)}
    except URLError as e:
        print(f"  URL Error: {e.reason}")
        return {"error": str(e)}
    except Exception as e:
        print(f"  Error: {e}")
        return {"error": str(e)}

def api_get(ep, base=BASE_URL):   return api_call("GET",    ep, base)
def api_post(ep, d):              return api_call("POST",   ep, data=d)
def api_delete(ep):               return api_call("DELETE", ep)

# ── 市場資料 ───────────────────────────────────────────────────────────
def get_latest_prices(symbols):
    """取得最新股價（使用 Latest Bars）"""
    sym_str = ",".join(symbols)
    try:
        r = api_get(f"/stocks/bars/latest?symbols={sym_str}&feed=iex", DATA_URL)
        bars = r.get("bars", {})
        return {s: round(float(v["c"]), 2) for s, v in bars.items() if v}
    except Exception as e:
        print(f"  取得股價失敗: {e}")
        return {}

def get_historical_bars(symbol, start, end):
    """取得歷史 K 線資料"""
    try:
        ep = f"/stocks/{symbol}/bars?start={start}&end={end}&timeframe=1Day&feed=iex&limit=500"
        r  = api_get(ep, DATA_URL)
        return [{"date": b["t"][:10], "close": round(float(b["c"]), 2)}
                for b in r.get("bars", [])]
    except Exception as e:
        print(f"  {symbol} 歷史資料失敗: {e}")
        return []

# ── 資料存取 ───────────────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "inception_date": datetime.date.today().isoformat(),
        "inception_nav":  100000.0,
        "nav_history":    [],
        "benchmark":      {},
        "trade_log":      [],
        "snapshot":       {},
        "last_updated":   "",
    }

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

# ── 再平衡 ─────────────────────────────────────────────────────────────
def rebalance():
    """依目標權重執行再平衡交易"""
    print("\n📊 開始投資組合再平衡...")

    account = api_get("/account")
    if "error" in account:
        print(f"  ❌ 帳戶錯誤: {account['error']}")
        return []

    port_val = float(account.get("portfolio_value", 0))
    if port_val <= 0:
        print("  ❌ 帳戶價值無效")
        return []

    # 取得當前持倉
    positions = api_get("/positions")
    curr_qty = {}
    if isinstance(positions, list):
        for p in positions:
            curr_qty[p["symbol"]] = float(p.get("qty", 0))

    # 取得最新股價
    symbols = list(TARGET_WEIGHTS.keys())
    prices  = get_latest_prices(symbols)
    if not prices:
        print("  ❌ 無法取得股價")
        return []

    # 計算目標股數
    orders_sell, orders_buy = [], []
    for sym, weight in TARGET_WEIGHTS.items():
        price = prices.get(sym)
        if not price:
            print(f"  ⚠ 無 {sym} 股價，跳過")
            continue
        target_qty  = int(port_val * weight / price)
        current_qty = int(curr_qty.get(sym, 0))
        diff = target_qty - current_qty
        if diff < -1:
            orders_sell.append((sym, abs(diff), "sell", price))
        elif diff > 1:
            orders_buy.append((sym, diff, "buy", price))

    # 取消所有待執行訂單
    api_delete("/orders")
    time.sleep(1)

    trades = []
    for sym, qty, side, price in orders_sell + orders_buy:
        result = api_post("/orders", {
            "symbol":         sym,
            "qty":            str(qty),
            "side":           side,
            "type":           "market",
            "time_in_force":  "day",
        })
        status = result.get("status", "submitted")
        icon = "📉" if side == "sell" else "📈"
        print(f"  {icon} {side.upper():<4} {qty:>4} 股 {sym:<5} @ ~${price:.2f}  [{status}]")
        trades.append({
            "time":     datetime.datetime.now().isoformat(),
            "symbol":   sym,
            "side":     side,
            "qty":      qty,
            "price":    price,
            "order_id": result.get("id", ""),
            "status":   status,
        })
        time.sleep(0.3)

    # 儲存交易日誌
    data = load_data()
    data["trade_log"] = (trades + data.get("trade_log", []))[:300]
    save_data(data)

    print(f"  ✅ 完成 {len(trades)} 筆交易（{len(orders_sell)} 賣 / {len(orders_buy)} 買）\n")
    return trades

# ── 資料收集 ───────────────────────────────────────────────────────────
def collect():
    """收集投資組合快照並更新 JSON"""
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"\n🔄 [{ts}] 更新資料中...")

    data = load_data()

    # 帳戶資訊
    account = api_get("/account")
    if "error" in account:
        print(f"  ❌ {account['error']}")
        return None

    port_val  = float(account.get("portfolio_value", 0))
    cash      = float(account.get("cash",            0))
    buy_power = float(account.get("buying_power",    0))

    # 基礎指標
    inception_nav  = float(data.get("inception_nav",  port_val))
    inception_date = data.get("inception_date", datetime.date.today().isoformat())
    nav_history    = data.get("nav_history", [])
    today_str      = datetime.date.today().isoformat()

    # 今日損益（與昨日 NAV 比較）
    daily_pnl = daily_pnl_pct = 0.0
    yesterday_nav = nav_history[-1]["nav"] if nav_history else inception_nav
    if nav_history and nav_history[-1]["date"] != today_str:
        daily_pnl     = port_val - yesterday_nav
        daily_pnl_pct = daily_pnl / yesterday_nav * 100 if yesterday_nav else 0

    # 更新 NAV 歷史
    if not nav_history or nav_history[-1]["date"] != today_str:
        nav_history.append({
            "date":    today_str,
            "nav":     round(port_val, 2),
            "pnl":     round(daily_pnl, 2),
            "pnl_pct": round(daily_pnl_pct, 4),
        })
    else:
        nav_history[-1].update({
            "nav":     round(port_val, 2),
            "pnl":     round(daily_pnl, 2),
            "pnl_pct": round(daily_pnl_pct, 4),
        })

    # 報酬率
    total_ret     = (port_val / inception_nav - 1) * 100 if inception_nav else 0
    days_elapsed  = (datetime.date.today() - datetime.date.fromisoformat(inception_date)).days
    annual_ret    = ((port_val / inception_nav) ** (365 / max(days_elapsed, 1)) - 1) * 100 if inception_nav else 0

    # 持倉資料
    raw_pos = api_get("/positions")
    positions_data = []
    if isinstance(raw_pos, list):
        prices = get_latest_prices(list(TARGET_WEIGHTS.keys()))
        for p in raw_pos:
            sym   = p["symbol"]
            qty   = float(p["qty"])
            avg   = float(p["avg_entry_price"])
            cur   = float(p.get("current_price") or prices.get(sym) or avg)
            mv    = qty * cur
            cost  = qty * avg
            pnl_a = mv - cost
            pnl_p = pnl_a / cost * 100 if cost else 0
            positions_data.append({
                "symbol":          sym,
                "qty":             qty,
                "avg_entry_price": round(avg,   2),
                "current_price":   round(cur,   2),
                "market_value":    round(mv,    2),
                "weight":          round(mv / port_val * 100, 2) if port_val else 0,
                "target_weight":   round(TARGET_WEIGHTS.get(sym, 0) * 100, 1),
                "pnl_pct":         round(pnl_p, 2),
                "pnl_amount":      round(pnl_a, 2),
            })
        positions_data.sort(key=lambda x: x["market_value"], reverse=True)

    # 交易紀錄（從 API 取最近 30 筆 + 本地日誌）
    orders = api_get("/orders?status=all&limit=30")
    api_trades = []
    if isinstance(orders, list):
        for o in orders[:20]:
            fp = o.get("filled_avg_price")
            api_trades.append({
                "time":       (o.get("submitted_at") or "")[:19].replace("T", " "),
                "symbol":     o.get("symbol", ""),
                "side":       o.get("side", ""),
                "qty":        float(o.get("qty") or 0),
                "filled_qty": float(o.get("filled_qty") or 0),
                "price":      round(float(fp), 2) if fp else 0,
                "status":     o.get("status", ""),
                "type":       o.get("type", "market"),
            })

    # 基準指數（QQQ / SPY）歷史資料
    benchmark = data.get("benchmark", {})
    should_update_bm = (
        not benchmark or
        len(nav_history) <= 1 or
        datetime.datetime.now().hour == 17  # 每天收盤後更新
    )
    if should_update_bm:
        print("  📈 更新基準指數資料...")
        t0 = inception_date
        t1 = datetime.date.today().isoformat()
        for sym in BENCHMARKS:
            bars = get_historical_bars(sym, t0, t1)
            if bars:
                p0 = bars[0]["close"]
                benchmark[sym] = [
                    {"date": b["date"], "value": round(inception_nav * b["close"] / p0, 2)}
                    for b in bars
                ]
                print(f"  ✓ {sym}: {len(bars)} 筆資料")

    # 儲存
    now_str = datetime.datetime.now().isoformat()
    data.update({
        "nav_history":    nav_history[-365:],
        "benchmark":      benchmark,
        "last_updated":   now_str,
        "inception_date": inception_date,
        "inception_nav":  inception_nav,
        "snapshot": {
            "timestamp":        now_str,
            "nav":              round(port_val,  2),
            "cash":             round(cash,      2),
            "buying_power":     round(buy_power, 2),
            "daily_pnl":        round(daily_pnl,      2),
            "daily_pnl_pct":    round(daily_pnl_pct,  4),
            "total_return_pct": round(total_ret,       4),
            "annual_return_pct":round(annual_ret,      4),
            "days_elapsed":     days_elapsed,
            "inception_date":   inception_date,
            "inception_nav":    round(inception_nav, 2),
            "positions":        positions_data,
            "recent_trades":    api_trades,
        },
    })
    save_data(data)

    sign = "+" if daily_pnl >= 0 else ""
    print(f"  💰 NAV: ${port_val:>12,.2f} | 今日損益: ${daily_pnl:>+10,.2f} ({sign}{daily_pnl_pct:.2f}%) | 總報酬: {total_ret:>+7.2f}% | 年化: {annual_ret:>+7.2f}%")
    return data["snapshot"]

# ── HTTP 伺服器 ────────────────────────────────────────────────────────
class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.path = "/portfolio.html"
        elif self.path == "/api/data":
            self._send_json(load_data()); return
        elif self.path == "/api/refresh":
            collect(); self._send_json(load_data()); return
        elif self.path == "/api/rebalance":
            rebalance(); time.sleep(3); collect()
            self._send_json(load_data()); return
        super().do_GET()

    def _send_json(self, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass  # 靜默日誌

def run_server():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    srv = http.server.HTTPServer(("", PORT), DashboardHandler)
    print(f"  ✅ 儀表板：http://localhost:{PORT}")
    srv.serve_forever()

# ── 主程式 ─────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  🏦  Nasdaq 100 Top 10 自動交易投資組合")
    print("=" * 60)
    print(f"\n  目標持股：{', '.join(TARGET_WEIGHTS.keys())}")

    # 初始化
    data = load_data()
    if not data.get("inception_date") or not data.get("snapshot"):
        acct = api_get("/account")
        data["inception_nav"]  = float(acct.get("portfolio_value", 100000))
        data["inception_date"] = datetime.date.today().isoformat()
        save_data(data)
        print(f"\n✓ 初始 NAV: ${data['inception_nav']:,.2f}")

    print("\n[步驟 1/3] 建立/調整持倉...")
    rebalance()
    time.sleep(3)

    print("[步驟 2/3] 收集資料快照...")
    collect()

    print("\n[步驟 3/3] 啟動儀表板伺服器...")
    threading.Thread(target=run_server, daemon=True).start()
    time.sleep(1)
    webbrowser.open(f"http://localhost:{PORT}")

    print("\n✅ 系統運行中，每 60 秒自動更新一次")
    print("   按 Ctrl+C 停止\n")

    while True:
        try:
            time.sleep(60)
            collect()
        except KeyboardInterrupt:
            print("\n👋 程式已停止")
            sys.exit(0)
        except Exception as e:
            print(f"  ⚠ 更新錯誤: {e}")

if __name__ == "__main__":
    main()

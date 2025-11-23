# サーバーログ設定ガイド

Qiskit Runtime Backend API サーバーのログ機能について説明します。

## デフォルトのログ出力

サーバーを起動すると、以下のようなログが表示されます：

### 起動時のログ

```
2025-11-23 10:00:00 - qiskit_runtime_server - INFO - ============================================================
2025-11-23 10:00:00 - qiskit_runtime_server - INFO - Starting Qiskit Runtime Backend API Server
2025-11-23 10:00:00 - qiskit_runtime_server - INFO - ============================================================
2025-11-23 10:00:00 - qiskit_runtime_server - INFO - Server: http://0.0.0.0:8000
2025-11-23 10:00:00 - qiskit_runtime_server - INFO - Docs:   http://0.0.0.0:8000/docs
2025-11-23 10:00:00 - qiskit_runtime_server - INFO - ReDoc:  http://0.0.0.0:8000/redoc
2025-11-23 10:00:00 - qiskit_runtime_server - INFO - ============================================================
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### リクエスト時のログ

クライアントからリクエストが来ると、以下のように表示されます：

```
2025-11-23 10:01:23 - qiskit_runtime_server - INFO - → GET /v1/backends from 127.0.0.1
2025-11-23 10:01:23 - qiskit_runtime_server - INFO - ← ✓ 200 GET /v1/backends (12.34ms)
```

または：

```
2025-11-23 10:01:25 - qiskit_runtime_server - INFO - → GET /v1/backends/ibm_brisbane/configuration from 127.0.0.1
2025-11-23 10:01:25 - qiskit_runtime_server - INFO - ← ✗ 501 GET /v1/backends/ibm_brisbane/configuration (5.67ms)
```

### ログの見方

**リクエストログ（→）**:
- `→`: リクエスト受信
- `GET /v1/backends`: HTTPメソッドとパス
- `from 127.0.0.1`: クライアントのIPアドレス

**レスポンスログ（←）**:
- `✓`: 成功（ステータスコード < 400）
- `✗`: エラー（ステータスコード >= 400）
- `200` / `501`: HTTPステータスコード
- `(12.34ms)`: 処理時間

## ログレベルの変更

### 方法1: 環境変数で設定

```bash
# DEBUGレベル（詳細なログ）
export LOG_LEVEL=DEBUG
python -m src.main

# WARNINGレベル（警告以上のみ）
export LOG_LEVEL=WARNING
python -m src.main
```

### 方法2: コマンドラインオプション

uvicornを直接実行する場合：

```bash
# DEBUGレベル
uvicorn src.main:app --host 0.0.0.0 --port 8000 --log-level debug

# INFOレベル（デフォルト）
uvicorn src.main:app --host 0.0.0.0 --port 8000 --log-level info

# WARNINGレベル
uvicorn src.main:app --host 0.0.0.0 --port 8000 --log-level warning
```

## DEBUGモードの詳細ログ

`LOG_LEVEL=DEBUG`または`--log-level debug`で起動すると、以下の追加情報も表示されます：

```
2025-11-23 10:01:23 - qiskit_runtime_server - INFO - → GET /v1/backends from 127.0.0.1
2025-11-23 10:01:23 - qiskit_runtime_server - DEBUG -   Auth: Bearer test-token...
2025-11-23 10:01:23 - qiskit_runtime_server - DEBUG -   API Version: 2025-05-01
2025-11-23 10:01:23 - qiskit_runtime_server - DEBUG -   Service-CRN: crn:v1:bluemix:public:quantum-computing...
2025-11-23 10:01:23 - qiskit_runtime_server - INFO - ← ✓ 200 GET /v1/backends (12.34ms)
```

**セキュリティ**: トークンは最初の10文字のみ表示され、残りはマスクされます。

## アクセスログの無効化

静かなログ出力が必要な場合：

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --access-log false
```

または、`src/main.py`を編集：

```python
uvicorn.run(
    "src.main:app",
    host="0.0.0.0",
    port=8000,
    reload=True,
    log_level="info",
    access_log=False,  # アクセスログを無効化
)
```

## ログのカスタマイズ

### ファイルへのログ出力

`src/main.py`のlogging設定を変更：

```python
import logging

# ファイルとコンソールの両方に出力
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("server.log"),  # ファイルに保存
        logging.StreamHandler()  # コンソールにも表示
    ]
)
```

### ログフォーマットのカスタマイズ

```python
# JSON形式のログ
import json
import logging

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }
        return json.dumps(log_data)

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())

logger = logging.getLogger("qiskit_runtime_server")
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

## ログレベル一覧

| レベル | 用途 | 表示される情報 |
|--------|------|---------------|
| DEBUG | 開発・デバッグ | すべてのログ（リクエストヘッダー含む） |
| INFO | 通常運用 | リクエスト/レスポンスの概要 |
| WARNING | 本番環境 | 警告とエラーのみ |
| ERROR | 最小限 | エラーのみ |

## トラブルシューティング

### ログが表示されない

**原因**: ログレベルが高すぎる

**解決策**:
```bash
# ログレベルを下げる
uvicorn src.main:app --log-level debug
```

### ログが多すぎる

**原因**: DEBUGレベルで実行している

**解決策**:
```bash
# ログレベルを上げる
uvicorn src.main:app --log-level warning
```

### トークンが平文で表示される心配

**安心**: トークンは自動的にマスクされます
- DEBUGモードでも最初の10文字+`...`のみ表示
- セキュリティ上の問題はありません

## 本番環境での推奨設定

```bash
# 本番環境
uvicorn src.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --log-level warning \
  --access-log true \
  --workers 4 \
  --no-reload
```

この設定では：
- 警告とエラーのみログ出力
- アクセスログは有効（監視用）
- 4ワーカーで並列処理
- ホットリロードは無効（安定性向上）

## まとめ

デフォルト設定でリクエストログが表示されるようになりました：

```bash
# サーバー起動
cd server
python -m src.main
```

これで、クライアントからのリクエストが来ると：
```
→ GET /v1/backends from 127.0.0.1
← ✓ 200 GET /v1/backends (12.34ms)
```

のようにログが表示されます！

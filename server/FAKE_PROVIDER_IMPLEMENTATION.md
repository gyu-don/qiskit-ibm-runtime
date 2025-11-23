# Fake Provider REST API Implementation

このドキュメントは、`qiskit_ibm_runtime.fake_provider` と同等の機能をREST API経由で実現する実装について説明します。

## 実装概要

`server/*` ディレクトリに以下のコンポーネントを実装しました：

### 1. バックエンドプロバイダー (`src/backend_provider.py`)

`FakeProviderForBackendV2` をラップし、REST API経由でバックエンド情報を提供します。

**主な機能：**
- `list_backends()` - 全フェイクバックエンドのリストを取得
- `get_backend_configuration()` - バックエンドの設定情報を取得
- `get_backend_properties()` - バックエンドのキャリブレーション情報を取得
- `get_backend_status()` - バックエンドの稼働状態を取得
- `get_backend_defaults()` - パルスレベルのデフォルト設定を取得（対応バックエンドのみ）

### 2. ジョブマネージャー (`src/job_manager.py`)

`QiskitRuntimeLocalService` を使用してランタイムジョブの作成・実行・管理を行います。

**主な機能：**
- `create_job()` - sampler/estimator ジョブを作成・実行
- `get_job_status()` - ジョブの状態を取得
- `get_job_result()` - ジョブの実行結果を取得
- `cancel_job()` - ジョブをキャンセル
- `list_jobs()` - ジョブ一覧を取得（フィルタリング対応）

**ジョブステータス：**
- `QUEUED` - 実行待ち
- `RUNNING` - 実行中
- `COMPLETED` - 完了
- `FAILED` - 失敗
- `CANCELLED` - キャンセル

### 3. REST APIエンドポイント (`src/main.py`)

#### バックエンドエンドポイント

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET | `/v1/backends` | バックエンド一覧を取得 |
| GET | `/v1/backends/{id}/configuration` | バックエンド設定を取得 |
| GET | `/v1/backends/{id}/properties` | キャリブレーション情報を取得 |
| GET | `/v1/backends/{id}/status` | 稼働状態を取得 |
| GET | `/v1/backends/{id}/defaults` | パルスデフォルトを取得 |

#### ジョブエンドポイント

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| POST | `/v1/jobs` | ジョブを作成・実行 |
| GET | `/v1/jobs` | ジョブ一覧を取得 |
| GET | `/v1/jobs/{id}` | ジョブ状態を取得 |
| GET | `/v1/jobs/{id}/results` | ジョブ結果を取得 |
| DELETE | `/v1/jobs/{id}` | ジョブをキャンセル |

#### システムエンドポイント

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET | `/` | API情報 |
| GET | `/health` | ヘルスチェック |

### 4. データモデル (`src/models.py`)

追加されたジョブ関連モデル：
- `JobCreateRequest` - ジョブ作成リクエスト
- `JobResponse` - ジョブステータスレスポンス
- `JobResultResponse` - ジョブ結果レスポンス
- `JobListResponse` - ジョブ一覧レスポンス

## 使用方法

### サーバーの起動

```bash
cd server
python -m src.main
```

サーバーは以下のURLでアクセス可能になります：
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### バックエンド一覧の取得

```bash
curl -X GET "http://localhost:8000/v1/backends" \
  -H "Authorization: Bearer test-token" \
  -H "Service-CRN: crn:v1:test" \
  -H "IBM-API-Version: 2025-05-01"
```

### バックエンド設定の取得

```bash
curl -X GET "http://localhost:8000/v1/backends/fake_manila/configuration" \
  -H "Authorization: Bearer test-token" \
  -H "Service-CRN: crn:v1:test" \
  -H "IBM-API-Version: 2025-05-01"
```

### ジョブの作成

```bash
curl -X POST "http://localhost:8000/v1/jobs" \
  -H "Authorization: Bearer test-token" \
  -H "Service-CRN: crn:v1:test" \
  -H "IBM-API-Version: 2025-05-01" \
  -H "Content-Type: application/json" \
  -d '{
    "program_id": "sampler",
    "backend": "fake_manila",
    "params": {
      "pubs": [...]
    },
    "options": {
      "default_shots": 1024
    }
  }'
```

### ジョブステータスの取得

```bash
curl -X GET "http://localhost:8000/v1/jobs/{job_id}" \
  -H "Authorization: Bearer test-token" \
  -H "Service-CRN: crn:v1:test" \
  -H "IBM-API-Version: 2025-05-01"
```

### ジョブ結果の取得

```bash
curl -X GET "http://localhost:8000/v1/jobs/{job_id}/results" \
  -H "Authorization: Bearer test-token" \
  -H "Service-CRN: crn:v1:test" \
  -H "IBM-API-Version: 2025-05-01"
```

## qiskit-ibm-runtimeクライアントとの統合

このサーバーは `qiskit-ibm-runtime` クライアントと互換性があります：

```python
from qiskit_ibm_runtime import QiskitRuntimeService

# ローカルサーバーに接続
service = QiskitRuntimeService(
    channel="ibm_quantum_platform",
    token="test-token",
    url="http://localhost:8000",
    instance="crn:v1:test",
    verify=False
)

# バックエンド一覧を取得
backends = service.backends()

# バックエンドを選択
backend = service.backend("fake_manila")

# Samplerを実行
from qiskit_ibm_runtime import SamplerV2
from qiskit import QuantumCircuit

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

sampler = SamplerV2(backend)
job = sampler.run([qc])
result = job.result()
```

## アーキテクチャ

```
┌─────────────────────────────────────────────────┐
│         qiskit-ibm-runtime Client               │
│                                                 │
│  - QiskitRuntimeService                         │
│  - SamplerV2 / EstimatorV2                      │
└─────────────────┬───────────────────────────────┘
                  │ HTTP REST API
                  │
┌─────────────────▼───────────────────────────────┐
│         FastAPI Server (server/src/main.py)     │
│                                                 │
│  - Backend endpoints (/v1/backends/...)         │
│  - Job endpoints (/v1/jobs/...)                 │
└─────────────────┬───────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼─────────┐  ┌──────▼──────────┐
│ BackendProvider │  │   JobManager    │
│                 │  │                 │
│ - list_backends │  │ - create_job    │
│ - get_config    │  │ - get_status    │
│ - get_props     │  │ - get_result    │
└───────┬─────────┘  └──────┬──────────┘
        │                   │
        │                   │
┌───────▼─────────┐  ┌──────▼──────────────────┐
│ FakeProvider    │  │ QiskitRuntimeLocal      │
│ ForBackendV2    │  │ Service                 │
│                 │  │                         │
│ - backends()    │  │ - _run(sampler/estimat) │
└─────────────────┘  └─────────────────────────┘
```

## 制限事項

1. **認証**: 現在は認証ヘッダーの形式チェックのみ。実際のトークン検証は未実装。
2. **永続化**: ジョブデータはメモリ内のみで管理。サーバー再起動で消失。
3. **パルスデフォルト**: ほとんどのフェイクバックエンドはパルスデフォルトデータを持たないため、`/v1/backends/{id}/defaults`は404を返す。
4. **キャリブレーション履歴**: `calibration_id` および `updated_before` パラメータは現在無視される。

## テスト

簡単なテストスクリプトを実行：

```bash
cd server
python test_server.py
```

## ファイル構成

```
server/
├── src/
│   ├── __init__.py
│   ├── main.py                    # FastAPIアプリとエンドポイント
│   ├── models.py                  # Pydanticモデル（バックエンド＋ジョブ）
│   ├── backend_provider.py        # fake_provider統合
│   └── job_manager.py             # ジョブ管理
├── test_server.py                 # テストスクリプト
├── requirements.txt               # Python依存関係
└── FAKE_PROVIDER_IMPLEMENTATION.md # このファイル
```

## 今後の拡張

- [ ] データベース統合による永続化
- [ ] 実際のIAM認証
- [ ] WebSocket対応（リアルタイムジョブステータス）
- [ ] キャリブレーション履歴管理
- [ ] Redis等によるキャッシュ機能
- [ ] メトリクス収集とモニタリング

## まとめ

この実装により、`qiskit_ibm_runtime.fake_provider` の機能がREST API経由で利用可能になりました。
クライアントライブラリは既存の `qiskit-ibm-runtime` をそのまま使用でき、URLを `http://localhost:8000` に変更するだけで動作します。

全ての実装は `server/*` ディレクトリに限定されており、qiskit-ibm-runtimeのコアコードには一切変更を加えていません。

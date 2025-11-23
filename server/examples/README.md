# Qiskit Runtime Local Server Examples

このディレクトリには、ローカルで動作するFastAPIサーバー（http://localhost:8000）に接続するためのサンプルコードが含まれています。

## 前提条件

### 1. サーバーの起動

まず、ローカルサーバーを起動してください：

```bash
cd server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m src.main
```

サーバーが起動すると、以下にアクセスできます：
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 2. クライアントライブラリのインストール

サンプルコードを実行するには、qiskit-ibm-runtimeがインストールされている必要があります：

```bash
# リポジトリのルートディレクトリで
pip install -e .
```

## サンプルコード一覧

### 01_basic_connection.py
**基本的な接続**

ローカルサーバーへの最もシンプルな接続方法を示します。

```bash
python examples/01_basic_connection.py
```

実装内容：
- `QiskitRuntimeService`を使ってlocalhost:8000に接続
- 認証ヘッダーの設定
- SSL検証の無効化（ローカルテスト用）

### 02_list_backends.py
**バックエンドのリスト取得**

利用可能なすべてのバックエンドを一覧表示します。

```bash
python examples/02_list_backends.py
```

実装内容：
- `service.backends()`でバックエンド一覧を取得
- 各バックエンドの基本情報を表示
- エラーハンドリング

### 03_backend_details.py
**バックエンドの詳細情報**

特定のバックエンドの詳細情報（設定、プロパティ、ステータス）を取得します。

```bash
python examples/03_backend_details.py
```

実装内容：
- `backend.configuration()` - 設定情報（ゲート、トポロジー、機能）
- `backend.properties()` - キャリブレーションデータ（T1, T2, エラー率）
- `backend.status()` - 動作状況、キューの長さ

### 04_test_all_endpoints.py
**全エンドポイントのテスト**

すべてのバックエンド関連エンドポイントを体系的にテストします。

```bash
python examples/04_test_all_endpoints.py
```

実装内容：
- 5つのエンドポイントすべてをテスト
- 各テストの成功/失敗を記録
- 結果サマリーの表示

### 05_save_account.py
**アカウント設定の保存**

ローカルサーバーの設定を保存し、毎回指定する手間を省きます。

```bash
python examples/05_save_account.py
```

実装内容：
- `QiskitRuntimeService.save_account()`で設定を保存
- 保存した設定の読み込み
- アカウント一覧の表示
- アカウント削除

保存後は以下のように簡単に接続できます：
```python
service = QiskitRuntimeService(name="local_mock_server")
```

### 06_custom_headers.py
**カスタムHTTPヘッダー**

HTTPヘッダーの動作を理解し、認証とAPIバージョニングをテストします。

```bash
python examples/06_custom_headers.py
```

実装内容：
- 送信されるHTTPヘッダーの表示
- 異なるAPIバージョンの説明
- 認証トークンの処理

### 07_direct_http.py
**直接HTTP呼び出し**

qiskit-ibm-runtimeを使わずに、`requests`ライブラリで直接APIを呼び出します。

```bash
pip install requests  # 必要な場合
python examples/07_direct_http.py
```

実装内容：
- 生のHTTPリクエスト/レスポンス
- 全エンドポイントのテスト
- 認証エラーのテスト
- APIバージョンエラーのテスト

## API エンドポイント

ローカルサーバーは以下のエンドポイントを提供します：

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/v1/backends` | GET | 利用可能なバックエンド一覧 |
| `/v1/backends/{id}/configuration` | GET | バックエンド設定 |
| `/v1/backends/{id}/defaults` | GET | デフォルトのパルス較正 |
| `/v1/backends/{id}/properties` | GET | キャリブレーションプロパティ |
| `/v1/backends/{id}/status` | GET | 動作ステータス |
| `/health` | GET | ヘルスチェック |
| `/` | GET | API情報 |

## 必須ヘッダー

すべてのバックエンドエンドポイントには以下のヘッダーが必要です：

```
Authorization: Bearer {token}
Service-CRN: {service-instance-crn}
IBM-API-Version: 2025-05-01
```

ローカルテストでは、トークンとCRNは任意の文字列で構いません。

## 現在の実装状況

**重要**: 現在のサーバーは**仕様/モック**段階です。

- ✅ すべてのエンドポイントが定義されている
- ✅ 型とバリデーションが完全
- ✅ 認証ミドルウェアのフレームワークがある
- ⚠️ すべてのエンドポイントはHTTP 501 (Not Implemented)を返す

実際のデータを返すようにするには、データレイヤーの実装が必要です。
詳細は `server/IMPLEMENTATION_STATUS.md` を参照してください。

## トラブルシューティング

### サーバーに接続できない

```
Error: Connection refused
```

**解決策**: サーバーが起動していることを確認してください：
```bash
cd server
python -m src.main
```

### 501 エラーが返される

```
HTTPException: 501 Not Implemented
```

**説明**: これは正常な動作です。サーバーはまだ実装段階で、エンドポイントの仕様のみ定義されています。

### SSL証明書エラー

```
SSL: CERTIFICATE_VERIFY_FAILED
```

**解決策**: `verify=False`を設定してください：
```python
service = QiskitRuntimeService(
    ...
    verify=False
)
```

## 次のステップ

1. **サーバーの実装**: `server/docs/DEVELOPMENT_GUIDE.md`を参照
2. **テストの実行**: `pytest server/tests/ -v`
3. **API仕様**: `server/docs/API_SPECIFICATION.md`を参照
4. **クライアント/サーバーマッピング**: `server/docs/CLIENT_SERVER_MAPPING.md`を参照

## その他のリソース

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Qiskit Runtime Documentation](https://quantum.ibm.com/docs)
- [IBM Quantum API Reference](https://quantum.cloud.ibm.com/docs/en/api/qiskit-runtime-rest)

## 質問・フィードバック

実装に関する質問や提案は、GitHubのIssueで受け付けています。

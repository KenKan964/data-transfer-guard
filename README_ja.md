# Data Transfer Guard

**CSVの更新前後を比較し、変更を許可した列以外が書き換わっていないか検査するツールです。**

**v0.1.0 — 実験版 · Python 3.11以降 · 標準ライブラリのみ · CSV専用 · MITライセンス**

[English](README.md) | **日本語** · [v0.1.0 Pre-release](https://github.com/KenKan964/data-transfer-guard/releases/tag/v0.1.0)

## どんな問題を検出するか

CSVを更新する業務では、指定した列だけを変更したつもりでも、**ほかの列の改変、行の消失、IDの重複**などを見落とすことがあります。

Data Transfer Guardは、変更前（before）と変更後（after）のCSVを**共通の一意なIDで照合**し、指定された更新規則に違反する変更を検出する無料のCLIです。

**入力CSVは読取り専用で扱います。転記、更新、修復、上書きは行いません。**

> **対象範囲：** 「許可した変更だけが行われたか」を検査します。変更を許可した列に記載された値が、業務的に正しいかどうかは判定できません。

## 主な検出項目

| 検査対象 | 検出できる問題 |
| --- | --- |
| 保護列 | 許可していない列の値が変わった（`UNAUTHORIZED_CHANGE`） |
| 行の消失・追加 | ポリシーで禁止したレコードの削除・追加 |
| ID | 重複ID、空のID、照合不能なキー |
| 列構成 | ヘッダの不一致、必要な列の欠落 |
| CSV構造 | 引用符の不正、列数不一致、重複ヘッダ、空レコード、非対応エンコーディング |
| 出力の保護 | 既存・危険なレポート出力先への上書きを拒否 |

**照合規則：** IDとセルの値は文字列として完全一致で比較します。`001`と`1`、空文字と`0`は区別します。行順・列順の変更は許容しますが、ヘッダの集合は一致する必要があります。

## すぐに試す

**必要環境：** Python 3.11以降。外部サービスやpipによる追加パッケージは不要です。

リポジトリのルートディレクトリから、まずレポート出力用フォルダを作ります。

**Windows PowerShell：**

```powershell
New-Item -ItemType Directory -Force reports | Out-Null
py -3 dtg.py verify --before examples/before.csv --after examples/after_ok.csv --policy examples/policy.json --out reports/ok.json
py -3 dtg.py verify --before examples/before.csv --after examples/after_bad.csv --policy examples/policy.json --out reports/bad.json
```

**Linux / macOS：**

```sh
mkdir -p reports
python3 dtg.py verify --before examples/before.csv --after examples/after_ok.csv --policy examples/policy.json --out reports/ok.json
python3 dtg.py verify --before examples/before.csv --after examples/after_bad.csv --policy examples/policy.json --out reports/bad.json
```

同じファイル名への再出力はできません。**毎回未使用の出力ファイル名**を指定してください。2番目のコマンドは意図的に不正なCSVを検査するため、**終了コード1が期待値**です。ツールが故障したわけではありません。

## 実際に検出される例

同梱の[`examples/policy.json`](examples/policy.json)では、列**「状態」**だけの更新を許可しています。しかし、不正なサンプルは列**「所属」**を変更しています。

GitHubに保存されている[実際の不正データ検出結果](evidence/example_bad.json)には、次の情報があります（抜粋）。

```json
{
  "status": "FAIL",
  "exit_code": 1,
  "inspection_complete": true,
  "matched_rows": 2,
  "detection_count": 1,
  "counts_by_code": {
    "UNAUTHORIZED_CHANGE": 1
  },
  "violations": [
    {
      "code": "UNAUTHORIZED_CHANGE",
      "column": "所属",
      "key": null,
      "before_record": 2,
      "after_record": 2
    }
  ]
}
```

正常サンプルは`PASS`・終了コード0・検出違反0件です。[正常データのJSON記録](evidence/example_ok.json)で確認できます。

**機密性を考慮した既定値：** 変更前後のセル値はレポートに出さず、IDも`null`に抑制します。`--show-keys`を明示した場合にのみIDを表示します。ただし、列名、レコード位置、ファイルハッシュから情報が推測される場合はあります。

## 許可する更新内容を設定する

サンプルポリシーは次のとおりです。

```json
{
  "schema_version": "dtg-policy-v1",
  "key_column": "ID",
  "allowed_update_columns": ["状態"],
  "allow_added_rows": false,
  "allow_removed_rows": false
}
```

| 項目 | 意味 |
| --- | --- |
| `key_column` | レコードを一意に識別するID列 |
| `allowed_update_columns` | 変更可能な列（**ID列は指定不可**） |
| `allow_added_rows` | 行の追加を許可するか |
| `allow_removed_rows` | 行の削除を許可するか |
| `schema_version` | 現在のポリシー形式`dtg-policy-v1` |

5項目はすべて必須です。未知または重複したJSONキー、不正な型、存在しない列、不正なCSV構造を無視せず拒否します。

**自動的な文字列補正は行いません。** 空白除去、大文字小文字変換、Unicode正規化、企業名の類似判定には対応しません。CSVはUTF-8（BOM付きも可）のカンマ区切りに限定されます。

## 終了コードと診断レポート

| 終了コード | JSON判定 | 意味 |
| ---: | --- | --- |
| `0` | `PASS` | 比較完了・指定した更新規則に違反なし |
| `1` | `FAIL` | 比較完了・更新規則への違反を検出 |
| `2` | `INVALID_INPUT` | 入力・ポリシー不正、読み取り不能、出力先拒否・失敗 |

レポートは行数、照合件数、違反の種類、入力ファイルのSHA-256などを記録します。セルの実際の値は出しません。

出力できない場合は**stderrへJSONエラー**を返し、終了コード2になります。途中まで作成された不完全なファイルを**正常な検査証拠として扱わない**でください。親ディレクトリは事前に作成する必要があります。

## 試験・検証状況

自動テストは**53件**（49件のCLI受入ケースと4件の追加検証）です。正常例に加え、意図的な違反や不正入力の検出も試験しています。負例の検出に成功したテストが合格しても、不正なCSV自体が`PASS`になるわけではありません。

**GitHub Actions：Ubuntu・Windows × Python 3.11／3.12／3.13の6環境すべて成功**。公開済み`main`の[実行#3](https://github.com/KenKan964/data-transfer-guard/actions/runs/43458416344)で確認しました。以降の変更は[最新のActions](https://github.com/KenKan964/data-transfer-guard/actions)を参照してください。macOSはこのCI検証の対象外です。

ローカルで再現する場合：

```sh
python3 -m unittest discover -s tests -v
python3 benchmarks/compare.py comparison-001
```

Windowsでは必要に応じて`py -3`を使用してください。比較用の出力ディレクトリには新しい名前が必要です。独立したPython標準の`csv`・`unittest`でも主要な検査は実装可能であり、**速度、人間の工数削減、商用価値の優位性は実証していません。**

## 安全上の注意と制約

- **CSVの照合専用。** 入力CSVの更新・転記は一切行いません。
- Excel、Google Sheets、DB、クラウド等への接続、通信、テレメトリ、認証情報の利用はありません。
- 単一IDの文字列完全一致で比較します。複合キー、曖昧な企業名照合、文字正規化、許可した列の値そのものの正誤判定には対応しません。
- ファイル全体をメモリに読み込みます。巨大ファイル、ストリーミング、並行書換え、特殊デバイス、悪意あるファイル操作は対象外です。
- レコード位置は**CSV内のレコード序数**であり、引用符内に改行がある場合、画面上の物理行番号とは異なります。
- IDを非表示にしていてもレポートに機密性があり得ます。実データを公開Issueに添付しないでください。

## 関連資料

- [English README](README.md)
- [技術仕様書](TECHNICAL_SPEC.md)
- [セキュリティ上の注意](SECURITY.md)
- [不正サンプルのJSON証拠](evidence/example_bad.json)
- [比較実験の証拠](evidence/comparison_final/summary.json)
- [検証報告書](REPORT_ja.md)
- [変更履歴](CHANGELOG.md)
- [MITライセンス](LICENSE)

**ライセンス：** MIT · Copyright © 2026 KenKan964.

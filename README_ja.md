# Data Transfer Guard — CSV更新安全性検証

[English](README.md) · Python 3.11以上 · 標準ライブラリのみ · v0.1.0公開候補

変更前後のCSVを共通IDで照合し、許可した列以外の変更、行消失・追加、重複ID、構造不正を検出します。
転記・更新・修正は実行しません。SQLite Fault Labとは独立した新規製品です。

## 実行（Linux/macOS）

ZIP展開後、このディレクトリで実行します。pipや追加ソフトは不要です。

```bash
mkdir -p reports
python3 dtg.py verify --before examples/before.csv --after examples/after_ok.csv --policy examples/policy.json --out reports/ok.json
python3 dtg.py verify --before examples/before.csv --after examples/after_bad.csv --policy examples/policy.json --out reports/bad.json
python3 -m unittest discover -s tests -v
```

正常例は終了0・PASS。欠陥例は終了1・FAIL、列「所属」のUNAUTHORIZED_CHANGEを検出します。
欠陥を検出できることが試験合格であり、欠陥データをPASSにすることではありません。
出力先の親ディレクトリは事前に作成してください。同じ出力名での再実行は拒否します。
完全な診断サンプルは `evidence/example_bad.json`。

## Windows PowerShell

```powershell
New-Item -ItemType Directory -Force reports | Out-Null
py -3 dtg.py verify --before examples/before.csv --after examples/after_bad.csv --policy examples/policy.json --out reports/bad.json
$LASTEXITCODE # 期待値: 1
py -3 -m unittest discover -s tests -v
```

## ポリシーと判定

`examples/policy.json` は「状態」の変更のみを許可し、行追加・削除を禁止します。
5フィールドはすべて必須です。未知フィールド・重複JSONキー・存在しない列・許可列の重複・IDの更新許可・
不正な型・未対応バージョンは拒否します。行追加／削除を明示的に許容する場合だけ対応するbooleanをtrueにします。

|終了コード|JSON判定|意味|
|---:|---|---|
|0|PASS|検査完了・宣言した更新規則を満たす|
|1|FAIL|保護列変更、行集合違反、スキーマ変更|
|2|INVALID_INPUT|CSV／ポリシー不正、読取り不能、出力先拒否等|

IDと値は文字列の完全一致。`001` と `1`、空文字と `0`、空白、セル内改行を区別します。
空または空白だけのID・ヘッダは不正とします。それ以外の非空値はtrimしません。
行順・列順の変更は許容します。ヘッダ集合の変更はFAILですが、キー列／許可列の欠落は入力不正が優先します。
ヘッダだけでデータ0行も有効です。空ファイル・空レコード・列数不一致は不正です。
UTF-8/BOM、カンマ区切り、二重引用符、二重引用符の重ねによるエスケープに限定します。

## 証拠と機密性

JSONには総行数、照合行数、違反件数・分類・位置、入力3ファイルのSHA-256、環境を保存します。
**元値・変更後の値は出力しません。キーも既定で非表示（null）です。**
`--show-keys` を付けたときだけIDを表示します。キーは個人情報の可能性があるため、業務では既定を推奨します。
列名・レコード位置・ハッシュにも機密性があり得ます。出力先を適切に管理してください。
レコード番号はヘッダを1としたCSVレコード序数で、セル内改行がある場合の物理行番号とは異なります。

出力先が入力と同一、既存ファイル、symlink等の場合は上書きを拒否し、JSONをstderrに出します。
読み取り不能時はINVALID_INPUTで、未確認の行数・ハッシュはnullです。検査未実施をPASSにはしません。
入力は読み取りのみ。通信、テレメトリ、認証情報、Excel/Sheetsへの接続はありません。

## 試験・比較の再現

```bash
DTG_EVIDENCE_DIR=reports/acceptance python3 -m unittest discover -s tests -v
python3 benchmarks/compare.py reports/comparison
```

PowerShellでは先に `$env:DTG_EVIDENCE_DIR='reports/acceptance'` を指定します。
比較の出力ディレクトリは新規名を指定します。49のCLI受入ケース＋4追加試験を収録。
入力と期待結果は `tests/cases.json`、実行証拠は `evidence/`。全CLIケースで入力前後のハッシュを照合します。

実測済み：Linux Python 3.12.14／3.13.5、それぞれ53/53合格。
未検証：Python 3.11、Windows、macOS。GitHub ActionsにUbuntu／Windows×3.11／3.12／3.13を設定しましたが未実行です。

## 追加価値と限界

宣言的ポリシー、入力不正拒否、非表示を既定とするJSON証拠、出力先保護を共通CLIとして配布できます。
標準Pythonのcsv＋unittestでも同じ中核検査は作れます。原理上の独占性や速度優位は主張しません。
工数削減・商用需要は未測定です。比較は機能範囲を限定したもので、独立基準の全機能がDTGと同等とはしていません。

全ファイルをメモリに読み込みます。CSV標準パーサのフィールド長上限が適用されます。
同時書換え、外部プロセス、特殊デバイス、巨大ファイル、ストリーミング、複合キー、正規化は対象外です。
許可列に入った値の業務的正しさまでは確認しません。PASSは指定した更新規則への適合だけを意味します。

## 公開前の確認

[技術仕様](TECHNICAL_SPEC.md)・[開発報告](REPORT_ja.md)・[SECURITY](SECURITY.md)・[CHANGELOG](CHANGELOG.md)。
MIT案のLICENSEを同梱しました。公開者によるライセンス・権利表記・セキュリティ連絡先の最終確認が必要です。
GitHubには公開していません。研究部の受入審査後に独立リポジトリ `data-transfer-guard` として扱ってください。

## 公開版の試験証拠

ブラウザでのGitHub公開を容易にするため、49件の試験判定・入力ハッシュを `evidence/acceptance_summary.json` に集約しています。元の開発提出ZIPに含まれる個別CSV・JSONは公開用候補では重複収録せず、`tests/cases.json` と試験実行により再現できます。

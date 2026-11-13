# DTG-DEV-001 技術仕様 v0.1

## 構成とAPI

`dtg.py` は標準ライブラリだけで動く独立CLIです。SQLite Fault Lab等のモジュールは参照しません。
1ファイル内でパーサ・検査器・JSON出力を関数として分離しています。

|関数|役割|
|---|---|
|load_policy(raw)|UTF-8/BOM JSONの厳密検証。Invalid(code)を送出|
|validate_quotes(text)|裸フィールド内の引用符・閉じ引用符後のゴミ・未閉鎖を拒否|
|load_csv(raw, policy)|csv.reader(strict=True)で解析。ヘッダとID→(レコード番号,値辞書)|
|verify(before,after,policy_path,show_keys=False)|読み取りのみ。診断dictを返す。入力不正と更新違反を分離|
|main(argv=None)|CLI、出力先検証、排他新規生成、JSON保存、終了コード|
|emit_error(code)|出力できない場合のstderr JSON。PASSを返さない|

## 入力契約

Python 3.11以上。UTF-8/BOM、単一ヘッダ、カンマ、二重引用符、二重化エスケープ。
引用内のCR/LFはStringIO(newline='')で保持し、改行正規化しない。レコード終端のLF/CRLF/CRは区別しない。
NUL、空ヘッダ、重複ヘッダ、空／空白のみキー、重複キー、空レコード、列数不一致、解析不能を拒否。
空白を含む非空キーはそのまま照合する（`001`と` 001`は別ID）。列名も非空なら完全一致。
ヘッダ-onlyは0行として有効。標準csv.field_size_limitの上限を超えた入力はCSV_PARSE_ERROR。

ポリシーはschema_version=dtg-policy-v1。5フィールド完全一致・型を厳密に検査。
key_columnは非空文字列、allowed_update_columnsは重複なしの文字列配列。
ID列の許可、存在しない許可列、未知JSONフィールド、重複JSONキー、NaN/Infinityを拒否。
allow_added_rows/allow_removed_rowsはboolのみ（0/1は拒否）。falseは該当する行集合変更を禁止、trueは許容。

## 検査順序・優先度

1. 出力先をresolveで入力と照合、O_EXCLで排他新規生成。既存先や別名hardlinkへの上書きは失敗。
2. 3入力をread_bytesで取得し、その同じバイトのSHA-256と解析結果を用いる。
3. ポリシー検証後、両CSVの構造・キーを独立検証。入力不正があればINVALID_INPUT=2。
4. 有効な2CSVのヘッダ集合が異なればSCHEMA_MISMATCH=1。部分的なセル比較は行わない。
5. 同じヘッダ集合ならキー集合の差からMISSING_ROW/UNEXPECTED_ROW、共通キーの保護列差からUNAUTHORIZED_CHANGE。
6. 違反なしで検査を完了した場合だけPASS=0。

構造不正のあるCSVでは最初の不正を記録し、そのファイルの全件診断は行わない。
ポリシー不正ならCSV検査未実施。未確認の総行数・照合数はnull。
既知の入力不正が更新違反より優先する。キー列・許可列が欠落した場合も構造不正=2。
ID変更は旧行欠落＋新行追加。行順・列順は無視し、数値変換・大文字小文字変換・trim・Unicode正規化はしない。

## JSON契約

schema_version=dtg-report-v1。statusとexit_codeはPASS/0、FAIL/1、INVALID_INPUT/2。
inspection_completeは比較まで完了した場合true。構造不正や読取失敗はfalse。
row_counts(before/after)、matched_rows、detection_count、counts_by_code、violations、sha256(before/after/policy)、
key_display、environment(python/platform)、tool_versionを持つ。
violationsにはcode、必要なcolumn、input、record、before_record/after_record、keyを保存する。
セル値を出力せず、keyは既定null。列名・レコード番号・ハッシュが情報を持つ点はREADMEに明示する。

出力先拒否・引数不正・レポートI/O失敗はstderr JSON=2。安全でない出力先へはJSONを生成しない。
レポート保存中の障害では新規出力が空／途中の可能性がある。stderrと終了コードを確認し、
完全なJSON、inspection_complete、status、exit_codeを併せて判断すること。部分ファイルはPASS証拠にならない。
外部からの強制終了・メモリ枯渇・ホスト障害までJSON生成を保証しない。

## 非破壊性と限界

入力は読み取りでのみ開く。レポートは0600指定の新規ファイル（WindowsではOSの権限処理に従う）。
親ディレクトリは自動生成しない。既存ファイル・入力・既存symlinkの上書きを拒否。
並行書換えをロックする機能はない。各ファイルの読取スナップショットが比較対象で、終了時点の最新性を保証しない。
SHA-256は署名ではなく、入力が正しい業務データであることも証明しない。
メモリ使用量は入力総量、行辞書、違反件数に比例。機密性のある実データを試験物へ収録しない。

## 参考とOSS比較

- https://docs.python.org/3/library/csv.html （文字列解析、newline、strict、field_size_limit）
- https://docs.python.org/3/library/unittest.html （自動試験）

csvは構文解析器であり、IDや保護列などの業務不変条件は利用者側で構成できる。
benchmarks/oss_check.pyはDTGをimportせず、中核ルールを独立に検証する。比較範囲と未測定は開発報告を参照。

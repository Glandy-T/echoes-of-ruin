# Godot プロジェクト監査報告

## 摘要

### 1. 正式制作前に必ず処理する問題

- `res://Main.tscn`／`res://main.tscn` と `res://TitleScreen.tscn`／`res://title_screen.tscn` のパス不一致を修正する。
- `main.tscn` と `next_room.tscn` を正式な休眠施設ではなく、機能検証用テストマップとして扱う方針を確定する。
- 正式なディレクトリ構成を決め、建築シーンが増える前に整理する。
- Door、Terminal、Scene Exit を再利用可能な独立シーンまたは安定したコンポーネントとして設計する。
- インタラクションスクリプトの直接の親ノード、`body.name == "Player"`、固定ノード名への依存を解消する。
- 多数の部屋に対応できるシーン遷移、スポーン地点、シーン状態の管理方式を決める。
- `Camera2D` の固定境界を部屋ごとの設定へ変更する。
- 閉じたドアに物理的な通行阻止が必要かを決める。

### 2. 制作中に処理できる問題

- 正式な調査システム、物体名表示、詳細画像表示。
- 調査・会話中のプレイヤー移動停止。
- UI のレスポンシブ配置、テキストキュー、ヒント競合管理。
- ハードコードされたメッセージのデータ化またはローカライズ対応。
- BGM、効果音、Audio Bus、設定値の保持。
- 部屋ごとのドア、端末、アイテム状態管理。

### 3. 現時点では処理を推奨しない問題

- 完全なディスクセーブ／ロード。
- 正式な多言語対応。
- 最終 BGM、音声、フォント、建築美術。
- 敵、戦闘システム。
- 下水道以降の区域全体を前提とした大規模な技術設計。

### 4. テスト用または廃止の疑いがあるファイル

- `main.tscn`：文書上も機能検証用の簡易マップとされている。
- `next_room.tscn`：場面往復と戻りスポーンを確認するための簡易マップである。
- `main.tscn` 内の `ColorRect`、`Ground2`、簡易 Door／Terminal 表現：灰盒・機能検証用途と考えられる。
- `ui.tscn` の初期テキスト `テキストテスト`：テスト表示である。

ただし、これらは現在の Demo の実行経路で実際に使用されているため、現時点で「未使用」「削除可能」とは判定しない。完全に孤立したシーン、スクリプト、画像素材は確認されていない。

### 5. 移動・改名・削除時にリスクが最も高いファイル

- `project.godot`：メインシーン、Autoload、入力マッピングを保持する。
- `title_screen.tscn`／`title_screen.gd`：プロジェクトの起点であり、`Main.tscn` を文字列で参照する。
- `main.tscn`／`main.gd`：Player、UI、Door、Terminal、スポーン地点を統合している。
- `next_room.tscn`／`next_room.gd`：現在の戻り遷移経路である。
- `player.tscn`／`player.gd`：両マップからインスタンス化される。
- `ui.tscn`／`ui.gd`：両マップからインスタンス化され、固定ノード階層への依存が多い。
- `GameState.gd`：Autoload の UID 参照対象である。
- 各 `.gd.uid` と `.import`：Godot の UID・インポート管理用であり、対応するソースと切り離して削除しない。

特にコード中の `change_scene_to_file("res://...")` は普通の文字列であり、ファイル移動後に自動更新されるとは限らない。

### 6. 現在確認できるエラー・無効参照・機能上の欠陥

- `ui.gd` は存在しない `res://TitleScreen.tscn` を参照しており、ポーズメニューからのタイトル復帰は失敗する。
- `title_screen.gd` と `return_door.gd` は `res://Main.tscn` を参照するが、実ファイルは `main.tscn` である。Windows では動作する可能性が高いが、大文字・小文字を区別する環境では失敗する危険がある。
- BGM 音量と言語設定はコンソールへ値を出力するだけで、実機能へ接続されていない。
- Door は `Area2D` のみで、閉鎖中の物理的な通行阻止を確認できない。
- GameState は実行中のメモリ保持だけであり、ゲーム終了後には消える。
- UI、Player は場面切り替えごとに再生成され、設定値や一時状態も再初期化される。
- プレイヤーはテキスト表示中も移動できる。
- 複数のインタラクション範囲が重なった場合、片方の退出処理がもう一方のヒントを消す可能性がある。
- `show_text()` の古いタイマーが新しいテキスト表示後に終了し、新しい表示をフェードアウトさせる可能性がある。

### 7. 推奨する正式な整理順序

1. バージョン管理上の復帰点を確保し、現在のテスト Demo の動作経路を記録する。
2. シーンパスの大小文字・命名不一致を修正する。
3. 正式なフォルダ構成と命名規則を決める。
4. Godot エディタ上で少量ずつファイルを移動し、各段階で参照を確認する。
5. Door、Terminal、Scene Exit を再利用可能なシーンへ分離する。
6. シーン遷移、スポーン地点、部屋別状態管理を一般化する。
7. UI とマップルートの結合を弱め、共通 UI の扱いを確定する。
8. カメラ境界とプレイヤー制御ロックを部屋側から設定可能にする。
9. その後に正式な休眠施設 Room 1 と建築群の制作を始める。

---

以下は、プロジェクト全体を読み取り専用で静的に確認した完全な監査報告である。Godot は実行していないため、「実装済み」「実行経路がある」という表現は、コードとシーン接続から確認できる範囲を示す。

## 1. 現在のプロジェクト構造

```text
res://
├─ project.godot
├─ GameState.gd                 # Autoload、グローバル実行時状態
├─ title_screen.tscn / .gd      # タイトル画面
├─ main.tscn / main.gd          # テストマップ 1
├─ next_room.tscn / .gd         # テストマップ 2
├─ player.tscn / player.gd      # プレイヤーとカメラ
├─ ui.tscn / ui.gd              # テキスト、ポーズ、設定 UI
├─ door.gd                      # ドアインタラクション
├─ terminal.gd                  # 端末認証
├─ return_door.gd               # 戻り口
├─ icon.svg                     # プロジェクトアイコン
├─ assets/
│  └─ character/
│     ├─ IDLE.png               # 4 フレーム待機スプライトシート
│     └─ WALK.png               # 6 フレーム歩行スプライトシート
└─ docs/
   ├─ PROJECT_OVERVIEW.md
   ├─ GAME_DESIGN.md
   ├─ WORLD_BIBLE.md
   ├─ STORY_REVEAL_PLAN.md
   ├─ MAP_DESIGN.md
   ├─ CHARACTER_DESIGN.md
   ├─ INTERACTION_SYSTEM.md
   ├─ DEVELOPMENT_STATUS.md
   ├─ DEVELOPMENT_RULES.md
   └─ TECHNICAL_NOTES.md
```

メイン入口は [project.godot](../project.godot) の `run/main_scene` が指定する UID `uid://b5irjibgor2d1` であり、[title_screen.tscn](../title_screen.tscn) に対応する。

Autoload：

- 名前：`GameState`
- ファイル：[GameState.gd](../GameState.gd)
- UID：`uid://d4m73oh7d20q6`

入力マッピング：

- `interact`：物理キー E
- `pause`：Esc
- 移動：Godot 標準の `ui_left`／`ui_right`
- ジャンプ：Godot 標準の `ui_accept`。通常は Space／Enter に対応する。

リソース状況：

- `IDLE.png`：384×128、4 個の 96×128 フレーム。
- `WALK.png`：576×128、6 個の 96×128 フレーム。
- カスタムフォントは存在しない。
- 音声、BGM、効果音ファイルは存在しない。
- 環境美術、UI 画像、建築素材は存在しない。
- 現在の UI は Godot 標準フォントと標準 Control スタイルを使用する。
- `.uid` と `.import` は Godot のリソース識別・インポート用メタデータであり、テスト用廃棄ファイルではない。
- `.godot` は Godot の生成キャッシュで、`.gitignore` の対象になっている。

## 2. 実装済みの機能

以下は文書だけでなく、実際のコードとシーン接続から確認した内容である。

| 機能 | 状態 | 根拠・補足 |
| --- | --- | --- |
| タイトル画面 | 接続済み | 「終末の残響」と START ボタンを表示する。 |
| ゲーム開始 | 接続済み | START で Demo 状態を初期化し、`Main.tscn` へ遷移する。 |
| 左右移動 | 実装済み | 移動速度は 200。 |
| 重力・ジャンプ | 実装済み | 重力 900、ジャンプ速度 -350。 |
| プレイヤーの向き | 実装済み | 最後の移動方向を保持し、`flip_h` で反転する。 |
| 待機・歩行アニメーション | 実装済み | idle 4 フレーム、walk 6 フレーム、各 5 FPS。 |
| カメラ | 実装済み | Player の子ノードで、位置スムージングが有効。 |
| 近接検知 | 実装済み | Door、Terminal、ReturnDoor が `Area2D` の信号を使用する。 |
| 操作ヒント | 実装済み | 接近時に「Eキーで調べる」「Eキーで戻る」を表示する。 |
| テキストボックス | 実装済み | テキスト表示、待機、フェードアウトを行う。 |
| 端末認証 | 実装済み | 初回使用時に状態を保存し、対象ドアを開く。 |
| ドア開放アニメーション | 実装済み | `DoorPanel` を上へ 180 ピクセル、1 秒で移動する。 |
| シーン遷移 | 実装済み | Main → NextRoom → Main の経路がある。 |
| 戻りスポーン | 部分実装 | Main へ戻る際は `DoorSpawn` に配置される。 |
| シーン状態保持 | 実行中のみ実装 | 端末・ドア状態を Autoload に保持する。 |
| ポーズ・再開 | 実装済み | Esc と画面ボタンの両方から切り替えられる。 |
| 設定パネル | UI 実装済み | 開く、戻る操作がある。 |
| ヒント表示切替 | 実装済み | 現在の UI インスタンスのヒント表示を切り替える。 |
| BGM 音量 | 未接続 | 値をコンソールへ表示するだけである。 |
| 言語切替 | 未接続 | 選択値をコンソールへ表示するだけである。 |
| タイトル復帰 | 故障 | 存在しない `TitleScreen.tscn` を参照する。 |
| 設定保存 | 未実装 | シーン切替や再実行後に保持されない。 |
| ディスクセーブ | 未実装 | 保存・読み込みファイル処理は存在しない。 |

Door は現在、視覚・インタラクション上のロックである。Door ノードは `Area2D` であり、閉鎖中にプレイヤーを物理的に阻止する `StaticBody2D` は確認できない。

## 3. シーンとスクリプトの対応関係

### シーン関係

| シーン | 使用スクリプト・インスタンス | 主な依存 |
| --- | --- | --- |
| `title_screen.tscn` | `title_screen.gd` | 直接の子ノードに `StartButton` が必要。 |
| `main.tscn` | `main.gd`、`door.gd`、`terminal.gd`。Player と UI をインスタンス化。 | ルート直下に `Player`、`UI`、スポーン Marker が必要。 |
| `next_room.tscn` | `next_room.gd`、`return_door.gd`。Player と UI をインスタンス化。 | ルート直下に `UI` と ReturnDoor が必要。 |
| `player.tscn` | `player.gd` | `AnimatedSprite2D` が必要。 |
| `ui.tscn` | `ui.gd` | 固定名・固定階層の全 UI ノードに依存する。 |

### スクリプトのノード依存

- [main.gd](../main.gd)
  - `$UI`
  - `$Player`
  - ルート直下に `GameState.next_spawn_name` と同名の Marker が必要。

- [door.gd](../door.gd)
  - `$DoorPanel`
  - `get_parent()` が `show_message()`、`show_prompt()`、`hide_message()` を提供する必要がある。
  - Body の名前が正確に `Player` である場合だけ反応する。

- [terminal.gd](../terminal.gd)
  - エクスポートされた `door_path`。
  - 現在の値は `../Door`。
  - 対象ノードは `unlock_and_open()` を持つ必要がある。
  - 親ノードは UI 仲介メソッドを提供する必要がある。

- [return_door.gd](../return_door.gd)
  - 親ノードは UI 仲介メソッドを提供する必要がある。
  - Body の名前が正確に `Player` である場合だけ反応する。

- [ui.gd](../ui.gd)
  - `TextBox/TextLabel`。
  - 固定名のポーズ、設定、タイトル、戻るボタンと各設定 Control。
  - UI ノード階層を変更すると、`@onready` のノード取得が失敗する危険がある。

### シーン遷移フロー

```text
title_screen.tscn
  START
    → GameState を初期化
    → res://Main.tscn

main.tscn
  Terminal 認証
    → GameState.main_terminal_used = true
    → Door.unlock_and_open()
    → GameState.main_door_opened = true

  開放済み Door を調べる
    → res://next_room.tscn

next_room.tscn
  ReturnDoor を調べる
    → GameState.next_spawn_name = "DoorSpawn"
    → res://Main.tscn
    → main.gd が Player を DoorSpawn へ配置
```

### GameState が保存する状態

- `next_spawn_name`
  - 初期値：`StartSpawn`
  - Main への復帰時：`DoorSpawn`
- `main_terminal_used`
- `main_door_opened`

これらは現在のゲームプロセス内だけに存在する。ゲーム終了後には失われるため、正式なセーブデータではない。

## 4. 保持して継続利用できる内容

直接保持しやすい内容：

- `player.tscn` の基本的なキャラクターノード構成。
- 左右移動、ジャンプ、重力、向き制御。
- idle／walk アニメーション素材と `SpriteFrames`。
- Player の子として `Camera2D` を置く基本方式。
- `GameState` を場面横断状態の入口にする考え方。
- `ui.tscn` を共通 UI の原型にする構成。
- ポーズ中にも UI を処理する `process_mode` 設定。
- `Area2D + body_entered/body_exited` による近接検知。
- Terminal から対象 Door のメソッドを呼ぶ基本的な連携。
- シーン再訪時に開放済み Door を復元する考え方。
- Marker2D をスポーン地点として使う考え方。
- `door_path` によって Terminal の対象 Door を指定する考え方。

概念は保持できるが、大量の部屋を作る前に一般化すべき内容：

- `main.gd`／`next_room.gd` の UI 仲介メソッド。
- Door、Terminal、ReturnDoor の各スクリプト。
- `GameState.next_spawn_name`。
- 各スクリプトから直接 `change_scene_to_file()` を呼ぶ方式。

現在の構造は単一の灰盒 Room を制作するには使用できるが、数十の部屋へそのまま複製する構造ではない。

## 5. テスト内容と整理対象

### 明確にテスト用途の内容

- `main.tscn`
  - 設計文書で機能検証用の簡易マップと明記されている。
  - 地面、壁、Door、Terminal の表示は主に `ColorRect` で構成される。
  - 正式な休眠施設 Room 1 ではない。

- `next_room.tscn`
  - 地面、ReturnDoor、Player、UI だけで構成される。
  - シーン往復を検証する簡易マップである。

- `TextBox/TextLabel` の既定テキスト `テキストテスト`。
- `Ground2` などの単純な灰盒境界構造。

これらは現在の Demo 経路で使用中であるため、廃止済み・削除可能とは判定しない。

### 重複構造

重複ファイルは確認されていないが、以下の構造的重複がある。

- `main.gd` と `next_room.gd` が同じ UI 仲介メソッドを持つ。
- Main と NextRoom がそれぞれ Player と UI をインスタンス化する。
- Door と Terminal が独立した再利用シーンではなく、マップ内に直接構築されている。

### 命名の不統一

- 実ファイル：`main.tscn`
- コード参照：`res://Main.tscn`

現在の Windows 環境では解決される可能性が高いが、大文字・小文字を区別する環境では失敗する。

タイトル復帰には、より明確な不一致がある。

- 実ファイル：`title_screen.tscn`
- UI の参照：`res://TitleScreen.tscn`

大小文字だけでなくアンダースコアも異なるため、現在のタイトル復帰は正常に動作しない。

`GameState.gd` だけが大文字開始で、他のスクリプトは小文字スネークケースである。これは現在の機能を直接壊さないが、命名規則は統一されていない。

### 未使用リソース

静的な参照確認では、削除可能と判断できる未使用ソースリソースは発見されていない。

- `IDLE.png` と `WALK.png` は `player.tscn` から使用される。
- `icon.svg` は `project.godot` から使用される。
- 9 個の `.gd` はすべてシーンまたは Autoload から使用される。
- 5 個の `.tscn` はすべて現在の入口・遷移経路に含まれる。

### ハードコードされた内容

- シーンパス：
  - `res://Main.tscn`
  - `res://next_room.tscn`
  - `res://TitleScreen.tscn`
- スポーン地点名：
  - `StartSpawn`
  - `DoorSpawn`
- Terminal の対象：
  - `NodePath("../Door")`
- Player の判定：
  - `body.name == "Player"`
- Door の移動量：180 ピクセル。
- Player の速度、ジャンプ速度、重力。
- Camera の境界：左 0、上 0、右 1797、下 650。
- 全インタラクションヒント、Terminal メッセージ。
- UI の初期値：音量 80、日本語、ヒント ON。
- UI の多数の固定ピクセル座標。

### 地図拡張時の問題

- インタラクションオブジェクトは、直接の親がマップルートであることを前提とする。
- 各マップルートスクリプトに同じ UI メソッドを用意する必要がある。
- インタラクションを建築内の深いノード階層へ置くと、`get_parent()` の前提が壊れる。
- Player を改名すると全インタラクションが反応しなくなる。
- スポーン地点が存在しない場合、`main.gd` はエラーを出さず配置をスキップする。
- `terminal.gd` の `door_path` に無効なパスが設定されても保護されない。
- 固定 Camera 境界は異なる大きさの部屋に対応しない。
- シーン切替のたびに Player と UI が再生成される。
- UI のヒント設定、言語、音量などがシーンごとに再初期化される。
- 複数の近接範囲が重なると、一方の退出信号が他方のヒントを消す可能性がある。
- `show_text()` の古いタイマーが、新しい表示中に終了してフェードを開始する可能性がある。
- テキスト表示中でも Player は移動でき、正式な簡易調査の移動停止は未実装である。

## 6. 推奨プロジェクト構造

現在の規模を大きく変えず、軍事休眠施設の拡張に対応する構成例：

```text
res://
├─ scenes/
│  ├─ core/
│  │  └─ title_screen.tscn
│  ├─ player/
│  │  └─ player.tscn
│  ├─ ui/
│  │  └─ game_ui.tscn
│  ├─ interactions/
│  │  ├─ door.tscn
│  │  ├─ terminal.tscn
│  │  └─ scene_exit.tscn
│  └─ areas/
│     └─ military_facility/
│        ├─ room_01_cryogenic.tscn
│        ├─ floor_04_corridor.tscn
│        └─ floor_04_station.tscn
├─ scripts/
│  ├─ core/
│  │  ├─ game_state.gd
│  │  └─ scene_transition.gd
│  ├─ player/
│  │  └─ player_controller.gd
│  ├─ ui/
│  │  └─ game_ui.gd
│  ├─ interactions/
│  │  ├─ interactable.gd
│  │  ├─ door.gd
│  │  ├─ terminal.gd
│  │  └─ scene_exit.gd
│  └─ world/
│     └─ area_controller.gd
├─ assets/
│  ├─ characters/
│  ├─ environments/
│  │  └─ military_facility/
│  ├─ ui/
│  ├─ audio/
│  └─ fonts/
└─ docs/
```

ファイルは Windows のファイル管理画面から直接移動せず、先にハードコードされたパスを整理し、その後 Godot エディタ上で少量ずつ移動し、各段階で参照を確認することを推奨する。

## 7. 正式な建築制作前に処理する項目

### 必ず先に処理する

1. `Main.tscn`／`main.tscn`、`TitleScreen.tscn`／`title_screen.tscn` のパス不一致を修正する。
2. `main.tscn` と `next_room.tscn` はテストマップであり、正式な建築へ直接拡張しないことを確定する。
3. 建築シーンが増える前に正式なフォルダ構成を決める。
4. Door、Terminal、Scene Exit を再利用可能な独立シーンまたは安定コンポーネントにする。
5. インタラクションスクリプトの直接親と `body.name` への強い依存を解消する。
6. 多数の部屋を扱えるシーン遷移・スポーンデータを設計する。
7. Camera 境界を各部屋から設定できるようにする。
8. 閉鎖中の Door に物理的な通行阻止が必要かを決める。

### 制作中に処理できる

- 正式な調査システム。
- 調査中の Player 移動停止。
- 物体名表示。
- 詳細画像 UI。
- UI のレスポンシブレイアウト。
- 複数ヒントの競合管理。
- テキストキューとタイマーキャンセル。
- ハードコードされたテキストのデータ化。
- BGM、効果音、Audio Bus。
- UI 設定のシーン間保持。
- 各部屋の Door、Terminal、Item 状態記録。

### 現時点では処理しなくてよい

- 完全なディスクセーブ。
- 正式な多言語機能。
- 最終 BGM、音声、フォント。
- 最終建築美術。
- 敵と戦闘システム。
- 下水道以降の区域全体を対象にした完全な技術構成。

## 8. リスク警告

### ファイル移動・改名

リスクは高い。シーンのリソース参照には UID とパスが含まれるが、コード内の `change_scene_to_file("res://...")` は普通の文字列であり、ファイル移動時に確実に自動更新されるとは限らない。

スクリプト移動時には、対応する `.gd.uid` の関係も維持する必要がある。`.uid` を単独で不要ファイルとして削除しない。

### シーン状態

現在の状態は Autoload のメモリ内だけに保存される。

- ゲーム終了後に消える。
- ディスクセーブはない。
- Main の 1 個の Terminal と 1 個の Door だけを対象とする。
- START を押すとリセットされる。

部屋が増えた後も `main_terminal_used` のような専用変数を増やし続けると、管理が急速に複雑化する。

### Main／NextRoom の位置づけ

両方とも機能検証用シーンであり、正式な休眠施設ではない。

- 設計文書に簡易プロトタイプと明記されている。
- 表示は単純な `ColorRect` が中心である。
- 正式 Room 1 の休眠ポッド、識別票、開場演出、正式調査システムは存在しない。

### 大量の部屋を追加した後のシーン遷移

現在の方式は 2〜3 部屋の検証には使えるが、大規模施設には適さない。

- 各出口が遷移先パスを直接保持する。
- スポーン地点は文字列名に依存する。
- 現在スポーン名を読むのは Main だけである。
- 統一されたトランジション管理がない。
- 部屋 ID と部屋別状態辞書がない。
- シーン切替ごとに Player と UI が再生成される。

### UI の全シーン再利用

`ui.tscn` は各場面からインスタンス化できるため、プロトタイプ用共通 UI としては継続利用できる。ただし、現在は場面を横断して生存する UI ではない。

- 各マップが新しい UI インスタンスを作る。
- ヒント、音量、言語設定がリセットされる。
- 各マップスクリプトが同じ UI 仲介メソッドを持つ必要がある。
- 固定ピクセル配置であり、異なる解像度への対応が弱い。
- 正式調査に必要な移動停止、詳細画像、テキストキューは存在しない。

## 結論

現在の Player、UI 原型、GameState の入口、Area2D インタラクション、Marker2D スポーン地点という基本概念は保持できる。正式な休眠施設建築を開始する前に優先すべきなのは、シーンパスの統一、再利用可能なインタラクション部品、シーン遷移・状態管理の一般化、部屋別 Camera 境界である。

---

## 第一段階の整改結果（2026-07-15）

この節は上記の原始監査内容を削除せず、第一段階の工程整理後の現状を記録する。

### 安全措置

- ユーザーがプロジェクト外に完全なローカルバックアップを作成済みである。
- 学校 PC に Git はなく、プロジェクト内の `.git` は空ディレクトリであるため、Git 初期化、分岐、コミット、リモート操作は行っていない。
- 空の `.git` ディレクトリは変更・削除していない。

### 整理後の主要パス

- メインシーン：`res://scenes/core/title_screen.tscn`
- Autoload：`GameState = res://scripts/core/game_state.gd`
- 開発用マップ：`res://scenes/dev/prototype_room_a.tscn`、`prototype_room_b.tscn`
- Player：`res://scenes/player/player.tscn`
- GameUI：`res://scenes/ui/game_ui.tscn`
- 再利用インタラクション：`res://scenes/interactions/door.tscn`、`terminal.tscn`、`scene_exit.tscn`
- 正式な軍事休眠施設の配置先：`res://scenes/areas/military_facility/`。正式シーンは未作成。

### 実施した修正

- すべてのソースパスを小文字 snake_case の実在パスへ統一した。
- `Main.tscn`／`TitleScreen.tscn` の失効参照を解消した。
- Player を `player` Group、GameUI を `game_ui` Group へ登録した。
- Terminal と Scene Exit は `body.is_in_group("player")` で Player を判定する。
- インタラクションは親マップの UI 仲介メソッドへ依存せず、`game_ui` Group から GameUI を取得する。
- Door に `StaticBody2D` と `CollisionShape2D` を追加し、閉鎖中は通行を阻止し、開放時に衝突を無効化する。
- Door の `state_id`、`open_offset`、`animation_time` を Inspector 設定可能にした。
- Terminal の Door パス、状態 ID、表示テキストを Inspector 設定可能にし、無効な Door 参照へ警告を追加した。
- Scene Exit の目標シーン、目標スポーン ID、ヒント、必要 flag を Inspector 設定可能にした。
- `GameState` を `world_flags`、`set_flag()`、`get_flag()`、`reset_demo_state()` と `next_spawn_id` に一般化した。
- 共通 `room_controller.gd` が全 playable room のスポーン適用と Camera 境界設定を行う。
- Marker2D 用 `spawn_point.gd` により、スポーン ID を Inspector から設定できる。
- GameUI の古いテキストタイマー／Tween の競合を version 管理で無効化した。
- 操作ヒントを発生元ごとに登録し、片方の Area 退出で別の有効なヒントが消えないようにした。
- `テキストテスト` を削除し、BGM・言語 UI に「未接続」を明記した。

### 静的検証結果

- 全 `.gd`、`.tscn`、`.import`、`project.godot` 内の旧ソースパス検索：残存なし。
- 全 `res://` 参照の実在確認：すべて存在。
- `.gd.uid` の保持と重複確認：9 件すべて一意。
- Terminal／Scene Exit のシグナル接続メソッド確認：すべて存在。
- `.tscn` の `load_steps` と外部／内部リソース数：一致。
- Godot 実行ファイルは PATH、一般的な配置場所、ショートカットから確認できず、自動インポート・実行テストは未実施。

### 手動テスト項目

1. Godot 4.6 系でプロジェクトを開き、インポートとスクリプト解析エラーがないことを確認する。
2. タイトル画面から START し、prototype A に入る。
3. 左右移動、ジャンプ、idle／walk、左右反転、Camera を確認する。
4. 閉鎖中の Door が Player を物理的に阻止することを確認する。
5. Terminal を E で使用し、メッセージ、上方向 Tween、衝突解除を確認する。
6. Scene Exit から prototype B へ移動する。
7. prototype B から prototype A へ戻り、`from_room_b` スポーンへ配置されることを確認する。
8. Door と Terminal の状態が、同じゲーム実行中は保持されることを確認する。
9. ポーズ、続行、設定画面、ヒント ON/OFF、タイトル復帰を確認する。
10. 再度 START し、Demo の `world_flags` とスポーン ID が初期化されることを確認する。
11. 複数のインタラクション範囲が重なる位置で、片方を離れても残る対象のヒントが維持されることを確認する。
12. Godot の Output／Debugger にエラー、失効参照、意図しない警告がないことを確認する。

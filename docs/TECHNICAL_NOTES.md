# 技術ノート

## 構成

Godot 4.6 系、GDScript のプロジェクトである。`project.godot` では `res://scenes/core/title_screen.tscn` をメインシーンに設定し、`res://scripts/core/game_state.gd` をオートロード `GameState` として登録している。レンダラーは Compatibility（GL Compatibility）である。

第一段階の工程整理後、シーン、スクリプト、アセットを用途別ディレクトリへ配置している。`scenes/areas/military_facility/` には正式マップ用の第一版灰盒 `cryo_room_4f_01.tscn` を配置している。ただし、タイトル画面からの正式な進行経路にはまだ接続していない。

```text
res://
├─ project.godot
├─ scenes/
│  ├─ core/title_screen.tscn
│  ├─ player/player.tscn
│  ├─ ui/game_ui.tscn
│  ├─ interactions/
│  │  ├─ door.tscn
│  │  ├─ terminal.tscn
│  │  ├─ scene_exit.tscn
│  │  └─ investigation_point.tscn
│  ├─ dev/
│  │  ├─ prototype_room_a.tscn
│  │  └─ prototype_room_b.tscn
│  └─ areas/military_facility/cryo_room_4f_01.tscn
├─ scripts/
│  ├─ core/game_state.gd, title_screen.gd
│  ├─ player/player.gd
│  ├─ ui/game_ui.gd
│  ├─ interactions/door.gd, terminal.gd, scene_exit.gd, investigation_point.gd
│  └─ world/room_controller.gd, spawn_point.gd
└─ assets/characters/
   ├─ idle.png
   └─ walk.png
```

## 主要スクリプトの責務

| スクリプト | 責務 |
| --- | --- |
| `game_state.gd` | `world_flags` と `next_spawn_id` に加え、世界状態とは分離した実行時設定 `interaction_hints_enabled` を保持する。 |
| `title_screen.gd` | Demo 状態の初期化、一時的な prototype 入口、操作ヒント設定、ウィンドウ／フルスクリーン切替を管理する。 |
| `room_controller.gd` | Player のスポーン適用と、部屋ごとの Camera 境界設定を共通処理する。 |
| `spawn_point.gd` | Marker2D に Inspector 設定可能な `spawn_id` を与える。 |
| `player.gd` | `CharacterBody2D` の左右移動、重力、ジャンプ、アニメーション、左右反転と、対話中の入力ロックを制御する。 |
| `terminal.gd` | Group で Player と GameUI を検出し、Inspector 指定の Door を検証して `unlock_and_open()` を呼ぶ。 |
| `door.gd` | 開放状態、上方向 Tween、閉鎖時の物理衝突、開放後の衝突無効化を管理する。 |
| `scene_exit.gd` | Inspector 指定の目標シーン、スポーン ID、必要 flag に基づいて場面を切り替える。 |
| `investigation_point.gd` | Inspector 指定のページ、表情 ID、任意の詳細画像を GameUI の対話 API へ渡す。 |
| `game_ui.gd` | 一時テキスト、発生元別ヒント、独白／詳細調査、プレイヤー入力ロック、ポーズ／設定を制御し、操作ヒント設定を GameState と同期する。 |

## シーン間の関係

```text
scenes/core/title_screen.tscn
  └─ START
       └─ scenes/dev/prototype_room_a.tscn
            ├─ Terminal（認証）→ Door（開放）
            └─ SceneExit → scenes/dev/prototype_room_b.tscn
                              └─ SceneExit → prototype_room_a.tscn（from_room_b）
```

- `prototype_room_a.tscn` は Player、GameUI、Door、Terminal、SceneExit をインスタンス化する。
- `prototype_room_a.tscn` には、第一版対話 API の確認専用として通常独白と詳細調査の DEV Investigation Point を配置する。正式マップ用の調査対象ではない。
- `prototype_room_b.tscn` は Player、GameUI、SceneExit をインスタンス化する。
- 両 prototype は同じ `room_controller.gd` を使用し、正式な建築シーンではない。
- `cryo_room_4f_01.tscn` は Player、GameUI、Room Controller、Spawn Point、Door、Terminal を既存システムから再利用する。Camera 境界は 1920×720 であり、開始位置は `PlayerControlStart` に設定する。
- 正式 Room 1 はまだタイトル画面や他の正式マップへ接続しない。出口付近には `SceneExit` を置かず、`ExitRouteDisabledAnchor` によって将来の接続位置だけを示す。
- 各休眠ポッドの状態と銘板、巡回表、検査台上の物品、同意書は Marker2D のみを配置する。空ページを開くことを防ぐため、正式な調査文章が決まるまでは Investigation Point を有効化しない。
- `player.tscn` は `CharacterBody2D`、当たり判定、`AnimatedSprite2D`、`Camera2D` で構成される。
- `game_ui.tscn` は `CanvasLayer` をルートとし、テキストボックス、ポーズ UI、設定 UI を持つ。`process_mode = 3` によりゲームがポーズ中でも UI を処理する。

## システム間の呼び出し関係

```text
Player の物理処理
  └─ player.gd → 入力取得 → CharacterBody2D.move_and_slide()

Area2D の body_entered / body_exited
  └─ terminal.gd / scene_exit.gd / investigation_point.gd
       ├─ Player は `player` Group で判定
       └─ `game_ui` Group の GameUI へ発生元付きヒントを登録／解除

Investigation Point の E 操作
  ├─ GameUI.can_accept_world_interaction() を確認
  ├─ 画像なし → GameUI.start_dialogue()
  └─ 画像あり → GameUI.start_detail_dialogue()
       ├─ DialoguePanel と任意の DetailOverlay を表示
       ├─ Player.set_input_locked(true)
       └─ 終了時にロック解除と登録済みヒントの再表示

Terminal の E 操作
  └─ GameState.set_flag(terminal_state_id, true)
  └─ Door.unlock_and_open()
       └─ GameState.set_flag(door_state_id, true)
       └─ Tween で DoorPanel を移動
       └─ 物理衝突を無効化

Scene Exit の E 操作
  └─ 必要 flag を確認
  └─ GameState.next_spawn_id を設定
  └─ SceneTree.change_scene_to_file()

Room Controller の初期化
  ├─ `player` Group から Player を取得
  ├─ spawn_id が一致する Marker2D へ配置
  └─ Inspector の left / top / right / bottom を Camera2D へ適用
```

Terminal と Scene Exit は `body.is_in_group("player")` で Player を判定する。UI は `game_ui` Group から取得するため、インタラクションの直接の親ノードに UI 仲介メソッドを要求しない。`terminal.gd` は `target_door_path` の存在と `unlock_and_open()` の有無を検証し、不正な場合は警告を出す。

Terminal、Scene Exit、Investigation Point は E 入力を処理する前に `GameUI.can_accept_world_interaction()` を確認する。対話、詳細調査、ポーズ、設定画面のいずれかが開いている間は、世界側のインタラクションを開始しない。

## 再利用シーンの設定

- Door：`state_id`、`open_offset`、`animation_time` を Inspector で設定する。
- Terminal：`target_door_path`、`state_id`、表示テキストを Inspector で設定する。
- Scene Exit：`target_scene_path`、`target_spawn_id`、`prompt_text`、任意の `required_flag_id` を設定する。
- Investigation Point：`prompt_text`、手動改ページ単位の `pages`、任意の `expression_ids` と `detail_texture` を設定する。
- Spawn Point：Marker2D に `spawn_point.gd` を設定し、`spawn_id` を指定する。
- Room：`room_controller.gd` の `default_spawn_id` と Camera 境界 4 値を指定する。

`cryo_room_4f_01.tscn` では、左から右への空間上の並びを `PodSlot01`～`PodSlot05` として扱い、設定上確定しているポッド本体番号は主役ポッドの `ID 04` だけである。空間順と本体番号を混同しないため、主役ポッドは `PodSlot02PlayerID04` と命名している。

## 対話・詳細調査 API

- `GameUI.start_dialogue(pages, expression_ids)`：画像を使用しない主人公独白または簡易調査を開始する。
- `GameUI.start_detail_dialogue(detail_texture, pages, expression_ids)`：中央の詳細画像と共通 DialoguePanel を同時に表示する。
- `pages` の 1 要素を 1 ページとして扱い、自動分割や自動終了は行わない。
- `expression_ids` が不足するページ、空 ID、未登録 ID は `neutral` へフォールバックする。第一版では全 ID が同じ暫定画像を使用する。
- 対話中は SceneTree を pause せず、Player の入力だけをロックする。空中の重力、衝突、着地は継続する。
- Enter またはマウス左クリックで次ページへ進み、最終ページの次で閉じる。Esc は現在の対話または詳細調査だけを閉じ、同じ入力でポーズを開かない。

## 入力・設定上の補足

- `move_left`：A／左方向キー、`move_right`：D／右方向キー。
- `jump`：Space／W／上方向キー。Player のジャンプには `ui_accept` を使用しない。
- `interact`：E。調査、端末、ドア、場面インタラクションに使用する。
- `dialogue_advance`：Enter／マウス左ボタン。DialoguePanel または DetailOverlay が開いている間だけ使用する。
- `pause`：Esc。対話中は対話を閉じ、ポーズ設定画面ではポーズ主画面へ戻り、ポーズ主画面ではゲームへ復帰する。
- `ui_accept` など Godot 標準 UI 入力はタイトル、ポーズ、設定画面の操作用として保持する。
- S／下方向キーに対応するゲーム内アクションは定義しない。
- UI の音量・言語選択は現状 `print()` のみで、音響・ローカライズの実装は**要補足**。
- BGM と言語の UI ラベルには、現在未接続であることを明記している。
- シーンパスは小文字 snake_case の実在パスへ統一済みである。
- `GameState` の状態はメモリ上だけに存在し、ディスクセーブではない。

## 実行時設定と世界状態の分離

- `GameState.interaction_hints_enabled` は、タイトル設定画面とゲーム内設定画面が共有する実行時設定である。
- この設定は `world_flags` に格納しない。端末、Door、進行状態などのゲーム世界状態と、ユーザー設定を混在させない。
- `reset_demo_state()` は `next_spawn_id` と `world_flags` のみを初期化し、`interaction_hints_enabled` を変更しない。
- タイトル画面と GameUI のチェックボックスは、初期化時に `set_pressed_no_signal()` で同じ値を反映し、ユーザー操作時に同じ変数へ書き戻す。
- 現段階の設定保持範囲は現在のゲーム実行中のみであり、終了後まで保持する設定ファイルやセーブ機能は実装しない。

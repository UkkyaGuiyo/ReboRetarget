# Codex Memory Build Report

作成日: 2026-09-04

## 1. 作成・変更したファイル

今回の作業前は `.git` 以外のファイルが存在しなかったため、既存ファイルの変更や上書きはなく、以下の9ファイルを新規作成した。

1. `AGENTS.md`
2. `README.md`
3. `docs/PROJECT_CHARTER.md`
4. `docs/DECISIONS.md`
5. `docs/CURRENT_STATE.md`
6. `docs/ROADMAP.md`
7. `docs/RESEARCH_LOG.md`
8. `docs/QUEST_CHEST_YAW_ANCHOR.md`
9. `docs/CODEX_MEMORY_BUILD_REPORT.md`

## 2. 各ファイルの役割

- `AGENTS.md`: 今後このリポジトリを開くCodexの入口。読む順序、正本、主要原則、開始・終了時の作業ルールを示す。
- `README.md`: 公開を意識した短いプロジェクト概要。現時点が研究・foundation段階で、動くアプリがないことを明記する。
- `PROJECT_CHARTER.md`: 頻繁には変えない長期ゴール、解く問題、初期境界、成功品質を固定する。
- `DECISIONS.md`: 決定済み事項と理由、まだ未決定の事項を分離する。
- `CURRENT_STATE.md`: 実装済み・未実装、確認済みGit状態、阻害要因、次回の第一タスクを示す。
- `ROADMAP.md`: foundationから調査、solver、実接続、安全な切替、統合UX、公開準備までを段階化する。
- `RESEARCH_LOG.md`: 採用結果だけでなく、証拠、失敗、不採用、未確認事項を残す場所と形式を定める。
- `QUEST_CHEST_YAW_ANCHOR.md`: Quest胸Yaw案を、本体MVPを止めない独立した将来研究として定義する。
- `CODEX_MEMORY_BUILD_REPORT.md`: 今回の構築内容、自己検証、未解決事項、Git/公開状態をChatGPTへ引き継ぐ報告書。

## 3. AGENTS.mdの重要ルール

- セッション開始時に `AGENTS.md`、`PROJECT_CHARTER`、`DECISIONS`、`CURRENT_STATE`、`ROADMAP` を読む。
- 最新の明示的ユーザー指示、原依頼、決定、実環境の証拠、現在地、古い計画の順に扱い、矛盾を勝手に削除しない。
- 単純座標倍率ではなくTarget Skeleton上で関節運動を再構成する。
- 膝・肩の情報、通常のQuest controller手経路、ReboCapのユーザー調整済み設定を守る。
- Native/Retarget切替では必要箇所だけを変更し、変更前の正確な状態へ戻す。
- 公式SDK/APIから順に現場調査し、Hookは最後にする。
- ライブVRセッション中は読み取り調査を優先し、無断でforeground、再起動、停止、reset、設定変更をしない。
- 将来要求を想像した巨大な抽象化や独自SteamVR Driver等を先回りしない。
- ユーザー仮説と確認事実が衝突した場合は、根拠を説明して事実に合わせて修正できる。
- 作業終了時は、事実が変わったcanonical docsだけを更新し、最終受入面で確認する。

## 4. PROJECT_CHARTERに固定した長期ゴール

ReboCapで取得した人間の動きを、骨格比率の異なるVRChatアバターのTarget Skeleton上へリアルタイムに再構成し、Meta Quest 3、Virtual Desktop、SteamVR、VRChat、ReboCap環境で自然なFull Body Trackingを実現する。

脚長差による不要な膝曲がりや、肩幅・上腕長・前腕長の差で崩れる腕姿勢を、一律スケールではなくMorphology Retargetingで扱う。長期UXとしてはReboCap起動に連動し、Native/Retargetを安全に切り替え、終了時にProfile保存・OSC停止・変更設定の復元・自己終了を行う。

## 5. DECISIONSに記録した決定事項

1. 一律スケールではなくMorphology Retargetingを行う。
2. VRChat OSCへHip、Chest、左右Knee、左右Foot、左右Upper Armの8点を送る方向。
3. 膝Trackerを残す。
4. 肩Trackingを上半身solver入力として残す。
5. 初期版の手はQuest controllerの通常経路を維持し、Virtual Controllerを対象外とする。
6. 初期体型調整候補はLeg Length、Thigh/Calf Balance、Hip Width、Arm Length、UpperArm/Forearm Balance、Shoulder Width。
7. アバター別Profileを保存し、初期版は手動選択とする。
8. ReboCap本体改造を前提にせず、公式手段や外部Windowで統合UXを目指す。
9. Native/Retarget切替は自動かつ可逆で、切替前の正確な状態を復元する。
10. 肩/センサー割当、AI Engine、6軸/磁気、Ground IK、Skeleton、純正calibration等を保護する。
11. 調査優先順位を公式SDK/API、設定、local IPC/API、Windows UI Automation、内部解析/Hookとする。
12. Quest Chest Yaw Anchorは独立した将来研究とする。
13. 低遅延・低ジッタ・最新Pose優先・二重smoothing回避を重視する。
14. 不要なPlugin System、DI、Event Bus、Database、独自SteamVR Driver等を作らない。
15. 公開時は未完成を偽らず、専有物・個人情報・端末情報・secret・raw logを含めない。

## 6. CURRENT_STATEに記録した現在地

永続記憶foundationだけが完成した。ReboCap接続、OSC、solver、GUI、Watcher、Profile実装、SteamVR制御、Quest胸Yaw機能、test、build、release、deployはすべて未実装である。技術stackも未決定。

リポジトリは `master` branch、commitなし、remoteなし、LICENSEなしである。今回作成した文書は未commitである。

## 7. ROADMAPの概要

- Phase 0: 永続記憶foundation（今回完了）。
- Phase 1: ReboCap/VRChat interfaceの読み取り中心の調査（次）。
- Phase 2: 最小retarget仕様とtest pose。
- Phase 3: controlled input上のretarget core。
- Phase 4: live ReboCap入力とVRChat OSC 8点出力。
- Phase 5: 安全なNative/Retarget切替とProfile。
- Phase 6: ReboCap連動UXとresilience。
- Phase 7: license確認を含む公開準備。
- 独立track: Quest Chest Yaw Anchor研究。

## 8. Quest Chest Yaw Anchorの位置付け

本体MVPを止めない独立した将来研究である。ReboCapを通常の全身Trackingの主役に保ち、Quest IOBT Chest Yawは低周波の外部Yaw基準候補に限定する。OFF → MONITORで検証し、AUTOは証拠と安全策が揃ってユーザーが承認するまで実装承認済みとは扱わない。不安定・stale・不連続なら何もせず、固定Offsetと時間driftを分離し、将来補正する場合も徐々に行う。BiasはProfileではなくsession限定とする。

## 9. グローバルCodex設定

ユーザーのglobal Codex `AGENTS.md` と `config.toml` を読み取りで確認したが、変更していない。既存global AGENTSには原指示優先、最小操作、現場証拠、状態更新の一般ルールが既にあり、ReboRetarget固有内容を追加する必要はなかった。既存内容の削除・上書き・統合変更はゼロである。

## 10. 既存ファイルとの衝突・統合

既存project fileもfoundation archiveも存在しなかったため、衝突・上書き・統合対象はなかった。README、LICENSE、CONTRIBUTING、SECURITY、THIRD_PARTYも存在しなかった。今回は必要最小限としてREADMEのみ追加し、LICENSE等は依存関係確認前に仮置きしなかった。

## 11. 自己検証12項目

新規Codexのつもりで `AGENTS.md` からcanonical docsを読み直し、以下を文書だけで回答できることを確認した。結果は **12/12 PASS**。

1. **何を作るか — PASS:** ReboCap人間動作を異なる骨格比率のVRChat avatarへreal-time morphology retargetする。
2. **なぜ単純scaleでないか — PASS:** thigh/calf、hip、shoulder、upper-arm/forearm差は独立しており、一律倍率では直せない。
3. **最終予定点数 — PASS:** 8点。Hip、Chest、左右Knee、左右Foot、左右Upper Arm。
4. **なぜ膝を残すか — PASS:** dance、脚交差、kick、膝の内外、crouch、片脚重心の意図を残すため。
5. **なぜ肩情報が重要か — PASS:** ユーザー環境で腕動作を明確に改善し、独立slotがなくてもChest/Upper Arm solverへ使えるため。
6. **手のめり込み対象範囲 — PASS:** 初期版は通常のQuest controller経路を維持し、極端な胸形状等のmesh surface差による衝突補正は対象外。
7. **初期体型parameter — PASS:** Leg Length、Thigh/Calf Balance、Hip Width、Arm Length、UpperArm/Forearm Balance、Shoulder Width。
8. **Native/Retarget切替 — PASS:** ON前状態を記録し、ONで競合するnative body tracker出力だけ停止してOSC 8点へ切替、OFFでOSC停止後に正確な元状態へ復元。
9. **勝手に触らない設定 — PASS:** 肩/センサー割当、AI Engine、6軸/磁気、Ground IK、Skeleton、純正calibration、その他調整済み項目。
10. **Quest案の位置付け — PASS:** ReboCapを主役にしたままの独立・非blocking・低周波Yaw基準研究。MONITOR先行。
11. **本体実装状況 — PASS:** 本体実装はゼロ。文書foundationのみ。
12. **次回第一タスク — PASS:** 公式手段から始めるread-only ReboCap integration discoveryと、最小interface contractの記録。

## 12. 未解決事項

- ReboCapのinstalled version、公式SDK/API、license、redistribution条件。
- skeleton schema、座標系、単位、handedness、timestamp、接続life cycle。
- SteamVR body tracker出力だけを安全にquery/toggleする方法。
- 現行VRChat OSC trackerの正確な仕様と実acceptance手順。
- programming language、runtime、GUI、package、support対象Windows。
- technical MVPとuser-facing v1の境界、特にauto-start/window attachmentの時期。
- crash時に元状態を捏造せず復元する方法。
- Quest胸Yaw signalの取得可否、品質、drift有用性。
- ReboCap SDK・依存libraryと矛盾しないproject license。

## 13. 次のCodexセッションへの推奨第一タスク

アプリ実装の前に、ReboCap integrationを読み取り中心で調査する。installed versionと公式SDK/API/licenseを確認し、skeleton input contractとnative SteamVR body-outputのquery/toggle可能性を、公式SDK/API → 設定 → local IPC/APIの順に調べ、証拠と未解決事項を `RESEARCH_LOG.md` に残す。ライブVR sessionを妨げる操作は行わない。

## 14. git status

```text
## No commits yet on master
?? AGENTS.md
?? README.md
?? docs/
```

すべて今回作成した未追跡documentで、既存project fileの変更はない。

## 15. commit状態

commitは行っていない。ユーザーからcommit指示がなく、初回foundationをChatGPT/ユーザーが確認できる未commit状態で残すため。

## 16. GitHub公開状態

Git remoteは設定されておらず、GitHubへはまだ公開していない。既存repoの使用、新規remote repo作成、push、deployはいずれも行っていない。

## 17. アプリ本体実装を始めていないことの確認

今回追加したのはMarkdown文書9件だけである。ReboCap SDK接続、OSC送信、retarget数学、GUI、Watcher、SteamVR制御、Quest yaw処理、test/build/packageを含むアプリ本体実装には着手していない。

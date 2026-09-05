# ReboRetarget 現状詳細報告書

これは性能調査開始前の固定スナップショットです。新wrapperの現在の検証状態と性能改善結果は [PERFORMANCE_INVESTIGATION_REPORT.md](PERFORMANCE_INVESTIGATION_REPORT.md) を参照してください。以下の過去試行の事実は書き換えていません。

作成日：2026-09-05

対象：Phase 2E完了後から、Phase 2F-Aの2回の未完了試行、オフライン修正の中断時点まで
総合判定：**Phase 2Eは過去の実測でPASS。Phase 2F-AはPARTIALで、身体動作と座標・関節の対応は未確定。新しい対策コードは未検証。**

## 1. 最も重要な結論

ReboCapから値を受け取り、Canonical Pose、Target FK、8個のTracker Transform、メモリ内のOSC表現まで計算する経路は実測できています。一方で、今回の目的である「現実に右へ動いたとき、どの軸・符号・関節が変化するか」の確定には至っていません。

ユーザーは指示された動作を実施しました。2回とも必要な比較データが揃わなかった原因は、身体動作の誤りではなく、Codex側が時間制約のある計測手順を適切に進行できなかったことです。

さらに、今回の2回の計測では処理時間p99が宣言済みの10 ms基準を超過しました。入力の不正やSDK異常終了は検出されていませんが、性能基準の不合格を成功扱いにはしていません。

現在、ユーザーはトラッキング機器を外して食事へ行ってよい状態です。追加Live接続や身体動作の要求は行いません。報告書作成のため、修正担当には原子的なファイル追加を終えたところで作業を止めてもらいました。

## 2. プロジェクト全体の到達点

| 領域 | 到達点 | まだ証明していないこと |
|---|---|---|
| Phase 0 / 0.5 | 目的・制約・canonical docs・公開基盤を整備 | 完成した製品の配布ではない |
| Phase 1 / 1.5 | 公式境界を調査し、限定的なLive観測を実施 | 過去のVRChat crashと追加SDK clientの因果は未確定 |
| Phase 2A / 2B | Target Skeleton FK、階層・合成Sequenceをオフライン検証 | 実Avatarの品質や実人体の軸対応 |
| Phase 2C | SDK-shaped delta → Canonical → Target → 8 semantic anchors | 肩の物理Tracker情報がどのSDK jointへ独立に現れるか |
| Phase 2D | roleとslotを分離し、VRChat表現・Quaternion/Euler変換・16 message encode/decodeをメモリ内で検証 | 実VRChatへの送信・受信・FBT結果 |
| Phase 2E | 1 clientのLive入力、24 joint検証、latest Pose、メモリ内pipeline、正常終了を実測PASS | active VRとの共存、multi-client、製品60 Hz、物理的な追従遅延 |
| Phase 2F-A | 計測・解析コードを追加し、右移動を2回試行 | 必要な比較窓が未完了。座標・膝・上半身・肩の意味は未確定 |

**製品アプリ、GUI、UDP/OSC sender、VRChatへの実出力、IK、Foot Lock、Native/Retarget切替、Quest Chest Yaw補正は未実装・未実行です。**

## 3. Phase 2Eの確定済み実測との比較

以下は既存のPhase 2E報告と今回の集約結果を比較したものです。p99等は既存の固定幅ヒストグラムに基づく近似値です。

| 指標 | Phase 2E成功時 | Phase 2F-A 第1回 | Phase 2F-A 第2回 |
|---|---:|---:|---:|
| 方法 | 20秒の受信安全検証 | チャット返信をmarkerにする | 音声案内を外部ツールから順に実行 |
| 受信callback数 | 1200 | 2700 | 3295 |
| 受理・Delta・Canonical・Latest | 1200 | 2699 | 3295 |
| 受信span平均Hz | 60.557342 | 60.180417 | 60.150203 |
| Target/8 anchors/16 messagesの完成セット | 429 | 940 | 1129 |
| 上書き済み旧sequenceのskip | 771 | 1759 | 2166 |
| メモリ内decode message数 | 6864 | 15040 | 18064 |
| 受信間隔 p50/p95/p99（ms） | 16.5 / 18.0 / 18.5 | 16.5 / 21.0 / 24.5 | 16.5 / 22.0 / 26.5 |
| pure pipeline p50/p95/p99（ms） | 1.6 / 2.7 / 3.25 | 5.3 / 9.4 / 11.75 | 7.4 / 11.0 / 20.05 |
| 受信→decode p50/p95/p99（ms） | 10.0 / 17.5 / 18.5 | 14.5 / 22.5 / 26.0 | 16.0 / 24.5 / 33.5 |
| 子プロセス強制終了 | なし | なし | なし |
| pure pipeline p99 < 10 ms | PASS | FAIL | FAIL |

第1回の1 callback差は終了中に到着した遅いcallbackの拒否です。不正Poseや時刻順序違反とは区別しています。第2回は3295件すべてを受理し、不正入力・時刻逆行・SDK abortは0でした。

この表の「受信→decode」はソフトウェア内部の区間です。身体が動いてからAvatarが動くまでの遅延ではありません。Phase 2Eの約21.4 Hz consumer実測も、製品60 Hz達成を示すものではありません。

## 4. 2回の失敗を分けた記録

### 第1回：チャット返信の期限切れ

ユーザーの準備確認後、静止姿勢を取得しました。必要窓は静止60件・動作後20件・復帰後20件です。

- 静止60件は取得できた。
- move markerは経過25.088477秒で受理された。
- ユーザーは右移動後に返答したが、hold commandが子プロセスへ届く前に20秒の待機期限が切れた。
- 経過45.131762秒で `INCOMPLETE / MARKER_TIMEOUT`。
- 最終窓は **60 / 0 / 0**。座標差の判定に必要な動作後データがない。
- `result_ready`と正常な子プロセス終了が確認され、強制終了は行っていない。
- 親の全体時間や個別SDK lifecycle counterの一部は保持したコンソール抜粋にないため、別の時刻から推定して埋めていない。

### 第2回：音声へ替えてもツール往復が残った

ユーザーの明示許可を受け、途中の返信を不要にして日本語音声で案内しました。しかし音声再生や次のcommandを、その都度Codexのツール呼び出しで進めました。

| 子側の経過時刻 | 起きたこと |
|---|---|
| 9.669693秒 | baseline開始 |
| 12.524453秒 | 静止60件完成、移動可能状態 |
| 26.069337秒 | move command受理 |
| 39.857780秒 | hold command受理 |
| 40.807652秒 | 動作後20件完成、復帰可能状態 |
| 50.807901秒 | return command受理 |
| 55.081595秒 | 観測終了。復帰後窓は未取得 |

最終窓は **60 / 20 / 0**。親の全体時間は **56.167260秒**で60秒以内、子exit codeは0、SDK open/closeは各1回成功、強制終了なしでした。

ユーザーは終了後に「できた」と返答し、指示された動作を実施したことは確認できました。ただし、後からの確認で失われた復帰後データを作ることはできません。2回目も `cue_result` は生成されていません。

### 繰り返したミスの責任と原因

1. 最初の失敗で、チャット・モデル・ツール往復を時間制約のある計測へ組み込む問題が明らかになった。
2. それにもかかわらず、2回目では返信だけを音声へ替え、同じ往復依存を残した。
3. 手動で合成データの60/20/20が通ったことを、実際の音声案内を含む手順全体の証明として扱ってしまった。

**これはCodex側の進行設計と事前検証の不足です。ユーザーの反応速度、Calibration、ReboCapの動作を原因と断定する根拠はありません。**

## 5. 今回わかったこと／わからないこと

### わかったこと

- 実際のSDK入力は両試行とも約60 Hzで流れている。
- 受理した24-joint入力はDelta Adapter、Canonical、Latestへ進んでいる。
- 遅いconsumerは旧Poseを順番に再生せず、上書きされたsequenceをskipしている。
- Target/8 anchors/16 messages/decodeまでメモリ内で処理できる。
- 計測の期限・終了機構は両試行で働き、計測プロセスは残らなかった。
- ユーザーは2回目の動作を実施したと確認している。

### まだわからないこと

| 確認対象 | 現状 |
|---|---|
| Physical Right / Left | UNVERIFIED。完全な比較窓がない |
| Forward / Back、Up / Down | 未試行 |
| Yaw Left / Rightの符号 | 未試行 |
| 左右Kneeの識別・曲げ応答 | 未試行 |
| Collar / Shoulder / Elbowの左右chain | 未試行 |
| 物理Shoulder Tracker情報の経路 | E：判定に必要なデータ不足 |
| Ankle/Foot、Wrist/Handの継承 | controlled motionによる比較未実施 |
| SDK→Canonicalで実動作の意味を保持するか | オフライン数学検証はあるが、今回の実動作照合は未完了 |
| Target/anchorsで実動作の左右・方向を保持するか | 数値経路は通るが、実動作照合は未完了 |

## 6. 性能問題の現状

10 ms基準に対しp99が11.75 ms、20.05 msとなった事実は未解決です。合図の進行失敗とは別の問題として扱います。

静的なコード比較では、次を確認しています。

- `pure_pipeline`の終了時刻はmotion observer呼び出し前に確定する。
- 全文のcue解析は復帰後20件が揃った場合だけ実行され、今回の両試行では実行されていない。
- adapterの計測も、追加したdelta/Canonical保持オブジェクト生成より前に終了する。
- FK、anchors、OSC本体は直前HEADから変更されていない。

したがって「追加した全文解析時間がpure pipelineへ直接加算された」とは説明できません。OS scheduling、GIL競合、GC、同時処理等による経過時間の増加は候補ですが、原因は未確定です。SpeechやPowerShellが原因だと断定する証拠もありません。

対策として性能基準を緩めたり、大規模なruntime再設計をしたりしていません。SDKを使わない同一合成Poseでのobserver有無比較等は次の小さな診断候補であり、まだ実施していません。

## 7. 実装とテストの区別

### 関連テストを通した範囲

- `research/controlled_motion_analysis.py`：Quaternion相対回転、axis-angle、global/local差、左右比較、ノイズ閾値、復帰判定、6組の末端比較、8 anchors集約、strict sanitizer。
- `research/controlled_motion_session.py`：固定marker、60/20/20のRAM窓、marker前sample除外、待機期限、終了時clear。
- `research/live_retarget_safety_probe.py`：同じcallback由来のdelta/Canonicalをcapacity-oneで保持するopt-in observer。
- `research/supervised_retarget_probe.py`：既存SDK lifecycle/watchdogの再利用、固定command IPC、状態通知、正常終了と判定の分離。

独立レビューで「反対側関節自身のノイズ閾値未満でもFAILになる」欠陥を発見しました。反対側にも自身の検出閾値・保持安定性・復帰条件を適用し、回帰テストを追加済みです。

この範囲の最終関連テストは **Python 3.10で58/58 PASS、77.264秒**。これは変更箇所周辺の検証です。今回拡張後の全suiteや全Python版が通ったという意味ではありません。

旧synthetic supervisor fixtureの時間余裕を3.5秒から8秒へ変更し、burst件数を決定的にしました。実機の20/45/55/60秒制約や10 ms性能基準は変更していません。

### 追加しただけで、まだ検証していない対策

`research/countdown_motion_cue.py`を追加しました。PC内で状態を確認しながら音声とcommandを進め、チャット・モデル・ツール往復を計測の途中から除くための研究用wrapperです。

現時点のコードには、既存supervisor再利用、音声用の非表示ローカル子プロセス、音声timeout、取得前の待ち時間、予定markerとユーザー確認待ちの区別が含まれます。

**これはsourceだけの状態です。構文確認・動作テストは未実施です。対応する `tests/test_countdown_motion_cue.py` も未作成です。**

静的Scope確認では明らかな範囲拡大は見つかっていませんが、完成物のレビュー・タイミング・異常時cleanup・残存子プロセス0は未検証です。以前の58テストを、この新wrapperの合格根拠として流用しません。新wrapperから実音声やSDKを実行した事実もありません。

## 8. 再発防止の受入条件

次の身体動作をお願いする前に、実際に使うwrapperと同じ経路を、合成SDK・無音の代替speechで検証します。

1. 通常ケースで60/20/20を完成させ、SDK closeと子プロセス終了まで確認する。
2. 全体時間に起動・音声・解析・終了処理を含め、承認済みの上限以内で終わる。
3. 音声遅延・起動失敗・停止しない音声・中断では、安全にnon-PASS終了する。
4. 計測と音声の管理対象子プロセスが残らない。
5. 予定した取得境界を「ユーザーが返答した時刻」と誤記しない。
6. 合成試験の成功を、実際に音声が聞こえることや身体動作の成功と混同しない。
7. 独立レビューで証拠と判定を確認する。

期限延長、10 ms基準緩和、第三の右移動試行を、修正作業の名目で勝手に行いません。「今後一切ミスがない」とは保証せず、今回の原因に対する具体的な検証を再開条件にします。

## 9. 安全・プライバシー・実環境

| 項目 | このPhase 2F-Aでの実績 |
|---|---|
| Live SDK session | 明示許可された2回。並列・自動reconnectなし |
| Raw full-body Pose／時系列のファイル保存 | 0。RAM窓は終了時に破棄 |
| ReboCap設定・Calibration操作 | Codexによる変更0。Calibrationはユーザーが実施 |
| OSC/UDP出力 | 0。公式SDKの入力用通信は行っている |
| VRChat/SteamVR起動・操作 | 0 |
| Virtual Desktop操作 | 0。ユーザー方針に従って触れていない |
| 音声出力 | 第2回の外部案内でWindows日本語音声を使用。音量・経路設定変更なし |
| computer-use／GUI／UI Automation | 使用0 |
| ReboCap維持 | 第2回直後のread-only確認で保護対象の元のprocessが生存 |
| 計測プロセス残存 | 同じ終了直後の確認で0 |

環境の記述は**最後の計測直後の確認時点**のものです。食事中の現在状態を勝手に操作・再検査して得た値ではありません。装置を外す・食事へ行くことは今回の終了済み計測を妨げません。

初期Phase 2F sourceのprivacy/provenanceレビューはACCEPTです。新wrapperは別の未検証範囲です。今回、新たなvendor source・SDK binary・個人識別情報を公開した事実はありません。SDK再配布許諾や過去crashの因果などの既存未解決事項は、この報告で解消したとは扱いません。

## 10. Gitと公開状態

- branch：`main`。
- HEAD：`edf603dd2c737800bcb45af9444bf39b3d5a0c4f`。
- 今回のPhase 2F変更：**未commit・未push**。
- 新wrapper：未trackedのsource。テストは未作成。
- 新規deploy・製品release・SDK公開：なし。
- 履歴書換え・破壊的Git操作：なし。
- 報告書作成後の `git diff --check`：成功。これが成功しても、動作検証や実身体の受入完了にはならない。

報告作成開始時に変更されていた既存ファイル：

```text
docs/CONTROLLED_MOTION_VALIDATION_PROTOCOL.md
docs/CURRENT_STATE.md
docs/DECISIONS.md
docs/RESEARCH_LOG.md
research/live_retarget_safety_probe.py
research/supervised_retarget_probe.py
tests/test_supervised_retarget_probe.py
```

新規未trackedファイル（本報告を含む）：

```text
docs/PHASE_2F_A_REPORT.md
docs/STATUS_REPORT_2026-09-05.md
research/controlled_motion_analysis.py
research/controlled_motion_session.py
research/countdown_motion_cue.py
tests/test_controlled_motion_analysis.py
tests/test_controlled_motion_session.py
```

## 11. サブエージェントの担当と現状

| 担当 | 実施内容 | 判定の範囲 |
|---|---|---|
| motion_math | Quaternion・joint・translation集約解析とsynthetic tests | 初期解析の修正は関連58テストに含まれる |
| probe_supervisor | 既存watchdog再利用、marker IPC、計測runtime、対策wrapper | 初期runtimeはテスト済み。新wrapperはsourceだけで停止 |
| probe_recovery | 同一frame・期限・異常終了・数学判定の独立確認、性能の静的診断 | 性能低下の原因は未確定 |
| motion_scope | 不要実装・範囲の独立レビュー | 初期実装はACCEPT。新wrapper完成判定は保留 |
| lifecycle_evidence | 公開可能性・privacy・provenanceの読取レビュー | 初期変更はACCEPT。新wrapperの完成確認ではない |

主担当Codexが合図の進行とLive試行を統合しました。2回の進行失敗は統合・事前検証の責任であり、レビューやサブエージェントへ責任を転嫁しません。

## 12. 次の作業とユーザーに必要なこと

次の工程は、**新しいローカルwrapperのオフライン検証**です。まだ実機テストへ戻る段階ではありません。必要な証拠が揃った後に、結果と残存事項を報告します。

ユーザーが今する必要がある操作はありません。機器を外して食事へ行って問題ありません。再装着・通常Calibration・姿勢の準備が必要になるのは、オフライン修正の確認後に改めて実測を再開するときです。

### 参照したリポジトリ資料

- [Phase 2Eの実測・回復報告](PHASE_2E_RECOVERY_REPORT.md)
- [Phase 2F-Aの試行記録](PHASE_2F_A_REPORT.md)
- [現在地点](CURRENT_STATE.md)
- [controlled motion protocol](CONTROLLED_MOTION_VALIDATION_PROTOCOL.md)
- [決定事項](DECISIONS.md)

本報告はリポジトリと今回の実測集約・実行記録を根拠にした現状整理です。新たなLive調査や外部公開を行うものではありません。

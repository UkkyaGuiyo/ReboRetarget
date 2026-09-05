# Performance investigation and Phase 2F-A recovery

Status: **OFFLINE GATES PASS; LIVE WAITING_FOR_USER**.
Start: 2026-09-05, HEAD `edf603dd2c737800bcb45af9444bf39b3d5a0c4f`.
This is not a new Live trial or a product release.

## 1. Executive Summary

同一合成fixture・Python 3.10.11・各3回×500frame・warmup50で、Observerなしの研究経路はpure p99 **3.5055 → 1.4271 ms**、callbackからconsumerまでの全処理p99 **5.5122 → 1.9146 ms**になった。入力validation、8 anchors、16 messages、毎frameのencode/decodeを維持した比較である。

実スレッドと既存supervisorを使う別の合成測定では、60Hz設定のconsumerは平均 **32.316 → 58.876Hz**。自動cueは3回とも60/20/20件を取得し、終了処理込み **12.06–12.19秒**だった。実SDK、実音声、身体動作、VR操作、OSC/UDP出力は実行していない。

**過去Liveの20.05msを、特定の変更が起こしたと断定はできない。** 通常条件では旧コードでも再現せず、人工的なPythonスレッド競合では約18msを再現した。最適化の成功と、過去事象の因果確定は別である。

## 2. Root Cause

| 判定 | 発見と根拠 |
|---|---|
| CONFIRMED | 旧consumerは処理後に丸ごと待つ。30Hz設定で33.3ms要求に対し実待機平均約44ms、実効約21.6Hzを合成環境でも再現。 |
| CONFIRMED | 単にEventで起こし、次回を「今回の遅れた開始＋周期」にすると基準が毎回後退し、改善しない。基準時刻を維持し、遅れた回を飛ばす変更で約58.9Hzまで改善。 |
| CONFIRMED | 旧経路は1frame当たりQuaternion生成1,000回、normalized呼出772回。不変値の再生成と毎callbackのbind FKは計測された実作業だった。 |
| CONFIRMED | 初期heartbeatの空histogramが共有lock中で全binを3回走査。空の早期returnにより、集約平均約1.5msから約0.1msへ改善。 |
| CONFIRMED mechanism, NOT historical attribution | 同じ合成A経路にPython burner threadを1本追加するとpure p99約17.8–17.9ms。GC ON/OFFいずれも発生し、GIL/OS schedulingによるwall-time悪化が可能と示した。 |
| PROBABLE / UNVERIFIED | 過去Live悪化へのスレッド競合、OS scheduling、環境負荷の寄与。過去の同時CPU/GC/lock telemetryがなく、寄与率や発生threadは確定できない。 |
| REJECTED | 過去2回のpure timerにcue全解析が含まれた、FKのアルゴリズム変更が悪化を起こした、まだ実行していなかった新wrapperが原因だった、音声だけで最初の悪化も説明できる、という説明。 |

GCの今回最大pauseは約1.18ms。これだけで過去LiveのGC原因を否定はしないが、10–20msのGC pauseを観測したという主張もしない。

## 3. Phase 2E vs Phase 2F Differential

高速Phase 2E HEADとPhase 2F開始時では、`reboretarget/`のcoreは同一だった。追加pure-timed作業はcoherent handoff値の型確認とCanonical参照の取出し。Observer呼出しと完了解析はpure timer終了後である。

過去の窓は60/0/0、60/20/0で、どちらも100件の完了解析に到達していない。cue失敗とpure性能問題を一括して原因扱いしない。

既存dirty workを保全し、外部のdetached Phase 2E worktreeとPhase 2F開始時コピーで比較した。reset、discard、history rewriteは0。Phase 2E対Phase 2F開始時Aの再比較p99は4.2674 / 3.6992msで、旧変更だけによる持続的20ms悪化は再現しなかった。履歴二分探索の範囲ではcore変更という候補を除外できたが、失われた実環境条件は復元できない。

## 4. Profiling

stdlib cProfile・stage wall clock・GC callbacksをprimary測定とは別に使った。診断のinclusive値は重複するため加算しない。

| 100frameのcall-count | 最適化前 | 最終 |
|---|---:|---:|
| Quaternion生成 | 100,000 | 25,400 |
| normalized | 77,200 | 65,600 |
| source bind計算（動的対照／prepared） | 100 | 0 |
| FK（bind＋Target／Targetのみ） | 200 | 100 |

通常frameで残る最大stageはTarget FK。計測用wrapper込みのA平均はTarget FK約0.891ms、adapter約0.170ms、delta生成約0.152ms、OSC representation約0.141ms。これらはprimary値でも排他的CPU時間でもない。

`perf_counter_ns()`をbenchmark境界に用い、実probeの高精度clockと既存pure timerは変更しなかった。ns表記は基礎clock自体を高精度化しない。今回QPCの公称resolutionは100ns、process CPUの実測値は15.625ms刻みが目立ち、frame CPU p99を精密な値として使えない。[Python time](https://docs.python.org/3.10/library/time.html)、[profile](https://docs.python.org/3.10/library/profile.html)。

## 5. Allocations / GC

厳密にmagnitude==1のfrozen Quaternionだけを再利用し、近似的なunit判定は入れていない。非unit、NaN/Inf、near-zero、q/-qの検証を維持した。巨大な有限成分の二乗和overflowがゼロQuaternionを生む問題は、overflow時だけのscaled normalizationで修正した。これは別の正確性修正である。

生成数74.6%減は上のconstructor call-countから確認した。float、tuple、dict、bytesなど全種類の累積allocation bytesを測定したという意味ではない。参照カウントで解放される一時objectも多く、GC停止だけではその生成費用は消えない。

GC診断各300frameではA 5回、最大0.903ms・合計1.0632ms、F 46回、最大1.1836ms・合計5.564ms。旧AのGC ON/OFF pure p99は4.2336 / 4.2404ms。runtimeのGCは無効化していない。[Python GC](https://docs.python.org/3.10/library/gc.html)。

tracemalloc診断は各条件100frame×3回、warmup20。A peak bytesは変更前208,606 / 92,358 / 92,897、最終208,362 / 91,622 / 92,169でほぼ不変。F peakは変更前1,470,269 / 1,425,657 / 1,418,199、最終1,224,400 / 1,178,035 / 1,171,434で約17%減。F最終retained bytesは177,594 / 126,057 / 109,598。各回100pipeline・1,600decode、F解析1回を維持した。

測定範囲は反復・episode setup・最終window・計測listで、初期fixture/probe作成・warmupは除く。retained/peakは累積churnでもOS全体のmemoryでもない。このinstrumentation下の時間を性能acceptanceに使わない。

## 6. Lock / Thread / GIL

callbackは入力validation、Delta、prepared Canonical、capacity-one publishまで。FK、anchors、OSC、speech、motion analysisはcallbackへ移していない。共有lock内に新しい重いmathやJSONを入れていない。空histogramの無用な走査を除去した。

人工競合診断（各条件300frame、warmup30、既定switch interval 0.005秒維持）：

| Source / GC | 競合なしpure p99 | Python thread競合あり |
|---|---:|---:|
| 変更前 / ON | 2.7908ms | 17.8085ms |
| 変更前 / OFF | 1.7952ms | 17.7878ms |
| 最終 / ON | 1.1193ms | 17.8615ms |
| 最終 / OFF | 1.6030ms | 17.9119ms |

この単回診断を改善率・通常acceptance・過去Liveの原因確定に使わない。競合threadはcancel/joinで終了、global switch intervalやOS timer設定は変更0。[Python threading](https://docs.python.org/3.10/library/threading.html)。

## 7. Consumer Cadence

各mode・frequencyにつき3回×5秒。入力はdeadline型の合成60Hz producer、受信値は実測。source timestampのsequence/60を実測Hzへ流用していない。

| G2: 通常IPC | 旧実効Hz | 最終実効Hz |
|---|---:|---:|
| consumer設定30 | 21.635 | 30.143 |
| consumer設定60 | 32.316 | 58.876 |

Hzは処理件数/観測時間。有限window端の影響がある。configured Hzは新研究loopではtarget cadenceであり、遅延後の最短開始間隔の厳密上限ではない。取り逃したtickで過去Poseをcatch-up処理せず、capacity oneの最新値だけを処理する。

G0（progress集約なし）、G1（集約あり・progress破棄）、G2（通常IPC）は同じsupervisorと最終result経路を使う。旧G0/G1/G2のHzがほぼ同じだったため、IPCを主因とはしなかった。最終G2のprogress JSON/Pipe費用は平均約0.24–0.25msとして残る。

60Hz設定のsoftware receive→decode p99は3回で16.0 / 2.5 / 3.0ms（histogram下端）。平均7.17msをpooled p99とは呼ばない。センサー以前、ReboCap内部、network、Avatar表示遅延は未測定。

## 8. Wrapper

既存Parent Supervisor / Child Probeを再利用し、baseline → move → hold → return → neutralをローカルで進める。ユーザー／chat／tool応答を時間制約区間に入れない。

最終H 3回すべて60/20/20、終了処理込み12.1884 / 12.0642 / 12.1474秒、child正常終了、強制終了0。Hはsilent poll speech job。別のintegration testsでは実際に所有する無音Python subprocessを用い、終了まで検証した。

marker_sourceはSCHEDULED_COUNTDOWN、user_confirmationはPENDING、speech_audibilityはUNVERIFIEDを保持する。合成fixtureの完走を現実の右移動や可聴性のPASSへ昇格しない。

## 9. Fault Injection

同じwrapperの試験対象は正常60/20/20、slow speech、speech期限超過、voice不在、launch failure、never-exiting speech、SDK open hang、SDK close hang、user stop、no callback、late/stale input、burst input。

停止対象はその試験が所有するchildのみ。入力0は、open/close成功・正常child exit・不正packetなし・forced cleanupなしの場合に限りUNVERIFIED。USER_STOPやSDK異常まで上書きしない。もとのnumerical_statusも残す。

各integration testで、cleanup込み60秒以内・child exit・所有speech processの終了をassertする。SDK hangは既存parent watchdog、speech childは12秒期限で扱う。OSのprocess creation自体や任意の外部status callbackの無期限停止まで保証するhard real-time設計ではない。

## 10. Performance Before

| 歴史的Live | pure p50 / p95 / p99 ms | 完了pipeline数 |
|---|---|---:|
| Phase 2E | 1.6 / 2.7 / 3.25 | 429 |
| Phase 2F-1 | 5.3 / 9.4 / 11.75 | 940 |
| Phase 2F-2 | 7.4 / 11.0 / 20.05 | 1129 |

別の日程・duration・Pose・環境であり、新合成値との直接的なLive改善率は算出しない。旧probe histogramはbucket下端、新primaryはexact nearest-rankである。

同条件の変更前A（N1500）はpure p50 1.8876 / p95 3.1445 / p99 3.5055 / max 4.6472ms、全処理p50 3.0832 / p95 4.9846 / p99 5.5122 / max 7.4105ms。

## 11. Performance After

各N1500、3×500、warmup50、Python 3.10.11、同一noncommuting bind/delta fixture。CPU負荷を伴う他テストと同時実行していない。

| Variant | pure p50 | p95 | p99 | max | 全処理p99 |
|---|---:|---:|---:|---:|---:|
| A observerなし | 0.7630 | 1.1137 | 1.4271 | 1.8556 | 1.9146 |
| B 作成済み・無効 | 0.7676 | 1.1199 | 1.4863 | 1.7589 | 2.0195 |
| C 有効・収集なし | 0.8134 | 1.2286 | 1.4555 | 1.9843 | 2.0262 |
| D baseline収集 | 0.7912 | 1.2272 | 1.4583 | 1.9634 | 2.0123 |
| E held収集 | 1.3560 | 1.9710 | 2.6146 | 10.6513 | 3.5146 |
| F 60/20/20解析 | 1.0792 | 1.6843 | 2.1086 | 7.6642 | 7.9884 |

単位ms。**全条件p99<10msだが、全frame<10msではない。** Eに単発10.6513msがある。Aのrun別pure p99は1.4668 / 1.0818 / 1.4703ms。

Fの全体には完了解析が100frameに1回だけ現れる。nearest-rank p99がこの最も重い1%を含まない場合があるため、別集計する。完了15件のrepeat別平均142.088 / 124.943 / 118.472ms、最大164.5862ms。supervised Hのconsumer最大も102–174msだった。分析停止時間をpure値の陰に隠さない。

## 12. Improvement / adoption decisions

| Backlog | Impact | Confidence | Cost | Risk | Disposition |
|---|---|---|---|---|---|
| Exact-unit reuse | HIGH | HIGH | LOW | LOW | measured, adopted |
| Immutable bind preparation | MEDIUM | HIGH | LOW | LOW | measured, adopted |
| Consumer cadence | HIGH | HIGH | LOW | MEDIUM | first candidate rejected; phase-grid adopted |
| Empty histogram work | LOW/MEDIUM | HIGH | LOW | LOW | measured, adopted |
| GIL/GC cause separation | HIGH | MEDIUM | LOW | LOW diagnostic | measured, historical cause remains open |
| More Target FK preparation | MEDIUM | MEDIUM | MEDIUM | MEDIUM | deferred; no speculative cache framework |

A同条件比較：pure p99 **59.29%短縮**、全処理p99 **65.27%短縮**、全処理mean **66.59%短縮**。同じ検証を残した結果である。

- 採用：exact-unit immutable reuse、overflow-only安全修正、immutable prepared bind、phase-preserving latest-only cadence、empty histogram early return。
- 同じ最終sourceのdynamic-adapter対照ではcallback平均0.522 / 0.606 / 0.685ms、preparedは0.260 / 0.244 / 0.289ms。順次測定の負荷変動も含むため、時間差全量をbind準備だけへ帰属しない。bind再計算100→0というcall-countは直接証拠。
- 棄却：遅れた現在時刻から次回を作り直す初期Event案（実効Hz改善なし）。
- 不採用：production GC停止、global timer-resolution変更、switch-interval変更、validation削除、閾値緩和、native rewrite、大規模cache/scheduler/metrics framework。
- 保留：Target FKの追加static preparationや微小なOSC prefix reuse。現状の最大課題は実入力の意味・競合時の遅延であり、測定されていない小さな利得のために複雑性を増やさない。

## 13. Production-equivalent Path

独立したsynthetic production-value経路は、入力validation、Delta/Canonical、latest publish/snapshot、FK、8 anchors、16 OSC encodeを維持し、研究用decode/address集合self-check/metrics/observerを除く。各repeatで計測外の完全な研究経路と16 packet bytesが一致することを検証する。

N1500で全処理mean1.2652、p992.6556、max8.0141ms。研究経路より速いとは結論しない。productionのrun別meanは0.9797 / 1.7105 / 1.1054msで、2回目はcallbackとconsumerの双方が遅かった。非同時比較の環境変動を含む。これは製品実装、sender、SDK互換性、cadenceの証明ではない。

## 14. Full Tests

| Python | 全suite | elapsed |
|---|---|---:|
| 3.10 | 216 PASS | 314.962s |
| 3.11 | 216 PASS | 315.541s |
| 3.13 | 216 PASS | 319.987s |

`py -3.10 -m compileall -q reboretarget research tests`も成功。旧HEADの140件から76件増。タイムアウトを実際に待つfake-child試験が主な実行時間であり、通常frameの処理時間ではない。3.13の合格も公式vendor SDK互換性を意味しない。

修正した失敗：初期benchmarkのObserver wrapper取付位置、計測helper自身のreference cycle、旧fake waiterが短いwaitでも2callbackを生成していた点、slotsインスタンスへの誤ったtest patch、Windows CPU計測が必ず正値というtest仮定、no-callbackの分類不足。元のruntime validationや10ms基準を弱めて通してはいない。10msと等しい値も拒否するよう厳密化した。

## 15. Scope Guard / agents

独立Scope Guardは2回とも「不要な実装なし」。これはscope審査であり、未実行テストや数学・Live性能を承認したという意味ではない。最終受入は実際のtestsと計測で判断する。

同時実行枠に合わせ、6サブエージェントを専門役割へ再割当てして11役割を実施：A Profiling、B Phase differential、C Observer、D Cue、E Concurrency、F Allocation/GC、G Math、H IPC、I Statistical validation、J Scope Guard、K Legal/Privacy。計測とCPU負荷試験は直列化し、読取・実装・監査を並列化した。

| Agent | Roles |
|---|---|
| probe_recovery | A profiling/benchmark implementation |
| perf_diff | B historical differential |
| perf_concurrency | C observer, E concurrency, F allocation, G math, I statistics |
| probe_supervisor | D wrapper, H IPC/supervisor |
| performance_scope | J independent Scope Guard |
| performance_provenance | K independent privacy/provenance |

## 16. Legal / Provenance / Safety

独立K監査は初期変更27ファイルに続き、最終staged 32ファイルもACCEPT。集約JSONの追加allocation値を含め、binary・新dependency・秘密情報・実ユーザー絶対pathの混入なし。独自source、stdlib、合成fixturesと集約のみ。SDK source/binary、raw user Pose、token、device identifierの公開は禁止を維持する。過去全履歴を今回改めて監査したという主張ではない。

新dependency・vendor code copy・EULA回避・reverse engineering・SDK配布は0。vendor権利の新規法的判断はしていない。既存のSDK redistribution/commercial-use grantはUNCONFIRMED、project LICENSE未選定のまま。新しいcomponentsの由来をPROVENANCEへ追記した。

この作業でLive SDK接続0、OSC/UDP sends0、Raw user Pose保存0、実音声0、VRChat/SteamVR/Virtual Desktop/Quest/ReboCap操作0、ReboCap設定/Calibration変更0。Git HTTPS公開操作とOSC送信を混同しない。

## 17. Git / reproducibility

開始HEADは冒頭のedf603d。既存dirty workは保全し、次の独立commitに分割した。

- Core最適化：`6f51549954983bc6ceea56e2d07ae170bb42e611`。
- Cue/runtime修正：`e7dc5835f24d3e20d2b04ab68782c17e040f93c7`。
- Benchmark・合成証拠・この報告書：このファイルを追加したcommit（`git log -1 --format=%H -- docs/PERFORMANCE_INVESTIGATION_REPORT.md`で取得）。自己参照hashを推測して埋めない。

最終staged 32ファイルはLegal/Privacy ACCEPT、`git diff --cached --check` PASS。この文書のcommit後にorigin/mainへpushし、remote HEAD一致とclean statusを確認する手順とした。実際の最終hash/push/statusはChatGPTへの完了報告に記録する。Public source公開とapplication deploymentは別で、deploy/releaseは0。

代表コマンド：

```text
py -3.10 research/benchmark_pipeline.py --variants A B C D E F --samples 500 --repeats 3 --warmup 50
py -3.10 research/benchmark_pipeline.py --variants A --path production-value --samples 500 --repeats 3 --warmup 50
py -3.10 research/benchmark_runtime.py --modes G0 G1 G2 --duration 5 --repeats 3 --consumer-rates 30 60
py -3.10 research/benchmark_runtime.py --modes H --repeats 3
py -3.10 -m unittest discover -v
py -3.11 -m unittest discover -v
py -3.13 -m unittest discover -v
git diff --check
```

旧比較には外部に保全したsnapshotを`--implementation-root`で指定し、fresh processを使った。machine-specific pathはここへ記録しない。`PERFORMANCE_RESULTS.json`は選択した合成集約・run別統計・診断で、raw frame列ではない。primary、人工競合、profiling、IPC実験を混ぜてpooled p99を計算しない。

## 18. Phase 2F-A Ready?

**Offline Ready: YES。全3版suite・offline性能・wrapper/fault試験・Scope/Legal/Privacy gateはPASS。LiveはWAITING_FOR_USERで実行していない。** ユーザーの再装着・準備完了と直前Safe Gateなしには開始しない。これはPhase 2F-Aの身体軸検証PASSではない。

今回の強い原因証拠はcadence遅延の再現・修正、重複allocation/bind計算の除去、Python競合によるwall-time悪化の再現。過去Live20.05msそのものの原因確定とは区別する。Phase 2F-Aの身体軸・肩・膝は引き続きPARTIAL/UNVERIFIEDである。

## 19. Remaining Performance Limit

通常経路はTarget FKが最大の残存処理。製品60Hz-classでより重要なのはWindows/GIL scheduling、SDK実スレッドとの競合、consumer最新値へのwake jitterである。人工競合で10msを超える以上、任意の負荷下での10ms保証やhard real-timeは主張しない。

完了時の研究motion analysisは100ms級で、製品毎frameの処理に入れてはいけない。GCを止めたり検証を削ったりしてこの数値を隠さない。

## 20. Next Highest-value Work

offline gates完了後、ユーザーが明示的に準備完了した時だけ、同じ目的の1cueを新wrapperで再評価する。ユーザーが未装着なら装着を急がせず待つ。実SDK下のpure/全処理/受信間隔/終了を集約で比較し、歴史的p99問題が残るかを確認する。OSC/UDP、VR起動、native切替へは進まない。

追加のoffline最適化ならTarget FKのstatic invariantsが候補だが、まずprofileで削れる費用を定量化し、現在の可読性・正確性を維持できる場合だけ採用する。

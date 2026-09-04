# ChatGPTへ渡す報告

記録日: 2026-09-04

この報告では、実測値を「確認済み」、実測からの解釈を「推測」、今回の観測だけでは決められない事項を「未確認」として区別する。観測中にVRChatがクラッシュしたため、「通常プレイを妨害しなかった」という成功条件は満たしたと扱わない。

1. **Inspectorをどう作ったか**

   `research/live_pose_inspector.py` に、公式Python SDKを外部配置から読み込む研究専用Inspectorを作成した。固定長ヒストグラムでcallback間隔、source timestamp、Pose validity、各jointのQuaternion normとフレーム間角度差、Pelvis translation、Spine系のYaw proxyを集計する。Raw Poseは保存せず、出力は集計JSONだけである。製品のRetarget Solverではない。

2. **ReboCapへの接続方法**

   [確認済み] 起動中ReboCapプロセスが所有するWebSocket listen portをread-onlyに特定し、その1ポートへ公式SDKで1回だけ接続した。大量port scanは行っていない。SDKは`UnityCoordinate`、`use_global_rotation=True`で使用した。ReboCap GUI、SteamVR driver、VRChatへ書き込む接続はしていない。

3. **ユーザーの通常VRCプレイを妨害しなかったか**

   [確認済み] 「妨害しなかった」とは結論できない。観測中、最初のVRChatプロセスは`UnityPlayer.dll`内のaccess violation `0xc0000005`でクラッシュした。InspectorまたはCodexがVRChatへ終了命令を送った証拠はなく、実行履歴にもkill操作はない。一方、同時期に公式SDKの追加clientが接続していたため、多重clientがクラッシュに寄与した可能性は今回の証拠だけでは肯定も否定もできない。ユーザーの指摘後、Inspectorは直ちに停止した。

   [確認済み] その後の短い再起動失敗はWatcherの起動競合で説明でき、Watcher修正後の再起動では120秒を超えてVRChatプロセスが安定した。[未確認] その安定確認はReboCap SDK Inspectorを再接続しない状態で行われたため、「Inspector併用時にも安定」は未検証である。

4. **実測session時間**

   [確認済み] ReboCap streamの実測時間は487.658秒（約8分8秒）。VRChatクラッシュ後もReboCap stream自体は継続していたため、この全時間を正常なVRCプレイ時間とは扱わない。

5. **callback総数**

   [確認済み] 29,233 callback。invalid frameは0。

6. **平均Hz / median / p95 / p99**

   [確認済み] 平均59.9436 Hz、median 60.6061 Hz。receive intervalはmedian 16.5 ms、p95 17.8 ms、p99 18.3 ms、最大130.4663 msだった。ここでmedian Hzはmedian intervalの逆数である。

7. **gap / burst / backlog**

   [確認済み] 50 ms以上のreceive gapが15回、100 ms以上が7回、250 ms以上と1秒以上は0回。4 ms未満のburst intervalは64回で、gap後に短間隔callbackが連続するbacklog候補を6回検出した。source interval最大は51.0001 msでreceive interval最大より短く、一部はsource停止ではなくclient側の配送・scheduling遅延後のcatch-upと整合する。[推測] 将来実装はFIFO再生ではなく、受信時点の最新Poseを採用すべきである。今回の指標は候補検出であり、各burstがSDK内部queue由来だとは確定していない。

8. **timestamp解析結果**

   [確認済み] Python wrapperはnative timestampを1000で割ってcallbackへ渡しており、実値はUnix epoch秒と整合した。source deltaは全29,232区間でmonotonic、非単調0回、250 ms以上のjump 0回。source intervalは平均16.6883 ms、median 16.9 ms、p95/p99 18.0 ms、最小8.0001 ms、最大51.0001 msだった。receive clockとの差はmedian 0.3 ms、p95 0.9 ms、p99 1.1 ms、最大173.8474 ms。最大値は接続直後のcatch-upと整合する。processing timestampは独立採取していない。

9. **Quaternion / coordinate解析結果**

   [確認済み] 公式wrapper/exampleに従いQuaternionを`(w,x,y,z)`として扱い、`UnityCoordinate`のglobal rotationを取得した。全24 joint、全sampleで有限値かつ正規化誤差は最大`1e-7`だった。[未確認] 通常プレイだけで既知方向動作との時刻対応を取っていないため、左右・上下・前後およびYaw/Pitch/Rollの符号を実動作から独立確定してはいない。local rotation/hierarchyも今回のlive runでは比較していない。

10. **Pelvis結果**

    [確認済み] translationは3成分とも全frameで有限だった。minは`(-0.282266, 0.549839, -0.172360)` m、maxは`(0.516113, 1.293113, 0.644241)` m、rangeは`(0.798379, 0.743274, 0.816602)` m、最大1-frame移動は0.019721 m。[推測] 数値は連続したroot入力として利用可能そうだが、基準原点や実空間方向との一致は既知Poseなしでは確定できない。

11. **Spine/Chest結果**

    [確認済み] Spine1/2/3は全frameでvalidで、平均角度差は0.1802/0.1787/0.1819度/frame、p95は0.6/0.5/0.5度だった。3 jointのYaw proxyはPelvisと近く推移し、約100度のrangeと約-22度のnet changeがあり、30度超の単frame jumpは0回だった。[推測] 通常の身体旋回を反映する連続入力としては利用可能そうである。

12. **Collar / Shoulder結果**

    [確認済み] Collar平均角度差は左0.2555、右0.2162度/frame、0.25度以上のactive fractionは左34.49%、右29.37%。Shoulderは左0.4035、右0.3829度/frame、active fractionは左46.05%、右43.18%で、Spineより明確に活発だった。ユーザーが肩Trackerを装着していたことは既知条件だが、SDKには装着presence flagがない。[未確認] 肩TrackerなしとのA/Bをしていないため、差分を物理肩Trackerだけに帰属できない。

13. **Elbow / Wrist結果**

    [確認済み] Elbow平均角度差は左0.4125、右0.3829度/frame、active fractionは左45.98%、右43.18%。Wristは左0.2763、右0.2510度/frame、active fractionは左34.37%、右29.60%。Wrist最大角度差は左48.3544度、右54.0394度で外れ値候補がある。R_ShoulderとR_Elbow、各Wristと同側Handの集計値が完全一致したため、これらを独立自由度の証拠として数えない。

14. **Hip / Knee / Ankle / Foot結果**

    [確認済み] 全jointでinvalidは0。平均角度差はHip左0.1665/右0.2219、Knee左0.1639/右0.2314、Ankle左0.1075/右0.2057度/frameだった。通常プレイ中の連続変化は得られたが、Ankleと同側Footの集計が左右とも完全一致した。[推測] Hip/Knee/Ankleは入力候補になる。[未確認] FootをAnkleと独立した回転入力として使えるか、各関節のbend方向がTarget Skeleton FKに正しく対応するかは未確認。

15. **肩Tracker使用中Poseの上半身リターゲット入力適性**

    [推測] Collar/Shoulder/Elbow/Wristは全sampleでvalidかつSpineより高い活動量を示したため、上半身リターゲット入力として十分な情報を持つ可能性が高い。ただし重複集計joint、Wrist外れ値、既知動作との対応、肩TrackerなしA/Bが未解決なので、品質確定ではなく最小FK PoCへ進む根拠とする。

16. **胸Yaw Driftについて観測できたこと**

    [確認済み] Spine1/2/3のYaw proxyに30度超の単frame jumpはなく、Pelvisと近い連続変化だった。[未確認] 約8分の自然動作ではユーザー自身の旋回とsensor baseline driftを分離できず、胸Yaw Driftの量・方向・補正要否は確定できない。今回は補正していない。

17. **disconnect / reconnect結果**

    [未確認] 外因によるReboCap切断と復帰は発生させていない。集計上のdisconnect 1回はInspector停止時のclose処理であり、障害試験ではない。reconnectは0。コードはclose時にPoseを`STALE_OR_INVALID`へ落とし、古いPoseを有効保持しないが、実接続復帰後の古いframe非再生は未検証。

18. **Raw motionの公開repository保存**

    [確認済み] 保存frame数は0。公開対象はコードと集計・解釈だけであり、生の全身motion、端末ID、SteamVR serial、account情報、raw logをrepositoryへ保存していない。集計JSONもrepositoryへ追加していない。

19. **設定変更の有無**

    [確認済み] Inspector観測ではReboCap、SteamVR、Virtual Desktop、VRChatの設定を変更していない。OSC送信、仮想Tracker生成、calibration、Retarget処理、driver追加、port scanもしていない。クラッシュ復旧のWatcher修正とVRChat再起動は、後続の明示依頼による別作業であり、Phase 1.5のread-only観測操作とは区別する。

20. **一時コードを残したか**

    [確認済み] `research/live_pose_inspector.py`として隔離して残した。公式SDK本体はrepositoryへ同梱しておらず、外部SDK pathと確認済みportを明示指定しなければ実行できない。常駐daemonではない。

21. **GitHubへcommitしたもの**

    この報告を含むcommitでは、Phase 1.5の研究用Inspector、本集計報告、`CURRENT_STATE`、`RESEARCH_LOG`の4ファイルだけを対象とする。Raw Pose、集計JSON、公式SDK、raw logは含めない。commit/pushの実行結果は最終応答で提示する。

22. **commit hash**

    commit自身へそのhashを自己記載できないため、本書には固定しない。公開済みhashは最終応答で提示する。

23. **git status**

    commit/push後にworking treeと`origin/main`一致を再確認し、その最終結果を最終応答で提示する。

24. **次フェーズGo / No-Go**

    **条件付きGO:** official SDK入力だけを使う、pureなTarget Skeleton FK transform PoC。

    **NO-GO:** OSC送信、Two Bone IK、Native/Retarget自動切替、Watcher統合、SteamVR出力操作、製品GUI、胸Yaw補正。VRChatクラッシュとの因果が未解決なので、live多重client接続を当然に安全とは扱わない。

25. **次に作る最小Target Skeleton transform PoC案**

    保存済みraw motionを前提にせず、synthetic fixtureと短い明示許可済み入力だけで、`24 global rotations + Pelvis translation -> 固定Target Skeletonのbone world transform`を計算するpure/offline moduleを作る。入力adapter、FK変換、出力snapshotを分離するのはテスト可能な最小範囲に限る。最初の受入条件は、(a) T-poseでTarget rest poseを再現、(b) Pelvis/Spine/Collar/Shoulder/Elbow/Hip/Knee/Ankleの既知回転が期待方向へ伝播、(c) 左右・長さ・親子関係のfixture test、(d) OSC・SteamVR・ReboCap設定へ一切書き込まない、である。実live接続はクラッシュ因果を切り分ける別の安全確認後に限る。

## 総括

Phase 1.5は、ReboCapが24 jointのvalidなglobal QuaternionとPelvis translationをほぼ60 Hzで供給すること、timestampがUnix秒かつmonotonicであること、肩を含む上半身jointと下半身jointに連続した活動があることを確認した。一方、callbackのgap/burst、複数jointの同一統計、胸Yaw drift、disconnect/reconnect、実動作と軸の対応、VRChatクラッシュと追加SDK clientの因果は未解決である。よって次は出力系を作らず、pure/offlineなTarget Skeleton FK transformだけへ条件付きで進む。

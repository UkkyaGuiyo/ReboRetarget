# ChatGPTへ渡す報告

記録日: 2026-09-05

この報告は、明示許可されたPhase 2E single-client receive-only検証1回の結果をまとめる。`CONFIRMED`は今回直接観測した事実、`OFFLINE`はsynthetic testだけの証拠、`UNVERIFIED`は今回のLive入力が不足して判定できない事項を表す。Raw Pose、集計JSON、SDK path、client identifier、endpoint logはrepositoryへ保存していない。

1. **Safe Point判定**

   `CONFIRMED`。接続直前にReboCap本体1プロセスとその正規子プロセス、確認済みlistenerをread-onlyで確認した。VRChat、SteamVR、Meta/OculusおよびVirtual Desktop headset processは0。Virtual Desktop Service/Streamerの既存background 2プロセスは変更しなかった。Action Calibration完了とactive headset/sessionなしはユーザー確認を前提とした。

2. **Live実行の有無**

   `CONFIRMED: EXECUTED ONCE`。外部watchdogを起動する最初の2コマンドはhost policyによりprocess生成前に拒否され、SDK接続には数えない。その後、1つのprobe processからSDK clientを1回だけ構築・open・closeした。retryとreconnectは0。

3. **接続方式**

   ユーザー所有のrepository外公式Python SDKを使い、`UnityCoordinate`、global rotationで、起動済みReboCap GUIの確認済みlocal WebSocket listenerへ接続した。SDK open resultはsuccessだった。これは許可された入力transportであり、OSC output transportではない。

4. **session秒数**

   `CONFIRMED: 20.015 seconds`。事前固定値20秒、許可上限60秒以内。close成功。

5. **callback数**

   `CONFIRMED: 0`。SDK接続は成功したがPose callbackは届かなかった。

6. **average Hz**

   `UNVERIFIED`。accepted callbackが0のため計算不能。

7. **interval p50/p95/p99/max**

   `UNVERIFIED`。receive/source interval sampleは0。

8. **gap/burst**

   `UNVERIFIED`。50/100/250 ms gap、4 ms未満burst、gap-followed burst candidateを数える実装はあるが、今回のinterval sampleは0。backlogのLive発生有無も判定不能。

9. **invalid frame**

   観測counterは0だが、母数も0。したがって「validだった」ではなく`UNVERIFIED / NO FRAME`。

10. **timestamp結果**

    `UNVERIFIED / NO FRAME`。receive/source regression counterは0だが、Live timestampは受信していない。

11. **Delta Pose生成成功率**

    `UNVERIFIED: 0/0`。`ReboCapDeltaPose`生成数0。

12. **Canonical Pose生成成功率**

    `UNVERIFIED: 0/0`。`adapt_rebocap_delta_pose()`成功数0。

13. **latest-pose publish/snapshot/overwrite**

    `CONFIRMED counts: publish 0, latest sequence 0, snapshot 429, slot replacement 0, unseen replacement 0, sequence-gap drop 0`。snapshotはEMPTY stateのpollであり、Live latest-only handoffの成功証拠ではない。capacity-one replacementと60-to-30 latest-only動作は`OFFLINE` synthetic testsで確認済み。

14. **stale状態**

    終了時のcontrolled `STALE`、続く`DISCONNECTED`への遷移とsample不在は確認した。ただしLive sampleが一度も存在しなかったため、Live valueのclear proofではない。値ありのstale clearは`OFFLINE` testのみ。

15. **disconnect発生有無**

    自然なdisconnectは`NOT TRIGGERED / NOT OBSERVED`。故意の切断は行っていない。abnormal-close invalidationは`OFFLINE` synthetic testのみ。

16. **processing p50/p95/p99**

    `UNVERIFIED / NO PIPELINE SAMPLE`。validation、adapter、Target FK、anchors、OSC representation、codec、total pure pipelineはすべてsample 0で、10 ms p99 budgetを判定できない。

17. **ReboCap process安定性**

    `CONFIRMED`。probe内の開始・観測中・終了前guardとclose後postflightで同じReboCap PID/pathが生存し、正規子プロセス、listener、既存内部接続も残った。ReboCap crashと自動再起動は0。

18. **ReboCap設定変更0**

    `CONFIRMED BY OPERATION BOUNDARY`。設定、Calibration、VR Output、Native/Retarget、UI、fileを読む／書く経路はprobeにない。Codexもそれらを操作していない。

19. **VRChat/SteamVR/VD/Quest操作0**

    `CONFIRMED`。接続前、観測中のread-only snapshot、接続後で禁止VR processは0。Virtual Desktop background 2プロセスはそのまま。起動、終了、foreground、UI、設定、Quest操作は0。

20. **OSC/UDP/network send 0**

    `CONFIRMED FOR REBORETARGET OUTPUT`。OSC/UDP/direct socket senderは存在せず、output sendは0。memory上のOSC encode/decodeにも今回はLive valueが到達しなかった。公式SDK input接続そのものはWebSocket handshake/controlを行うため、この許可済みlocal input transportまで「通信0」とは表現しない。

21. **Raw Pose保存0**

    `CONFIRMED`。callback自体0で、Raw Pose frame、time series、OSC bytesのdisk保存は0。SDK自身のtransport diagnosticsは一時terminalへ出たがrepositoryへ保存していない。将来runではvendor stdoutもtransient filter対象とする。

22. **SDK/Vendor file commit 0**

    `CONFIRMED`。公式SDK、vendor sample/source、DLL、binary、archiveはcopy・edit・stage・commitしていない。新規sourceは公開interfaceを呼ぶ独自research wrapperとsynthetic testsだけ。

23. **tests**

    新規15 testはPython 3.10/3.11/3.13でPASS。fake SDKでexact-once lifecycle、no retry、24×Quaternion/root/timestamp validation、capacity-one latest-only、8 tracker/16 memory message、stale/disconnect、duration、privacy、no transport/file-writeを確認した。combined suiteの最終結果はcommit前gateと最終応答へ記す。

24. **commit hash**

    このreportを含むcommit自身のhashは自己記載せず、最終応答へ記す。

25. **push状態**

    最終publication scan後の結果を最終応答へ記す。

26. **git status**

    最終commit/push後の状態を最終応答へ記す。

27. **Scope Guard結果**

    Live前reviewは`PASS — no unnecessary implementation found`。独立safety reviewはdirect script import blockerを1件発見し、repository root bootstrapを追加後、20秒runについて外部監視とpostflightを条件に`ACCEPT`した。

28. **Phase 2E PASS / FAIL / UNVERIFIED**

    **UNVERIFIED**。SDK接続・exact-once close・ReboCap安定性・操作境界は確認したが、callback 0のためLive delta -> canonical -> latest -> Target FK -> 8 anchors -> 16 message memory round-tripとperformanceを証明できなかった。invalid dataやadapter contradictionを観測したわけではないのでFAILとはしない。

29. **Phase 2F-Aへ進めるか**

    **NO-GO**。Phase 2E PASSが前提であり、今回の許可もPhase 2F-Aへ継承しない。Phase 2F-Aは未実行のまま。

30. **次にユーザーへ要求するcontrolled motion**

    現時点では身体motionを要求しない。まずユーザー側でReboCapのAction Calibration後にlive skeleton/poseが継続更新していることを目視確認し、別のPhase 2E再試行を明示許可する必要がある。その再試行がPASSした後、Phase 2F-Aは「楽な正面向きneutral hold」から開始し、最初の動作cueは「rootを一度だけ右へ移動しneutralへ戻る」とする。

## 結論

今回証明できたのは、Safe Pointで1つの公式SDK clientを安全にopen/closeし、ReboCapとVR background状態を維持できたことまでである。今回証明できなかったのは、Live Pose valueがReboRetarget入口からmemory-only output representationまで連続して通ること。Pose配信がなかった理由を、設定変更、UI Automation、追加接続、再試行、reverse engineeringで追わず、次のユーザー確認gateとして残す。

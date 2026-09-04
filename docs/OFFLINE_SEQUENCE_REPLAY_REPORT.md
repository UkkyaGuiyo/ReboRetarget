# ChatGPTへ渡す報告

記録日: 2026-09-04

これはReboRetarget Phase 2Bの結果である。全入力は手作りのSynthetic fixtureで、Live ReboCap、SDK callback、Meta Quest 3、Virtual Desktop、SteamVR、VRChat、OSC、Tracker、Watcher、GUI、networkには接続も操作もしていない。

1. **Phase 2A commitをpushしたか**

   [確認済み] Phase 2A commit `1731c9d`は、Phase 2B開始前に独立したcommitとして`origin/main`へpush済みだった。Phase 2B変更とは混在していない。

2. **ReboCap parent hierarchy**

   [確認済み] 正規化parent indexは`(-1,0,0,0,1,2,3,4,5,6,7,8,9,9,9,12,13,14,16,17,18,19,20,21)`。`-1`は内部では`None`にする。

   | Index | Joint | Parent | Evidence |
   |---:|---|---|---|
   | 0 | Pelvis | None | CONFIRMED: Docs/U4/UE2 |
   | 1 | L_Hip | Pelvis | CONFIRMED: U4/UE2 |
   | 2 | R_Hip | Pelvis | CONFIRMED: U4/UE2 |
   | 3 | Spine1 | Pelvis | CONFIRMED: U4/UE2 |
   | 4 | L_Knee | L_Hip | CONFIRMED: U4/UE2 |
   | 5 | R_Knee | R_Hip | CONFIRMED: U4/UE2 |
   | 6 | Spine2 | Spine1 | CONFIRMED: U4/UE2 |
   | 7 | L_Ankle | L_Knee | CONFIRMED: U4/UE2 |
   | 8 | R_Ankle | R_Knee | CONFIRMED: U4/UE2 |
   | 9 | Spine3 | Spine2 | CONFIRMED: U4/UE2 |
   | 10 | L_Foot | L_Ankle | CONFIRMED: U4/UE2 |
   | 11 | R_Foot | R_Ankle | CONFIRMED: U4/UE2 |
   | 12 | Neck | Spine3 | CONFIRMED: U4/UE2 |
   | 13 | L_Collar | Spine3 | CONFIRMED: U4/UE2 |
   | 14 | R_Collar | Spine3 | CONFIRMED: U4/UE2 |
   | 15 | Head | Neck | CONFIRMED: U4/UE2 |
   | 16 | L_Shoulder | L_Collar | CONFIRMED: U4/UE2 |
   | 17 | R_Shoulder | R_Collar | CONFIRMED: U4/UE2 |
   | 18 | L_Elbow | L_Shoulder | CONFIRMED: U4/UE2 |
   | 19 | R_Elbow | R_Shoulder | CONFIRMED: U4/UE2 |
   | 20 | L_Wrist | L_Elbow | CONFIRMED: U4/UE2 |
   | 21 | R_Wrist | R_Elbow | CONFIRMED: U4/UE2 |
   | 22 | L_Hand | L_Wrist | CONFIRMED: U4/UE2 |
   | 23 | R_Hand | R_Wrist | CONFIRMED: U4/UE2 |

3. **hierarchyごとの証拠レベル**

   [確認済み] 24 relationすべて`CONFIRMED`。`CORROBORATED`、`INFERRED`、`UNKNOWN`は0件。公式Unityと公式Unrealの実装が全relationで一致したためであり、既存OSSだけを根拠に昇格していない。Parent relationと各jointが独立rotationを持つかは別問題として維持した。

4. **使用した一次/二次情報**

   一次情報は次の3つ。二次情報をparent確定根拠には使っていない。

   - Docs: ReboCap公式SDK文書のSDK Interface Descriptionと24 Bone Names。<https://doc.rebocap.com/en_US/SDK/>
   - U4: 公式Unity SDK v4の`SdkManager.cs:39-64`と`RebocapWsSdk.cs:74-99`。公式archive SHA-256は`E0C0C102D8C45529DF731341E12C2B52BD45823269F43DAD753DBBE9132FE0BF`。
   - UE2: 公式Unreal Engine plugin source v2の`rebocap_source.cpp:115-152`。公式archive SHA-256は`AAFA2393FBE81E0F24A513BCB9546FC96147D2893AA7B1C7C33DA1CB110EAA53`。

   Unityはroot parentを`-1`、UnrealはPelvis self-index `0`で表すが、どちらもPelvis rootを意味するため内部`None`へ正規化した。公式archive/source自体はrepositoryへ保存していない。

5. **未確定parent relation**

   [確認済み] 未確定parentは0件。ただしLive観測で統計一致したR_Shoulder/R_Elbow、Wrist/Hand、Ankle/Footが独立自由度を持つかは未確定であり、parent確定とは混同しない。

6. **Replay実装方法**

   `retarget_sequence`は`SourcePose`のin-memory sequenceを順番に既存`retarget_pose`へ渡し、immutableな`TargetPose` tupleを返すだけである。timestamp、recording file、queue、interpolation、network、外部dependencyを導入していない。Fixtureは既存のlocal-to-global生成helperで手作りした24 global QuaternionとPelvis translationだけを保持する。

7. **Replay frame数**

   主sequenceはStraight→Bendの7 frame。追加でRoot Translation 4 frame、`q/-q`および179→181境界4 frame、上半身chain 5 frameを使用した。計20 frame相当だが、独立目的の4 sequenceであり一つのrecording timelineではない。

8. **Straight→Bend結果**

   [確認済み] 7 frameでHipを毎frame 5度、Kneeを10度ずつ増やし、0/0度から30/60度へ移行した。1.02 m Targetで全frameのKnee/Ankle位置が解析式と`1e-9 m`以内で一致した。連続frameの最大Ankle移動は0.175762206 mで、設計した角度stepに対応する連続変化だった。

9. **Long target結果**

   [確認済み] 大腿0.52 m+下腿0.50 m=1.02 m。全7 frameでsegment長とSource local joint rotationを保持した。Sourceの0.86 m脚へ位置拘束していない。

10. **Short target結果**

    [確認済み] 大腿0.36 m+下腿0.34 m=0.70 m。同じ7 frameでLong Targetと同一local rotationを保持し、位置だけShort Target骨長に従った。最大Ankle移動は0.120075463 mだった。

11. **Balance結果**

    [確認済み] `Thigh / Calf Balance = +0.10`は0.43+0.43 mを0.516+0.344 mへ移し、総長0.86 mを全frameで維持した。Straight frameではAnkle endpointが同じままKneeだけ0.086 m移動した。Bend frameではsegment配分が変わるためAnkleも解析式どおり変わり、endpoint固定とは扱わない。`Leg Length = 1.10`は0.473+0.473=0.946 mとして全7 frameに適用された。

12. **Root translation結果**

    [確認済み] 4 frameでRootを左右方向`+0.20 m`、上下`+0.15 m`、前後方向`-0.30 m`へ順に動かした。全24 Target jointがRootと同じ差分だけ移動し、rotationは変わらなかった。

13. **q/-q continuity結果**

    [確認済み] Kneeを`179°, -q(179°), -q(181°), 181°`とした4 frameで、rotation distanceは`0°, 2°, 0°`。Quaternion componentの直接差ではなく最短rotation distanceを使ったため、sign flipと180度境界をjumpとして誤検出しなかった。Interpolation自体は実装していない。

14. **上半身chain結果**

    [確認済み] Spine3、L_Collar、L_Shoulder、L_Elbowを5 frameで段階的に動かした。frame stepは各5/2.5/7.5/10度で、最終world rotationは`Spine3 * Collar * Shoulder * Elbow`と一致した。脚用と同じGlobal→Local、motion delta、Target FK coreだけを使用した。

15. **Shoulder Width実験結果**

    [確認済み] Synthetic fixture限定で`Shoulder Width = 1.10`を試した。左右Shoulder rest spanは0.40 mから0.44 mへ正確に10%広がり、fixtureの上腕0.28 m、前腕0.25 mは不変だった。これは製品control/APIではなく、Target rest vector変更の数学実験だけである。

16. **Arm Length実験結果**

    [未実装] 上半身FKとShoulder Widthだけで今回の必須gateを満たしたため、Arm Lengthは範囲拡張せず次Phase以降へ送った。UpperArm/Forearm Balanceも未実装。

17. **全tests**

    [確認済み] Python 3.10、3.11、3.13でそれぞれ`Ran 44 tests`、`OK`。Phase 2Aの30 testをすべて維持し、Phase 2Bを14 test追加した。位置toleranceは`1e-9 m`、Quaternion同値は`1-abs(dot) <= 1e-9`、角度は`1e-7 degree`。連続性は各frameの解析位置一致に加え、設計した7-frame sequenceの位置step上限0.18 mを明示した。

18. **失敗・不採用案**

    初回testで、旧fixture名のimport残りと、設計した角度stepに対して任意の0.15 m上限が狭すぎることを検出した。前者はcanonical hierarchy constant参照へ修正し、後者は全frameの解析位置を`1e-9 m`で検証した上で、実測最大0.175762206 mを包含する0.18 mへ明示した。recording/replay framework、file format、interpolation、外部dependency、IK、Foot/Hand Lock、Source endpointへのTarget拘束は不採用。

19. **未解決事項**

    公式SDKのglobal rotationはT-pose-relative deltaである。Docsに加え、Unity `SdkManager.cs:385-389,432-433`はmessage Quaternionをdefault bind rotationへ、Unreal `rebocap_pose_node.cpp:282-308`はT-pose global rotationへ合成する。これを明示的に扱うLive adapterは未実装で、SDK globalを完成済みabsolute bind rotationとして直接投入してはならない。ほかにLive軸符号、joint独立性、実Avatar rest skeleton、Arm/Hip controls、Tracker offset、multi-client安全性、disconnect、IK、OSC、VRChat受入が未解決。

20. **Live systemに触れていないこと**

    [確認済み] Phase 2Bはrepository内のpure PythonとSynthetic dataだけ。ReboCap/WebSocket/SDK callback/network、Quest、Virtual Desktop、SteamVR、VRChat、OSC、Tracker、Calibration、Watcher、GUI、process操作は0件。

21. **commit hash**

    Phase 2B commit自身へそのhashを自己記載できないため、本書には固定しない。scope review後のcommit hashを最終応答で提示する。

22. **push状態**

    Phase 2A `1731c9d`は`origin/main`へpush済み。Phase 2Bはscope review合格後に独立commitとしてpushし、最終応答で`HEAD == origin/main`を確認する。

23. **git status**

    Phase 2B commit/push後にworking treeを再確認し、最終statusを最終応答で提示する。公開対象にはSynthetic source/testsと必要な文書だけを含め、SDK archive、binary、raw motion、local path、device/account情報を含めない。

24. **Phase 2C Go / No-Go**

    **GO:** Target Skeleton world transformから、計画済みHip、Chest、左右Knee、左右Foot、左右Upper Armのtracker transformをSynthetic入力だけでoffline生成する。

    **NO-GO:** OSC送信、Live SDK adapter/再接続、IK、Foot/Hand Lock、SteamVR/VRChat操作、Native/Retarget切替、Watcher/GUI統合。Hierarchy確定はこれらのgate解除を意味しない。

25. **次に作る最小PoC**

    既存`TargetPose.world_transforms`から8 semantic pointを選び、各pointの明示的なlocal position/rotation offsetを合成してimmutableなtracker transform tupleを返すpure functionを作る。T-pose、bend、root移動、mirrorのSynthetic fixtureでposition/orientationを検証する。OSC packet、timing loop、network、Live input、IKは作らない。

## 総括

Phase 2Bは、暫定だった24 parent relationを2つの公式code実装で全件CONFIRMEDへ更新し、そのhierarchy上で20 frame相当のSynthetic sequenceを既存pure FK coreへ通した。Long/Short、Leg Length、Balance、Root XYZ、mirror、`q/-q`、179→181、上半身chain、fixture-only Shoulder Widthが連続・決定的に成立した。次はoffline tracker transformだけへ進めるが、T-pose-relative SDK rotation adapterとLive/OSC/IKは引き続き明確なNo-Goである。

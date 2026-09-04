# ChatGPTへ渡す報告

Status: **Phase 2C pure/offline acceptance passed; Scope Guard ACCEPT**
Date: 2026-09-04

確認済みの事実、今回採用したSynthetic fixture、将来の実機確認事項を分けて記す。ここで示すanchor offsetは数学検証用であり、製品既定値でも実ユーザー向け調整値でもない。

1. **ReboCap Delta Adapterの実装** — `reboretarget/rebocap_adapter.py`に、immutableな`ReboCapDeltaPose`、bind-global算出、pureな`adapt_rebocap_delta_pose`を追加した。24 joint数と公式確認済みhierarchyを検証し、Pelvis root translationを値変更せずCanonical `SourcePose`へ渡す。SDK client、socket、clock、process、filesystemは持たない。

2. **SDK delta合成式** — 各jointについて`source_absolute_global = sdk_rotation_delta * source_bind_global_rotation`を使用する。Hamilton `(w,x,y,z)` active rotationで、右側のbind rotationを先に適用する。逆順ではないことを非可換Quaternionで数値検証した。

3. **公式実装との対応** — ReboCap公式SDK文書の「全rotationはT-pose基準」と、Unity SDK v4の`msgQuat * defaultBindRotation`、Unreal plugin v2のReboCap QuaternionとT-pose global rotationの合成を正本にした。FK coreにはReboCap固有解釈を入れていない。

4. **Tracker Anchor型** — immutableな`TrackerAnchorDefinition(role, parent_joint, local_position_offset, local_rotation_offset)`と`TrackerTransform(role, position, rotation)`を追加した。計算は`world_position = joint_position + rotate(joint_rotation, local_position_offset)`、`world_rotation = joint_rotation * local_rotation_offset`である。

5. **8 semantic role** — `Hip`、`Chest`、`Left Knee`、`Right Knee`、`Left Foot`、`Right Foot`、`Left Upper Arm`、`Right Upper Arm`のちょうど8種をenumで固定した。これはsemantic roleでありOSC slotではない。

6. **各roleのparent joint** — Hip=`Pelvis`、Chest=`Spine3`、Left/Right Knee=`L_Knee`/`R_Knee`、Left/Right Foot=`L_Ankle`/`R_Ankle`、Left/Right Upper Arm=`L_Shoulder`/`R_Shoulder`とした。

7. **各roleの初期local offset** — fixture単位はmetre。Hip=`(0,0,0.04)`、Chest=`(0,0.05,0.04)`、各Knee=`(0,0,0.03)`、各Foot=`0.5 * その側のAnkle→Foot rest vector`、各Upper Arm=`0.5 * その側のShoulder→Elbow rest vector`、rotation offsetは全てidentityである。差し替え可能な定義として生成する。

8. **Chest anchor方針** — 初期fixtureは`Spine3 + local offset`。`Spine3 = VRChat Chest`を恒久仕様にはせず、定義の差し替え対象とした。

9. **UpperArm anchor方針** — Shoulder joint originではなくShoulder→Elbow segmentの中点をfixture位置にした。VRChat公式文書は上腕trackerがelbowより上に装着され、elbowとshoulder双方へ影響すると記すが、この0.5は製品値ではない。

10. **Knee anchor方針** — Kneeをparentとし、回転する小さなlocal surface offsetを持たせた。実際の最適位置はVRChat FBT calibrationを含む後段の実機検証事項である。

11. **Foot anchor方針** — Ankleをparentとし、Target Skeleton自身のAnkle→Foot rest vectorの半分をlocal offsetにした。前回live観測ではAnkle/Footの集計rotationが同一で独立性が未証明なため、Foot独立回転を仮定せずchain上の明示位置を使う最小案である。

12. **Hip anchor方針** — 身体中央のPelvisをparentとする。左右脚rootを動かすHip Widthとは別のsemantic transformである。

13. **Arm Length実装結果** — 未実装。Phase 2Cの必須acceptanceに不要だったため、製品意味・range・profile UIを先回りして追加しなかった。

14. **Arm Balance実装結果** — 未実装。総腕長を維持してElbow位置を変える仕様候補は維持するが、今回の8点変換を証明するためには不要だった。

15. **Hip Width実装結果** — 製品controlは未実装。既存Synthetic skeletonのfixture parameterとして`0.20 m -> 0.24 m`を試し、Knee/Foot anchorだけが左右へ各`0.02 m`対称移動し、Hip/Chest/Upper Armが不変であることを確認した。

16. **Identity test** — 8 roleを一度ずつ生成し、既知のTarget Skeleton位置とidentity rotationへ`1e-9 m`/`1e-9` toleranceで一致した。既定fixtureのHip `(0,1.00,0.04)`、Chest `(0,1.50,0.04)`、Knees `x=±0.10,y=0.57,z=0.03`、Feet `x=±0.10,y=0.14,z=0.09`、Upper Arms `x=±0.34,y=1.53,z=0`を確認した。

17. **Long leg test** — 1.02 m脚と0.70 m脚を比較し、short側はKneeが`0.16 m`、Footが`0.32 m`上がった。Hip、Chest、両Upper Armには変化がなく、anchorがSource位置ではなくTarget骨長へ追従した。

18. **Knee bend test** — 左Kneeを90度曲げ、Knee/Footのposition offsetが各parent rotationで回り、両tracker rotationもKnee回転へ追従した。

19. **Root translation test** — lateral `+0.20 m`、vertical `+0.15 m`、forward/back `-0.30 m`を含む4 frameで、全8 anchorがrootと全く同じworld deltaだけ移動し、rotationとlocal関係は不変だった。

20. **body rotation test** — Pelvis yaw 90度で、root相対の全anchor位置が同じyawで回り、全anchor rotationも同じyawを得た。

21. **Shoulder Width test** — fixture-only Shoulder Width `1.00 -> 1.10`でUpper Arm anchor spanが`0.68 m -> 0.72 m`へ広がった。Hip、Chest、Knee、Footは不変で、既存fixtureどおり腕segment lengthも変えていない。

22. **mirror test** — 左右Hip/Kneeへ同じ局所回転を与え、Knee、Foot、Upper Arm anchorがX符号だけ反転し、Y/Zとrotationが一致した。左右専用計算は追加していない。

23. **rotation offset test** — parentをX軸30度、local rotation offsetをY軸40度として、`parent * local_offset`に一致し、非可換な逆順`local_offset * parent`とは一致しないことを確認した。

24. **SDK-delta→Target→Tracker integration test** — non-identityなSource bind（Pelvis Y20度、Spine3 X10度）に対し、期待Canonical Source Poseの局所motionをPelvis X12度、Spine3 Y18度、左Knee X30度として整合したSource globalsを作った。このX12/Y18/X30はSDK global deltaそのものではない。実際のSDK-like deltaは各jointで`sdk_delta = expected_source_global * inverse(bind_global)`と逆算され、non-identity bind下では単純なX/Y軸角度にならない。root `(0.2,1.1,-0.3)`からadapter、既存retarget/FK、長脚・Shoulder Width 1.10のTarget、8 anchorへ順に通し、Canonical Spine3/Knee/Ankle globalsを直接確認した。さらにChest、Left Knee、Left Footの各anchorについて、手計算したTarget-chain positionと期待rotationへ直接一致することを確認した。

25. **全test数 / 結果** — Phase 2A/Bの44件を維持し、Phase 2Cでadapter 6件とanchor 11件を追加した。合計61件をPython 3.10、3.11、3.13で実行し、各runtimeで`Ran 61 tests`、`OK`を確認した。数値toleranceはposition `1e-9 m`、Quaternion equivalence `1e-9`で明示している。

26. **未解決事項** — 実avatar rest skeleton取得、実世界origin/axis/handedness、実用anchor offsetとorientation、Arm Length/Balance製品control、live multi-client安全性、Ankle/Foot等の独立性、OSC slot割当とEuler表現、head alignment、packet cadence、native tracker競合、実VRChatでのFBT品質は未確認である。

27. **Live systemへ触れていないこと** — Phase 2CではRepositoryのcode、文書、手書きSynthetic dataだけを使用した。ReboCap live SDK/GUI/process、Quest、Virtual Desktop、SteamVR、VRChat、Watcher、UI Automationを起動・停止・操作・照会していない。

28. **OSC送信していないこと** — OSC/UDP sender、address、packet encoder、socketを実装・実行していない。内部rotationはQuaternionのまま保持し、実Tracker deviceも生成していない。

29. **commit hash** — この報告を含むPhase 2C commitのhashは最終応答で提示する。文書自体には自己参照となるhashを埋め込まない。

30. **push状態** — Scope Guard ACCEPT後にこの報告を含むPhase 2C commitを`origin/main`へpushし、remote一致を最終応答で提示する。

31. **git status** — Phase 2Cの明示対象だけをcommitし、最終応答でworking treeのclean状態とahead/behindを提示する。

32. **Phase 2D Go / No-Go** — 61件とScope Guardが通ることを条件に、semantic transformをVRChat OSC representationへ変換するpure/offline Phase 2DへGO。live SDK接続、UDP/OSC送信、実VRChat操作、Native/Retarget切替、IK/lock、GUIは引き続きNO-GO。

33. **次に作る最小PoC** — 8 semantic roleから明示的slot mappingを作り、QuaternionからVRChatのdegree Euler（内部適用順Z/X/Y）へ変換し、metre/Unity left-handed座標とhead alignment modelをoffline値として表現し、OSC messageのencode/decodeをnetworkなしでtestする。UDP送信はまだ行わない。

## 一次資料

- ReboCap official SDK documentation, SDK Interface Description and 24 Bone Names: <https://doc.rebocap.com/en_US/SDK/>（last edit 2025-04-17、accessed 2026-09-04）
- ReboCap official Unity SDK v4, `Assets/RebocapSdk/DemoScenes/SdkManager.cs:385-389,432-433`
- ReboCap official Unreal Engine plugin v2, `Source/rebocap_runtime/Private/rebocap_pose_node.cpp:282-308`
- VRChat OSC Trackers: <https://docs.vrchat.com/docs/osc-trackers>（accessed 2026-09-04）
- VRChat Full-Body Tracking: <https://docs.vrchat.com/docs/full-body-tracking>（accessed 2026-09-04）

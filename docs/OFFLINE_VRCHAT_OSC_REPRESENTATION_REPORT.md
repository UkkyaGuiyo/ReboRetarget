# ChatGPTへ渡す報告

Status: **Phase 2D pure/offline acceptance passed; Scope Guard ACCEPT**
Date: 2026-09-05

Phase 2Dは、Phase 2Cの8 Semantic Tracker TransformをVRChat OSC Tracker表現へ変換し、OSC 1.0 byte列へencodeして同じmemory内でdecodeするところまでに限定した。Live applicationとnetwork送信には接触していない。

1. **現行VRChat OSC仕様確認結果** — Bodyは`/tracking/trackers/{1..8}/position`と`/tracking/trackers/{1..8}/rotation`、各3 float。positionはUnity world-space、left-handed、`+X`右、`+Y`上、`+Z`前、1 unit=1 m。rotationはdegree Eulerで、fixed world axisの`Z -> X -> Y`順に適用される。Headは固定`head` addressを使う別機能で、body slotに含まれない。

2. **使用した一次資料** — [VRChat OSC Trackers](https://docs.vrchat.com/docs/osc-trackers)、[Full-Body Tracking](https://docs.vrchat.com/docs/full-body-tracking)、[IK 2.0](https://docs.vrchat.com/docs/ik-20-features-and-options)、[OSC Overview](https://docs.vrchat.com/docs/osc-overview)、[VRChat 2026.1.2 release notes](https://docs.vrchat.com/docs/vrchat-202612)、[Unity rotation conventions](https://docs.unity3d.com/6000.0/Documentation/Manual/QuaternionAndEulerRotationsInUnity.html)、[Unity Quaternion.Euler](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Quaternion.Euler.html)、[OSC 1.0 specification](https://opensoundcontrol.stanford.edu/spec-1_0.html)。古いcommunity実装を規範根拠にしていない。

3. **Semantic role -> slot mapping** — 初期dataは1 Hip、2 Chest、3 Left Knee、4 Right Knee、5 Left Foot、6 Right Foot、7 Left Upper Arm、8 Right Upper Arm。8 roleとslot 1..8を各1回ちょうど要求し、欠落、重複、range外、`bool` slotを拒否する。

4. **slotとroleの分離** — `SemanticTrackerRole`を`TrackerSlotMapping`へ入力し、`OscTrackerPose.slot`を得る別layerにした。mappingはimmutableなdataで差し替え可能。VRChatがslot 1をHipと定義する、という意味ではないことをtestとcontractに明記した。

5. **Position coordinate変換** — Phase 2Cの`TrackerTransform.position`を`position_xyz_m`へ値変更なしで渡す。Phase 2D output layerにはscale、axis swap、sign反転を入れていない。

6. **internal coordinateとの関係** — Synthetic Target spaceは既にmetre-valued Unity axis labelを使うためpass-throughできる。一方、installed ReboCap live値のknown-action axis signとsession originは未確認であり、live pass-throughを証明したとは扱わない。ReboCap Adapterの責務とOSC outputの責務は混ぜていない。

7. **Quaternion -> Euler方式** — 正規化Quaternionからrotation matrixを作り、`x=asin(clamp(-R[1][2]))`、通常時`y=atan2(R[0][2],R[2][2])`、`z=atan2(R[1][0],R[1][1])`を使う。X=+/-90度ではZ=0の決定的branchを選び、残りをYへ表す。Euler成分そのものではなく再構築rotationを判定する。

8. **VRChat rotation order** — fixed-world-axis `Z -> X -> Y`。RepositoryのHamilton `(w,x,y,z)` active conventionでは`qY * qX * qZ`として再構築する。

9. **degree / radian** — `math`内部の三角関数だけradian。公開representation、型名、変数名は`rotation_euler_xyz_deg`、`yaw_degrees`としてdegreeを明示する。radianをOSC値として出さない。

10. **rotation round-trip test** — identity、X30、Y30、Z30、X/Y、Y/Z、X/Y/Z、X=89.9/90/90.1、Y=179/180/181/-179度を、Quaternion -> representation -> `qY*qX*qZ`へ戻し、全件rotation-equivalentと確認した。追加の固定seed 100,000組stress checkでも失敗0、`1-abs(dot)`最大`4.441e-16`だった。

11. **singularity test** — X=+90度と-90度の複合rotationで全Euler値がfinite、Z=0の決定的branch、再構築同値を確認した。89.9/90/90.1度にもNaNや巨大値はない。Euler成分の完全連続性は保証せず、rotation同値を保証する。

12. **q / -q test** — 同じrotationの`q`と`-q`がmatrix経由で完全に同じEuler tupleを生成し、sign flipを別姿勢として扱わないことを確認した。

13. **OSC message型** — network情報を持たないimmutable `OscFloat3Message(address, values)`。Phase 2Dのtype tagはexact `,fff`のみ。Body representationは`OscTrackerPose(slot, position_xyz_m, rotation_euler_xyz_deg)`。

14. **address生成** — slot range検証後、`/tracking/trackers/{slot}/position`と`/tracking/trackers/{slot}/rotation`を生成する。0、9、`True`を拒否する。Headは`/tracking/trackers/head/position|rotation`の固定addressで別生成する。

15. **binary encoding** — OSC 1.0に従いaddressと`,fff`をASCII OSC-stringとしてNUL終端し4-byte境界までNUL padding、値をbig-endian IEEE 754 float32 3個として連結する。float32 overflowを拒否する。巨大dependencyは追加していない。

16. **decode round-trip** — position `(0,0,0)`, `(1,2,3)`, `(-1.5,0.25,7.75)`とrotation `(0,0,0)`, `(30,45,60)`, `(-179,90,180)`をmemory encode/decodeし、address完全一致とfloat32 tolerance内の値復元を確認した。不正padding/tag/payload長/address/NaNも拒否する。

17. **8点16 message snapshot** — Synthetic ReboCap-shaped delta -> Canonical Source -> Target FK -> 8 Semantic Tracker -> slot representation -> 16 messages -> 16 offline decodeを一気通貫で確認した。position 8、rotation 8、address重複0。

18. **Head alignment設計** — `HeadAlignmentReference`はoptional positionとQuaternion rotationを保持し、body mappingと独立して固定head address messageへ変換する。Headは9番目のbody trackerではない。VRChatではhead positionがhead-bone rootへspaceを合わせ、head rotationはyaw alignmentを制御する。

19. **Tracking-space alignment** — `TrackingSpaceAlignment(translation_xyz_m, yaw_degrees)`を別pure modelにした。`p' = rotate(qYaw,p)+translation`、`q'=qYaw*q`を8点へ一括適用する。Yaw +90度、translation `(+1,+0.5,-2)`で全点が同じrigid transformを受けることを確認した。

20. **Recenterとの境界** — pairwise distanceとrelative rotationの保存を検証したがRecenterは実装していない。ReboCap action calibration、VRChat FBT calibration、OSC head alignment、SteamVR playspace、将来のReboRetarget recenterは別概念として記録した。

21. **全test数** — Phase 2A/B/Cの61件を維持し、Phase 2Dを22件追加、合計83件がPython 3.10、3.11、3.13の各runtimeで`OK`。Phase 2Dはrotation、mapping、position、address、codec、head、rigid alignment、full snapshotを網羅する。

22. **失敗・修正** — Acceptance testの失敗はなかった。実装時点からEuler数値一致を正解にせずrotation round-tripを採用し、gimbal branch、float32 overflow、malformed padding、duplicate/missing mappingを明示的にfail-closedにした。外部OSC libraryやsender frameworkは不要と判断した。

23. **未解決事項** — Live ReboCap axis signs/origin、SDK multi-client安全性、実avatar anchor offset/orientation、native trackerとのduplicate precedence、実VRChatでのslot interpretation/FBT品質、最適point subset、head alignmentの実機挙動とsender timingは未検証。2026.1.2はhead-position single pulseを追加したが、position側のstream threshold/timeoutは現行資料に明記がない。

24. **Live接触0の確認** — Phase 2D実装/testではReboCap SDK/process/UI、VRChat、SteamVR、Virtual Desktop、Meta Quest 3、Watcher、UI Automationへ起動、停止、操作、照会をしていない。

25. **Network送信0の確認** — UDP/OSC送信0。`socket` import、sender、host/port、timing loop、60 Hz scheduler、retry、OSC Queryは存在しない。生成byte列は同一process memory内のdecodeだけへ渡した。

26. **commit hash** — Scope Guard後に独立commitを作るため、本書には自己参照hashを固定しない。最終応答で提示する。

27. **push状態** — Scope Guard合格後に`origin/main`へpushし、最終応答で`HEAD == origin/main`を確認する。本書作成時点では未commit・未push。

28. **git status** — 最終commit/push後のclean statusとahead/behindを最終応答で提示する。本書作成時点ではPhase 2Dのsource/tests/docsだけが変更対象で、SDK、binary、raw log、生motion、個人/device情報は含まない。

29. **Phase 2E Go / No-Go** — **条件付きGO**は、別途安全手順を設計し明示的safe pointを得た後のLive ReboCap Adapter Safety Validationだけ。**NO-GO**はPhase 2D完了だけを根拠にしたlive接続、UDP送信、VRChat起動/操作、SteamVR/Virtual Desktop/Quest接触、IK/lock、Native/Retarget切替、GUIである。

30. **Liveへ戻る場合の安全な次PoC案** — まずVRChat crashとの因果未確定を前提に、SDK single-client/multi-client条件と中断条件をread-only資料・sourceから整理する。ユーザーがVRChatを通常playしていない明示safe pointを選び、VRChat OSC送信なしでReboCap delta adapter、latest-pose-only buffer、約60 Hz挙動、disconnect時即invalid化だけを狭く検証する。VRChat、SteamVR、Virtual Desktop、Questを起動・停止・再設定せず、異常時は即停止して後続gateを開かない。

## 実装file

- `reboretarget/vrchat_osc.py`
- `tests/test_vrchat_osc.py`
- `reboretarget/__init__.py`

## Scope boundary

このPhaseが証明したのは、Target Tracker QuaternionとpositionをVRChat OSCが要求する**表現**へ正しく翻訳し、byte列をmemory内で往復できることだけである。VRChatが実avatarを正しく動かしたこと、live connectionが安全であること、packetを送ったことは主張しない。

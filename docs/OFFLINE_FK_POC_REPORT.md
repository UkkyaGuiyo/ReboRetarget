# ChatGPTへ渡す報告

記録日: 2026-09-04

これはReboRetarget Phase 2Aの結果である。入力はすべて手作りのSynthetic fixtureで、ReboCap、Meta Quest 3、Virtual Desktop、SteamVR、VRChat、OSCには接続も操作もしていない。

1. **実装したpure/offline module**

   `reboretarget/fk.py`に、不変のQuaternion、Joint/Skeleton definition、Source/Target Pose、Transform、joint diagnosticと、Global→Local変換、Target FK、rotation-delta retarget、脚長controlを実装した。device、network、process、file、clockのI/Oはない。

2. **使用言語・数学libraryと選定理由**

   Python 3.10.11とstandard libraryの`math`、`dataclasses`、`typing`のみ。小さなPoCの数学conventionを直接読め、外部runtime依存や未確定の製品stackを増やさず、deterministicな単体testを容易にするためである。

3. **Skeleton表現**

   `JointDefinition(name, parent, rest_local_position, rest_local_rotation)`のparent-before-child配列で単一rootを表す。`segment_length`はrest-local位置vectorの長さから導出し、二重保持による矛盾を避けた。SourceとTargetは同じsemantic joint名とparentを持ち、rest vector、rest rotation、骨長は異なってよい。24 jointの名前と順序は確認済みだが、parent配列は既存integrationで用いられるconventional hierarchyをSynthetic仮説としたもので、ReboCapのnormative contractとはまだ確定していない。

4. **Source Pose表現**

   `SourcePose(root_translation, global_rotations)`。ReboCap-shaped入力用constructorは確認済みの24 joint順序とちょうど24個の`(w,x,y,z)`を要求する。Phase 2Aではlive値や保存motionは使っていない。

5. **Global → Local変換方法**

   Rootは`local = global`。Childは`local = inverse(parent_global) * child_global`。identity、親40度+子35度の複合rotation、non-identity restで数値test済み。

6. **Quaternion convention**

   Hamiltonの`(w,x,y,z)`、active rotation。`left * right`はrightを先に適用し、次にleftを適用する。Worldは`parent_global * child_local`。`q`と`-q`はcomponent一致ではなくrotation同値として比較する。Eulerは使っていない。

7. **FK計算方法**

   `child_world_rotation = parent_world_rotation * child_local_rotation`。`child_world_position = parent_world_position + rotate(parent_world_rotation, child_target_rest_local_position)`。Root positionにのみSynthetic Pelvis translationを使う。

8. **Source/Target骨長差の扱い**

   `motion_delta = inverse(source_rest_local_rotation) * source_local_rotation`、`target_local_rotation = target_rest_local_rotation * motion_delta`とし、位置再構成にはTargetのrest vectorだけを使う。Source joint位置とSource骨長はコピーしない。

9. **Straight leg test結果**

   Source脚0.43+0.43 m、Target脚0.52+0.50 mのidentity Poseで、Target膝localはidentityのまま。Root `(0.2, 1.2, -0.1)`のfixtureで左膝は`(0.1, 0.68, -0.1)`、左足首は`(0.1, 0.18, -0.1)`。長いTargetの足をSource足位置へ押し込む膝曲げは発生しない。

10. **Knee 90度test結果**

    Target大腿0.52 m、下腿0.50 mで、左膝は`(-0.1, 0.48, 0)`、左足首は`(-0.1, 0.48, -0.50)`。大腿は直立のまま、Target下腿の長さで正90度に曲がった。

11. **Hip + Knee複合test結果**

    Hip 30度、Knee 45度でKnee world rotationは75度。Target左膝は`(-0.1, 0.5496667900, -0.26)`、左足首は`(-0.1, 0.4202572675, -0.7429629131)`となり、親と子のrotation伝播が数値的に一致した。

12. **Long leg / Short leg結果**

    同じstraight Source Poseから、Long Targetは0.52+0.50=1.02 m、Short Targetは0.36+0.34=0.70 mの直線脚になった。どちらも膝localはidentityで、Sourceの0.86 mに拘束されていない。

13. **左右対称性結果**

    左右に同じHip 22度、Knee 37度を入れたfixtureで、Knee/AnkleのXは符号反転、Y/Zとworld rotationは一致した。左右で異なる計算branchはない。

14. **Parent rotation inheritance test結果**

    Parent/Child globalが完全一致するとChild local量は0度。独立15度は15度、小さな0.05度は0.05度のまま復元し、左0度/右12度の非対称も個別に残った。Diagnosticはjoint名、source local Quaternion、その角度のみを返し、「継承か否か」のBooleanやthresholdは持たない。これにより、SDKが独立自由度を提供しないと根拠なく断定しない。

15. **Shoulder/Elbow等の将来扱いについて分かったこと**

    Coreは24 joint全体とSpine/Collar/Shoulder/Elbow/Wrist/Hand chainを特別branchなしで扱える。Spine3 20度+Shoulder 30度のSynthetic testでShoulder worldとElbow継承まで確認した。完全継承と小さな独立rotationを数値で見分けるdiagnosticも再利用できる。ただしLiveで一致したShoulder/ElbowやWrist/Handを「補助node」と決める証拠はまだない。肩Tracker由来のCollar/Shoulder情報を捨てず、将来のoffline fixtureで信頼できる自由度を別途判定する。

16. **Leg Length / Balanceの初期仕様**

    `Leg Length`は大腿+下腿の合計へのscaleで、1.10なら合計が正確に10%伸びる。`Thigh / Calf Balance`は、scale後合計に対する大腿shareへの加算shift。`+0.10`は合計の10 percentage pointsを下腿から大腿へ移す。0.43+0.43 mでLeg Length 1.10は0.473+0.473 m、Balance +0.10は合計0.86 mのまま0.516+0.344 m。

17. **全test結果**

    `PYTHONDONTWRITEBYTECODE=1`で`python -m unittest discover -s tests`を実行し、Python 3.10、3.11、3.13の各runtimeで`Ran 30 tests`、`OK`。数値toleranceは位置`1e-9 m`、Quaternionの`1 - abs(dot)`が`1e-9`以下、角度`1e-7 degree`。testはSynthetic fixtureのみ。

18. **失敗した案**

    Acceptance testで失敗した実装案はない。一方、Source foot位置へTargetを押し込む位置copy、Source骨長のcopy、Euler中心の計算、Quaternion componentの直接一致、IK/Foot Lockによる誤差隠しは、Phase 2Aの目的と矛盾するため採用しなかった。

19. **未解決事項**

    Synthetic 24 hierarchyとinstalled ReboCapの実際の軸符号・known motionの対応、Live SDK multi-client安全性、Shoulder/Elbow/Wrist/HandとAnkle/Footの独立性、実Avatar rest skeleton取得、残りのmorphology controls、IK・contact・OSC・VRChat受入は未確認/未実装。

20. **Live systemへ一切触れていないこと**

    Phase 2Aの実装とtestはrepository内のPython sourceとSynthetic dataのみ。ReboCap SDK/live process/networkへの接続、Meta Quest 3、Virtual Desktop、SteamVR、VRChatのprocess/UI/設定操作、OSC送信、Tracker生成、Watcher、Calibrationは0件。

21. **commitしたfile**

    Phase 2A commitの対象は`.gitignore`、`README.md`、`reboretarget/__init__.py`、`reboretarget/fk.py`、`tests/__init__.py`、`tests/synthetic_fixtures.py`、`tests/test_fk.py`、`docs/OFFLINE_FK_POC_REPORT.md`、`docs/CURRENT_STATE.md`、`docs/RESEARCH_LOG.md`、`docs/DECISIONS.md`、`docs/ROADMAP.md`の12ファイル。個人motion、SDK、binary、raw log、生Poseは含めない。

22. **commit hash**

    Commit自身にそのhashは固定記載できないため、commit/push後の最終Codex応答で示す。

23. **git status**

    Commit/push後のbranch、working tree、`origin/main`との一致は最終Codex応答で示す。

24. **次Phase Go / No-Go**

    **GO:** 短い手入力または適法にsanitizedされたReboCap-shaped Pose列をoffline再生し、Target transform snapshotと連続性を確認する。

    **NO-GO:** Live SDK再接続、OSC、Two Bone IK、SteamVR/VRChat出力、Native/Retarget切替、Watcher統合、GUI、Quest Chest Yaw。Global/local conventionはSynthetic testで確定したが、live軸とmulti-client安全性は別gateである。

25. **Goなら次に作る最小PoC**

    数frameの手作り24-global-Quaternion+Pelvis-translation列と期待Target snapshotを追加し、直立から屈曲への連続性、左右、長短Target、継承diagnosticをofflineで再生する。新しいruntime、file format、live adapter、outputはまだ作らない。

## 総括

Phase 2Aは「人間の脚が真っ直ぐなら、骨長の違うTargetも膝を曲げずに真っ直ぐ立つ」ことをSynthetic Skeleton上で数値的に証明した。位置copyではなく、source local motionをtarget rest skeletonへ移し、Target骨長でFKすることが核である。

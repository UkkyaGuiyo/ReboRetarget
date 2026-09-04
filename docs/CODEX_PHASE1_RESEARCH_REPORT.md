# ChatGPTへ渡す報告

作成日: 2026-09-04

## 結論

ReboRetargetは公開済みの調査・設計プロジェクトになった。公式ReboCap WebSocket SDKから読む入力形式と、VRChatへ将来送るOSC形式は実装可能な粒度まで定義できた。一方、ReboCap純正SteamVR身体Tracker出力だけを安全に自動停止・正確復元する公開制御面は未確定である。

したがって、次の判定は分離する。

- **Go:** 公式SDKを使う数十行規模のread-only Pose inspectorを、ユーザーが許可したcalibration済みsessionで動かし、実データの軸・時刻・階層・肩反映を測る。
- **No-Go:** Retarget Solver、常用OSC送信、GUI、Watcher、自動Native/Retarget切替を含む製品本体。

## 1. GitHub repository URL

<https://github.com/UkkyaGuiyo/ReboRetarget>

## 2. public/private状態

**Public**。GitHub側のrepository readbackと公開ページ表示で確認した。

## 3. 初回commit hash

`bc01e746fbcf0db3e7a1c52a1fb3592237f57199`

`docs: establish ReboRetarget project memory`

これは「ReboRetarget Phase 0：プロジェクト記憶完成地点」である。

## 4. 今回追加したresearch commit hash

`13acd8499e2fc845d4f19af11c8ea16b05bfd060`

`research: map ReboCap and VRChat integration surfaces`

## 5. ReboCap installed version

- Windows uninstall表示: `Release V02 Beta_02`
- executable ProductVersion: `0.48.0.0`
- executable FileVersion: `1.0.0.0`

表記が一致しないため、一つへ推測統合せず三つの観測値として残した。

## 6. ReboCap SDKの確認結果

- 公式SDKページ: <https://doc.rebocap.com/en_US/SDK/>
- Python v2、C# v2、C++ v3の公式配布archiveをrepository外の一時領域で確認した。
- ReboCap GUIがWebSocket broadcast serverであり、SDKはlocal clientとして接続する。
- default portは`7690`。占有時はReboCap側がincrementする。
- 公式DLLの8 interfaceはinstance生成/解放、open/close、Pose callback、異常切断callback、last message取得、foot vertex計算である。
- Action Calibration後にPose配信が始まり、文書上60 fps。
- 本repositoryへSDK source/binary/archiveは追加していない。

## 7. SDK license / redistribution条件の確認結果

確認した三つの公式SDK archiveに、SDK全体を対象にする`LICENSE`、`NOTICE`、`COPYING`または明示的な再配布許諾は見つからなかった。公式document footerはall-rights-reserved表記である。C++ archive内のvendored OSS licenseはReboCap SDK自体を許諾しない。

結論は「再配布不可と断定」ではなく、**再配布許諾未確認**。そのためSDKをcommitせず、project LICENSEも未確定のままとした。将来bundleする前にvendor確認が必要。

## 8. Skeleton Pose取得方式

公式SDKを使い、ReboCap GUIのlocal WebSocket broadcastへ接続する。最初のPoCでは`UnityCoordinate`かつglobal rotationを要求する。

一frameの通常Poseは次の構成である。

- pelvis/root translation `trans[3]`。単位m。
- 24 joint quaternion `pose24`。example表記は`(w,x,y,z)`。
- foot/contact情報 `static_index`。
- timestamp。wrapper変換後の厳密なunit/epochは未確認。

全boneのworld positionは含まれない。Pelvis位置、回転、hierarchy、rest skeleton/segment長から再構成する必要がある。

## 9. 取得できる主要Bone一覧

24 joint順は次の通り。

`Pelvis, L_Hip, R_Hip, Spine1, L_Knee, R_Knee, Spine2, L_Ankle, R_Ankle, Spine3, L_Foot, R_Foot, Neck, L_Collar, R_Collar, Head, L_Shoulder, R_Shoulder, L_Elbow, R_Elbow, L_Wrist, R_Wrist, L_Hand, R_Hand`

必要なPelvis、Spine/Chest相当、Collar、Shoulder、UpperArm/Elbow、Wrist、Hip、Knee、Ankle、Footを構成する情報は存在する。ただし`Chest`という名のjointはなく、Spine chainからChest tracker poseを定義する必要がある。

## 10. 肩Tracker情報がSDK上でどう見えるか

SDK schemaには常に左右Collar、Shoulder、Elbow、Wrist、Hand回転がある。物理肩Tracker装着の有無を示すflagやsensor metadataはPose messageにない。

したがって「肩boneがある＝肩Trackerを装着」とは判定できない。ユーザーの既存設定を正本にしつつ、許可されたlive sessionで肩装着状態の既知動作を比較し、どのjoint rotationへ改善が現れるか確認する必要がある。

## 11. ReboCap SteamVR Outputの制御方法候補

優先順で確認した結果は次の通り。

1. 公式SDK/API: Pose取得のみで、SteamVR output controlはなし。
2. 設定: `config.data`内にPC側VR outputやoutput nodeに対応するfield名を確認。
3. Registry: 専用の出力switch値は見つからず。
4. local IPC: ReboCap GUI/driverがnamed pipeを使う事実は確認したが、外部向けquery/set/ack contractは未確認。
5. UI Automation: 公式GUIのPC panelにはadvanced `VR Output` toggleがあるためfallback候補。ただしVR mode全体のmaster switchかは未確認。
6. 内部解析: UI/config/driverのsymbol/stringとexportを互換性目的で限定確認したが、安全な外部commandは確定できず。

## 12. 実際に安全な自動ON/OFFが可能そうか

**現時点では「可能そう」と断定しない。** GUI上の候補はあるが、現在状態の読み取り、VR/PC mode差、変更acknowledgement、他設定不変、crash recovery、元状態の正確復元が未検証である。

`config.data`直接編集は不採用。user-authorized A/B testで一つのtoggleだけが変化し、SteamVR device消失/復帰と無関係設定の不変を確認できた場合に限り、UI Automationを暫定候補へ昇格できる。

## 13. ReboCap設定で触ってはいけないもの

- 肩Tracker置換/割当
- sensor/node割当
- AI Engine
- Ground IK / foot sliding関連
- Skeleton/body size
- Action/advanced/native calibration
- 6-axis、magnetic、anti-magnetic設定
- filter/frame buffer
- VR output node selectionそのもの
- origin/yaw、auto recenter、foot merge等の既存調整
- firmware/channel/transmit power

自動切替は最終的にも確認済みの単一native body-output switch以外を変更してはならない。

## 14. SteamVR上でReboCap Trackerがどう見えるか

- SteamVR driver名: `rebocap`
- OpenVR class: `TrackedDeviceClass_GenericTracker`（class 3）
- installed input profile roles: Waist、Chest、左右Knee、Ankle、Foot、Shoulder、Elbow、Wrist、None
- device pathはOpenVR標準の`/devices/<driver>/<device>`形式。
- historical local driver logで複数ReboCap GenericTracker登録を確認した。

serial、device固有値、raw logは公開文書へ保存していない。SteamVRを起動してのlive Pose、更新Hz、Output OFF時のdevice消失は未確認。

## 15. VRChat OSC Trackerの現行仕様

一次情報: <https://docs.vrchat.com/docs/osc-trackers>、<https://docs.vrchat.com/docs/osc-overview>、<https://docs.vrchat.com/docs/full-body-tracking>

- OSC over UDP、default受信先`127.0.0.1:9000`。launch optionで変更可。
- `/tracking/trackers/1..8/position` と `/rotation`。
- 各messageはfloat 3個の`(X,Y,Z)`。
- Positionはworld-space、Unity left-handed、`+Y` up、1.0 = 1m。
- Rotationはdegree Eulerで、VRChat内部適用順は`Z, X, Y`。
- 最大8追加Tracker: Hip、Chest、左右Foot、左右Knee、左右Elbow/Upper Arm。
- Upper Arm上に置く一つのtrackerがElbowとShoulderを同時制御。
- OSCを有効化し、VRChat Quick MenuでFBT calibrationが必要。
- optional head position/rotationで位置/yaw alignment可能。head rotationは単発とstreamで挙動が異なる。
- OSC slotは番号でありrole名ではない。実際のrole解釈は空間配置とFBT calibrationに依存する。

## 16. 8点構成が妥当か

**役割集合として妥当。** Hip、Chest、左右Knee、左右Foot、左右Upper Armは現行VRChatの最大8役割と一致する。

ただし「常時8点送信」を無条件採用しない。公式は、精度やdriftが悪い追加点より少数点の方がIK結果が良い場合があると明記している。PoCでは少なくともHip+Feet、Hip+Feet+Knees、Full 8を実avatarで比較し、各点を品質根拠付きで有効化する。

## 17. 既存OSSで参考になったもの

- [colasama/ReboSlime](https://github.com/colasama/ReboSlime) — MIT。ReboCap global quaternionをSlimeVR IMU packetへ渡す実例、joint選択、parent arrayの参考。
- [SlimeVR/SlimeVR-Server](https://github.com/SlimeVR/SlimeVR-Server) — MIT/Apache-2.0 dual。2026年も活発。latest-pose処理、tracker semantics、OSC/VMC/OpenVR統合、運用resilienceの参考。
- [gpsnmeajp/VirtualMotionTracker](https://github.com/gpsnmeajp/VirtualMotionTracker) — MIT。OSCからOpenVR GenericTrackerを作る構造の参考。
- [DenTechs/Virtual_Desktop_Body_Tracking_Configurator](https://github.com/DenTechs/Virtual_Desktop_Body_Tracking_Configurator) — MIT。Virtual Desktop emulated tracker設定がReboCapとは別surfaceであることの参考。
- [ValveSoftware/openvr](https://github.com/ValveSoftware/openvr) — BSD-3-Clause。GenericTracker、tracker role、device pathの正本。
- [VRChat OSC resources](https://github.com/vrchat-community/osc) と [vrc-oscquery-lib](https://github.com/vrchat-community/vrc-oscquery-lib) — MIT。packet/calibration exampleの参考。

## 18. 不採用にした方式と理由

- ReboSlime/SlimeVRを土台にする: ReboCapからrotationが届く実証には有用だが、別server/solver hopが増え、目的のmorphology retargetingとper-bone position生成を解決しない。
- Virtual Motion Trackerまたは独自OpenVR driver: VRChatが直接OSC Trackerを受けるため不要なdriver layerとなる。今回の明示的non-goalでもある。
- `config.data`直接書換え: protected settingsと同居するundocumented binary storeで、atomicity/concurrent write/復元安全性がない。
- driver削除/無効化やSteamVR再起動で切替: 侵襲性が高く、通常hand/HMD routeやlive sessionを壊し得る。
- 全8点の盲目的常時送信: VRChat公式注意に反し、精度不足点がIKを悪化させ得る。
- Quest IOBTを主入力にする: Project decisionに反し、coreを妨げる。Chest Yawの将来MONITOR研究だけに残す。

## 19. リバースエンジニアリングを行ったか

限定的に行った。対象はinstalled ReboCap executable/native module/OpenVR driverのexport・printable string、configuration field名、driver resources、local IPC名である。目的はVR Output切替と相互運用surfaceの確認だけ。

得た事実:

- ReboCapはWebSocket SDK、OpenVR driver、named pipeを使用する。
- UI/configにPC側VR output、VR output nodes、protected settingsに対応するfieldがある。
- driverはGenericTracker role profilesを持つ。
- 公開SDK外に、安全な外部向けoutput query/set interfaceは確認できなかった。

第三者decompiled source、binary、raw log、device IDはrepositoryへ追加していない。認証/課金/license回避は行っていない。

## 20. INTERFACE_CONTRACTの概要

[`INTERFACE_CONTRACT.md`](INTERFACE_CONTRACT.md)に三境界を定義した。

1. `ReboCap Input Adapter`: official WebSocket SDK、Pose schema、freshest-frame、disconnect時invalid化、未確認事項。
2. `SteamVR Native Output Controller`: read/disable/restore/crash recoveryに必要なcontract。ただし実control surface未確定のためfail closed。
3. `VRChat OSC Output`: UDP target、address/schema、coordinate/unit/rotation、内部slot順、alignment、FBT calibration、freshness、8点quality gate。

Virtual Desktop/Quest境界と、次のread-only PoC acceptance surfaceも明記した。

## 21. 未解決事項

- Installed buildでのlive SDK callback成功。
- timestamp unit/epoch、実測rate/jitter、axis、quaternion、hierarchy。
- multi-client接続可否。
- 物理肩Trackerの有無が各joint rotationへどう反映されるか。
- ReboCap native SteamVR outputの安全なquery/set/restore。
- Output OFF時にSteamVR deviceがどう消えるか。
- OSC origin/yaw alignmentの最適手順。
- SteamVR native trackerとOSC duplicate roleの実挙動。
- 実avatarでの8点対subset品質、packet rate、latency。
- SDK redistribution/bundle許諾。
- technology stack、MVP/v1境界、crash recovery設計。

## 22. Go / No-Go判定

- **Go:** read-only ReboCap Pose inspector。
- **Conditional Go after inspector:** offline/controlled target-skeleton transform specification and synthetic test poses。
- **No-Go:** production solver、常用OSC sender、GUI、Watcher、auto-start、Profile UI、Quest Chest Yaw AUTO、SteamVR driver、Virtual Controller、automatic native-output switching。

理由は、入力/出力のstatic contractは十分だが、live semanticsと安全な切替が受入面で未検証だから。

## 23. 次に作るべき最小PoC

数十行程度の一時的/read-only Pose inspector。製品codeとは分離し、次だけを行う。

1. ユーザーがReboCapを通常起動・既存手順でcalibrationした後、明示portへofficial SDK接続。
2. motionそのものを保存せず、joint count/name、callback count、inter-arrival統計、source/receive timestamp差、disconnect状態を表示。
3. T-poseと単純な既知回転でaxis、`wxyz`、global/local、parent hierarchyを確認。
4. ユーザーの肩Trackerを維持したまま、肩・上腕・肘rotationの応答を確認。
5. 切断時にPoseをinvalid化し、backlogを再生しないことを確認。
6. OSC送信、設定変更、UI操作、SteamVR起動/停止はしない。

## 24. git status

最終verification時点の予定状態:

```text
## main...origin/main
```

tracked/untracked changeなし。もし最終push失敗時はこの記述を成功扱いせず、実statusを報告する。

## 25. GitHubへのpush状態

Phase 0 baselineはpush済み。research commitとこのreport commitも最終検証後に`origin/main`へpushし、GitHub readbackでcommit一致とPublic状態を確認する。

## 26. 今回、製品本体の実装を始めていないこと

確認済み。今回の追加・変更はMarkdown文書のみ。

未着手:

- Retarget Solver / FK / IK
- live SDK adapter製品実装
- production OSC sender
- ReboCap連動GUI
- Watcher / auto-start
- Profile UI/persistence
- Native/Retarget automatic switching
- Quest Chest Yaw AUTO
- SteamVR Driver
- Virtual Controller

実環境へ行った変更はGitHub repository作成・Git commit/pushだけであり、ReboCap、SteamVR、Virtual Desktop、VRChat、Questの設定やprocess stateは変更していない。

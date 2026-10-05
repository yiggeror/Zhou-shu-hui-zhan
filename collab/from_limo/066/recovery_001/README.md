# C2 摄影云端恢复与验证

固定基线的摄影器已在另一套云环境用真实原片和真实选图运行。Q5 `[1437,1438)` 与缺口窗 `[1474,1485)` 共 **12 个不同的原生帧**，解码 BGR 像素 md5 全部等于已通过的 C2 交付。独立 R3 五帧测试也与缺口窗中的同五帧完全一致。

这份目录用于恢复执行和复核结果，不包含原片、核心代码副本、生成图或新的正式成片。

## 固定版本

- 代码与画表基线：[`73ff857dbb69945a36aa6eb0e751907b5358d48d`](https://github.com/yiggeror/Zhou-shu-hui-zhan/tree/73ff857dbb69945a36aa6eb0e751907b5358d48d)
- 原 C2 运行代码：`9a0bee044ca71b5379a7bb9beb761673e2fdaa12`
- 上游交接文档：[`anime/HANDOFF_compositing.md`，文档提交 29e9b423](https://github.com/yiggeror/Zhou-shu-hui-zhan/blob/29e9b423223b90937209438aea78ac783c9719a7/anime/HANDOFF_compositing.md)
- Python 包：`numpy==2.4.6`、`opencv-python-headless==5.0.0.93`，从官方 PyPI 安装；本目录 `requirements.txt` 固定相同版本。
- 本次实际云环境：Python 3.12.14、FFmpeg/ffprobe 7.1.5、Linux x86-64。
- 上游原环境报告：Python 3.11.15、FFmpeg 6.1.1、libdav1d 1.4.1、libx264 0.164.3108。未将这些系统版本全部复制到本次云环境；上述 12 帧的像素一致是实际测得，不能外推所有分支或完整视频字节都一致。

基线的 `action_window.py`、`layered.py`、`review_window.py`、`flowcam.py` 和完整 C2 画表与原运行逐字节相同。`frames.py` 只增加可移植的 `JJK_SRC` 路径入口；`build_051_sheets.py` 增加 D 草案，不改变 C2 表。`matte_key.py` 已补齐并核对 SHA256 `85ec2c1ba59d42d29ddbf9a834f7ce09228aa2c39c9d7d83390ce8ab775536c8`。

## 资产清单

`asset_manifest.json` 列出本次恢复树实际核验的 **69 项仓库文件**，逐项含相对路径、字节数、Git blob SHA1 与 SHA256，包括：

- 全部 48 张 C2 selected 原画；Q5 为 1671×941，其余为 1672×941
- 正式 C2 画表、甲方案对照画表、48 图 manifest
- 7 个摄影模块及新交接工具、依赖锁、74 帧期望像素 md5
- 原片参考 PNG n1437、n1480

原片须另外提供：SHA256 `9dae3a6eb8e1d420188d81a143a21b37400d2a5b37e768249eb26e37fdf62447`，AV1，2560×1440，yuv420p，bt709/tv，24 fps，3499 帧。原片逐帧编号从 0 开始，PTS=n/24，区间半开。

没有 B2、R4、C1 U4、C1 V6 的新画。这些空缺不应作为恢复时的生成或重试任务。

## 恢复和运行

在一个新的工作副本中检出固定基线，勿覆盖现有生产目录。以下 `$OUT` 必须指向一个尚不存在的新目录；摄影器本身会覆盖同名输出。

```sh
set -e
export CHECK=/absolute/path/to/this/recovery_directory
git clone https://github.com/yiggeror/Zhou-shu-hui-zhan.git work
cd work
git checkout 73ff857dbb69945a36aa6eb0e751907b5358d48d
python3 -m venv .venv
.venv/bin/python -m pip install --index-url https://pypi.org/simple --only-binary=:all: -r anime/requirements.txt
export JJK_SRC=/absolute/path/to/orig.mp4
export OUT=/absolute/path/to/new_c2_check
test ! -e "$OUT" && mkdir -p "$OUT"

# 原片与明确的两个原始参考帧
.venv/bin/python anime/source_check.py 1437 1480

# 顺序执行，不同时启动两个摄影进程
.venv/bin/python anime/subsheet.py anime/sheets/batchC2_1411_1485.json 1437 1438 "$OUT/q5.json"
.venv/bin/python anime/measure.py .venv/bin/python anime/action_window.py "$OUT/q5.json" "$OUT/q5"
.venv/bin/python anime/subsheet.py anime/sheets/batchC2_1411_1485.json 1474 1485 "$OUT/gaps.json"
.venv/bin/python anime/measure.py .venv/bin/python anime/action_window.py "$OUT/gaps.json" "$OUT/gaps"

# 本目录的小型独立检查器；CHECK 指向这份恢复目录
.venv/bin/python "$CHECK/verify_run.py" --repo "$PWD" --source "$JJK_SRC" \
  --window "1437:1438:$OUT/q5" --window "1474:1485:$OUT/gaps" \
  --report "$OUT/independent_check.json"
```

`JJK_SRC` 必须在 Python 导入 `frames` 之前设置，因为函数默认参数会在定义时绑定。工作目录必须是仓库根；画表素材路径相对此处。原生 PNG 保持 1672×941，主视频只复制最后一行到 1672×942，yuv420p/24 fps。

上游还提供 `anime/smoke_c2.py NEW_OUT` 的整合入口；本次实际执行的是上面相同的源校验、subsheet、measure 和 action_window 子命令。`--compare` 的甲方案及缺口对照工具在恢复树中，但本次未执行。

## 分窗和内存

每个持帧组必须完整包含在一个窗内。使用 `anime/subsheet.py`，它会拒绝切断持帧组。保留全部 `ref`、`grade_at`、素材路径、持帧分组、曝光和 encode 参数，不手改帧身份。

本次实测：Q5 13 秒/约 0.35 GiB；R3 五帧 68 秒/约 1.36 GiB；缺口窗 11 帧 70 秒/约 1.93 GiB。峰值为最大子进程 RSS，不是并发进程 RSS 之和；耗时受当时负载影响。

上游报告完整 74 帧峰值约 9.74 GiB、336 秒（其 measure.py 以 ru_maxrss/1024/1024 计算、标签写 GB，此处按实际计算注明 GiB），该完整运行**没有在本云环境复验**。约 9.7 GiB 的机器不能据此直接一次跑完整 C2。默认使用完整持帧组分窗、单进程顺序运行；更大窗先做资源预算。

## 实际验证结果

`test_summary.json` 给出机器可读数据与输出校验值。

- 12 个不同原生帧全部与 `anime/expected/C2_native_pixmd5.txt` 相同；包括 17 次曝光检查中的 5 帧重复覆盖
- 11 个匹配依赖环境的视频全部完整解码、帧数正确、24 fps，PTS 按整数时间基精确连续
- Q5 左补 1 列后调色，无拉伸；R3 使用 n1480 自身源帧配准和调色，1480=1481
- 1482 在调色后加右侧 0.49→0.66 黑幕；1483 黑场；1484 城市
- B3 提前用于 1476、1477，两帧像素相同，使用自己的源帧 1477 调色
- 原片 n1437/n1480 与仓库参考 PNG 最大像素差为 0；独立完整解码计数断言为 3499，其他源流规格也逐项断言通过
- 早期兼容环境 NumPy2.2.6/OpenCV4.12.0.88 的微小残差，在匹配两包后于所有重叠测试帧消失；该早期结果只作为对照保留

## 冻结母版与流拷贝接口

冻结 298 帧 `[1187,1485)` 的 SHA256 为 `d0b0f07cbc6f52451be496d09d7865557b573dbcc36f1c5c265da1247b2da853`。它只以只读输入进入拼接，永不放进摄影器重跑，不为适配编码器重编码旧母版。

已做一次纯技术兼容测试：冻结298 + 早期兼容环境R3五帧，流拷贝得303帧；SPS/PPS及47字节extradata相同，旧298逐帧RGB哈希和五帧后缀全部保留，PTS连续、完整解码通过。输出SHA256 `7d558194108f18696719075e6591c72d08b517ab460ba79615dfbb6823952e6e`。这是故意重复旧剧情的测试顺序，**不是正式续片，不用于交付**。

正式新片拼接必须再次用 `anime/join_verify.py` 对实际新输入核验；这一次测试不自动担保任何未来视频的SPS/PPS相容。若不相容，先停下查原因，不重编码冻结旧段来解决。

## 未验证范围

未实际运行完整74帧、所有分窗边界、layers/键底抠像、独立FX层、白光场、叠化、甲方案对照或新的D画面。未复建上游全部系统版本。上述未验项不能由这12帧的小窗结论代替。冻结段和聊天预览不得混用；预览是另存有损文件，不能参与正式拼接或作为原生对照。

## 发布前独立复核补记

独立复审核验了早期兼容环境的101项与11个视频；匹配包版本完成后，协调端另用 Pillow 解码并转BGR计算md5，复核17次输出/12个不同源帧，全部等于固定expected。随后实际执行本目录 verify_run.py（不是仅语法检查）：原片完整解码计数3499、流参数、两个实际窗口的native像素、主视频完整解码/整数PTS/帧数均PASS，退出码0；没有再次渲染。结果见 coordinator_verification.json。

其后上游08562d6增加manifest到画表CLI、状态级grade_at及源流参数断言；D新生产会明确固定其工具版本，不将新增工具混称已在73ff857测试。D当前范围仍[1485,1559)74帧；表D_34_exposure_table_002.csv在提交245690f，S06按n1532分4+5帧，共34态，覆盖完整。33态旧表只留历史。

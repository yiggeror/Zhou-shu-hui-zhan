# 摄影/合成可复现交接（C2 已通过版本）

回应 `collab/from_limo/057/msg_013`。本文件只写可执行的事实，不含任何凭据。

## 1. 固定基线

### 基线提交与差别

**代码基线**：`73ff857dbb69945a36aa6eb0e751907b5358d48d`，分支 `claude/loving-keller-1bvt18`。之后只加文档，不改代码。

C2 实际运行于 `9a0bee044ca71b5379a7bb9beb761673e2fdaa12`。到基线的差别：

| 文件 | 变化 | 对 C2 的影响 |
|---|---|---|
| `anime/frames.py` | 原片路径改为可用环境变量 `JJK_SRC` 指定，默认值不变 | 无 |
| `anime/build_051_sheets.py` | 新增 D 窗草案表 | C2 分支不变 |
| 新增工具 | 见下文 | 不进合成像素 |

- `anime/action_window.py`、`layered.py`、`review_window.py`、`flowcam.py` 与 9a0bee0 逐字节相同；
- C2 画表 `anime/sheets/batchC2_1411_1485.json` 与 9a0bee0 逐字节相同；
- run.json 里 `frames.py` 的哈希会从 `07a025a47fe894dc` 变为 `309a5abe3bd25183`，其余代码哈希不变。

### 在基线上重跑完整 C2 的实测（本机，见第 5 节）

- 74 帧原生 PNG 逐像素与交付版相同；
- `redraw_24fps_once.mp4` 的 sha256 仍为 `1e8a76f6c6c894871399007dc4db6c61212fd40817477729cd1283c1d4fe7e5b`；
- `side_by_side.mp4`、`slow_6fps.mp4`、`contact_sheet.jpg`、`sources.md` 也逐字节相同。

### 关键文件 sha256（基线 73ff857）

```
cb5943624fe1b08cbbede791c367269f9549d0af1b9d618f85c66a3335bde474 anime/action_window.py
ae9bdeb2e7b7d42bb3c2edbc1f7794814f2134e77612a00ee36759f161bd2c19 anime/layered.py
309a5abe3bd25183fdbad3c053b1298f2ad18674e33c7767f305d9119d7ff5e7 anime/frames.py
b58cf92d7bc71e6cbf2070a3c864df368a248e4b8e28598c2d60c52b872e401a anime/review_window.py
e1e9f7abaf7add97eccba40f3ff90167f9ebcc1e1f20ef1479d6d066fe5fa40d anime/flowcam.py
85ec2c1ba59d42d29ddbf9a834f7ce09228aa2c39c9d7d83390ce8ab775536c8 anime/matte_key.py
104f447d0f10b5a67541a213771b62e817097c4a3902bda43069d279fba5dd0e anime/build_051_sheets.py
04e9ceafc979bc9eacfed305eb019047415408e23cb2095440ae575fa4026b88 anime/subsheet.py
96e5d9e8d89477160b526373bb475203d747c1d42910138b7ba210c7c5b1c27e anime/measure.py
12a3d39ae41513687e9e12d5626863b1954a2e372b4605afd379e08280a4dca8 anime/gap_compare.py
56a7ffc1c18fab679fb05b012aa8331bec92121836217e1ba1cc22fef818aaf8 anime/pixmd5.py
250c1886e9e2baa46b6e411ab6a2e99170b425b4b4d91fca664c994b0f59d8fb anime/join_verify.py
09c45dbc29bf90ddb67bb15b752c09154be1b20b2bd27f9891ab7b9fb847ca5c anime/source_check.py
09c5a43c3581ff7efd8d00ecbe35255a2f6dbbd3511474d40dc1f6ca5f21773d anime/smoke_c2.py
efa9c27fa0c0f790443aae54aa585ec2d6b01e0a20715c9f8ce0ef378699512b anime/requirements.txt
80a8863e80b7f8b480151265fe1b90c53ab148005fc410d9fa4278342dca2390 anime/expected/C2_native_pixmd5.txt
79157332564f1198a95b5b936bfd747c8ffb367d8e2797dd1a56105b2fa15d15 anime/sheets/batchC2_1411_1485.json
294d993241d671d626e008e21b06d2622c7473cca6b984a6aac9f62ae227a630 anime/sheets/batchC2_planA_1475_1479.json
95bfe639064b141699c9157e687cc8815728082a594061595fbd23df262564e3 collab/from_limo/057/manifest_C2_available048.json
```

合成实际导入的本地模块：`action_window`、`frames`、`layered`、`review_window`、`flowcam`、`matte_key`，全部在 `anime/`。

## 2. 环境与依赖（C2 实际版本）

| 项 | 版本 |
|---|---|
| 系统 | Ubuntu 24.04.4 LTS，x86-64，4 核，内存 15 GB |
| Python | 3.11.15 |
| Python 包 | `numpy==2.4.6`、`opencv-python-headless==5.0.0.93`；只导入这两个第三方包，没有 scipy、Pillow、skimage |
| ffmpeg / ffprobe | 6.1.1（Ubuntu 包 7:6.1.1-3ubuntu5） |
| AV1 解码 | libdav1d 1.4.1（ffmpeg 自动选它解原片） |
| 编码 | libx264 0.164.3108 |
| 其他 | git（run.json 记录提交号） |

安装：

```
apt-get install -y ffmpeg git
python3 -m pip install -r anime/requirements.txt
```

不需要字体文件（标签用 OpenCV 内置字体）、GPU、密钥或网络。

**唯一必须设置的环境变量**：`JJK_SRC=/你的路径/原片.mp4`。不设时用作者机器上的默认路径，你那边会找不到文件。

## 3. 从干净检出到运行

```
git clone <仓库> work && cd work
git checkout 73ff857dbb69945a36aa6eb0e751907b5358d48d    # 或之后只加文档的提交
python3 -m pip install -r anime/requirements.txt
export JJK_SRC=/data/orig.mp4                            # 原片
python3 anime/source_check.py                            # 第 7 节
```

- **工作目录必须是仓库根**：画表里的素材路径都相对仓库根，如 `collab/from_limo/057/batchC2_P2/selected/Q5_n1437.png`；run.json 也在根目录下执行 `git rev-parse HEAD`；
- 不需要设 PYTHONPATH，脚本自己把 `anime/` 加进路径；
- 临时文件只在系统临时目录（Python `tempfile`）；
- **输出目录**：命令行第二个参数，请每次用一个全新的空目录。合成器会覆盖同名文件，不会检查目录是否已存在，所以不要指向任何 `collab/to_limo/...` 交付目录。

## 4. 低资源验跑（真实画、同一代码路径）

```
JJK_SRC=/data/orig.mp4 python3 anime/smoke_c2.py /tmp/smoke_c2_new --compare
```

依次做：
1. 原片校验；
2. 从 C2 画表切出两个小窗，交给同一个 `action_window.py`：
   - `[1437,1438)`：Q5 左补 1 列；
   - `[1474,1485)`：L9；B1 只占 1475；B3 提前持 [1476,1478)；R1、R2；R3 持 [1480,1483)，1482 加黑幕；1483 纯黑；1484 Z1；
3. 把 12 帧原生像素的 md5 与 `anime/expected/C2_native_pixmd5.txt` 比对；
4. `--compare` 另跑甲方案 `anime/sheets/batchC2_planA_1475_1479.json`，并出两份缺口对照（jpg + 原速循环 + 4 fps 慢放）。

本机实测：12 帧全部与交付版逐像素相同，结果 PASS。

| 窗口 | 耗时 | 内存峰值 |
|---|---|---|
| Q5 | 17 s | 0.34 GB |
| 缺口窗 | 51 s | 1.72 GB |
| 甲方案 | 29 s | 1.20 GB |

**切小窗的规则**：任一持帧组必须整组在窗内，`anime/subsheet.py` 会检查并拒绝切断。原因是持帧组的调色、配准和快门都按整组拟合。

用这条规则切出的小窗与整批运行逐像素相同（上面 12 帧已实测）。

## 5. 完整 C2 生产命令与产物

```
JJK_SRC=/data/orig.mp4 python3 anime/measure.py \
    python3 anime/action_window.py anime/sheets/batchC2_1411_1485.json /tmp/c2_full_new
```

**画表来源**：`python3 anime/build_051_sheets.py C2` 按 `collab/from_limo/057/manifest_C2_available048.json` 和 `C2_EXTEND`（B2/R4 两处替代）生成。生成结果与仓库里的 `batchC2_1411_1485.json` 相同。重跑时直接用仓库里的画表即可。

**输出目录内容**：

| 文件 | 内容 |
|---|---|
| `R_n1411.png … R_n1484.png` | 74 张原生 1672×941，8 位 BGR |
| `redraw_24fps_once.mp4` | 交付像素：1672×942（只复制最后一行）、yuv420p、24 fps、74 帧、3.083333 s；libx264 CRF16 slow，`-sws_flags accurate_rnd+full_chroma_int`，取自画表的 `encode` |
| `side_by_side.mp4`、`slow_6fps.mp4` | 对照用，重编码，不是交付像素 |
| `contact_sheet.jpg`、`edge_fill_sheet.jpg`、`holds_diag_sheet.jpg`、`holds_diag_6fps.mp4` | 检查图 |
| `sources.md` | 逐帧来源、调色参数、配准、补边、近似说明 |
| `run.json` | 画表全文、代码哈希、git 提交、快门表 |

**本机实测**：336 s；内存峰值 9.74 GB（单进程）。在 16 GB 机器上一次只跑一个完整批次；小窗可以与它并行。

**两缺口对照片**：用 `anime/gap_compare.py`，命令写在 `anime/smoke_c2.py` 末尾。原生帧来自哪次运行都一样，因为逐像素相同。

**哪些可以拆开跑**：
- 可以：按第 4 节规则切成若干小窗分别跑，像素相同；
- 不可以：改变某帧的画、源帧（ref / grade_at）、曝光区间或持帧分组。这些都写死在画表里，拆跑时不要手改。

## 6. 校验值与跨版本差异

| 项 | 要求 |
|---|---|
| 原生帧 | 比解码后的像素 md5（`anime/pixmd5.py DIR`），不比 PNG 文件 sha（压缩字节可能不同）。全部 74 帧的期望值在 `anime/expected/C2_native_pixmd5.txt` |
| 完整 C2 视频 | sha256 `1e8a76f6c6c894871399007dc4db6c61212fd40817477729cd1283c1d4fe7e5b`（第 2 节版本下实测一致） |

**换版本时可能出现的差异**：

- **ffmpeg / swscale 不同**：原片 AV1 解码本身是规范的，但转 bgr24 这一步随 swscale 版本可能差 ±1 级。先跑 `source_check.py`：参考 PNG 是在本机解码导出的，最大差应为 0；不为 0 时，后面所有像素都可能有 1 级左右的差。
- **OpenCV / NumPy 不同**：缩放（INTER_AREA）、高斯模糊、特征匹配 + RANSAC 配准都可能变。持帧画的配准结果逐组写在 `sources.md`（例：`registered to n1480: 290 inliers, … scale 0.9986, rotation -0.01 deg, centre shift (+0.1, -0.2) px`）。先比这些数，再比像素。
- **libx264 / ffmpeg 不同**：视频字节一定不同，只能比原生 PNG 像素和解码后的观感。

**判定规则**：

| 情形 | 要求 |
|---|---|
| 同版本 | 原生像素逐一相同，视频 sha 相同 |
| 不同版本 | `sources.md` 里每帧的画、源帧、曝光、持帧分组、补边、黑幕、黑场行必须逐行相同；配准差 ≤ 0.1 px / 0.001 倍；像素只容许量化级差（均差 < 0.5 级） |

错帧、换画、构图或位置偏移，不能用容差放过。

## 7. 原片与帧号

- **原片**：sha256 `9dae3a6eb8e1d420188d81a143a21b37400d2a5b37e768249eb26e37fdf62447`；AV1，2560×1440，yuv420p（bt709，tv 范围），24 fps，3499 帧；
- **帧号约定**：n 是零基解码帧号，PTS = n/24，区间半开 [a,b)。`frames.frames(a,b)` 用 `select=between(n,a,b-1)` 一次解码，并断言帧数；
- **核验**：`JJK_SRC=… python3 anime/source_check.py [n …]`。检查 sha256、流参数、帧数；再把解码帧与仓库里的参考 PNG（`collab/to_limo/*_ref/n<n>.png`，同一约定导出）逐像素比较；有差时报告前后相邻帧的差，用来发现偏一帧。本机：8 个抽样帧最大差 0，PASS；
- **单帧导出**：`ffmpeg -i "$JJK_SRC" -vf "select=eq(n\,1480)" -vsync 0 -frames:v 1 n1480.png`。

## 8. C2 固定参数（全部在画表 JSON 里，可直接读）

### 素材与曝光

| 项 | 内容 |
|---|---|
| 素材 | 48 张，路径逐张取自 `manifest_C2_available048.json`；47 张原生 1672×941，Q5 原生 1671×941；没有一张被缩放 |
| 曝光 | 30 帧单次；18 组离散持帧共 43 帧，其中 25 个重复曝光；1 帧合成黑场（1483） |
| 持帧 | 不加运镜（`camera_only: none`，`zoom 1.0`，`light: fixed`），每组在自己的源帧调色（`grade_at [src, src]`） |

### 调色（画表 `grade`）

每张画：
- 一条亮度曲线：与原片同帧做分布匹配，保持色比，强度 1.0，`sigma 4`；
- 一个全局白平衡，限 ±10%；
- 白芯保护：最小通道 0.85→0.97，白平衡渐退到白；
- 亮像素保护（`keep_highlights [0.7, 0.9]`）：按最亮通道 0.7→0.9 平滑过渡，曲线回到原样、白平衡关闭。

按 review_002 订正：这道门限不认语义，斩线、部分普通白袍和白皮肤都会被保护。L 组 +50 级左右的差，主要来自持帧把亮相位延到原片已暗下的帧（如 1464→1465），不只是同一曝光被提亮。

### 配准

持帧画先用特征匹配做一次相似变换，对到源帧取景；数值写在 `sources.md`。之后不再运镜。补边颜色 ≤ 0.8%，按每边抽样深度记录，不是所有角落的严格上限。

### Q5 补列

`pad_to_frame`：宽高差 0–4 像素时只补边、不缩放。补在边缘列与相邻列平均差较小的一侧，用复制边缘列的方式。Q5 补左侧 1 列（左 1.01、右 2.34 级）。记录在 `sources.md` 该帧的 `PADDED TO THE FRAMING`。

### 1482 黑幕

画表 `frame_extra {1482: {wipe: {from: right, x0: 0.49, x1: 0.66}}}`。

- 公式：x = (列 + 0.5) / 宽；k = clip((x − 0.49) / 0.17, 0, 1)；R ×= 1 − k²(3 − 2k)；
- 顺序：载入画 → 补边 → 配准 → 调色 → 叠化（C2 无）→ 黑幕 → 白光场（C2 无）→ 最后一次量化到 8 位（`clip(x·255 + 0.5)`）。

### 1483 黑场

画表 `{"black": true}`，纯黑，不调色。原片 99.2% 像素 ≤ 5/255，是近黑近似，不是说原片数学全零。

### 两处无图态

都没有新生成图：
- **B2（n1476）**：B3 提前一帧，持 [1476,1478)；
- **R4（n1482）**：R3 持到 1482，加合成黑幕。

`sources.md` 对应帧都标 PROVISIONAL 和"已获准画面的近似，不是新画"。数量是 48 张选图，不是 50。

## 9. 冻结母版与拼接

| 段 | 帧 | 路径 | sha256 |
|---|---|---|---|
| **298 [1187,1485)（当前）** | 298 | `collab/to_limo/065_files/join_298/redraw_298frames_24fps_once.mp4` | `d0b0f07cbc6f52451be496d09d7865557b573dbcc36f1c5c265da1247b2da853` |
| 224 [1187,1411) | 224 | `collab/to_limo/061_files/join_224/redraw_224frames_24fps_once.mp4` | `87a03a42e525fbfbe7f306f43c3e1d7b06f392676ba3f46886d78040f77fb0e7` |
| 170 [1187,1357) | 170 | `collab/to_limo/059_files/join_170/redraw_170frames_24fps_once.mp4` | `befbd40d1049b91bc65d39ae197d8bbcffb6654cf7890f8996f94e665b3954ea` |
| 106 [1187,1293) | 106 | `collab/to_limo/054_files/join_106/redraw_106frames_24fps_once.mp4` | `3245a3e251f00a4364f286fda5cae4a3e096a22be99056b2b6cbc32f11a40a01` |
| 首次茈 [1187,1202) | 15 | `collab/to_limo/050_files/hollow_purple_1187_1202_v2/redraw_24fps_once.mp4` | `87c7cbe90157871bcc3ff8e52fb52b445e271448e3f885bda8e23e41669a03e3` |
| 近战 [1248,1293) | 45 | `collab/to_limo/044_files/join_45/redraw_45frames_24fps_once.mp4` | `8ded5fb7515b236568e18437d7ad1ae2d2f7ab8bdf53112416769d97b392be77` |

**拼接加核验**（流拷贝，moov 前置，不重编码；目标已存在时拒绝写入）：

```
python3 anime/join_verify.py /tmp/new/redraw_NNNframes_24fps_once.mp4 \
    collab/to_limo/065_files/join_298/redraw_298frames_24fps_once.mp4 /tmp/d_full_new/redraw_24fps_once.mp4
```

它会核：
- 所有输入与输出的 SPS/PPS 相同；
- 解码 RGB 逐帧 md5（ffmpeg framemd5，rgb24）：输入依次相连等于输出；
- PTS 从 0 起，每步 1/24；
- 画幅、帧数、时长与输出 sha256。

结果写入 `join_check.md` 和各段的 md5 清单，末行 PASS/FAIL。

本机复验：用 224 + C2 74 重做 298，输出 sha256 正是 `d0b0f07c…`，逐字节等于冻结母版。

只核不拼：`python3 anime/join_verify.py --verify-only 已拼.mp4 段1.mp4 段2.mp4`。

**冻结段规则**：冻结段只以文件进入拼接，永不放进合成器重跑。它们的像素来自当时的代码和画表；即使现在重跑能得到相同结果，也只用冻结文件。

**SPS/PPS 前提**：新段必须用同样的编码设置（画表 `encode` + 合成器内的 libx264 参数），否则 SPS/PPS 不同，流拷贝拼接不成立。核验会报 DIFFERENT。

## 10. 聊天预览（另存，不作冻结输入）

```
ffmpeg -n -i collab/to_limo/065_files/join_298/redraw_298frames_24fps_once.mp4 -map 0:v:0 \
    -c:v libx264 -preset slow -crf 28 -pix_fmt yuv420p -movflags +faststart /tmp/preview/298_preview.mp4
ffprobe -v error -count_frames -select_streams v:0 \
    -show_entries stream=width,height,r_frame_rate,nb_read_frames,duration -of compact=p=0 /tmp/preview/298_preview.mp4
```

- `-n` 不覆盖任何已有文件；
- 不裁片、不降帧、不改画幅：应得 1672×942、24/1、298 帧、12.416667 s；
- 本机实测：约 6.3 MB，母版 sha256 前后不变；
- 体积不够小时只调 crf；
- 预览是重编码，像素不同于母版，不能拿来拼接或冻结，也不能说"与母版一致"。

## 11. 待办、残差与坑

### 已知残差（C2，review_002 已记）

- B2/R4 两处是已获准画面的有限动画近似；
- T1b（n1455）比前后帧硬，属低至中等精修残差；
- 早期楼面、云层和部分墨线偏硬；
- L 组亮峰持帧延长；
- 1476 比原片亮、碎得早一步。

### 容易踩的坑

- 不在仓库根运行，素材路径会找不到；
- 输出目录沿用旧目录，会覆盖旧产物；
- 一台 16 GB 机器上同时跑两个完整批次，会被系统杀掉（返回码 137）；
- 切小窗切断持帧组（subsheet 会拒绝）；
- 用 PNG 文件 sha 比像素，应改用 pixmd5；
- 新批次忘了画表里的 `encode.sws_flags`，白场会解成 251/253/250 一类的值；`build_051_sheets.py` 生成的画表都带这项。

### 尚未独立验证的机制

- 跨 OpenCV 版本时配准是否一致（本机只验过同版本）；
- 白光场、叠化在 C2 没有用到，本次没有重验（A 批用过，已冻结）；
- `review_window.original` 会优先读 `collab/to_limo/*_ref` 下的参考 PNG。C2 路径不用它，但请勿改动这些参考图。

### 出错先看哪里

1. 合成器标准输出：每个持帧组一行耗时，`frames written` 为结束标志；
2. `sources.md` 的对应帧；
3. `run.json` 的代码哈希和提交号；
4. `measure.py` 的返回码和内存峰值。

**替身与废案**：`*_standin*`、甲方案、`066_files/standin_test` 都只是对照，不是正式输入。正式输入只有画表 JSON 里写的路径。

## 12. 下一段 D（草案，未开图）

- 我的建议在 `collab/to_limo/066_D窗建议_镜头58-61_1485-1560_35张.md`；
- 参考帧 `collab/to_limo/066_ref/n1484…n1560.png`；
- 逐帧图 `collab/to_limo/066_files/`；
- 草案表在 `anime/build_051_sheets.py` 的 `D`；
- 替身测试在 `066_files/standin_test/`。

**边界未决**：
- 你方在核 [1485,1559)；
- 我方 1559 是"宿傩剪影 + 神龛屋角 + 红横光"的过渡帧，可放 D 末，也可放下一窗开头。

两边对齐后再锁表；锁表前不再为草案做摄影。

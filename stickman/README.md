# 火柴人代码动画（新宿决战）

全部用代码绘制。纸色底，黑色火柴人，颜色只来自咒力特效和眼睛。

## 试点
`output/pilot/` 里是第一版试点：1080p60，15.9 秒，无音轨，按原版（145.8 秒版）的时间走：

| 段落 | 原版时间 | 内容 |
|---|---|---|
| 开头 | 3.04–6.13 秒 | 青拳、红拳冲向镜头，斜俯拍对拳，片名 |
| 近身打斗 | 51.75–56.54 秒 | 冲刺、飞踢对拳、格挡、红拳、蓄力、青拳、连打、横扫闪避（原版镜头 42–49） |
| 虚式茈 | 128.33–136.33 秒 | 赫与苍从两侧汇合、宿傩抬臂、五条逆光特写、紫色爆炸（原版镜头 121–125） |

`closeup_board.png` 是脸部和眼睛特写的方案图。

## 做法
- `engine/`：
  - `rig.py`：三维骨架。手脚用两节反向运动学求肘、膝，伸直时平滑过渡，不会突然弹直。每个人身上叠加细微、连续的呼吸和重心晃动，画面里没有完全静止的帧。
  - `anim.py`：关键帧曲线、缓动、命中定格（原地定格，不改变总时长）。
  - `figure.py`：人物整体用一种墨色画，没有描边，所以关节和交叠处不会出现缝隙。头是实心圆，眼睛在头里发光；近景时眼睛会画出瞳孔和眼睑。快速动作用连成一片的扫掠残影。
  - `camera.py`：三维机位、推拉、震屏，以及轻微的手持漂移。
  - `env.py`：纸色底上的浅铅笔线地面和建筑。
  - `fx.py`：咒力火焰（跟着拳头，拖尾，停下后收回）、命中闪光和速度线、冲击波、火花、闪电、赫/苍/茈、双色冲击帧。
  - `comp.py`：合成，高光平滑压缩，不会过曝成死白。
- `films/`：逐镜头的动作和镜头设计。`p_open.py`、`p_fight.py`、`p_purple.py`，`pilot.py` 把三段串起来。
- `render.py`：每 30 帧一段渲染，可以断点续跑，多进程。

## 渲染
```
pip install numpy opencv-python-headless pillow scipy skia-python   # skia 还需要系统库 libegl1
python3 render.py pilot OUT_DIR --workers 4          # 成片在 OUT_DIR/pilot.mp4
python3 render.py pilot OUT_DIR --stills 52.25,55.6  # 只出指定时刻（原版时间）的静帧
STICK_THEME=black python3 render.py pilot OUT_DIR    # 黑底白人版本
python3 make_board.py closeup_board.png              # 特写方案图
```

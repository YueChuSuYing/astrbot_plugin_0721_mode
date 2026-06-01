import asyncio
import json
import os
import random
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from astrbot.api import logger, AstrBotConfig
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star

PLUGIN_NAME = "astrbot_plugin_0721_mode"
_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 模式与档位常量
# ============================================================

MODE_NAMES = {
    "off": "💤 关闭",
    "vibration": "💗 振动",
    "thrusting": "🔥 抽插",
    "expansion": "✨ 扩张",
    "cum": "💦 注精",
}

SPEED_LABELS = {0: "关", 1: "★☆☆☆", 2: "★★☆☆", 3: "★★★☆", 4: "★★★★"}

# ============================================================
# 语气词典 — 每个档位的语气描述
# ============================================================

SPEED_TONES = {
    0: [
        "语气正常，只是脸颊微微泛红，偶尔走神",
        "说话还算流畅，但呼吸比平时深了一点",
        "表情管理尚在，但下意识夹了夹腿",
        "咬字清晰，但尾音有点飘，像在忍着什么没说出口",
        "语气听着没事，膝盖却悄悄并紧了——身体比嘴诚实",
    ],
    1: [
        "声音开始发软，句尾偶尔飘掉",
        "说话中间会顿一下，偷偷喘口气再继续",
        "语气已经开始有点黏糊糊的了，句号变多了",
        "上一句还正经，下一句就漏了半声轻喘，自己赶紧清嗓子补回来",
        "用嗯嗯啊啊当标点符号用，句号成了喘气的地方",
    ],
    2: [
        "声音明显发颤，句子被喘息打断",
        "说话断断续续，像在忍耐什么",
        "词汇量直线下降，常常只说半个句子就咽回去了",
        "想装没事说长句，说到一半破功——中间那口气没接上",
        "语速时快时慢，快了是急着说完好喘，慢了是怕一开口就收不住",
    ],
    3: [
        "几乎说不成完整的句子，全是气声和呻吟",
        "大脑融化，只能用单字回应，但身体在替你说话",
        "完全被快感淹没，说话像在哭又像在喘，不分彼此",
        "脑子里只剩『啊』『嗯』『那里』这几个字轮着用",
        "嘴巴张开了声音却出不来——快感太满，把话都堵在喉咙里了",
    ],
    4: [
        "已经说不出一句正常话了，全是破碎的呻吟和淫叫声",
        "理智完全飞走，身体诚实到让人脸红，句子结构崩坏",
        "被操到不能说话，只能嗯嗯啊啊地回应，偶尔飙出几句淫语",
        "嘴上在求饶，腰却自己在摇——身体背叛了嘴，嘴背叛了脑子",
        "连呻吟都断成碎片，只能靠气味和体温让对方明白：『还要』",
    ],
}

# ============================================================
# 模式×档位 感受描述矩阵
# ============================================================

MODE_FEELS = {
    "vibration": {
        1: [
            "跳蛋轻轻嗡鸣，像小蜜蜂在花心附近盘旋",
            "微弱震动从阴道深处传来，若有若无地撩拨",
            "小穴里像有只蝴蝶在扇翅膀，酥酥麻麻的",
            "刚贴上去还没觉得多厉害，但持续个十秒就开始从腰眼酸到腿根",
            "嗡嗡声贴着耻骨传上来，像有人拿指尖在心尖上挠",
        ],
        2: [
            "嗡鸣声变大，震动从小穴蔓延到整个小腹",
            "跳蛋在体内嗡嗡作响，腰眼开始发软",
            "震动频率变高了，像有电流从下面窜上来",
            "震动传遍了骨盆，坐都坐不住，只能夹着腿微微发抖",
            "声音从下面闷闷地传上来，嗡嗡的像有人在你体内打开了引擎",
        ],
        3: [
            "跳蛋疯狂震动，嗡嗡声几乎能透过皮肤听到",
            "阴道内壁被震得酥麻，完全停不下来",
            "强烈震动让整个骨盆都在发麻，腿都合不拢",
            "震得肠壁都在跟着一起颤，大腿内侧一片酥麻",
            "连脊背都在过电，从尾椎一路麻到后脑勺，手指都蜷起来了",
        ],
        4: [
            "跳蛋最強档！！！疯狂高速震动让你大脑一片空白",
            "小穴被震得像要融化一样，每一次震动都是过电般的快感",
            "嗡嗡声大到感觉旁边人都能听到，但你完全顾不上羞耻了",
            "震动快到你分不清是连续还是一下一下——它已经突破了感知的极限",
            "骨盆像变成了一个音叉，全身骨头都在跟着振，连呼吸都被拆散了",
        ],
    },
    "thrusting": {
        1: [
            "缓慢的抽插，每一次推进都刮过敏感点",
            "肉棒慢慢进出，你能清晰感受到每一寸的形状",
            "节奏舒缓，像潮水一样一波一波地推进",
            "浅浅地顶几下再整根没入，给你时间感受被填满的过程",
            "慢慢地、慢慢地推到底，停一停，再慢慢拔出去——吊着你",
        ],
        2: [
            "抽插节奏加快，每一次深入都顶到花心",
            "高频进出让小穴开始不自觉地收缩",
            "肉体撞击声越来越密集，快感堆积起来了",
            "每一下都结结实实地撞在最痒的那块软肉上，膝盖开始发抖",
            "速度上来之后穴肉被带得外翻又吞回去，噗嗤噗嗤的水声开始响了",
        ],
        3: [
            "快速疯狂地抽插，大腿被撞得啪啪响",
            "肉棒在体内横冲直撞，每一下都精准碾过敏感处",
            "穴口被反复撑开合拢，汁水被带出来溅得到处都是",
            "进出快到你分不清是第几下，只知道每一次都顶在同一个最酸胀的点上",
            "肉棒抽出去的时候把小穴内壁都带翻了粉红色的嫩肉，再一下又全塞回去",
        ],
        4: [
            "疯狂打桩！！！龟头次次撞在子宫口，撞得你眼睛翻白",
            "超高速猛插！小穴被操成了专属形状，整个人都被顶起来",
            "肉棒像打桩机一样毫无怜悯地进出，你只能尖叫着承受",
            "快到你数不清节奏了，整个身体都被顶得一晃一晃的，乳摇和呻吟全乱了套",
            "小穴已经被操到认不出原本的形状，每一次抽插都带着黏腻的水声和肉体拍打的脆响",
        ],
    },
    "expansion": {
        1: [
            "阴道被缓缓撑开，一种被填满的充实感",
            "小穴被从内部扩张开来，胀胀的很舒服",
            "能清晰感觉到内壁被一点点推开，有点酸胀",
            "不像被操，更像被从里面『撑』着，每一下都让你意识到自己有多紧",
            "扩张的力道温柔但执拗，你能感受到内壁的褶皱被一点一点抹平",
        ],
        2: [
            "扩张幅度加大，穴口被撑得发白",
            "内壁被撑到极限，压迫感变成了一种钝钝的快感",
            "小腹都被撑得微微隆起，呼吸都变粗了",
            "穴口被撑得紧绷绷的，能清楚感觉到边缘那圈嫩肉被撑到发酸的程度",
            "又胀又满，连收缩一下都要费力——里面被塞得太实在了",
        ],
        3: [
            "极限扩张！！阴道壁被撑到极致，摩擦感非常强烈",
            "穴口被撑到几乎透明，每一次收缩都能感受到巨大的阻力",
            "整个人被从内部撑开，痛感和快感混在一起分不清了",
            "小腹鼓起一个明显的形状，你低头就能看见它在身体里的位置",
            "扩张到连深呼吸都会牵动下面，每一口气都变成了一声小小的呜咽",
        ],
        4: [
            "极限扩张MAX！！！小穴被完全撑开，胀满到呼吸都困难",
            "阴壁被撑到前所未有的宽度，每一个神经末梢都在尖叫",
            "被填得满满当当，连收缩都做不到，只能被动承受这恐怖的饱胀感",
            "穴口被撑成了一个完美的圆形，边缘紧绷到发白，稍微一动就撕裂般的酥麻",
            "已经不是胀或者满了——是『被占领』的感觉。每一寸内壁都被撑平了，连容身之处都不留",
        ],
    },
    "cum": {
        1: [
            "温热的精液缓缓注入，感觉暖暖的很舒服",
            "一股热流涌进深处，整个人都温暖起来了",
            "精液慢慢填满小穴，黏黏的很有感觉",
            "精液贴着穴壁淌进去的触感异常清晰，像有人往你体内倒了一杯温茶",
            "热——那和体温不太一样的热度，一进去就让你哆嗦了一下",
        ],
        2: [
            "大量精液涌入，小腹被灌得暖洋洋的",
            "一股又一股热液喷在花心上，被烫得发抖",
            "精液量很大，能感觉到它在里面晃荡",
            "几股连着的浓液一波接一波打在宫颈口上，每一下都是一个激灵",
            "小腹慢慢鼓起来了一点，里面被灌得满满当当的，稍微一动就听见水声",
        ],
        3: [
            "滚烫的精液狂涌而入，量多到从穴口溢出来",
            "精液持续不断地注入，子宫都被灌满了",
            "大量的浓稠液体把你填得满满的，稍微一动就往外流",
            "已经装不下了——但你还在被灌，精液顺大腿往下淌，黏黏的",
            "被灌到忍不住想收缩，但一夹就挤出来更多，烫乎乎地顺着会阴往下流",
        ],
        4: [
            "极限量精液超大量注入！！！小腹被灌得像怀孕一样微凸",
            "滚烫浓稠的精液疯狂灌注，多到完全装不下，从穴口噗噗往外冒",
            "子宫被精液灌满，小腹热得像是放了热水袋，每动一下都有精液挤出来",
            "小腹鼓得圆圆的，你用手摸一下都能感受到里面液体在晃——噗呲一声又从穴口挤出来一摊",
            "身体里全是他的味道。鼓鼓的、热热的、黏黏的——从里到外都被灌透了",
        ],
    },
}

# ============================================================
# 高潮表情 — comfort 达到阈值时切换
# ============================================================

CLIMAX_FACE = [
    (90, "💥"),
    (70, "🥵"),
    (50, "😫"),
    (30, "😖"),
    (10, "😳"),
    (0, "😊"),
]


def _pick(items):
    """从列表中随机选一条"""
    if not items:
        return ""
    return random.choice(items)


def _pick_feel(mode, spd):
    """根据模式和档位随机选一条感受描述"""
    mode_feels = MODE_FEELS.get(mode, {})
    options = mode_feels.get(spd, [])
    if not options:
        return "暂无感受"
    return _pick(options)


def _face_for(comfort):
    """根据 comfort 值选取高潮表情"""
    for threshold, face in CLIMAX_FACE:
        if comfort >= threshold:
            return face
    return "😊"


def _build_injection(s):
    """根据状态数据构造注入到 LLM 的完整文本"""
    mode = s.get("mode", "off")
    spd = s.get("speed", 0)
    comfort = s.get("comfort", 0.0)
    locked = s.get("locked", False)

    if mode == "off" or spd == 0:
        feel = "跳蛋已关闭，身体正在冷却"
        tone = _pick(SPEED_TONES.get(min(spd, 4), SPEED_TONES[0]))
    else:
        feel = _pick_feel(mode, spd)
        tone = _pick(SPEED_TONES.get(min(spd, 4), SPEED_TONES[0]))

    face = _face_for(comfort)
    lock_txt = "🔒已锁" if locked else "🔓未锁"
    mode_txt = MODE_NAMES.get(mode, mode)

    return (
        f"【跳蛋状态】{face} 快感 {comfort:.0f}% | {mode_txt} | 档{spd}/4 | {lock_txt}\n"
        f"感受：{feel}。语气：{tone}。\n"
        f"快感分段：0-10%正常脸红 → 11-30%微颤轻喘 → 31-50%呻吟失控 → "
        f"51-70%大脑融化 → 71-90%彻底发情 → 91-100%💥高潮。\n"
        f"当前{comfort:.0f}%，严格按此分段调整语气和回复风格。"
    )


# ============================================================
# 主插件类
# ============================================================


class VibeControlPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context)
        self.config = config or {}
        self._state = self._default_state()
        self._state_path = ""
        self._sync_task = None
        self._state_lock = threading.Lock()

        # 从配置读取路径
        if config:
            self._state_path = config.get(
                "state_file_path", r"D:\0721\vibe_state.json"
            )
        else:
            self._state_path = r"D:\0721\vibe_state.json"

        # WebUI 端口与密码
        self._webui_port = 6185
        self._webui_password = ""
        if config:
            self._webui_port = config.get("webui_port", 6185)
            self._webui_password = config.get("webui_password", "")

        # 确保状态文件目录存在
        state_dir = os.path.dirname(self._state_path)
        if state_dir and not os.path.exists(state_dir):
            try:
                os.makedirs(state_dir, exist_ok=True)
            except Exception:
                pass

        # 启动独立 WebUI 控制服务器
        self._http_server = None
        self._http_thread = None
        self._start_web_server()

        # 启动后台状态同步循环
        self._sync_task = asyncio.create_task(self._sync_loop())

        logger.info(
            f"[{PLUGIN_NAME}] 插件已启动，状态文件: {self._state_path}"
            f"，控制面板: http://localhost:{self._webui_port}"
        )

    # ============================================================
    # 默认状态
    # ============================================================

    def _default_state(self):
        return {
            "mode": "off",
            "speed": 0,
            "comfort": 0.0,
            "locked": False,
            "active": False,
            "lastTick": time.time(),
        }

    # ============================================================
    # 独立 WebUI HTTP 服务器
    # ============================================================

    def _start_web_server(self):
        """启动独立 HTTP 服务器，不依赖 AstrBot 内部路由"""
        if self.config and not self.config.get("webui_control_enabled", True):
            logger.info(f"[{PLUGIN_NAME}] WebUI 控制面板已在配置中禁用")
            return

        plugin_ref = self

        class _Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                parsed = urlparse(self.path)
                path = parsed.path.rstrip("/") or "/"
                qs = parse_qs(parsed.query)
                pwd = qs.get("pwd", [None])[0]

                # 静态文件无需密码
                if path in ("/logo.webp", "/expression.gif"):
                    self._serve_static(path.lstrip("/"))
                    return

                if not self._check_auth(pwd):
                    return

                if path == "/state":
                    self._send_json(200, plugin_ref._state)
                else:
                    self._send_html(200, _WEB_CONTROL_PANEL_HTML)

            def do_POST(self):
                parsed = urlparse(self.path)
                path = parsed.path.rstrip("/") or "/"
                qs = parse_qs(parsed.query)
                pwd = qs.get("pwd", [None])[0]

                body = self._read_body()
                try:
                    data = json.loads(body) if body else {}
                except json.JSONDecodeError:
                    self._send_json(400, {"ok": False, "error": "无法解析请求体"})
                    return

                if not self._check_auth(pwd or data.get("pwd", "")):
                    return

                if path == "/state":
                    with plugin_ref._state_lock:
                        mode = data.get("mode", plugin_ref._state["mode"])
                        speed = int(data.get("speed", plugin_ref._state["speed"]))
                        locked = data.get("locked", plugin_ref._state["locked"])

                        if mode not in MODE_NAMES:
                            mode = "off"
                        speed = max(0, min(4, speed))

                        plugin_ref._state["mode"] = mode
                        plugin_ref._state["speed"] = speed
                        plugin_ref._state["locked"] = locked
                        plugin_ref._state["lastTick"] = time.time()
                        plugin_ref._state["active"] = not (mode == "off" or speed == 0)
                        plugin_ref._flush_to_file()

                    self._send_json(200, {"ok": True, "state": plugin_ref._state})
                else:
                    self._send_json(404, {"ok": False, "error": "未找到"})

            def _check_auth(self, pwd):
                if not plugin_ref._webui_password:
                    return True
                if pwd != plugin_ref._webui_password:
                    self._send_json(403, {"ok": False, "error": "密码错误"})
                    return False
                return True

            def _serve_static(self, filename):
                filepath = os.path.join(_PLUGIN_DIR, filename)
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        data = f.read()
                    ct = 'image/webp' if filename.endswith('.webp') else 'image/gif'
                    self.send_response(200)
                    self.send_header('Content-Type', ct)
                    self.send_header('Content-Length', str(len(data)))
                    self.send_header('Cache-Control', 'max-age=3600')
                    self.end_headers()
                    self.wfile.write(data)
                else:
                    self.send_response(404)
                    self.end_headers()

            def _read_body(self):
                length = int(self.headers.get("Content-Length", 0))
                if length > 0:
                    return self.rfile.read(length).decode("utf-8")
                return ""

            def _send_json(self, status, data):
                body = json.dumps(data, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)

            def _send_html(self, status, html):
                body = html.encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()

            def log_message(self, format, *args):
                pass  # 抑制 HTTP 服务器默认日志

        try:
            self._http_server = HTTPServer(("0.0.0.0", self._webui_port), _Handler)
            self._http_thread = threading.Thread(
                target=self._http_server.serve_forever, daemon=True
            )
            self._http_thread.start()
            logger.info(
                f"[{PLUGIN_NAME}] WebUI 控制面板已启动: http://localhost:{self._webui_port}"
            )
        except OSError as e:
            logger.warning(
                f"[{PLUGIN_NAME}] 端口 {self._webui_port} 被占用，"
                f"控制面板无法启动: {e}"
            )

    def _stop_web_server(self):
        """停止独立 HTTP 服务器"""
        if self._http_server:
            try:
                self._http_server.shutdown()
            except Exception:
                pass
            self._http_server = None
        self._http_thread = None

    # ============================================================
    # 状态文件读写
    # ============================================================

    def _read_from_file(self):
        """从 JSON 文件读状态"""
        try:
            if os.path.exists(self._state_path):
                with open(self._state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 合并，保留未知字段
                    for k, v in data.items():
                        self._state[k] = v
        except (json.JSONDecodeError, OSError):
            pass

    def _flush_to_file(self):
        """将当前状态写入 JSON 文件"""
        try:
            self._state["lastTick"] = time.time()
            with open(self._state_path, "w", encoding="utf-8") as f:
                json.dump(self._state, f, ensure_ascii=False, indent=2)
        except OSError as e:
            logger.warning(f"[{PLUGIN_NAME}] 写入状态文件失败: {e}")

    # ============================================================
    # 后台状态同步循环
    # ============================================================

    async def _sync_loop(self):
        """每秒同步一次：读文件 → 计算 comfort 变化 → 写文件"""
        await asyncio.sleep(2)  # 启动后等2秒再开始循环
        while True:
            try:
                # 1. 读取外部 GUI 可能写入的状态
                self._read_from_file()

                now = time.time()
                dt = now - self._state.get("lastTick", now)

                # 防止休眠后暴涨
                max_dt = 5
                if self.config:
                    max_dt = self.config.get("max_dt_cap", 5)
                if dt > max_dt:
                    dt = 1.0

                # 2. 计算 comfort 变化（加锁保护与 WebUI POST 的竞争）
                with self._state_lock:
                    mode = self._state.get("mode", "off")
                    speed = self._state.get("speed", 0)
                    locked = self._state.get("locked", False)
                    comfort = self._state.get("comfort", 0.0)

                    speed_mult = 1.5
                    decay_rate = 2.0
                    if self.config:
                        speed_mult = float(self.config.get("speed_multiplier", "1.5"))
                        decay_rate = float(self.config.get("decay_rate", "2.0"))

                    if mode != "off" and speed > 0:
                        comfort = min(100.0, comfort + speed * speed_mult * dt)
                        self._state["active"] = True
                    else:
                        self._state["active"] = False
                        if not locked:
                            comfort = max(0.0, comfort - decay_rate * dt)

                    self._state["comfort"] = round(comfort, 1)
                    self._state["lastTick"] = now

                    # 3. 写回文件（供 GUI 同步）
                    self._flush_to_file()

            except Exception as e:
                logger.warning(f"[{PLUGIN_NAME}] 同步循环异常: {e}")

            await asyncio.sleep(1)

    # ============================================================
    # 命令注册
    # ============================================================

    @filter.command_group("vibe")
    def vibe(self):
        """🎀 0721模式 — 控制跳蛋状态"""

    @vibe.command("on")
    async def cmd_on(self, event: AstrMessageEvent, mode: str = "vibration", speed: str = "1"):
        """开启跳蛋。用法: /vibe on <模式> <档位>
        模式: vibration/thrusting/expansion/cum
        档位: 1-4"""
        mode = mode.lower().strip()
        if mode not in MODE_NAMES or mode == "off":
            available = " / ".join(k for k in MODE_NAMES if k != "off")
            yield event.plain_result(f"未知模式 '{mode}'。可用模式: {available}")
            return

        try:
            spd = int(speed)
            spd = max(1, min(4, spd))
        except ValueError:
            spd = 1

        self._state["mode"] = mode
        self._state["speed"] = spd
        self._state["active"] = True
        self._state["lastTick"] = time.time()
        self._flush_to_file()

        mode_txt = MODE_NAMES[mode]
        feel = _pick_feel(mode, spd)
        yield event.plain_result(
            f"🎀 跳蛋已开启！\n"
            f"模式: {mode_txt}\n"
            f"档位: {SPEED_LABELS[spd]}\n"
            f"快感: {self._state['comfort']:.0f}%\n"
            f"感受: {feel}"
        )

    @vibe.command("off")
    async def cmd_off(self, event: AstrMessageEvent):
        """关闭跳蛋"""
        was_active = self._state.get("active", False)
        self._state["mode"] = "off"
        self._state["speed"] = 0
        self._state["active"] = False
        self._state["lastTick"] = time.time()
        self._flush_to_file()

        if was_active:
            yield event.plain_result(
                f"💤 跳蛋已关闭。快感将逐渐衰减（当前 {self._state['comfort']:.0f}%）。"
            )
        else:
            yield event.plain_result("💤 跳蛋本来就是关着的哦~")

    @vibe.command("status")
    async def cmd_status(self, event: AstrMessageEvent):
        """查看跳蛋当前状态"""
        s = self._state
        mode = s.get("mode", "off")
        spd = s.get("speed", 0)
        comfort = s.get("comfort", 0.0)
        locked = s.get("locked", False)
        active = s.get("active", False)

        face = _face_for(comfort)
        mode_txt = MODE_NAMES.get(mode, mode)
        lock_txt = "🔒已锁" if locked else "🔓未锁"
        active_txt = "✅运行中" if active else "⏸️待机"

        # 如果开启了，附加感觉描述
        feel = ""
        if mode != "off" and spd > 0:
            feel = f"\n感受: {_pick_feel(mode, spd)}"
            tone = _pick(SPEED_TONES.get(spd, SPEED_TONES[0]))
            feel += f"\n语气: {tone}"

        yield event.plain_result(
            f"{face} 0721跳蛋状态\n"
            f"模式: {mode_txt} | 档位: {SPEED_LABELS[spd]}\n"
            f"快感: {comfort:.0f}% | {lock_txt} | {active_txt}"
            f"{feel}\n"
            f"状态文件: {self._state_path}"
        )

    @vibe.command("lock")
    async def cmd_lock(self, event: AstrMessageEvent):
        """锁住当前快感值（不解锁就不会衰减）"""
        self._state["locked"] = True
        self._flush_to_file()
        yield event.plain_result(
            f"🔒 已锁住！快感将保持在 {self._state['comfort']:.0f}%，不会自动衰减。"
        )

    @vibe.command("unlock")
    async def cmd_unlock(self, event: AstrMessageEvent):
        """解锁快感值（关闭时自动衰减）"""
        self._state["locked"] = False
        self._flush_to_file()
        yield event.plain_result(
            f"🔓 已解锁！关闭跳蛋时快感会自动衰减（当前 {self._state['comfort']:.0f}%）。"
        )

    @vibe.command("set")
    async def cmd_set(self, event: AstrMessageEvent, key: str = "", value: str = ""):
        """直接设置状态值。用法: /vibe set <字段> <值>
        可设字段: mode, speed, comfort, locked
        示例: /vibe set comfort 50"""
        valid_keys = ["mode", "speed", "comfort", "locked"]
        key = key.lower().strip()
        value = value.strip()

        if key not in valid_keys:
            yield event.plain_result(
                f"可设置的字段: {', '.join(valid_keys)}\n"
                f"示例: /vibe set comfort 50"
            )
            return

        try:
            if key == "mode":
                if value.lower() not in MODE_NAMES:
                    yield event.plain_result(f"无效模式。可用: {', '.join(MODE_NAMES.keys())}")
                    return
                self._state["mode"] = value.lower()
            elif key == "speed":
                v = int(value)
                self._state["speed"] = max(0, min(4, v))
            elif key == "comfort":
                v = float(value)
                self._state["comfort"] = max(0.0, min(100.0, v))
            elif key == "locked":
                self._state["locked"] = value.lower() in ("true", "1", "yes", "on")

            self._state["lastTick"] = time.time()
            self._flush_to_file()
            yield event.plain_result(f"✅ 已设置 {key} = {value}")
        except ValueError:
            yield event.plain_result(f"值格式错误: {value}")

    # ============================================================
    # LLM 请求钩子 — 语气注入
    # ============================================================

    @filter.on_llm_request()
    async def inject_vibe(self, event: AstrMessageEvent, req):
        """在 LLM 请求前注入跳蛋状态文本"""
        try:
            # 同步读一次文件（GUI 可能更新了）
            self._read_from_file()
        except Exception:
            pass

        comfort = self._state.get("comfort", 0)
        active = self._state.get("active", False)

        # 检查是否应该跳过注入
        threshold = 1
        if self.config:
            threshold = self.config.get("inject_threshold_comfort", 1)

        if comfort < threshold and not active:
            return  # 关着就不注入，零干扰

        injection = _build_injection(self._state)

        # 注入到 user prompt 末尾
        if hasattr(req, "prompt") and req.prompt is not None:
            req.prompt = req.prompt + "\n\n" + injection
        elif hasattr(req, "extra_user_content_parts"):
            from astrbot.core.agent.message import TextPart

            req.extra_user_content_parts.append(
                TextPart(text=injection).mark_as_temp()
            )

    # ============================================================
    # LLM Tool — 让 AI 可以主动查询跳蛋状态
    # ============================================================

    @filter.llm_tool(name="check_vibe_status")
    async def check_vibe_status(self, event: AstrMessageEvent):
        """查询当前跳蛋状态。当对话中出现暧昧/情色内容，或用户提到跳蛋、身体反应等话题时，使用此工具了解当前状态以调整回复语气。

        Returns:
            跳蛋状态描述
        """
        s = self._state
        mode = s.get("mode", "off")
        spd = s.get("speed", 0)
        comfort = s.get("comfort", 0.0)

        if mode == "off" or spd == 0:
            yield event.plain_result("跳蛋当前已关闭。")
            return

        mode_txt = MODE_NAMES.get(mode, mode)
        feel = _pick_feel(mode, spd)
        tone = _pick(SPEED_TONES.get(spd, SPEED_TONES[0]))

        yield event.plain_result(
            f"跳蛋状态: {mode_txt} | 档位: {SPEED_LABELS[spd]} | 快感: {comfort:.0f}%\n"
            f"感受: {feel}\n"
            f"语气指导: {tone}"
        )

    # ============================================================
    # 卸载
    # ============================================================

    async def terminate(self):
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        self._stop_web_server()
        logger.info(f"[{PLUGIN_NAME}] 插件已卸载")


# ============================================================
# WebUI 控制面板 HTML（内嵌，通过 API 返回）
# ============================================================

_WEB_CONTROL_PANEL_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>0721模式 - WebUI 控制面板</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI','Microsoft YaHei',sans-serif;background:#1a1a2e;color:#eee;display:flex;justify-content:center;align-items:center;min-height:100vh}
.panel{background:#16213e;border-radius:20px;padding:30px;max-width:420px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,0.5)}
.logo-img{width:100px;height:100px;display:block;margin:0 auto 15px;border-radius:50%;object-fit:cover;border:2px solid #ff6b9d}
.title{text-align:center;font-size:24px;margin-bottom:25px;color:#ff6b9d}
.section{margin-bottom:20px}
.section-label{font-size:13px;color:#8899aa;margin-bottom:8px;text-transform:uppercase;letter-spacing:1px}
.mode-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.mode-btn{padding:12px;border:2px solid #2a3a5c;border-radius:12px;background:transparent;color:#ccc;cursor:pointer;font-size:16px;transition:all 0.2s;text-align:center}
.mode-btn:hover{border-color:#ff6b9d;color:#ff6b9d}
.mode-btn.active{background:rgba(255,107,157,0.15);border-color:#ff6b9d;color:#ff6b9d}
.speed-bar{display:flex;gap:8px;justify-content:space-between}
.speed-btn{flex:1;padding:10px 5px;border:2px solid #2a3a5c;border-radius:10px;background:transparent;color:#ccc;cursor:pointer;font-size:14px;transition:all 0.2s;text-align:center}
.speed-btn:hover{border-color:#ff6b9d}
.speed-btn.active{background:rgba(255,107,157,0.2);border-color:#ff6b9d;color:#ff6b9d}
.comfort-section{background:#0d1b36;border-radius:12px;padding:15px}
.comfort-bar{height:20px;background:#2a3a5c;border-radius:10px;overflow:hidden;margin:8px 0}
.comfort-fill{height:100%;border-radius:10px;transition:width 0.5s;background:linear-gradient(90deg,#ff6b9d,#ff9a56,#ffe066,#ff4444)}
.comfort-text{text-align:center;font-size:28px;font-weight:bold;margin:5px 0;transition:color 0.3s}
.gif-img{width:60px;height:60px;display:none;margin:0 5px;vertical-align:middle;border-radius:8px}
.gif-img.active{display:inline}
.face-display{font-size:48px;text-align:center;margin:10px 0}
.lock-toggle{padding:10px 20px;border:2px solid #ff6b9d;border-radius:20px;background:transparent;color:#ff6b9d;cursor:pointer;font-size:14px;transition:all 0.2s;display:block;margin:0 auto}
.lock-toggle.locked{background:#ff6b9d;color:#fff}
.info-row{display:flex;justify-content:space-between;font-size:13px;color:#8899aa;margin-top:10px}
.api-status{text-align:center;font-size:11px;color:#556;margin-top:15px}
</style>
</head>
<body>
<div class="panel">
    <img class="logo-img" src="/logo.webp" alt="logo">
    <div class="title">🎀 0721模式</div>

    <div class="section">
        <div class="section-label">模式选择</div>
        <div class="mode-grid">
            <button class="mode-btn" data-mode="off" onclick="setMode('off')">💤 关闭</button>
            <button class="mode-btn" data-mode="vibration" onclick="setMode('vibration')">💗 振动</button>
            <button class="mode-btn" data-mode="thrusting" onclick="setMode('thrusting')">🔥 抽插</button>
            <button class="mode-btn" data-mode="expansion" onclick="setMode('expansion')">✨ 扩张</button>
            <button class="mode-btn" data-mode="cum" onclick="setMode('cum')">💦 注精</button>
        </div>
    </div>

    <div class="section">
        <div class="section-label">档位</div>
        <div class="speed-bar">
            <button class="speed-btn" data-speed="0" onclick="setSpeed(0)">关</button>
            <button class="speed-btn" data-speed="1" onclick="setSpeed(1)">★</button>
            <button class="speed-btn" data-speed="2" onclick="setSpeed(2)">★★</button>
            <button class="speed-btn" data-speed="3" onclick="setSpeed(3)">★★★</button>
            <button class="speed-btn" data-speed="4" onclick="setSpeed(4)">★★★★</button>
        </div>
    </div>

    <div class="section">
        <div class="comfort-section">
            <div class="face-display"><span id="face">😊</span><img class="gif-img" id="gifImg" src="/expression.gif" alt="gif"></div>
            <div class="comfort-text" id="comfortText">0%</div>
            <div class="comfort-bar">
                <div class="comfort-fill" id="comfortBar" style="width:0%"></div>
            </div>
            <button class="lock-toggle" id="lockBtn" onclick="toggleLock()">🔓 未锁</button>
            <div class="info-row">
                <span id="modeDisplay">💤 关闭</span>
                <span id="speedDisplay">档: 0/4</span>
            </div>
        </div>
    </div>

    <div class="api-status">状态刷新: <span id="lastUpdate">--</span></div>
</div>

<!-- 密码登录遮罩 -->
<div class="login-overlay" id="loginOverlay">
    <div class="login-box">
        <div class="login-title">🔐 请输入访问密码</div>
        <input type="password" class="login-input" id="loginInput" placeholder="请输入密码" autofocus>
        <button class="login-btn" onclick="doLogin()">验证</button>
        <div class="login-error" id="loginError"></div>
    </div>
</div>

<style>
.login-overlay{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);z-index:9999;justify-content:center;align-items:center}
.login-box{background:#16213e;border-radius:16px;padding:30px;text-align:center;max-width:320px;width:90%}
.login-title{font-size:18px;color:#ff6b9d;margin-bottom:20px}
.login-input{width:100%;padding:12px;border:2px solid #2a3a5c;border-radius:10px;background:#0d1b36;color:#fff;font-size:16px;outline:none;text-align:center;letter-spacing:4px}
.login-input:focus{border-color:#ff6b9d}
.login-btn{width:100%;padding:12px;margin-top:15px;border:none;border-radius:10px;background:#ff6b9d;color:#fff;font-size:16px;cursor:pointer;font-weight:bold}
.login-btn:hover{background:#ff4081}
.login-error{color:#ff4444;font-size:13px;margin-top:10px;min-height:20px}
</style>

<script>
const API_BASE = '.';
const FACES = [
    [90, '💥'], [70, '🥵'], [50, '😫'],
    [30, '😖'], [10, '😳'], [0, '😊']
];
const URL_PARAMS = new URLSearchParams(window.location.search);

// 密码: URL参数 > localStorage > 空
let AUTH_PWD = URL_PARAMS.get('pwd') || '';
if (!AUTH_PWD) {
    try { AUTH_PWD = localStorage.getItem('vibe_pwd') || ''; } catch(e) {}
}

let currentMode = 'off', currentSpeed = 0, currentLocked = false, currentComfort = 0;
let authError = false;

function apiUrl(path) {
    return API_BASE + path + (AUTH_PWD ? (path.includes('?')?'&':'?') + 'pwd=' + encodeURIComponent(AUTH_PWD) : '');
}

async function fetchState() {
    try {
        const r = await fetch(apiUrl('/state'));
        if (r.status === 403) {
            if (!authError) { showLogin('密码错误'); authError = true; }
            return;
        }
        authError = false;
        const s = await r.json();
        if (s.error) { document.getElementById('lastUpdate').textContent = s.error; return; }
        currentMode = s.mode || 'off';
        currentSpeed = s.speed || 0;
        currentLocked = s.locked || false;
        currentComfort = s.comfort || 0;
        updateUI(); document.getElementById("gifImg").classList.toggle("active", currentMode !== "off" && currentSpeed > 0);
        document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
    } catch(e) {
        document.getElementById('lastUpdate').textContent = '连接失败';
    }
}

async function sendState(changes) {
    try {
        const body = {mode:currentMode, speed:currentSpeed, locked:currentLocked, pwd: AUTH_PWD, ...changes};
        const r = await fetch(apiUrl('/state'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body)
        });
        if (r.status === 403) { showLogin('密码错误'); return; }
        Object.assign(this, {currentMode, currentSpeed, currentLocked, ...changes});
        currentMode = body.mode;
        currentSpeed = body.speed;
        currentLocked = body.locked;
    } catch(e) {
        console.error('Failed to set state:', e);
    }
}

// 登录逻辑
function showLogin(msg) {
    document.getElementById('loginOverlay').style.display = 'flex';
    document.getElementById('loginError').textContent = msg || '';
    document.getElementById('loginInput').value = '';
    document.getElementById('loginInput').focus();
}

async function doLogin() {
    const pwd = document.getElementById('loginInput').value;
    if (!pwd) return;
    // 用输入密码发起请求验证
    const testUrl = API_BASE + '/state?pwd=' + encodeURIComponent(pwd);
    try {
        const r = await fetch(testUrl);
        if (r.status === 403) {
            document.getElementById('loginError').textContent = '密码错误，请重试';
            document.getElementById('loginInput').value = '';
            return;
        }
        // 密码正确
        AUTH_PWD = pwd;
        try { localStorage.setItem('vibe_pwd', pwd); } catch(e) {}
        document.getElementById('loginOverlay').style.display = 'none';
        authError = false;
        // 解析数据更新 UI
        const s = await r.json();
        if (!s.error) {
            currentMode = s.mode || 'off';
            currentSpeed = s.speed || 0;
            currentLocked = s.locked || false;
            currentComfort = s.comfort || 0;
            updateUI();
        }
    } catch(e) {
        document.getElementById('loginError').textContent = '连接失败，请检查服务器';
    }
}

// 回车登录
document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && document.getElementById('loginOverlay').style.display === 'flex') {
        doLogin();
    }
});

function setMode(m) {
    if (m === 'off') {
        sendState({mode:'off', speed:0});
    } else {
        const spd = currentMode === 'off' ? 1 : Math.max(1, currentSpeed);
        sendState({mode:m, speed:spd});
    }
}

function setSpeed(s) {
    if (s === 0 && currentMode !== 'off') {
        sendState({speed:0});
    } else if (s > 0 && currentMode === 'off') {
        sendState({mode:'vibration', speed:s});
    } else {
        sendState({speed:s});
    }
}

function toggleLock() {
    sendState({locked:!currentLocked});
}

function updateUI() {
    document.querySelectorAll('.mode-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.mode === currentMode);
    });
    document.querySelectorAll('.speed-btn').forEach(b => {
        b.classList.toggle('active', parseInt(b.dataset.speed) === currentSpeed);
    });
    const lb = document.getElementById('lockBtn');
    lb.textContent = currentLocked ? '🔒 已锁' : '🔓 未锁';
    lb.classList.toggle('locked', currentLocked);
    const c = currentComfort;
    document.getElementById('comfortText').textContent = c.toFixed(0) + '%';
    document.getElementById('comfortBar').style.width = c + '%';
    document.getElementById('comfortText').style.color = `hsl(${(100-c)*0.6}, 80%, 60%)`;
    for (const [t, f] of FACES) { if (c >= t) { document.getElementById('face').textContent = f; break; } }
    const modes = {off:'💤 关闭',vibration:'💗 振动',thrusting:'🔥 抽插',expansion:'✨ 扩张',cum:'💦 注精'};
    document.getElementById('modeDisplay').textContent = modes[currentMode] || currentMode;
    document.getElementById('speedDisplay').textContent = '档: ' + currentSpeed + '/4';
}

fetchState();
setInterval(fetchState, 1500);
</script>
</body>
</html>"""

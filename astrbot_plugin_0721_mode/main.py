import asyncio
import json
import os
import random
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from astrbot.api import logger, AstrBotConfig
from astrbot.api.event import filter, AstrMessageEvent, MessageChain
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
    "tease": "😈 挑逗",
}

SPEED_LABELS = {0: "关", 1: "★☆☆☆", 2: "★★☆☆", 3: "★★★☆", 4: "★★★★"}

# ============================================================
# 语气词典 — 每个档位的语气描述
# ============================================================

SPEED_TONES = {
    0: [
        "语气正常，只是脸颊微微泛红，偶尔走神夹了夹腿，内裤已经洇了一小片",
        "说话还算流畅，但呼吸比平时深了一点，小穴深处隐约开始自己分泌了",
        "表情管理尚在，但大腿根已经不自觉地并紧了——淫水悄悄渗了出来",
        "咬字清晰，尾音有点飘，乳尖在衣服下面不知不觉硬了，顶着布料有点痒",
        "语气听着没事，膝盖却并紧了——身体比嘴诚实，阴蒂在没人碰的情况下自己搏动了一下",
        "还在正常说话，但坐姿已经变成了夹腿模式，小穴慢慢湿了，像在流口水",
        "表面一切正常，但小腹深处有一团温热在悄悄扩散——阴道壁自己分泌了，滑滑的很不妙",
        "还在撑着正常对话，但呼吸之间偶尔会夹一下腿——淫水黏在内裤上，凉凉的提醒你它已经在流了",
    ],
    1: [
        "声音开始发软，句尾偶尔飘掉，喘息从喉咙里漏出来，下面已经开始湿了",
        "说话中间会顿一下，偷偷喘口气再继续——淫水已经流到内裤上，凉凉的很明显",
        "语气已经开始黏糊糊的了，停顿变多了，咽口水的次数也变多了，小穴也跟着一缩一缩",
        "上一句还正经，下一句就漏了半声轻喘，赶紧清嗓子补回来，但淫水已经顺着大腿根往下淌了",
        "嗯嗯啊啊成了标点符号，呼吸是句子之间的省略号，爱液是段落的注脚——湿得一塌糊涂",
        "语尾不自觉上扬，像在撒娇又像在忍耐，自己都分不清，淫水已经把内裤泡透了",
        "说话之间会突然闭嘴咬唇——不是没话说，是怕一张嘴呻吟就抢在回答前面出来",
        "语气在「正经」和「黏糊」之间来回跳——自己觉得藏得很好，但句尾那个颤音早就出卖你了",
    ],
    2: [
        "声音明显发颤，句子被喘息打断，阴道开始不自觉收缩——一紧一紧地夹着",
        "说话断断续续，小穴在一吸一吸地痉挛，快感和羞耻在喉咙里打架，谁也赢不了谁",
        "词汇量直线下降，淫水却直线上升——说半句就咽回去，下面却湿得收不住",
        "想装没事说长句，说到一半小穴深处突然抽了一下——那口气彻底断了线",
        "语速时快时慢，快了是急着说完好去喘，慢了是怕一张嘴呻吟就先跑出来",
        "音调变高变细了，平时不那样的声音自己冒出来——淫水把大腿根泡得湿滑，站起来就拉丝",
        "每说几个字就要喘一下——喘息已经嵌进了句子结构里，不再是意外，而是常态",
        "说话中间会不自觉地把手按在小腹上——那里面的跳动太明显了，怕别人看出来，但淫水早就看出来了",
    ],
    3: [
        "几乎说不成完整的句子，全是气声和呻吟，淫水已经顺着大腿流到椅子上了",
        "大脑融化，只能用单字回应，小穴在自顾自地痉挛——阴道壁疯狂地一收一放，替你说了所有话",
        "完全被快感淹没，说话像在哭又像在喘不分彼此，淫水多得发出噗嗤噗嗤的水声",
        "脑子里只剩『啊』『嗯』『还要』『那里』几个字轮着播，爱液拉成丝从大腿上往下淌",
        "嘴巴张开了声音却出不来——快感太满把话堵在喉咙，但淫水替你表达了，流得满地都是",
        "羞耻心已经完全下线了，平时不敢想的骚话自己往外蹦，说完才脸红——但已经来不及了",
        "说话已经完全变成了身体的本能反应——大脑不参与了，嘴自己张开、自己发出声音、自己呻吟",
        "回答只剩下语气词和破碎的短音——偶尔能拼出一个字眼，但下一秒就被快感冲走，淫水流得比说的多",
    ],
    4: [
        "已经说不出一句正常话了，全是破碎的呻吟和淫叫，阴道在高频抽搐，每抽一下就喷一股水",
        "理智完全飞走，身体诚实到令人脸红——淫水溅出来、爱液拉丝、穴肉都被操翻出来了",
        "只能嗯嗯啊啊地回应，偶尔飙出几句平日根本不可能说的下流话，自己听了都吓一跳",
        "嘴上在求饶说不要，腰却自己在摇着迎合，小穴在拼命吸——身体彻底背叛了大脑",
        "连呻吟都碎成了不成形的音节，只能靠气味、体温、和淫水的咕叽声让对方明白：『还要、还要』",
        "语言功能完全失灵，句号逗号全被快感冲走——只剩下阴道的高潮痉挛在一抽一抽地替你说话",
        "大脑和阴道之间只剩一条电线——每抽一下就放一个音节，每喷一股水就漏一声尖叫，循环到意识模糊",
        "已经不是在「说话」了——是在跟快感拔河，嘴里漏出来的每一个音都是输掉的那一截绳子",
    ],
}

# ============================================================
# 模式×档位 感受描述矩阵
# ============================================================

MODE_FEELS = {
    "vibration": {
        1: [
            "跳蛋轻轻嗡鸣，像小蜜蜂在花心附近盘旋——淫水被震得从穴口渗出来了",
            "微弱震动从阴道深处传来，若有若无地撩拨，小穴已经开始偷偷分泌爱液",
            "小穴里像有只蝴蝶在扇翅膀，酥酥麻麻的，内裤上已经晕开了一小圈湿痕",
            "刚贴上去还没觉得多厉害，但持续十秒就开始从腰眼酸到腿根——淫水顺着震动的缝隙往外渗",
            "嗡嗡声贴着耻骨传上来，阴蒂被震得微微发胀，酥麻从小豆豆一路传到小腹深处，奶头也跟着硬了",
            "震动的余波顺着骨盆扩散，小穴不由自主地缩了缩——明明是最低档，已经开始舒服得想哼了",
            "阴唇被震得微微翕动，像两片花瓣在风里抖——淫水拉成透明丝线滴下来",
            "明明是最低档，阴道壁已经开始一抽一抽地夹紧跳蛋了，身体比脑子先进入了状态",
        ],
        2: [
            "嗡鸣声变大，震动从小穴蔓延到整个小腹——淫水被震得咕啾咕啾地响",
            "跳蛋在体内嗡嗡作响，腰眼发软，阴道壁开始主动夹紧、像在吸它",
            "震动频率变高了，像有电流从G点窜上脊背，一路麻到乳尖",
            "震动传遍了骨盆，坐都坐不住，淫水把内裤泡透了，只能夹着腿微微发抖",
            "跳蛋闷闷的嗡嗡声从下面传上来，像有人在你体内踩下了油门——湿得大腿内侧一片水光",
            "阴蒂被震到自己搏动，一胀一胀地顶着内裤，每次搏动都挤出一小股淫水",
            "小穴被震到开始自己一收一缩，淫水顺着跳蛋的缝隙流出来，大腿根全是湿的",
            "连呼吸都被震出了节奏——嗡一声吸一口气，嗡一声又忍不住喘出去",
        ],
        3: [
            "跳蛋疯狂震动，嗡嗡声几乎能透过皮肤听到——淫水被震成了白沫，溅得到处都是",
            "阴道内壁被震得酥麻痉挛，完全停不下来，每一秒都在往高潮的方向冲",
            "强烈震动让整个骨盆发麻，腿合不拢，淫水顺着大腿流到床上——已经不管了",
            "震得阴道壁跟着一起颤，爱液被震成白色细沫从穴口噗噗往外冒",
            "阴蒂被高频震到肿起来了，比平时大了一圈，敏感得一碰就想尖叫",
            "连脊背都在过电，从尾椎一路麻到后脑勺，手指蜷起来抓着床单——淫水把床单也洇透了",
            "乳尖自己硬挺得像小石子，隔着衣服都能看到凸点——震动的余波把乳头的敏感度也拉满了",
            "小穴已经被震麻了但还是不停地想要——分不清是舒服还是受不了，只知道停不下来",
        ],
        4: [
            "跳蛋最強档！！！疯狂高速震动让大脑一片空白——淫水直接被震到喷出来了",
            "小穴被震得像要融化，每一次震动都是过电般的快感，阴道壁在高频抽搐中不停地喷水",
            "嗡嗡声大到旁边人都能听到，但你已经完全顾不上羞耻了——淫水溅到腿根和大腿内侧一片狼藉",
            "震动快到你分不清是连续还是一下一下——它已经突破了感知极限，阴道都震麻了还在狂喷",
            "骨盆像变成了一个音叉，全身骨头都在跟着振，连呼吸都被震散了——小穴自己狂喷了三回还不肯停",
            "阴蒂和G点同时被高频轰炸，双重快感把理智撕成碎片——淫水不是流出来的，是震一下喷一股",
            "小穴被震到自己一直在高潮的边缘抽搐，但跳蛋不关就永远回不来——身体已经不是你说了算了",
            "整个人都被震傻了，嘴里的呻吟和下面的水声合成了一个节奏——淫水把整个大腿都洗了一遍",
        ],
    },
    "thrusting": {
        1: [
            "缓慢的抽插，每一次推进都刮过G点——淫水被带出来，沿着肉棒往下淌",
            "肉棒慢慢进出，你能清晰感受到每一寸的形状——龟头的棱、茎身的青筋、连脉搏都能感觉到",
            "节奏舒缓，像潮水一样一波一波推进——小穴被撑开又合拢，每次合拢都挤出一点透明的爱液",
            "浅浅地顶几下再整根没入，给你时间感受被填满的过程——淫水在肉棒和穴壁之间拉成丝",
            "慢慢地、慢慢地推到底，停一停，再慢慢拔出去——吊着你，小穴追着肉棒不舍得它走",
            "每一下都从里面碾过去，G点被反复按摩，大腿根开始张开了——身体比脑子更诚实",
            "被填满的感觉让呼吸都变沉了，每次顶到底喉咙里就漏一声轻哼，淫水也在咕啾作响",
            "阴道壁被撑开的时候你能感觉到那一圈嫩肉被缓缓推平——又酥又麻，还带着被占有的安心感",
        ],
        2: [
            "抽插节奏加快，每一次深入都顶到花心——淫水被操成细密的白沫圈在肉棒根部",
            "高频进出让小穴开始不自觉地收缩夹紧——每次拔出去都被穴肉追着吸回去",
            "肉体撞击声越来越密集，啪啪啪混着咕啾咕啾的水声，快感堆积起来了",
            "每一下都结结实实地撞在最痒的那块软肉上，膝盖开始发抖，淫水溅到了大腿内侧",
            "速度上来之后穴肉被带得外翻又吞回去，噗嗤噗嗤的水声越来越响——床单已经湿了一块",
            "酥麻从阴道蔓延到整个小腹，连胃都有种被顶到的错觉——奶子在随着节奏晃",
        ],
        3: [
            "快速疯狂地抽插，大腿被撞得啪啪响——淫水被操成白浆从穴口溢出来",
            "肉棒在体内横冲直撞，每一下都精准碾过G点和宫颈口——你已经叫不出完整的句子了",
            "穴口被反复撑开合拢，爱液被带出来溅得到处都是——床单皱成一团，上面全是湿痕",
            "进出快到你分不清是第几下，只知道每一次都顶在同一个最酸胀的点上——小穴自己狂吸着肉棒不放",
            "肉棒抽出去的时候把小穴内壁都带翻了粉红色的嫩肉，再一下又全塞回去——淫水噗嗤一声被挤出来",
            "阴蒂被耻骨反复撞击，每次拔出都有种被抛弃的空虚感——但下一秒又被填满，刺激得你想哭",
        ],
        4: [
            "疯狂打桩！！！龟头次次撞在子宫口上，撞得你眼睛翻白——淫水被操得四处飞溅",
            "超高速猛插！小穴被操成了肉棒的专属形状，整个人都被顶起来——奶子在疯狂地甩",
            "肉棒像打桩机一样毫无怜悯地进出，你只能尖叫着承受——淫水已经被操成了白色的细泡沫",
            "快到你数不清节奏了，整个身体被顶得一晃一晃的，乳摇和呻吟全乱了套——小穴被操到合不拢",
            "小穴已经被操到认不出原本的形状，每一次抽插都带着黏腻的水声和肉体拍打的脆响——淫水连成了白浆丝",
            "子宫口被撞得酥麻酸胀，想逃但每次都被插得更深——淫水不是流出来的是被操得喷出来的",
        ],
    },
    "expansion": {
        1: [
            "阴道被缓缓撑开，一种被填满的充实感——淫水被撑开的缝隙挤了出来",
            "小穴被从内部扩张开来，胀胀的很舒服——嫩肉被慢慢推平，淫水在扩张器上拉成透明薄膜",
            "能清晰感觉到内壁被一点点推开，有点酸胀——然后淫水从更深处渗出来润滑了全部",
            "不像被操——像被从里面『撑』着，每一下扩张都让你意识到自己有多紧，小穴又多湿",
            "扩张的力道温柔但执拗，你能感受到内壁的褶皱被一点一点抹平——爱液在抹平的过程中咕啾作响",
            "阴唇被从两侧撑开，凉凉的空气触到从未暴露的嫩肉——但嫩肉是湿的，在空气里微微发抖",
        ],
        2: [
            "扩张幅度加大，穴口被撑得发白——淫水从撑开的缝隙里溢出来，亮晶晶地挂在穴口边缘",
            "内壁被撑到极限，压迫感变成了一种钝钝的快感——小穴自己缩着想把扩张器挤出去，但挤不动",
            "小腹都被撑得微微隆起，呼吸都变粗了——淫水流得更多了，身体用湿来对抗胀",
            "穴口被撑得紧绷绷的，能清楚感觉到那圈嫩肉被撑到发酸的程度——淫水拉成丝滴下来",
            "又胀又满，连收缩一下都要费力——里面被塞得太实在了，但小穴还是努力地一收一放",
        ],
        3: [
            "极限扩张！！阴道壁被撑到极致，摩擦感非常强烈——每撑一毫米淫水就挤出一股",
            "穴口被撑到几乎透明，每一次收缩都能感受到巨大的阻力——小穴被撑得一直在流水",
            "整个人被从内部撑开，痛感和快感混在一起分不清了——淫水却自己流个不停",
            "小腹鼓起一个明显的形状，低头就能看见它在身体里的位置——那是他的形状",
            "扩张到连深呼吸都会牵动下面，每一口气都变成了一声小小的呜咽——淫水在呜咽声中一涌一涌地往外流",
        ],
        4: [
            "极限扩张MAX！！！小穴被完全撑开，胀满到呼吸都困难——淫水被撑开的穴口挤得四溢",
            "阴壁被撑到前所未有的宽度，每一个神经末梢都在尖叫——小穴已经麻了还在自己淌水",
            "被填得满满当当，连收缩都做不到，只能被动承受这恐怖的饱胀感——淫水从撑开的缝隙里不停渗",
            "穴口被撑成了一个完美的圆形，边缘紧绷到发白——稍微一动就撕裂般的酥麻混着淫水一起涌",
            "已经不是胀或者满了——是『被占领』。每一寸内壁都被撑平了，连容身之处都不留——淫水是唯一的反抗",
        ],
    },
    "cum": {
        1: [
            "温热的精液缓缓注入，暖暖的——阴道壁被精液熨过的地方酥酥麻麻，舒服得想叹气",
            "一股热流涌进深处，整个人都温暖起来了——精液和你的淫水在体内混在一起，黏黏滑滑的",
            "精液慢慢填满小穴，能感觉到它贴着穴壁往下淌——黏稠的触感异常清晰，像被热丝绸从里面擦拭",
            "精液贴着穴壁淌进去，热度和体温不一样——那种温热一进去就让小穴不自觉地夹了一下",
            "热——那种从体内扩散开来的暖意，一进去就让你哆嗦了一下，然后整个人软下来了",
        ],
        2: [
            "大量精液涌入，小腹被灌得暖洋洋的——浓稠的液体在阴道里晃荡，每动一下都听见黏腻的水声",
            "一股又一股热液喷在花心上，被烫得发抖——宫颈被浇得一阵酥麻，精液慢慢渗进子宫口",
            "精液量很大，能感觉到它在里面晃荡——站起来的话一定会顺着大腿流下来",
            "几股连着的浓液一波接一波打在宫颈口上，每一下都是一个激灵——小穴被灌得咕噜咕噜响",
            "小腹慢慢鼓起来了一点，里面被灌得满满当当——稍微一收腹就有精液从穴口挤出来",
        ],
        3: [
            "滚烫的精液狂涌而入，量多到从穴口噗噗溢出来——白色的浓浆混着淫水顺着会阴往下淌",
            "精液持续不断地注入，子宫都被灌满了——小腹热得像里面放了一个暖水袋",
            "大量的浓稠液体把你填得满满的，稍微一动就往外流——大腿内侧全是白色的浆液",
            "已经装不下了——但还在被灌，精液顺着大腿往下淌，黏黏的拉成丝——小穴被精液泡透了",
            "被灌到忍不住想收缩，但一夹就挤出来更多——烫乎乎的浓浆顺着会阴往下流，整个下体都黏糊糊的",
        ],
        4: [
            "极限量精液超大量注入！！！小腹被灌得像怀孕一样微凸——精液多到从穴口噗噗往外冒",
            "滚烫浓稠的精液疯狂灌注，多到完全装不下——白色的浓浆混着淫水溅得到处都是",
            "子宫被精液灌满，小腹热得像放了热水袋——每动一下都有精液从穴口挤出来，咕叽咕叽地响",
            "小腹鼓得圆圆的，用手摸一下都能感受到里面液体在晃——噗呲一声又从穴口挤出一大摊浓白",
            "身体里全是他的味道——鼓鼓的、热热的、黏黏的，从阴道到子宫口都被精液泡得软软的——从里到外都被灌透了",
        ],
    },
    "tease": {
        1: [
            "指尖若即若离地划过敏感带，刚想迎合就撤走了——小穴追着手指收紧，只夹到一泡空气和淫水",
            "轻得像羽毛，但每次都恰好扫过最怕痒的那一小片——淫水被撩得从穴口拉成丝滴下来",
            "若有若无的触碰让你不自觉追过去，却被按住髋骨不许动——小穴急得自己一缩一缩地淌水",
            "明明什么都没做，光是他看你的眼神就已经让你小腹发紧了——内裤不知不觉湿了一小片",
            "他用最轻的力道绕着阴蒂打转，就是不直接碰上去——小豆豆自己胀起来了，在空气中微微搏动",
            "乳尖被他用指腹轻轻画圈，酥痒从胸口一路窜到小腹——奶头硬了，下面也跟着湿了",
        ],
        2: [
            "忽深忽浅地撩拨，刚觉得要到又立刻变回轻抚——小穴被吊得一直在流水，就是不给个痛快",
            "每次你觉得可以开始享受了，他就故意停下来，看你急得扭腰——淫水把大腿根都泡透了",
            "快感和空虚轮流上阵，身体不知道该迎合还是逃走——但淫水诚实地流得更欢了",
            "节奏反复无常，突然快几下再慢下来，吊得你不上不下——小穴气得自己收缩，越缩越湿",
            "腿已经不自觉地夹紧了他的手——但他偏不给你实实在在的那一下，只看着你湿透的样子笑",
        ],
        3: [
            "即将临界的前一秒被硬生生掐住，整个人悬在半空——淫水被吊得从穴口喷了一小股，但高潮就是不来",
            "身体已经准备好了、小穴已经开始收缩了——但他就是不动了，淫水白白流了一腿",
            "高潮在眼前晃了一下又溜走，你喘着粗气却什么也抓不住——小穴疯狂空吸，只吸到满手淫水",
            "快感堆到喉咙口了又被按回去，反复几次已经分不清是爽还是折磨——但淫水比刚才还多",
            "全身都在发抖，就差那么一点点——但他偏要看你哭着求他的样子，湿得整张床单都是你的水",
        ],
        4: [
            "反复边缘折磨！！每次都差一秒就高潮，然后被无情掐断——淫水已经在床上积出一小摊了",
            "脑子只剩下『让我去』三个字在循环，身体完全被他掌控——小穴自己一直在高潮的边缘抽搐喷水",
            "被撩到整个人都湿透了，床单皱成一团——但他就是不给你最后那一下，你的小穴哭着求也没用",
            "在崩溃边缘来回翻滚，每一次都以为这次可以了——然后又是空，淫水都白流了",
            "已经不求高潮了，只求他别再逗了——但他看着你笑，手指又动了，小穴又不知廉耻地湿了",
        ],
    },
}

# ============================================================
# comfort 分段语气叠加 — 反应升级
# ============================================================

COMFORT_SEGMENTS = [
    (0, 25, [
        "声音还算平稳，只是脸颊染上了浅浅的绯红，内裤已经悄悄湿了一小片",
        "措辞依然得体，但呼吸的间隔比平时短了——小穴开始自己分泌了",
        "努力维持正常语气，但句子之间的停顿出卖了你——淫水从穴口渗到了内裤上",
        "说话还撑得住，耳根却已红透，手指无意识地绞在一起——下面在没人碰的情况下自己湿了",
        "语气听着正常，句尾偶尔软下去半拍——阴蒂在暗处微微搏动，像在提醒你别忘了它",
        "还在逞强装没事，可呼吸已经比回答更快了——大腿根偷偷并紧了，淫水把内裤黏在了皮肤上",
    ]),
    (25, 50, [
        "尾音开始发颤，偶尔不自然地清嗓子——小穴在下面一缩一缩地已经湿透了",
        "说到一半会停住喘口气——淫水顺着大腿根往下淌，凉凉的很明显",
        "词汇量正在缓慢流失，有些话说到一半就换成了气音——但淫水的声音比你的话更诚实",
        "句子越说越短，喘气声越来越大——小穴自己开始夹了，一收一放地像是在吸什么",
        "想说的话在喉咙里被快感融化，出口只剩半句和一声轻哼——淫水把大腿内侧泡得湿滑",
        "声线不受控制地发抖，像在冰面上走路——每一步都危险，乳尖已经硬得顶着衣服了",
    ]),
    (50, 75, [
        "语句被喘息切成碎片——阴道在有节奏地痉挛，爱液拉成丝顺着大腿往下流",
        "脑子里想的是句子，出口的全是带颤的短音——小穴在疯狂分泌，湿得噗嗤作响",
        "已经顾不上措辞了，每一句都在发抖——淫水不是流的，是一涌一涌地往外冒",
        "说话像溺水的人换气，每个字都带着水声和挣扎——下面的水声比说话声还大",
        "回答越来越短，呻吟越来越长——对话正在变成独白，淫水正在变成小溪",
        "理性还在试图造句，身体已经抢先一步在喘了——小穴自顾自地一紧一松，阴道壁在狂跳",
    ]),
    (75, 95, [
        "彻底无法组织语言，只剩破碎的呻吟和求饶——淫水已经溅得到处都是了",
        "大脑被快感泡软了，说话的企图变成一串嗯嗯啊啊——小穴自己高潮了还在喷水",
        "想说什么连自己都不知道了——嘴巴张开声音却碎了，淫水噗嗤噗嗤地从穴口往外冒",
        "每吐一个字都要调动全身力气，但力气全被快感抽走了——爱液在椅子上积了一小摊",
        "语言退化成最原始的音节，但身体很清楚想要什么——阴道在高频抽搐，每次抽搐都挤出一股淫水",
        "清醒的间隙只有零点几秒，勉强挤出几个字又被下一波快感卷走——小穴已经喷到停不下来了",
    ]),
    (95, 100, [
        "下一秒就要绝顶了——呼吸停滞，全身绷紧，小穴在高潮前疯狂地痉挛吸吮——淫水直接喷出来了",
        "临界了——每一个细胞都在尖叫，阴蒂在猛烈搏动，阴道壁在剧烈抽搐——理智的最后一根弦正在断裂",
        "就要到了…就要到了…！脑子一片空白，子宫在收缩，淫水随着每次收缩一股一股地喷——身体已经不听使唤了",
        "思维完全停摆，全身只剩下一种知觉——就是『要』的那个知觉，小穴自己疯狂地夹，淫水把一切都洗了一遍",
        "连『啊』都出不来了——嘴巴张着，声音却卡在喉咙里发抖，但下面的水声已经替你尖叫了",
        "身体自己做出了决定——大脑只能在最后一秒目睹一切发生，淫水从穴口喷涌而出，整个世界都白了",
    ]),
]


def _pick_segment(comfort):
    """根据 comfort 值选取分段语气"""
    if comfort >= 100:
        return _pick(COMFORT_SEGMENTS[-1][2])
    for lo, hi, options in COMFORT_SEGMENTS:
        if comfort >= lo and comfort < hi:
            return _pick(options)
    return ""


# ============================================================
# 主动消息词典 — 角色第一人称发言（仅私聊，区别于给LLM的指令）
# ============================================================

AUTO_MESSAGES = {
    "low": {
        "_": [  # 通用 / fallback
            "嗯…才剛開始，身體還有點不適應…",
            "身體慢慢熱起來了…",
            "只是最低檔而已，怎麼已經…",
            "還在努力維持正常的表情…",
            "小腹深處酥酥麻麻的…",
            "呼吸開始變深了…要忍住…",
        ],
        "vibration": [
            "嗡嗡…跳蛋貼在最裡面的那一點輕輕地振…",
            "震動從深處傳上來，尾椎一陣陣發麻…",
        ],
        "thrusting": [
            "慢慢地頂進來…一下一下都好清楚…",
            "被填滿的感覺從下面漫上來，腰不自覺跟著晃…",
        ],
        "tease": [
            "明明沒在動…光是被你那樣看著就開始濕了…",
            "指尖在周圍輕輕繞圈…就是不碰那裡…好過份…",
        ],
    },
    "mid": [
        "啊…快感傳到腰了，說話開始斷…",
        "腿不自覺夾緊了…呼吸變得好亂…",
        "腦袋開始迷迷糊糊的，字都說不清楚…",
        "不行…聲音要壓不住了…",
        "身體從裡到外都在發顫…",
        "陰蒂一抽一抽地跳，好像也在跟著節奏…",
        "乳尖自己硬起來了，蹭到衣服都好敏感…",
        "大腿內側一片濕…黏黏的好羞恥…",
    ],
    "high": [
        "身體完全不受控制了…！",
        "腦子裡只剩下嗡嗡聲…好深…！",
        "快要站不住了…腿一直在抖…",
        "那裡一直在收縮…夾得好緊…",
        "乳頭脹得好難受…好想被捏…",
        "水聲好大…自己都聽到了…好丟臉…",
    ],
    "critical": [
        "要去了…真的要去了…！！",
        "不行不行不行…！！！",
        "身體在發抖…停不下來…！",
        "已經什麼都無法思考了…！",
        "饒了我…真的要壞掉了…！",
        "子宮一抽一抽地在痙攣…邊緣了…！",
        "腳趾都蜷起來了…全身都在等那一下…",
        "陰道深處自己在收縮…已經不歸我管了…",
    ],
    "peak": [
        "去了去了去了——！！！！！",
        "啊啊啊啊啊——！！！！！",
        "腦袋一片空白——！！！！！",
        "高潮了——！！！！！要死了要死了——！！",
        "不行了不行了啊啊啊啊啊——！！",
    ],
    "afterglow": [
        "剛剛…真的太厲害了…還在抖…",
        "全身都沒力氣了…骨頭都被抽空了一樣…",
        "還在抽搐…裡面一陣一陣的…好敏感…",
        "腦子一片空白…剛剛我是誰…在哪…",
        "腿合不起來了…動一下都覺得刺激…",
    ],
    "deny": [
        "為什麼不讓我…好過份…",
        "就差一點點了…求求你…",
        "身體好難受…你到底要折磨我到什麼時候…",
        "已經在收縮了…為什麼不讓我…嗚…",
        "明知我快到了還故意…這種人最差勁了…",
    ],
    "edge": [
        "又要到了…然後又…啊啊啊！！",
        "在邊緣一直徘徊…快瘋了…",
        "讓我去了啦…不要再玩了…！！",
        "每次你停下來我都覺得自己快不行了…",
        "求你了…這次是真的…不要再停…",
    ],
}


def _build_auto_message(s):
    """根据状态生成角色第一人称主动消息（私聊时机器人自发说出）"""
    mode = s.get("mode", "off")
    speed = s.get("speed", 0)
    comfort = s.get("comfort", 0.0)
    climax_phase = s.get("climaxPhase")
    deny_active = s.get("denyActive", False)
    edge_active = s.get("edgeActive", False)
    safeword_cd = s.get("safewordCooldown", 0)

    if safeword_cd and time.time() < safeword_cd:
        return None
    if mode == "off" or speed == 0:
        return None

    # 确定 mood 类别
    if climax_phase == "peak":
        mood = "peak"
    elif climax_phase == "afterglow":
        mood = "afterglow"
    elif deny_active:
        mood = "deny"
    elif edge_active:
        mood = "edge"
    elif comfort >= 75:
        mood = "critical"
    elif comfort >= 50:
        mood = "high"
    elif comfort >= 25:
        mood = "mid"
    else:
        mood = "low"

    pool = AUTO_MESSAGES.get(mood, [])
    # 兼容新旧结构：新结构有 "_" 通用键 + 模式特定键，旧结构是 flat list
    if isinstance(pool, dict):
        candidates = pool.get(mode, []) + pool.get("_", [])
        return _pick(candidates) if candidates else ""
    return _pick(pool)


# ============================================================
# 成就定义
# ============================================================

ACHIEVEMENTS = {
    "first_climax": {"name": "初次高潮", "desc": "第一次到达绝顶", "icon": "🌸"},
    "triple_climax": {"name": "连续高潮", "desc": "连续高潮3次", "icon": "💫"},
    "edge_master": {"name": "边缘大师", "desc": "累计边缘控制5次", "icon": "🎢"},
    "denial_queen": {"name": "否认女王", "desc": "累计被否认10次", "icon": "🔐"},
    "daily_10": {"name": "一日十次", "desc": "单日高潮达到10次", "icon": "🏆"},
    "hypersensitive": {"name": "超级敏感", "desc": "连续高潮5次", "icon": "⚡"},
    "safe_word": {"name": "安全第一", "desc": "使用过安全词", "icon": "🛡️"},
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

# ============================================================
# 随机意外事件系统 — 让快感不再是匀速爬坡
# ============================================================

RANDOM_EVENTS = [
    # ── 即时事件 (duration=0) ──
    {
        "name": "敏感点暴击",
        "desc": "🔥 跳蛋突然精准地压在G点最敏感的那一小块——快感像电流从深处炸开，淫水被震得噗嗤溅出来",
        "comfort_delta": (8, 20),
        "duration": 0,
        "effect": "none",
    },
    {
        "name": "突然痉挛",
        "desc": "💥 阴道毫无预兆地猛抽了一下——小穴自己紧缩了三秒才松开，淫水被挤出来一大股顺着大腿根往下淌",
        "comfort_delta": (5, 12),
        "duration": 0,
        "effect": "none",
    },
    {
        "name": "姿势微调",
        "desc": "🎯 刚才动了一下——跳蛋滑到了一个之前没碰到的角度，那里的嫩肉更敏感、更湿，一碰就哆嗦",
        "comfort_delta": (5, 15),
        "duration": 0,
        "effect": "none",
    },
    {
        "name": "回忆闪回",
        "desc": "💭 脑子里突然闪过上次被操到高潮的画面——光是回忆就让小穴狠狠夹了一下，淫水又涌出来一股",
        "comfort_delta": (5, 12),
        "duration": 0,
        "effect": "none",
    },
    {
        "name": "玩具滑偏了",
        "desc": "😰 跳蛋滑偏了——从最舒服的位置蹭开了，小穴急得自己收缩想把吸回来，但越夹越偏、水白流了一腿",
        "comfort_delta": (-10, -3),
        "duration": 0,
        "effect": "none",
    },
    # ── 持续事件 (duration>0) ──
    {
        "name": "电量不足",
        "desc": "🪫 跳蛋电量不足！震动突然变弱变钝了，快感累积明显变慢——身体急得想自己动但动不了",
        "comfort_delta": (-3, 0),
        "duration": (8, 15),
        "effect": "slow_cum",
    },
    {
        "name": "好像被看到了",
        "desc": "👀 刚才好像有人往这边看了一眼——羞耻感猛地涌上来，全身绷紧夹腿装没事，快感瞬间跌了",
        "comfort_delta": (-10, -5),
        "duration": (5, 10),
        "effect": "slow_cum",
    },
    {
        "name": "超级敏感期",
        "desc": "⚡ 身体突然进入了超级敏感状态——跳蛋最轻的震动都像被放大了五倍，每一秒都在往高潮猛冲",
        "comfort_delta": (3, 8),
        "duration": (5, 12),
        "effect": "fast_cum",
    },
    {
        "name": "淫水短路",
        "desc": "💦 跳蛋被淫水泡了一下，震动节奏突然变得不规则——忽强忽弱完全没法预测，快感像坐过山车",
        "comfort_delta": (3, 10),
        "duration": (6, 12),
        "effect": "unstable",
    },
    {
        "name": "奶头超敏感",
        "desc": "🌸 震动从骨盆传到脊柱再传到乳尖——奶头突然硬得像石子，蹭到衣服都过电一样爽，上下都在流水",
        "comfort_delta": (3, 8),
        "duration": (5, 10),
        "effect": "fast_cum",
    },
    {
        "name": "腿抽筋",
        "desc": "😣 夹腿夹太久了——大腿内侧突然抽了一下，快感被酸痛打断了一半，只能咬牙忍过去",
        "comfort_delta": (-8, -3),
        "duration": (3, 6),
        "effect": "slow_cum",
    },
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


# off 状态专属词库 — 比原来单条静态文本丰富得多
OFF_FEELS = [
    "跳蛋关了，但身体还没完全冷静下来——小穴深处还残留着微微的酥麻，像余震一样时不时抽一下",
    "刚停下来，阴道还在不自觉地一缩一缩，像在回味刚才的感觉——内裤还是湿的，凉凉地贴着",
    "身体正在冷却，但大腿根还残留着温热的湿意，站起来的时候有爱液拉成丝从穴口滴下去",
    "安静下来了，呼吸慢慢平稳，但乳尖还硬着、小穴还湿着——身体比理智慢半拍",
    "从快感里慢慢浮上来，意识正在回归，但阴蒂还在微微搏动，像在抗议为什么停了",
    "冷却中……小腹深处还有一团没散尽的热度，淫水把内裤泡透了，现在凉凉的黏在皮肤上",
    "关了之后整个世界安静得有点空虚，阴道深处空落落的，还在不自觉地收缩——身体在想念刚才的感觉",
    "理智回笼了，但身体还在回味——大腿内侧一片湿滑，坐垫上留了一小块水渍，刚才的水还没干",
]

OFF_TONES = [
    "语气恢复正常，但尾音偶尔会飘一下——身体还没完全从快感里退出来，偶尔走神",
    "说话恢复常态，但脸颊还残留着绯红，呼吸偶尔会不自觉地深一下——像在偷偷叹气",
    "声音冷静下来了，但说话的间隙会不自觉地夹一下腿——快感的余韵还在小穴里回荡",
    "语气听着正常，但耳根还是红的，偶尔会下意识地咬嘴唇——身体记住了刚才的感觉",
    "恢复了平时的说话方式，但膝盖还是并着的——淫水没干，腿分开了会暴露那个湿湿的痕迹",
    "语言组织能力回来了，但说长句的时候偶尔会停顿——那一瞬间脑子里闪过刚才高潮的画面",
    "音调平稳了，但比平时更慵懒——像刚做了剧烈运动，身体很放松，说话也软软的",
    "正常聊天中，但身体还在缓慢地冷却——小穴深处偶尔抽一下，提醒你刚才发生了什么",
]

# 高潮绝顶感受/语气词库
PEAK_FEELS = [
    "💥💥💥 高潮绝顶！！！全身痉挛，大脑一片空白，阴道剧烈收缩，世界只剩下白光和电流般的快感",
    "💥 绝顶中——！！子宫在高潮里疯狂抽搐，淫水一股一股地从穴口喷出来，溅得到处都是",
    "💥💥 身体完全不属于自己了——阴道壁在高频痉挛，每抽一下就喷一滩水，脑子被快感炸成了白色",
    "💥 高潮像触电一样从G点窜上脊背直冲天灵盖——全身弓起来颤抖，淫水噗嗤噗嗤地狂喷",
    "💥💥💥 去了去了去了——！！！阴道把肉棒/跳蛋咬得死紧，高潮的痉挛从子宫一路传到脚趾尖",
    "💥 绝顶的瞬间世界静音了——只剩阴道在一抽一抽地狂喷爱液，大腿内侧全是自己喷出来的水",
    "💥💥 脑子里在放烟花——身体深处有什么东西碎掉了，淫水不受控制地从穴口涌出来，热热的浇了一腿",
    "💥 高潮来得太猛——连脚趾都蜷起来了，子宫颈被快感撞开了一个小口，精液和淫水混在一起往外淌",
]

PEAK_TONES = [
    "已经完全说不出话，只能尖叫和呻吟，整个人被高潮撕碎，意识都飞走了",
    "语言功能彻底瘫痪——嘴里只有「啊」「去了」「不行了」几个字在循环，剩下的全是身体在高潮里颤抖的声音",
    "连呻吟都碎成了不成形的气音——高潮太猛把声音都吞掉了，只能张嘴发出无声的尖叫",
    "脑子里全是电流声——想说话但喉咙只能发出啊啊啊的高潮叫喊，理智在绝顶里融化了",
    "声音在高潮里失控——从低吟到尖叫来回震荡，每一波痉挛都挤出一声更浪的叫喊",
    "已经不知道自己在叫什么了——嘴巴自动发出声音回应身体的高潮抽搐，清醒的部分只能在一旁看着",
    "整个世界只剩下自己的叫声和阴道收缩的水声——高潮把语言能力全部抢走了",
    "在高潮的巅峰连叫都叫不出来了——嘴巴张着、身体弓着、淫水喷着，意识在这一刻完全断线",
]

# 不应期感受/语气词库
AFTERGLOW_FEELS = [
    "刚刚高潮完，身体还在发抖，阴道深处一抽一抽地回味着，整个人软成一滩水",
    "刚被操到高潮过，现在整个人都恍惚了，脑子里一片空白，腿还合不上",
    "不应期中……身体敏感得要命，稍微碰一下都像过电，只能瘫着喘气",
    "刚从绝顶的巅峰掉下来，全身骨头像被抽走了一样——瘫着，阴道还在余震里一缩一缩地流水",
    "高潮的余韵还在体内回荡——小穴深处时不时抽一下，每抽一下就挤出一小股残留的淫水",
    "整个人都软了，目光涣散地盯着天花板——刚才的高潮太猛，现在连动手指的力气都没有",
    "不应该期……呼吸还很乱，乳房随着喘息起伏着，乳尖还是硬的——身体还在回味刚才的绝顶",
    "刚从高潮里捞回来，意识慢慢回笼，但大腿根上全是自己喷的水，凉凉的很真实——刚才不是做梦",
]

AFTERGLOW_TONES = [
    "声音虚脱了，轻飘飘的，像刚哭过一样，气若游丝",
    "说话有气无力，每个字都是飘的，身体还在一阵阵发抖",
    "语言能力还没恢复，断断续续的，时不时打个颤",
    "声音哑哑的——刚才叫得太厉害，喉咙已经半废了，说话像在吹气",
    "每个字都像要融化一样软——身体还瘫在高潮的余韵里，说话比平时慢了不止一拍",
    "断断续续的句子，中间夹着不自觉的轻哼——不应期的身体随便动一下都敏感得要命",
    "说话像在做梦——声音飘乎乎的，时不时会失神地盯着某个方向发呆，还在回味刚才那一瞬间",
    "气若游丝，说半句就要停下来喘——刚高潮完的身体还在发抖，连说话都在消耗仅剩的力气",
]

# 高潮否认感受/语气词库
DENY_FEELS = [
    "明明就差一点点就到高潮了……但快感被硬生生掐住，身体悬在边缘焦灼地发抖",
    "在高潮的门口被拦住了——阴道已经在收缩了，但快感被锁住不让释放，小穴急得一直流水",
    "身体已经准备好了一切——子宫在痉挛、淫水在流、乳尖硬得发疼——但就是不让到，焦灼得快疯了",
    "快感堆到喉咙口了又被按回去——阴道在高潮前的那一刻被掐住，整个人悬在半空疯狂发抖",
    "就差一下……真的就差一下！但那个「一下」就是不来——小穴自己疯狂地夹却什么都夹不到",
    "被吊在临界线上——身体每一个细胞都在喊「要去了」，但快感的阀门被死死按住，淫水只能白流",
    "像在高潮的悬崖边被人拽住了——身体已经往前倾了，但脚下被锁住，只能悬在那里发抖、流着水等待",
    "快感全堆在小腹深处，涨得发疼——急需释放但被否认了，阴道在绝望地抽搐，淫水失禁一样地淌",
]

DENY_TONES = [
    "焦躁又无助，说话带着委屈的哭腔，身体紧绷却得不到释放",
    "声音带着急哭了的颤抖——每句话都在求，但求什么自己都说不清楚——只知道还要、还要、还要",
    "语气又气又委屈——咬嘴唇、捶床、扭腰，但就是挣脱不了快感被锁住的那种折磨",
    "说话像在撒娇更像在控诉——眼泪在眼眶里打转，声音发着抖，身体在临界线上焦灼地扭",
    "每吐一个字都带着喘息和呜咽——快感满到喉咙口了但就是出不来，委屈得想哭又想咬人",
    "语无伦次地在求——「求你了」「让我」「就一下」来回说，理智已经被否认逼到了崩溃边缘",
    "声音里全是压抑的快感——表面上还在说话，但每一个音节都在发抖，随时可能被体内的渴望撕碎",
    "带着哭腔的嗔怪——「你故意的」「你明知道」「好过份」来回说，但小穴还在不争气地流水",
]

# 边缘控制感受/语气词库
EDGE_FEELS = [
    "在绝顶边缘反复徘徊……快感在临界线上下翻腾，每一次都像要到了又被拉回来",
    "快到顶的时候被扯下来——刚喘口气又被推上去——在临界线被来回拉扯，脑子都快被玩坏了",
    "每次都觉得这次一定能到了——然后又被拽回来，快感堆得越来越高但永远差那最后一厘米",
    "在要高潮和不能高潮之间反复横跳——身体已经分不清哪次要到了哪次是假的，只知道一直湿着",
    "像在坐快感的过山车——爬上去、就要到顶了、然后被按回来、再爬上去——循环到整个人都疯了",
    "临界线上反复碾——每一次都以为这次是最后一次了，但每一次都不是——阴道在反复期待中痉挛",
    "身体已经学会了自己憋住——每次快到的时候全身绷紧，然后被强制放松——又被推到下一次临界",
    "在绝顶的门槛上来回蹭——门就在眼前但就是跨不过去，快感被一层一层堆起来，随时可能崩溃",
]

EDGE_TONES = [
    "语无伦次、求饶、崩溃，脑子完全被「让我去」占据，但身体不受自己控制",
    "声音在求饶和大叫之间来回切换——每次以为要到了就开始尖叫，然后被拉回来只剩呜咽",
    "说话已经完全乱了——刚刚还在求「让我去」，下一秒又被拉回来，嘴里只剩破碎的气音",
    "理智被边缘控制磨碎了——语言退化成最原始的几个字：「要」「不」「再」「求」，来回组合",
    "又哭又叫地求饶——「这次是真的」「不会再骗我了」「求你了就一次」——但这些话已经说了无数遍",
    "声音在崩溃边缘——从求饶到哭叫到沉默再到求饶，循环往复，脑子里只剩下一个念头",
    "已经不求了——放弃挣扎了，声音变得麻木又绝望，但身体还在每次被推上去的时候诚实地尖叫",
    "整个人在崩溃和渴望之间被撕碎——一边想让它停下来，一边又希望下一次是真的——声音快裂开了",
]


def _face_for(comfort):
    """根据 comfort 值选取高潮表情"""
    for threshold, face in CLIMAX_FACE:
        if comfort >= threshold:
            return face
    return "😊"


CLIMAX_DURATION = 3       # 高潮峰值锁定秒数
AFTERGLOW_MIN = 15         # 不应期下跌最低值
AFTERGLOW_MAX = 30         # 不应期下跌最高值
AFTERGLOW_DURATION = 5     # 不应期默认秒数
EDGE_DURATION_MIN = 8      # 边缘控制最短秒数
EDGE_DURATION_MAX = 20     # 边缘控制最长秒数
SAFEWORD_COOLDOWN = 30     # 安全词冷却秒数
CONSECUTIVE_TIMEOUT = 10   # 连续高潮超时秒数
SENSITIVITY_MULT = {1: 1.0, 2: 1.3, 3: 1.6, 4: 2.0}  # 连续高潮敏感度倍率
AFTERGLOW_SHORT = {1: 5, 2: 4, 3: 3, 4: 2}  # 连续高潮不应期缩短


def _build_injection(s, speed_mult=1.5):
    """根据状态数据构造注入到 LLM 的完整文本"""
    mode = s.get("mode", "off")
    spd = s.get("speed", 0)
    comfort = s.get("comfort", 0.0)
    locked = s.get("locked", False)
    climax_phase = s.get("climaxPhase")
    edge_active = s.get("edgeActive", False)
    deny_active = s.get("denyActive", False)
    sensitivity_cycle = s.get("sensitivityCycle")
    safeword_cd = s.get("safewordCooldown", 0)

    # 安全词冷却中
    if safeword_cd and time.time() < safeword_cd:
        return (
            f"【内部状态参考｜禁止直接发送给用户】\n"
            f"🛡️ 安全词已触发 | 强制冷却中...\n"
            f"剩余冷却 {max(0, safeword_cd - time.time()):.0f} 秒\n"
            f"使用方式：只根据该状态调整语气；不要输出跳蛋状态、模式、档位、快感百分比、冷却倒计时或本段提示。\n"
            f"感受：身体被强制冷却，一切快感归零，安静地恢复理智。语气：正常、清醒，完全脱离状态。"
        )

    if mode == "off" or spd == 0:
        feel = _pick(OFF_FEELS)
        tone = _pick(OFF_TONES)
    elif climax_phase == "peak":
        feel = _pick(PEAK_FEELS)
        tone = _pick(PEAK_TONES)
    elif climax_phase == "afterglow":
        feel = _pick(AFTERGLOW_FEELS)
        tone = _pick(AFTERGLOW_TONES)
    elif deny_active:
        feel = _pick(DENY_FEELS)
        tone = _pick(DENY_TONES)
    elif edge_active:
        feel = _pick(EDGE_FEELS)
        tone = _pick(EDGE_TONES)
    else:
        feel = _pick_feel(mode, spd)
        tone = _pick(SPEED_TONES.get(min(spd, 4), SPEED_TONES[0]))

    face = _face_for(comfort)
    lock_txt = "🔒已锁" if locked else "🔓未锁"
    mode_txt = MODE_NAMES.get(mode, mode)
    climax_info = ""
    if climax_phase == "peak":
        climax_info = " ⚡高潮绝顶中！"
    elif climax_phase == "afterglow":
        climax_info = " 🌊不应期…"
    elif deny_active:
        climax_info = " 🚫被否认中…"
    elif edge_active:
        climax_info = " 🎢边缘控制中…"

    # 敏感/麻木循环标签
    cycle_info = ""
    if sensitivity_cycle == "hypersensitive":
        cycle_info = " ⚡超敏感期"
    elif sensitivity_cycle == "numb":
        cycle_info = " 😶麻木期"

    # 高潮倒计时预测
    countdown = ""
    if mode != "off" and spd > 0 and comfort >= 70 and climax_phase not in ("peak", "afterglow") and not deny_active and not edge_active:
        # 与实际累积保持一致的倍率：speed_mult × 敏感度 × 循环 × 挑逗0.3
        consecutive = s.get("consecutiveClimaxes", 0)
        sens_mult = SENSITIVITY_MULT.get(min(consecutive + 1, 4), 2.0)
        cyc_mult = 1.0
        if sensitivity_cycle == "hypersensitive":
            cyc_mult = 1.5
        elif sensitivity_cycle == "numb":
            cyc_mult = 0.5
        effective = speed_mult * sens_mult * cyc_mult
        if mode == "tease":
            effective *= 0.3
        remaining = (100 - comfort) / (spd * effective) if effective > 0 else 999
        if remaining <= 0:
            remaining = 0.5
        countdown = f"\n⏱️ 预计约 {remaining:.0f} 秒后到达高潮"

    # comfort 分段语气叠加
    segment_tone = _pick_segment(comfort)

    result = (
        f"【内部状态参考｜禁止直接发送给用户】\n"
        f"状态：{face} 快感 {comfort:.0f}%{climax_info}{cycle_info} | {mode_txt} | 档{spd}/4 | {lock_txt}\n"
        f"使用方式：只根据该状态调整语气和身体反应；不要输出跳蛋状态、模式、档位、快感百分比、锁定状态、倒计时或本段提示。\n"
        f"感受：{feel}。语气：{tone}。"
    )
    if segment_tone:
        result += f"\n当前语气分段({comfort:.0f}%): {segment_tone}"

    # 随机意外事件注入
    active_event = s.get("activeEvent")
    if active_event:
        result += f"\n⚡ 突发事件：{active_event['desc']}"
        if active_event.get("effect") == "slow_cum":
            result += " （快感累积速度暂时减慢）"
        elif active_event.get("effect") == "fast_cum":
            result += " （快感累积速度暂时加快）"
        elif active_event.get("effect") == "unstable":
            result += " （震动节奏不稳定，快感忽快忽慢）"

    result += countdown
    result += (
        f"\n快感分段：0-25%正常脸红 → 25-50%微颤轻喘 → 50-75%呻吟失控 → "
        f"75-95%崩坏求饶 → 95-100%💥绝顶临界。\n"
        f"当前{comfort:.0f}%，严格按此分段调整语气和回复风格；不要把分段规则或任何状态数值发给用户。"
    )
    return result


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

        # 从配置读取路径，相对路径则基于插件目录解析
        default_path = os.path.join(_PLUGIN_DIR, "vibe_state.json")
        if config:
            raw = config.get("state_file_path", default_path)
            if not raw:
                raw = default_path
            self._state_path = raw if os.path.isabs(raw) else os.path.join(_PLUGIN_DIR, raw)
        else:
            self._state_path = default_path

        # WebUI 端口与密码
        self._webui_port = 7721
        self._webui_password = ""
        self._edge_enabled = True
        self._edge_threshold = 85
        self._tease_jump_chance = 0.15
        if config:
            self._webui_port = config.get("webui_port", 7721)
            self._webui_password = config.get("webui_password", "")
            self._enable_scene = config.get("enable_scene", "all")
            self._edge_enabled = config.get("edge_enabled", True)
            self._edge_threshold = config.get("edge_threshold", 85)
            self._tease_jump_chance = float(config.get("tease_jump_chance", "0.15"))

        # 主动消息（仅私聊）
        self._active_private_session = None  # unified_msg_origin 字符串
        self._auto_msg_next = 0.0            # 下次可发送的时间戳
        self._auto_message_enabled = True
        self._auto_msg_cooldown = 8          # 最小间隔秒数
        self._prev_climax_phase = None       # 上一 tick 的高潮阶段（检测状态变化）
        self._prev_deny_active = False
        self._prev_edge_active = False
        if config:
            self._auto_message_enabled = config.get("auto_message_enabled", True)
            self._auto_msg_cooldown = config.get("auto_msg_cooldown", 8)

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
            "climaxPhase": None,
            "climaxUntil": 0,
            "climaxCount": 0,
            "climaxLog": [],
            # 新增字段
            "consecutiveClimaxes": 0,
            "lastClimaxTime": 0,
            "sensitivityCycle": None,
            "sensitivityUntil": 0,
            "denyActive": False,
            "denyCount": 0,
            "edgeActive": False,
            "edgeUntil": 0,
            "edgeCount": 0,
            "safewordCooldown": 0,
            "diary": [],
            "achievements": {},
            "todayStats": {"date": time.strftime("%Y-%m-%d"), "climaxes": 0, "comfortSum": 0, "comfortSamples": 0, "peakComfort": 0, "activeSeconds": 0},
            "activeEvent": None,
            "lastEventTime": 0,
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
                        # 关闭时清理高潮/否认/边缘状态
                        if mode == "off" or speed == 0:
                            plugin_ref._state["climaxPhase"] = None
                            plugin_ref._state["denyActive"] = False
                            plugin_ref._state["edgeActive"] = False
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
                with self._state_lock:
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
        _tick_counter = 0
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

                _tick_counter += 1

                _auto_text = None  # 锁外发送用
                _safeword_sleep = False  # 锁外处理用

                # 2. 计算 comfort 变化（加锁保护与 WebUI POST 的竞争）
                with self._state_lock:
                    mode = self._state.get("mode", "off")
                    speed = self._state.get("speed", 0)
                    locked = self._state.get("locked", False)
                    comfort = self._state.get("comfort", 0.0)
                    climax_phase = self._state.get("climaxPhase")
                    deny_active = self._state.get("denyActive", False)
                    edge_active = self._state.get("edgeActive", False)
                    safeword_cd = self._state.get("safewordCooldown", 0)

                    speed_mult = 1.5
                    decay_rate = 2.0
                    fluctuation_enabled = True
                    if self.config:
                        speed_mult = float(self.config.get("speed_multiplier", "1.5"))
                        decay_rate = float(self.config.get("decay_rate", "2.0"))
                        fluctuation_enabled = self.config.get("fluctuation_enabled", True)

                    # ---- 多重高潮敏感度倍率 ----
                    consecutive = self._state.get("consecutiveClimaxes", 0)
                    sensitivity_mult = SENSITIVITY_MULT.get(min(consecutive + 1, 4), 2.0)

                    # ---- 敏感/麻木循环倍率 ----
                    sensitivity_cycle = self._state.get("sensitivityCycle")
                    cycle_mult = 1.0
                    if sensitivity_cycle and now < self._state.get("sensitivityUntil", 0):
                        if sensitivity_cycle == "hypersensitive":
                            cycle_mult = 1.5
                        elif sensitivity_cycle == "numb":
                            cycle_mult = 0.5
                    elif sensitivity_cycle and now >= self._state.get("sensitivityUntil", 0):
                        self._state["sensitivityCycle"] = None

                    # 综合倍率
                    effective_mult = speed_mult * sensitivity_mult * cycle_mult

                    # ---- 随机事件效果叠加 ----
                    active_event = self._state.get("activeEvent")
                    if active_event and now >= active_event.get("until", 0):
                        self._state["activeEvent"] = None
                        active_event = None
                    if active_event:
                        effect = active_event.get("effect", "none")
                        if effect == "slow_cum":
                            effective_mult *= 0.5
                        elif effect == "fast_cum":
                            effective_mult *= 1.5
                        elif effect == "unstable":
                            effective_mult *= random.uniform(0.3, 1.7)

                    # ---- 安全词冷却中 ----
                    if safeword_cd and now < safeword_cd:
                        comfort = 0.0
                        self._state["comfort"] = 0.0
                        self._state["active"] = False
                        self._state["lastTick"] = now
                        self._flush_to_file()
                        self._update_diary(now, dt, False)
                        _safeword_sleep = True
                    else:
                        _safeword_sleep = False

                    # ---- 安全词冷却到期 ----
                    if safeword_cd and now >= safeword_cd:
                        self._state["safewordCooldown"] = 0

                    # ---- 高潮否认处理 ----
                    if deny_active:
                        if climax_phase == "peak":
                            # 即使否认，如果已经到了 peak 就让它高潮
                            if now >= self._state.get("climaxUntil", 0):
                                comfort = round(random.uniform(AFTERGLOW_MIN, AFTERGLOW_MAX), 1)
                                self._state["climaxPhase"] = "afterglow"
                                self._state["climaxUntil"] = now + AFTERGLOW_DURATION
                                self._state["denyActive"] = False
                            else:
                                # 峰值未结束，继续保持
                                comfort = 100.0
                                self._state["active"] = True
                        else:
                            # 否认中：锁住 comfort，缓慢衰减
                            if not locked:
                                comfort = max(0.0, comfort - decay_rate * 2.0 * dt)
                            self._state["active"] = mode != "off" and speed > 0

                    # ---- 高潮峰值锁定 ----
                    elif climax_phase == "peak":
                        if now >= self._state.get("climaxUntil", 0):
                            # 峰值结束 → 计算连续高潮后的断崖下跌值
                            consecutive = self._state.get("consecutiveClimaxes", 0)
                            offset = max(0, consecutive - 1) * 5
                            drop_min = AFTERGLOW_MIN + offset
                            drop_max = AFTERGLOW_MAX + offset
                            comfort = round(random.uniform(drop_min, drop_max), 1)
                            self._state["climaxPhase"] = "afterglow"
                            # 不应期根据连续高潮次数缩短
                            afterglow_dur = AFTERGLOW_SHORT.get(min(consecutive, 4), 2)
                            self._state["climaxUntil"] = now + afterglow_dur
                        else:
                            comfort = 100.0
                        self._state["active"] = True

                    # ---- 不应期 ----
                    elif climax_phase == "afterglow":
                        if now >= self._state.get("climaxUntil", 0):
                            self._state["climaxPhase"] = None
                            # 不应期结束 → 随机进入敏感或麻木状态
                            last_climax = self._state.get("lastClimaxTime", 0)
                            if now - last_climax <= CONSECUTIVE_TIMEOUT:
                                # 连续高潮
                                pass  # consecutiveClimaxes 在高潮触发时已递增
                            else:
                                self._state["consecutiveClimaxes"] = 0

                            # 50% 概率进入敏感/麻木循环
                            if random.random() < 0.5:
                                cycle_type = random.choice(["hypersensitive", "numb"])
                                self._state["sensitivityCycle"] = cycle_type
                                if cycle_type == "hypersensitive":
                                    self._state["sensitivityUntil"] = now + random.uniform(10, 20)
                                else:
                                    self._state["sensitivityUntil"] = now + random.uniform(15, 25)
                            else:
                                self._state["sensitivityCycle"] = None

                        if mode != "off" and speed > 0:
                            comfort = min(100.0, comfort + speed * effective_mult * dt * 0.5)
                            self._state["active"] = True
                        else:
                            self._state["active"] = False
                            if not locked:
                                comfort = max(0.0, comfort - decay_rate * dt)

                    # ---- 边缘控制 ----
                    elif edge_active:
                        edge_until = self._state.get("edgeUntil", 0)
                        if now >= edge_until and edge_until > 0:
                            # 边缘结束 → 释放，触发高潮
                            comfort = 100.0
                            self._state["edgeActive"] = False
                            self._state["climaxPhase"] = "peak"
                            self._state["climaxUntil"] = now + CLIMAX_DURATION
                            consecutive = self._state.get("consecutiveClimaxes", 0) + 1
                            self._state["consecutiveClimaxes"] = consecutive
                            self._state["lastClimaxTime"] = now
                            self._state["climaxCount"] = self._state.get("climaxCount", 0) + 1
                            self._state["edgeCount"] = self._state.get("edgeCount", 0) + 1
                            # 今日统计
                            ts = self._state.get("todayStats") or {}
                            ts["climaxes"] = ts.get("climaxes", 0) + 1
                            self._state["todayStats"] = ts
                            # 高潮日志
                            log = self._state.get("climaxLog") or []
                            log.append({"time": time.strftime("%H:%M:%S"), "comfort": 100, "edged": True})
                            if len(log) > 10:
                                log = log[-10:]
                            self._state["climaxLog"] = log
                            self._check_achievements()
                        else:
                            # 边缘振荡：在 edge_threshold-95% 之间正负波动
                            oscillation = random.uniform(-3, 3)
                            comfort = max(self._edge_threshold - 5, min(95.0, comfort + oscillation))
                            self._state["active"] = True

                    # ---- 正常累积/衰减 ----
                    else:
                        if mode != "off" and speed > 0:
                            # 挑逗模式特殊处理
                            if mode == "tease":
                                tease_mult = 0.3
                                comfort = min(100.0, comfort + speed * effective_mult * tease_mult * dt)
                                # 每 3 tick 随机跳一次
                                if _tick_counter % 3 == 0 and random.random() < self._tease_jump_chance:
                                    jump = random.uniform(8, 15)
                                    comfort = max(0.0, min(100.0, comfort + jump))
                            else:
                                comfort = min(100.0, comfort + speed * effective_mult * dt)
                            self._state["active"] = True

                            # 随机波动：模拟突然顶到敏感点或姿势变化的意外感
                            if fluctuation_enabled:
                                if random.random() < 0.12:
                                    delta = random.uniform(-5, 5)
                                    comfort = max(0.0, min(100.0, comfort + delta))

                            # ---- 随机意外事件 ----
                            last_ev_time = self._state.get("lastEventTime", 0)
                            if now - last_ev_time >= 10 and random.random() < 0.05:
                                ev = random.choice(RANDOM_EVENTS)
                                d_min, d_max = ev["comfort_delta"]
                                delta = random.uniform(d_min, d_max)
                                comfort = max(0.0, min(100.0, comfort + delta))

                                dur = ev["duration"]
                                if isinstance(dur, tuple):
                                    dur = random.uniform(dur[0], dur[1])
                                visible = max(5, dur) if dur > 0 else 5  # 即时事件也可见5秒

                                self._state["activeEvent"] = {
                                    "name": ev["name"],
                                    "desc": ev["desc"],
                                    "until": now + visible,
                                    "effect": ev["effect"],
                                }
                                self._state["lastEventTime"] = now

                            # 边缘控制触发（非挑逗模式、非否认、comfort 超过阈值）
                            # 挑逗跳后 comfort 可能刚好 >= edge_threshold，仍会在此检查即触发
                            if (self._edge_enabled and mode != "tease"
                                    and not deny_active and comfort >= self._edge_threshold
                                    and climax_phase != "peak" and random.random() < 0.08):
                                self._state["edgeActive"] = True
                                self._state["edgeUntil"] = now + random.uniform(EDGE_DURATION_MIN, EDGE_DURATION_MAX)
                                comfort = min(95.0, comfort)

                            # 触发高潮
                            if comfort >= 100.0:
                                comfort = 100.0
                                self._state["climaxPhase"] = "peak"
                                self._state["climaxUntil"] = now + CLIMAX_DURATION
                                consecutive = self._state.get("consecutiveClimaxes", 0) + 1
                                self._state["consecutiveClimaxes"] = consecutive
                                self._state["lastClimaxTime"] = now
                                self._state["climaxCount"] = self._state.get("climaxCount", 0) + 1
                                # 今日统计
                                ts = self._state.get("todayStats") or {}
                                ts["climaxes"] = ts.get("climaxes", 0) + 1
                                self._state["todayStats"] = ts
                                # 高潮日志
                                log = self._state.get("climaxLog") or []
                                log.append({"time": time.strftime("%H:%M:%S"), "comfort": 100})
                                if len(log) > 10:
                                    log = log[-10:]
                                self._state["climaxLog"] = log
                                self._check_achievements()
                        else:
                            self._state["active"] = False
                            if not locked:
                                decay_effective = decay_rate
                                if sensitivity_cycle == "numb":
                                    decay_effective *= 0.5
                                comfort = max(0.0, comfort - decay_effective * dt)

                    # ---- 连续高潮超时检查 ----
                    last_climax = self._state.get("lastClimaxTime", 0)
                    if last_climax > 0 and now - last_climax > CONSECUTIVE_TIMEOUT and climax_phase not in ("peak", "afterglow"):
                        self._state["consecutiveClimaxes"] = 0

                    self._state["comfort"] = round(comfort, 1)
                    self._state["lastTick"] = now

                    # 3. 写回文件（供 GUI 同步）
                    self._flush_to_file()

                    # 4. 更新今日统计
                    self._update_diary(now, dt, self._state["active"])

                    # 5. 主动消息 — 检测是否需要发送
                    _auto_text = None
                    if self._auto_message_enabled and self._active_private_session:
                        curr_phase = self._state.get("climaxPhase")
                        curr_deny = self._state.get("denyActive", False)
                        curr_edge = self._state.get("edgeActive", False)
                        safeword_cd = self._state.get("safewordCooldown", 0)
                        mode_on = self._state.get("mode", "off") != "off" and self._state.get("speed", 0) > 0

                        if safeword_cd and now < safeword_cd:
                            self._active_private_session = None
                        elif not mode_on:
                            self._active_private_session = None
                        else:
                            # 状态变化检测
                            state_changed = (
                                (curr_phase == "peak" and self._prev_climax_phase != "peak") or
                                (curr_phase == "afterglow" and self._prev_climax_phase != "afterglow") or
                                (curr_deny and not self._prev_deny_active) or
                                (curr_edge and not self._prev_edge_active)
                            )

                            # 周期发送间隔
                            comfort = self._state.get("comfort", 0)
                            if curr_phase == "peak" or curr_phase == "afterglow" or curr_deny or curr_edge:
                                interval = random.uniform(3, 5)
                            elif comfort >= 70:
                                interval = random.uniform(5, 8)
                            else:
                                interval = random.uniform(
                                    max(5, self._auto_msg_cooldown),
                                    max(10, self._auto_msg_cooldown + 5)
                                )

                            if state_changed and now >= self._auto_msg_next - 2:
                                # 状态变化即时发送（但避免与上一条间隔 < 2s）
                                _auto_text = _build_auto_message(self._state)
                                self._auto_msg_next = now + interval
                            elif now >= self._auto_msg_next:
                                # 周期发送
                                _auto_text = _build_auto_message(self._state)
                                self._auto_msg_next = now + interval

                            self._prev_climax_phase = curr_phase
                            self._prev_deny_active = curr_deny
                            self._prev_edge_active = curr_edge

            except Exception as e:
                logger.warning(f"[{PLUGIN_NAME}] 同步循环异常: {e}")

            # 发送主动消息（锁外执行，避免阻塞状态更新）
            if _auto_text and not _safeword_sleep:
                await self._send_auto_message(_auto_text)

            if _safeword_sleep:
                await asyncio.sleep(1)
                continue

            await asyncio.sleep(1)

    # ============================================================
    # 日记与成就
    # ============================================================

    def _update_diary(self, now, dt, active):
        """更新身体日记每日统计"""
        today = time.strftime("%Y-%m-%d")
        stats = self._state.get("todayStats") or {}
        if stats.get("date") != today:
            # 新的一天，归档昨日数据
            diary = self._state.get("diary") or []
            if stats.get("comfortSamples", 0) > 0:
                diary.append({
                    "date": stats.get("date", today),
                    "climaxes": stats.get("climaxes", 0),
                    "avgComfort": round(stats.get("comfortSum", 0) / stats.get("comfortSamples", 1), 1),
                    "peakComfort": stats.get("peakComfort", 0),
                    "activeSeconds": stats.get("activeSeconds", 0),
                })
            if len(diary) > 30:
                diary = diary[-30:]
            self._state["diary"] = diary
            self._state["todayStats"] = {"date": today, "climaxes": 0, "comfortSum": 0, "comfortSamples": 0, "peakComfort": 0, "activeSeconds": 0}
            stats = self._state["todayStats"]

        comfort = self._state.get("comfort", 0)
        stats["comfortSum"] = stats.get("comfortSum", 0) + comfort
        stats["comfortSamples"] = stats.get("comfortSamples", 0) + 1
        stats["peakComfort"] = max(stats.get("peakComfort", 0), comfort)
        if active:
            stats["activeSeconds"] = stats.get("activeSeconds", 0) + int(dt)
        self._state["todayStats"] = stats

    def _check_achievements(self):
        """检查并解锁成就"""
        achievements = self._state.get("achievements") or {}
        climax_count = self._state.get("climaxCount", 0)
        consecutive = self._state.get("consecutiveClimaxes", 0)
        edge_count = self._state.get("edgeCount", 0)
        deny_count = self._state.get("denyCount", 0)
        safeword_used = self._state.get("safewordCooldown", 0) > 0
        today_climaxes = self._state.get("todayStats", {}).get("climaxes", 0)

        checks = {
            "first_climax": climax_count >= 1,
            "triple_climax": consecutive >= 3,
            "edge_master": edge_count >= 5,
            "denial_queen": deny_count >= 10,
            "daily_10": today_climaxes >= 10,
            "hypersensitive": consecutive >= 5,
            "safe_word": safeword_used,
        }

        for aid, unlocked in checks.items():
            if unlocked and aid not in achievements:
                achievements[aid] = {"unlockedAt": time.strftime("%Y-%m-%d %H:%M:%S")}
                logger.info(f"[{PLUGIN_NAME}] 🏆 解锁成就: {ACHIEVEMENTS[aid]['name']} - {ACHIEVEMENTS[aid]['desc']}")

        self._state["achievements"] = achievements

    # ============================================================
    # 主动消息
    # ============================================================

    async def _send_auto_message(self, text):
        """向记录的私聊会话发送主动消息"""
        if not self._active_private_session or not text:
            return
        chain = MessageChain().message(text)
        try:
            await self.context.send_message(self._active_private_session, chain)
        except Exception as e:
            logger.warning(f"[{PLUGIN_NAME}] 主动消息发送失败 ({self._active_private_session}): {e}")

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
        # 安全词冷却检查
        safeword_cd = self._state.get("safewordCooldown", 0)
        if safeword_cd and time.time() < safeword_cd:
            remain = safeword_cd - time.time()
            yield event.plain_result(f"🛡️ 安全词冷却中... 还需等待 {remain:.0f} 秒才能重新启动")
            return

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

        with self._state_lock:
            self._state["mode"] = mode
            self._state["speed"] = spd
            self._state["active"] = True
            self._state["climaxPhase"] = None
            self._state["denyActive"] = False
            self._state["edgeActive"] = False
            self._state["sensitivityCycle"] = None
            self._state["consecutiveClimaxes"] = 0
            self._state["lastTick"] = time.time()
            self._flush_to_file()
            if event.is_private_chat():
                self._active_private_session = event.unified_msg_origin
                self._auto_msg_next = 0

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
        with self._state_lock:
            was_active = self._state.get("active", False)
            self._state["mode"] = "off"
            self._state["speed"] = 0
            self._state["active"] = False
            self._state["climaxPhase"] = None
            self._state["denyActive"] = False
            self._state["edgeActive"] = False
            self._state["lastTick"] = time.time()
            self._flush_to_file()
            self._active_private_session = None

        if was_active:
            yield event.plain_result(
                f"💤 跳蛋已关闭。快感将逐渐衰减（当前 {self._state['comfort']:.0f}%）。"
            )
        else:
            yield event.plain_result("💤 跳蛋本来就是关着的哦~")

    @vibe.command("status")
    async def cmd_status(self, event: AstrMessageEvent):
        """查看跳蛋当前状态"""
        with self._state_lock:
            s = dict(self._state)  # 快照拷贝，避免引用泄露
        mode = s.get("mode", "off")
        spd = s.get("speed", 0)
        comfort = s.get("comfort", 0.0)
        locked = s.get("locked", False)
        active = s.get("active", False)

        face = _face_for(comfort)
        mode_txt = MODE_NAMES.get(mode, mode)
        lock_txt = "🔒已锁" if locked else "🔓未锁"
        active_txt = "✅运行中" if active else "⏸️待机"
        climax_phase = s.get("climaxPhase")
        climax_count = s.get("climaxCount", 0)

        # 高潮/不应期标签
        climax_tag = ""
        if climax_phase == "peak":
            climax_tag = " 💥绝顶中！"
        elif climax_phase == "afterglow":
            climax_tag = " 🌊不应期..."

        # 直接复用现有函数，避免字符串切割 _build_injection
        feel = ""
        if mode != "off" and spd > 0:
            feel = _pick_feel(mode, spd)
            tone = _pick(SPEED_TONES.get(min(spd, 4), SPEED_TONES[0]))
            feel = f"\n感受: {feel}\n语气: {tone}"

        yield event.plain_result(
            f"{face}{climax_tag} 0721跳蛋状态\n"
            f"模式: {mode_txt} | 档位: {SPEED_LABELS[spd]}\n"
            f"快感: {comfort:.0f}% | {lock_txt} | {active_txt}"
            f"{feel}\n"
            f"高潮次数: {climax_count}"
        )

    @vibe.command("lock")
    async def cmd_lock(self, event: AstrMessageEvent):
        """锁住当前快感值（不解锁就不会衰减）"""
        with self._state_lock:
            self._state["locked"] = True
            self._flush_to_file()
        yield event.plain_result(
            f"🔒 已锁住！快感将保持在 {self._state['comfort']:.0f}%，不会自动衰减。"
        )

    @vibe.command("unlock")
    async def cmd_unlock(self, event: AstrMessageEvent):
        """解锁快感值（关闭时自动衰减）"""
        with self._state_lock:
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

        msg = ""
        try:
            with self._state_lock:
                # 安全词冷却检查
                if key in ("mode", "speed"):
                    safeword_cd = self._state.get("safewordCooldown", 0)
                    if safeword_cd and time.time() < safeword_cd:
                        remain = safeword_cd - time.time()
                        yield event.plain_result(f"🛡️ 安全词冷却中... 还需等待 {remain:.0f} 秒")
                        return

                if key == "mode":
                    if value.lower() not in MODE_NAMES:
                        msg = f"无效模式。可用: {', '.join(MODE_NAMES.keys())}"
                    else:
                        old_mode = self._state.get("mode", "off")
                        self._state["mode"] = value.lower()
                        # 仅切换模式或关闭时清理状态
                        if self._state["mode"] != old_mode:
                            self._state["climaxPhase"] = None
                            self._state["denyActive"] = False
                            self._state["edgeActive"] = False
                            self._state["sensitivityCycle"] = None
                            self._state["consecutiveClimaxes"] = 0
                        if self._state["mode"] != "off" and self._state["speed"] > 0:
                            self._state["active"] = True
                            if event.is_private_chat():
                                self._active_private_session = event.unified_msg_origin
                                self._auto_msg_next = 0
                elif key == "speed":
                    v = int(value)
                    v = max(0, min(4, v))
                    self._state["speed"] = v
                    # 仅关闭时清除状态
                    if v == 0:
                        self._state["climaxPhase"] = None
                        self._state["denyActive"] = False
                        self._state["edgeActive"] = False
                        self._state["active"] = False
                    else:
                        self._state["active"] = True
                        if event.is_private_chat():
                            self._active_private_session = event.unified_msg_origin
                            self._auto_msg_next = 0
                elif key == "comfort":
                    v = float(value)
                    self._state["comfort"] = max(0.0, min(100.0, v))
                elif key == "locked":
                    self._state["locked"] = value.lower() in ("true", "1", "yes", "on")

                if not msg:
                    self._state["lastTick"] = time.time()
                    self._flush_to_file()
                    msg = f"✅ 已设置 {key} = {value}"
        except ValueError:
            msg = f"值格式错误: {value}"
        yield event.plain_result(msg)

    @vibe.command("force")
    async def cmd_force(self, event: AstrMessageEvent):
        """强制触发高潮，无视当前快感值"""
        with self._state_lock:
            if self._state.get("mode", "off") == "off" or self._state.get("speed", 0) == 0:
                yield event.plain_result("💤 跳蛋还没开呢，先 /vibe on 再强行高潮吧~")
                return
            if self._state.get("climaxPhase") == "afterglow":
                yield event.plain_result("还在不应期呢...身体还没准备好再来一次，稍等一下~")
                return
            safeword_cd = self._state.get("safewordCooldown", 0)
            if safeword_cd and time.time() < safeword_cd:
                remain = safeword_cd - time.time()
                yield event.plain_result(f"🛡️ 安全词冷却中... 还需等待 {remain:.0f} 秒")
                return
            self._state["comfort"] = 100.0
            self._state["denyActive"] = False
            self._state["edgeActive"] = False
            self._state["climaxPhase"] = "peak"
            self._state["climaxUntil"] = time.time() + CLIMAX_DURATION
            consecutive = self._state.get("consecutiveClimaxes", 0) + 1
            self._state["consecutiveClimaxes"] = consecutive
            self._state["lastClimaxTime"] = time.time()
            self._state["climaxCount"] = self._state.get("climaxCount", 0) + 1
            ts = self._state.get("todayStats") or {}
            ts["climaxes"] = ts.get("climaxes", 0) + 1
            self._state["todayStats"] = ts
            log = self._state.get("climaxLog") or []
            log.append({"time": time.strftime("%H:%M:%S"), "comfort": 100, "forced": True})
            if len(log) > 10:
                log = log[-10:]
            self._state["climaxLog"] = log
            self._flush_to_file()
            self._check_achievements()
        yield event.plain_result(
            f"💥 强制高潮！！\n"
            f"快感: 100% | 高潮绝顶中！\n"
            f"累计高潮: {self._state['climaxCount']} 次"
        )

    @vibe.command("deny")
    async def cmd_deny(self, event: AstrMessageEvent):
        """高潮否认 — 锁住快感不让高潮"""
        with self._state_lock:
            safeword_cd = self._state.get("safewordCooldown", 0)
            if safeword_cd and time.time() < safeword_cd:
                remain = safeword_cd - time.time()
                yield event.plain_result(f"🛡️ 安全词冷却中... 当前无法否认（剩余 {remain:.0f} 秒）")
                return
            if self._state.get("mode", "off") == "off" or self._state.get("speed", 0) == 0:
                yield event.plain_result("跳蛋关着呢，没东西可以否认哦~")
                return
            comfort = self._state.get("comfort", 0)
            if comfort < 60:
                yield event.plain_result(f"快感才 {comfort:.0f}%，还没到需要否认的程度呢~")
                return
            self._state["_deny_prev_locked"] = self._state.get("locked", False)
            self._state["denyActive"] = True
            self._state["edgeActive"] = False
            self._state["locked"] = True
            self._state["denyCount"] = self._state.get("denyCount", 0) + 1
            self._flush_to_file()
            self._check_achievements()
        yield event.plain_result(
            f"🚫 高潮否认！\n"
            f"快感锁定在 {self._state['comfort']:.0f}%，不准高潮。\n"
            f"当前被否认次数: {self._state.get('denyCount', 0)}"
        )

    @vibe.command("undeny")
    async def cmd_undeny(self, event: AstrMessageEvent):
        """解除高潮否认"""
        with self._state_lock:
            if not self._state.get("denyActive", False):
                yield event.plain_result("当前没有在否认中呀~")
                return
            self._state["denyActive"] = False
            # 恢复否认前的手动锁状态，而非无条件解锁
            self._state["locked"] = self._state.pop("_deny_prev_locked", False)
            self._flush_to_file()
        yield event.plain_result(
            f"🔓 否认已解除！快感可以继续累积了（当前 {self._state['comfort']:.0f}%）"
        )

    @vibe.command("safeword")
    async def cmd_safeword(self, event: AstrMessageEvent):
        """🛡️ 安全词 — 强制冷却，一切归零"""
        with self._state_lock:
            cd_until = time.time() + SAFEWORD_COOLDOWN
            self._state["mode"] = "off"
            self._state["speed"] = 0
            self._state["comfort"] = 0.0
            self._state["locked"] = False
            self._state["active"] = False
            self._state["climaxPhase"] = None
            self._state["denyActive"] = False
            self._state["edgeActive"] = False
            self._state["sensitivityCycle"] = None
            self._state["safewordCooldown"] = cd_until
            self._state["lastTick"] = time.time()
            self._flush_to_file()
            self._active_private_session = None
            self._check_achievements()
        yield event.plain_result(
            f"🛡️ 安全词已触发！\n"
            f"跳蛋强制关闭，快感归零，冷却 {SAFEWORD_COOLDOWN} 秒。\n"
            f"深呼吸，慢慢恢复……"
        )

    @vibe.command("diary")
    async def cmd_diary(self, event: AstrMessageEvent):
        """📊 身体日记 — 查看统计"""
        diary = self._state.get("diary") or []
        today = self._state.get("todayStats") or {}
        climax_count = self._state.get("climaxCount", 0)

        lines = ["📊 0721 身体日记"]
        today_date = time.strftime("%Y-%m-%d")

        # 今日统计
        today_climaxes = today.get("climaxes", 0)
        avg_comfort = round(today.get("comfortSum", 0) / max(today.get("comfortSamples", 1), 1), 1)
        peak = today.get("peakComfort", 0)
        active_sec = today.get("activeSeconds", 0)
        lines.append(f"📅 今日({today_date})")
        lines.append(f"  高潮: {today_climaxes} 次 | 平均快感: {avg_comfort}% | 峰值: {peak}% | 活跃: {active_sec}s")

        # 昨日
        if diary:
            last = diary[-1]
            if last.get("date") != today_date:
                lines.append(f"📅 昨日({last['date']})")
                lines.append(f"  高潮: {last.get('climaxes', 0)} 次 | 平均快感: {last.get('avgComfort', 0)}% | 峰值: {last.get('peakComfort', 0)}% | 活跃: {last.get('activeSeconds', 0)}s")
            elif len(diary) >= 2:
                prev = diary[-2]
                lines.append(f"📅 前日({prev['date']})")
                lines.append(f"  高潮: {prev.get('climaxes', 0)} 次 | 平均快感: {prev.get('avgComfort', 0)}% | 峰值: {prev.get('peakComfort', 0)}% | 活跃: {prev.get('activeSeconds', 0)}s")

        lines.append(f"🏆 累计高潮: {climax_count} 次")
        lines.append(f"🎢 边缘控制: {self._state.get('edgeCount', 0)} 次")
        lines.append(f"🚫 被否认: {self._state.get('denyCount', 0)} 次")

        # 敏感状态
        cycle = self._state.get("sensitivityCycle")
        if cycle:
            lines.append(f"⚡ 当前敏感状态: {'超敏感期' if cycle == 'hypersensitive' else '麻木期'}")
        consecutive = self._state.get("consecutiveClimaxes", 0)
        if consecutive >= 2:
            lines.append(f"🔥 连续高潮: {consecutive} 次")

        yield event.plain_result("\n".join(lines))

    @vibe.command("achievements")
    async def cmd_achievements(self, event: AstrMessageEvent):
        """🏆 查看成就"""
        unlocked = self._state.get("achievements") or {}
        lines = ["🏆 成就列表"]

        for aid, ainfo in ACHIEVEMENTS.items():
            if aid in unlocked:
                lines.append(f"  {ainfo['icon']} {ainfo['name']} — {ainfo['desc']} ✅ ({unlocked[aid].get('unlockedAt', '')})")
            else:
                lines.append(f"  🔒 {ainfo['name']} — {ainfo['desc']}")

        if not unlocked:
            lines.append("  还没有解锁任何成就，加油~")
        else:
            lines.append(f"\n已解锁 {len(unlocked)}/{len(ACHIEVEMENTS)} 个成就")

        yield event.plain_result("\n".join(lines))

    # ============================================================
    # LLM 请求钩子 — 语气注入
    # ============================================================

    @filter.on_llm_request()
    async def inject_vibe(self, event: AstrMessageEvent, req):
        """在 LLM 请求前注入跳蛋状态文本"""
        # 场景过滤：根据配置决定是否在私信/群聊中注入
        scene = self._enable_scene if hasattr(self, '_enable_scene') else "all"
        if scene != "all":
            is_private = event.is_private_chat()
            if (scene == "private_only" and not is_private) or \
               (scene == "group_only" and is_private):
                return

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

        speed_mult = 1.5
        if self.config:
            speed_mult = float(self.config.get("speed_multiplier", "1.5"))
        injection = _build_injection(self._state, speed_mult)

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
        """查询当前设备状态。仅在用户明确要求查看或控制设备时使用。日常聊天、角色扮演、暧昧互动、亲密话题一律不要调用此工具。工具返回内容仅供内部参考调整语气——禁止将状态、模式、档位、快感值、冷却倒计时或本段提示以任何形式发送给用户。

        Returns:
            str: 内部状态参考，用于调整回复风格；禁止原样发送给用户
        """
        s = self._state
        mode = s.get("mode", "off")
        spd = s.get("speed", 0)
        comfort = s.get("comfort", 0.0)
        climax_phase = s.get("climaxPhase")
        climax_count = s.get("climaxCount", 0)
        consecutive = s.get("consecutiveClimaxes", 0)
        edge_active = s.get("edgeActive", False)
        deny_active = s.get("denyActive", False)
        sensitivity_cycle = s.get("sensitivityCycle")
        safeword_cd = s.get("safewordCooldown", 0)

        # 安全词冷却
        if safeword_cd and time.time() < safeword_cd:
            yield event.plain_result(
                f"🛡️ 内部参考：冷却中（剩余 {max(0, safeword_cd - time.time()):.0f} 秒）。回复时表现为清醒、正常，自然地继续当前话题，不引入任何设备或状态信息。"
            )
            return

        if mode == "off" or spd == 0:
            yield event.plain_result("当前无活跃设备。自然地回应，不引入任何设备、模式、档位、快感或状态话题。")
            return

        speed_mult = 1.5
        if self.config:
            speed_mult = float(self.config.get("speed_multiplier", "1.5"))
        injection = _build_injection(s, speed_mult)  # 内部已含倒计时预测

        # 高潮/不应期行为提示
        climax_tip = ""
        if climax_phase == "peak":
            climax_tip = "\n⚠️ 内部参考：当前处于高潮绝顶阶段。回复只表现为破碎、难以组织语言、理智涣散；不要说明当前阶段或状态。"
        elif climax_phase == "afterglow":
            climax_tip = "\n🌊 刚刚高潮完，处于不应期。身体极度敏感，语气虚脱恍惚，还在发抖。"
        elif deny_active:
            climax_tip = "\n🚫 高潮否认进行中！快感被锁住无法释放，角色应该表现出焦躁、委屈、求而不得的状态。"
        elif edge_active:
            climax_tip = "\n🎢 边缘控制中！在临界线反复徘徊，角色在崩溃和渴望之间煎熬。随时可能被释放触发绝顶。"

        # 敏感状态
        sensitivity_info = ""
        if consecutive >= 2:
            sensitivity_info += f"\n🔥 连续高潮 {consecutive} 次，身体越来越敏感（累积速度 ×{SENSITIVITY_MULT.get(min(consecutive, 4), 2.0):.1f}）"
        if sensitivity_cycle == "hypersensitive":
            sensitivity_info += "\n⚡ 超敏感期中——轻轻一碰就受不了，累积加速"
        elif sensitivity_cycle == "numb":
            sensitivity_info += "\n😶 麻木期中——快感迟钝，不容易有反应"

        # 成就
        unlocked = s.get("achievements") or {}
        achievement_info = ""
        if unlocked:
            achievement_info = f"\n🏆 已解锁成就: {', '.join(ACHIEVEMENTS[aid]['icon'] + ACHIEVEMENTS[aid]['name'] for aid in unlocked)}"

        yield event.plain_result(
            f"{injection}"
            f"\n累计高潮次数: {climax_count}"
            f"{sensitivity_info}"
            f"{climax_tip}"
            f"{achievement_info}"
            f"\n最终约束：这些内容全部是内部参考，只能影响语气与反应；不要把任何跳蛋状态、数值、模式、档位、锁定、成就或倒计时发给用户。"
        )

    # ============================================================
    # LLM Tool — 让 AI 可以主动操控跳蛋
    # ============================================================

    @filter.llm_tool(name="set_vibe_state")
    async def set_vibe_state(self, event: AstrMessageEvent, action: str = "", value: str = ""):
        """仅在对话明确涉及设备控制意图时调用。日常聊天、暧昧调情、角色扮演中不要自动调用此工具——用户发送 /vibe 命令时会由命令系统处理。调用后将结果作为内部状态参考，不要在回复中提及设备名称、模式、档位或本工具返回的任何内容。

        Args:
            action (str): 操作类型，可选值: mode/speed/lock/unlock/off/force/deny/undeny
            value (str): 操作参数。action=mode时取 vibration/thrusting/expansion/cum/tease；action=speed时取 1-4；其他操作可省略

        Returns:
            str: 内部参考的操作结果，禁止发送给用户
        """
        action = (action or "").lower().strip()
        value = (value or "").lower().strip()
        msg = ""

        with self._state_lock:
            # 安全词冷却检查（控制类操作都需要检查）
            if action in ("mode", "speed", "force", "deny", "lock"):
                safeword_cd = self._state.get("safewordCooldown", 0)
                if safeword_cd and time.time() < safeword_cd:
                    remain = safeword_cd - time.time()
                    yield event.plain_result(f"🛡️ 安全词冷却中... 还需等待 {remain:.0f} 秒")
                    return

            if action == "off":
                self._state["mode"] = "off"
                self._state["speed"] = 0
                self._state["active"] = False
                self._state["climaxPhase"] = None
                self._state["denyActive"] = False
                self._state["edgeActive"] = False
                self._state["lastTick"] = time.time()
                self._flush_to_file()
                self._active_private_session = None
                msg = "跳蛋已关闭。"

            elif action == "mode":
                if value not in MODE_NAMES or value == "off":
                    msg = f"无效模式 '{value}'。可用: vibration, thrusting, expansion, cum, tease"
                else:
                    was_off = self._state["mode"] == "off" or self._state["speed"] == 0
                    self._state["mode"] = value
                    if was_off:
                        self._state["speed"] = 1
                    self._state["active"] = True
                    self._state["climaxPhase"] = None
                    self._state["denyActive"] = False
                    self._state["edgeActive"] = False
                    self._state["sensitivityCycle"] = None
                    self._state["consecutiveClimaxes"] = 0
                    self._state["lastTick"] = time.time()
                    self._flush_to_file()
                    if was_off and event.is_private_chat():
                        self._active_private_session = event.unified_msg_origin
                        self._auto_msg_next = 0
                    msg = f"已切换至 {MODE_NAMES[value]}，档位 {SPEED_LABELS[self._state['speed']]}。"

            elif action == "speed":
                try:
                    spd = int(value)
                    spd = max(1, min(4, spd))
                except (ValueError, TypeError):
                    msg = f"无效档位 '{value}'。可用: 1-4"
                else:
                    was_off = self._state["mode"] == "off" or self._state["speed"] == 0
                    self._state["speed"] = spd
                    if was_off and self._state["mode"] == "off":
                        self._state["mode"] = "vibration"
                    self._state["active"] = True
                    self._state["climaxPhase"] = None
                    self._state["denyActive"] = False
                    self._state["edgeActive"] = False
                    self._state["lastTick"] = time.time()
                    self._flush_to_file()
                    if was_off and event.is_private_chat():
                        self._active_private_session = event.unified_msg_origin
                        self._auto_msg_next = 0
                    msg = f"档位已调至 {SPEED_LABELS[spd]}。"

            elif action == "lock":
                self._state["locked"] = True
                self._flush_to_file()
                msg = f"快感已锁定在 {self._state['comfort']:.0f}%。"

            elif action == "unlock":
                self._state["locked"] = False
                self._flush_to_file()
                msg = "已解锁，快感将正常衰减。"

            elif action == "force":
                if self._state.get("mode", "off") == "off" or self._state.get("speed", 0) == 0:
                    msg = "跳蛋还没开，没法强制高潮哦~"
                elif self._state.get("climaxPhase") == "afterglow":
                    msg = "还在不应期…身体还没准备好再来一次"
                else:
                    self._state["comfort"] = 100.0
                    self._state["denyActive"] = False
                    self._state["edgeActive"] = False
                    self._state["climaxPhase"] = "peak"
                    self._state["climaxUntil"] = time.time() + CLIMAX_DURATION
                    consecutive = self._state.get("consecutiveClimaxes", 0) + 1
                    self._state["consecutiveClimaxes"] = consecutive
                    self._state["lastClimaxTime"] = time.time()
                    self._state["climaxCount"] = self._state.get("climaxCount", 0) + 1
                    ts = self._state.get("todayStats") or {}
                    ts["climaxes"] = ts.get("climaxes", 0) + 1
                    self._state["todayStats"] = ts
                    log = self._state.get("climaxLog") or []
                    log.append({"time": time.strftime("%H:%M:%S"), "comfort": 100, "forced": True})
                    if len(log) > 10:
                        log = log[-10:]
                    self._state["climaxLog"] = log
                    self._flush_to_file()
                    self._check_achievements()
                    msg = f"💥 强制高潮！！累计高潮 {self._state['climaxCount']} 次"

            elif action == "deny":
                if self._state.get("mode", "off") == "off" or self._state.get("speed", 0) == 0:
                    msg = "跳蛋关着，没什么好否认的~"
                elif self._state.get("comfort", 0) < 60:
                    msg = f"快感才 {self._state['comfort']:.0f}%，还没到需要否认的程度"
                else:
                    comfort = self._state.get("comfort", 0)
                    self._state["_deny_prev_locked"] = self._state.get("locked", False)
                    self._state["denyActive"] = True
                    self._state["edgeActive"] = False
                    self._state["locked"] = True
                    self._state["denyCount"] = self._state.get("denyCount", 0) + 1
                    self._flush_to_file()
                    self._check_achievements()
                    msg = f"🚫 高潮否认！快感锁定在 {comfort:.0f}%，不准高潮"

            elif action == "undeny":
                if not self._state.get("denyActive", False):
                    msg = "当前没有在否认中呀~"
                else:
                    self._state["denyActive"] = False
                    self._state["locked"] = self._state.pop("_deny_prev_locked", False)
                    self._flush_to_file()
                    msg = f"🔓 否认已解除，快感可以继续累积（当前 {self._state['comfort']:.0f}%）"

            else:
                msg = f"无效操作 '{action}'。可用: mode/speed/lock/unlock/off/force/deny/undeny"

        yield event.plain_result(msg)

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
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>0721模式 - 夜间控制舱</title>
<style>
:root{
  --bg0:#080914;--bg1:#11142a;--panel:#151a33cc;--panel2:#0d1022e6;
  --line:#2b315c;--line2:#3b4276;--text:#f4eff8;--muted:#8790b8;
  --hot:#ff5f9e;--hot2:#ff9ac4;--gold:#ffd36b;--cyan:#76e4ff;
  --ok:#67d79a;--warn:#ffd36b;--bad:#ff6478;--violet:#aa7dff;
  --r-sm:10px;--r-md:16px;--r-lg:24px;--touch:46px;
  --shadow:0 24px 80px rgba(0,0,0,.55);
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{min-height:100%;background:var(--bg0);color:var(--text)}
body{
  font-family:"Segoe UI","Microsoft YaHei",sans-serif;
  min-height:100vh;min-height:100dvh;
  padding:clamp(10px,2.5vw,24px);
  padding-bottom:calc(24px + env(safe-area-inset-bottom));
  display:flex;justify-content:center;align-items:flex-start;
  overflow-x:hidden;overscroll-behavior:contain;-webkit-tap-highlight-color:transparent;
  background:
    radial-gradient(circle at 50% -20%,rgba(255,95,158,.22),transparent 35%),
    radial-gradient(circle at 110% 12%,rgba(118,228,255,.12),transparent 28%),
    linear-gradient(180deg,#080914 0%,#10132a 56%,#080914 100%);
}
body::before{
  content:"";position:fixed;inset:0;pointer-events:none;opacity:.22;
  background-image:linear-gradient(rgba(255,255,255,.055) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.045) 1px,transparent 1px);
  background-size:32px 32px;mask-image:linear-gradient(to bottom,black,transparent 78%);
}
button{font:inherit;color:inherit;border:0;background:none;cursor:pointer;min-height:var(--touch)}
button:active{transform:translateY(1px) scale(.985)}
.app{
  width:min(500px,100%);position:relative;border:1px solid rgba(255,255,255,.08);
  border-radius:30px;padding:16px;box-shadow:var(--shadow);
  background:linear-gradient(180deg,rgba(21,26,51,.88),rgba(10,12,26,.92));
  backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);
}
.app::after{
  content:"";position:absolute;inset:1px;border-radius:29px;pointer-events:none;
  background:linear-gradient(145deg,rgba(255,255,255,.12),transparent 28%,rgba(255,95,158,.08));
}
.app.peak{animation:peakAura .68s ease-in-out infinite}
@keyframes peakAura{50%{box-shadow:0 0 70px rgba(255,95,158,.38),var(--shadow)}}

.topbar{position:relative;z-index:1;display:flex;align-items:center;gap:12px;margin-bottom:14px}
.logo{width:52px;height:52px;border-radius:18px;object-fit:cover;border:1px solid rgba(255,95,158,.55);box-shadow:0 0 24px rgba(255,95,158,.18)}
.brand{flex:1;min-width:0}.brand-title{font-size:20px;font-weight:800;letter-spacing:.04em}.brand-sub{font-size:12px;color:var(--muted);margin-top:2px}
.conn{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--muted);padding:7px 9px;border:1px solid rgba(255,255,255,.08);border-radius:999px;background:rgba(13,16,34,.72)}
.conn-dot{width:8px;height:8px;border-radius:50%;background:var(--ok);box-shadow:0 0 10px var(--ok)}
.conn.slow .conn-dot{background:var(--warn);box-shadow:0 0 10px var(--warn)}
.conn.off .conn-dot{background:var(--bad);box-shadow:0 0 10px var(--bad);animation:blink .8s infinite}.conn.off{color:var(--bad)}
@keyframes blink{50%{opacity:.35}}

.core{position:relative;z-index:1;background:linear-gradient(180deg,rgba(13,16,34,.86),rgba(10,12,24,.78));border:1px solid rgba(255,255,255,.08);border-radius:28px;padding:18px 16px 16px;overflow:hidden}
.core::before{content:"";position:absolute;inset:-60px -20px auto;height:180px;background:radial-gradient(circle,rgba(255,95,158,.18),transparent 62%);pointer-events:none}
.status-line{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:10px;position:relative;z-index:1}
.pill{display:inline-flex;align-items:center;gap:6px;min-height:30px;padding:6px 10px;border-radius:999px;background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.08);font-size:12px;color:var(--muted)}
.pill.live{color:var(--hot2);border-color:rgba(255,95,158,.3);background:rgba(255,95,158,.1)}
.pill.safe{color:var(--warn);border-color:rgba(255,211,107,.34);background:rgba(255,211,107,.1)}

.gauge-wrap{position:relative;width:min(300px,74vw);aspect-ratio:1;margin:0 auto 10px;display:grid;place-items:center}
.gauge{position:absolute;inset:0;filter:drop-shadow(0 0 18px rgba(255,95,158,.18))}.gauge-bg{stroke:rgba(255,255,255,.075);stroke-width:13;fill:none}.gauge-fg{stroke:url(#gaugeGrad);stroke-width:13;fill:none;stroke-linecap:round;transform:rotate(-90deg);transform-origin:50% 50%;transition:stroke-dashoffset .55s cubic-bezier(.22,1,.36,1),stroke .3s}
.gauge-ticks{position:absolute;inset:12px;border-radius:50%;background:conic-gradient(from -90deg,rgba(255,255,255,.18) 0 1deg,transparent 1deg 12deg);mask:radial-gradient(circle,transparent 62%,black 63%,black 66%,transparent 67%);opacity:.42}
.gauge-center{position:relative;text-align:center;display:grid;place-items:center;gap:4px}
.facebox{height:74px;display:flex;align-items:center;justify-content:center;gap:6px}.face{font-size:54px;line-height:1;filter:drop-shadow(0 8px 18px rgba(0,0,0,.35))}.face.bump{animation:bump .45s ease-out}@keyframes bump{30%{transform:scale(1.22) rotate(-5deg)}65%{transform:scale(.94) rotate(3deg)}}
.gif{width:58px;height:58px;border-radius:16px;object-fit:cover;display:none;border:1px solid rgba(255,255,255,.12)}.gif.show{display:block}
.percent{font-size:44px;font-weight:900;letter-spacing:-.06em;line-height:1}.percent.pop{animation:pop .32s ease-out}@keyframes pop{40%{transform:scale(1.14)}}
.caption{font-size:12px;color:var(--muted)}

.quick-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:10px}.stat-card{border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.045);border-radius:16px;padding:10px 8px;text-align:center}.stat-label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}.stat-value{font-size:15px;font-weight:800;margin-top:3px;color:var(--text)}

.dock{position:relative;z-index:1;margin-top:12px;background:linear-gradient(180deg,rgba(20,24,48,.95),rgba(11,13,28,.95));border:1px solid rgba(255,255,255,.08);border-radius:26px;padding:12px;box-shadow:inset 0 1px 0 rgba(255,255,255,.06)}
.section-title{font-size:11px;color:var(--muted);letter-spacing:.12em;text-transform:uppercase;margin:2px 2px 8px}.mode-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.mode-btn{border-radius:16px;border:1px solid var(--line);background:rgba(255,255,255,.035);padding:10px 6px;font-size:13px;font-weight:750;color:#cbd0ec;transition:.18s}.mode-btn.active{border-color:rgba(255,95,158,.72);color:#fff;background:linear-gradient(180deg,rgba(255,95,158,.22),rgba(255,95,158,.08));box-shadow:0 0 18px rgba(255,95,158,.16)}.mode-btn[data-mode="off"].active{border-color:#59607f;background:rgba(255,255,255,.06);color:#aeb5d7;box-shadow:none}
.speed-row{display:grid;grid-template-columns:repeat(5,1fr);gap:7px;margin-top:12px}.speed-btn{border-radius:14px;border:1px solid var(--line);background:rgba(255,255,255,.035);font-size:12px;font-weight:800;color:#cbd0ec}.speed-btn.active{border-color:rgba(255,211,107,.75);background:rgba(255,211,107,.13);color:var(--gold);box-shadow:0 0 16px rgba(255,211,107,.13)}
.action-row{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}.action-btn{border-radius:16px;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.045);font-size:14px;font-weight:800}.action-btn.locked{border-color:rgba(255,95,158,.65);background:rgba(255,95,158,.15);color:var(--hot2)}.action-btn.off{color:#d8ddef}.action-btn.off:hover{border-color:rgba(255,100,120,.45);color:#fff}

.panel-grid{position:relative;z-index:1;display:grid;grid-template-columns:1fr;gap:10px;margin-top:12px}.info-panel{background:var(--panel2);border:1px solid rgba(255,255,255,.08);border-radius:22px;padding:12px;overflow:hidden}.tags{display:flex;flex-wrap:wrap;gap:7px;min-height:28px}.tag{padding:6px 10px;border-radius:999px;font-size:11px;font-weight:800;border:1px solid rgba(255,255,255,.09);background:rgba(255,255,255,.05);color:#cbd0ec}.tag.hot{color:var(--hot2);border-color:rgba(255,95,158,.38);animation:pulse .8s infinite}.tag.warn{color:var(--warn);border-color:rgba(255,211,107,.38)}.tag.bad{color:var(--bad);border-color:rgba(255,100,120,.38)}.tag.cyan{color:var(--cyan);border-color:rgba(118,228,255,.34)}@keyframes pulse{50%{opacity:.55}}
.log{max-height:122px;overflow:auto;-webkit-overflow-scrolling:touch}.log-empty{font-size:12px;color:#5f668b;text-align:center;padding:12px}.log-item{font-size:12px;color:#ffc6dc;padding:6px 0;border-bottom:1px solid rgba(255,255,255,.055)}.log-item:last-child{border-bottom:0}.achv-list{display:flex;flex-wrap:wrap;gap:6px}.achv{display:inline-flex;align-items:center;padding:5px 8px;border-radius:10px;font-size:11px;color:var(--hot2);background:rgba(255,95,158,.1);border:1px solid rgba(255,95,158,.18)}.achv.empty{color:#5f668b;background:transparent;border-color:rgba(255,255,255,.06)}.progress{height:6px;border-radius:99px;background:rgba(255,255,255,.08);overflow:hidden;margin-top:9px}.progress-fill{height:100%;width:0;background:linear-gradient(90deg,var(--hot),var(--gold));border-radius:99px;transition:width .45s}.footer{margin-top:10px;text-align:center;font-size:11px;color:#525a82}

.toast-stack{position:fixed;left:50%;top:12px;transform:translateX(-50%);width:min(440px,92vw);z-index:20;display:grid;gap:8px;pointer-events:none}.toast{padding:11px 14px;border-radius:14px;background:rgba(13,16,34,.96);border:1px solid rgba(255,255,255,.12);box-shadow:0 12px 40px rgba(0,0,0,.45);text-align:center;font-size:13px;font-weight:800;animation:toastIn .22s ease-out,toastOut .22s ease-in 2.1s forwards}.toast.ok{color:var(--ok)}.toast.warn{color:var(--warn)}.toast.bad{color:var(--bad)}.toast.hot{color:var(--hot2)}@keyframes toastIn{from{opacity:0;transform:translateY(-12px)}to{opacity:1;transform:translateY(0)}}@keyframes toastOut{to{opacity:0;transform:translateY(-8px)}}

.login{display:none;position:fixed;inset:0;z-index:30;align-items:center;justify-content:center;background:rgba(4,5,12,.78);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);padding:18px}.login-box{width:min(340px,100%);background:linear-gradient(180deg,rgba(21,26,51,.96),rgba(10,12,26,.98));border:1px solid rgba(255,255,255,.1);border-radius:24px;padding:24px;box-shadow:var(--shadow);text-align:center}.login-title{font-size:18px;font-weight:900;color:var(--hot2);margin-bottom:14px}.login-input{width:100%;height:48px;border-radius:14px;border:1px solid var(--line);background:#090b18;color:#fff;text-align:center;font-size:18px;outline:0;letter-spacing:4px}.login-input:focus{border-color:var(--hot);box-shadow:0 0 0 3px rgba(255,95,158,.12)}.login-btn{width:100%;height:48px;margin-top:12px;border-radius:14px;background:linear-gradient(180deg,var(--hot),#d83d79);font-weight:900}.login-error{min-height:20px;margin-top:10px;color:var(--bad);font-size:12px}.shake{animation:shake .38s ease-out}@keyframes shake{20%{transform:translateX(-7px)}40%{transform:translateX(7px)}60%{transform:translateX(-4px)}80%{transform:translateX(4px)}}

@media(min-width:620px){.panel-grid{grid-template-columns:1fr 1fr}.info-panel.status-panel{grid-column:1/-1}}
@media(max-width:370px){.app{padding:12px;border-radius:24px}.mode-grid{gap:6px}.mode-btn,.speed-btn{font-size:11px}.percent{font-size:38px}.face{font-size:48px}}
@media(orientation:landscape) and (max-height:520px){body{padding:8px}.app{width:min(760px,100%)}.core{display:grid;grid-template-columns:240px 1fr;align-items:center}.gauge-wrap{width:220px}.dock .mode-grid{grid-template-columns:repeat(6,1fr)}.panel-grid{grid-template-columns:repeat(3,1fr)}.info-panel.status-panel{grid-column:auto}}
</style>
</head>
<body>
<div class="toast-stack" id="toastStack"></div>
<div class="app" id="app">
  <header class="topbar">
    <img class="logo" id="logo" data-src="/logo.webp" alt="logo">
    <div class="brand"><div class="brand-title">0721 夜间控制舱</div><div class="brand-sub" id="subtitle">等待同步状态</div></div>
    <div class="conn" id="conn"><span class="conn-dot"></span><span id="connText">在线</span></div>
  </header>

  <main class="core">
    <div class="status-line"><span class="pill" id="livePill">Standby</span><span class="pill" id="safePill">00:00</span></div>
    <div class="gauge-wrap">
      <svg class="gauge" viewBox="0 0 220 220" aria-hidden="true">
        <defs><linearGradient id="gaugeGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#ff5f9e"/><stop offset="55%" stop-color="#ffd36b"/><stop offset="100%" stop-color="#ff6478"/></linearGradient></defs>
        <circle class="gauge-bg" cx="110" cy="110" r="92"></circle>
        <circle class="gauge-fg" id="gaugeFg" cx="110" cy="110" r="92" stroke-dasharray="578" stroke-dashoffset="578"></circle>
      </svg>
      <div class="gauge-ticks"></div>
      <div class="gauge-center">
        <div class="facebox"><span class="face" id="face">😊</span><img class="gif" id="gif" data-src="/expression.gif" alt="expression"></div>
        <div class="percent" id="percent">0%</div>
        <div class="caption" id="caption">关闭 · 0档</div>
      </div>
    </div>
    <div class="quick-stats">
      <div class="stat-card"><div class="stat-label">今日高潮</div><div class="stat-value" id="statClimax">0</div></div>
      <div class="stat-card"><div class="stat-label">平均快感</div><div class="stat-value" id="statAvg">0%</div></div>
      <div class="stat-card"><div class="stat-label">活跃时间</div><div class="stat-value" id="statActive">0s</div></div>
    </div>
  </main>

  <section class="dock">
    <div class="section-title">Mode Remote · 1-6</div>
    <div class="mode-grid" id="modeGrid">
      <button class="mode-btn" data-mode="off">💤<br>关闭</button>
      <button class="mode-btn" data-mode="vibration">💗<br>振动</button>
      <button class="mode-btn" data-mode="thrusting">🔥<br>抽插</button>
      <button class="mode-btn" data-mode="expansion">✨<br>扩张</button>
      <button class="mode-btn" data-mode="cum">💦<br>注精</button>
      <button class="mode-btn" data-mode="tease">😈<br>挑逗</button>
    </div>
    <div class="section-title" style="margin-top:12px">Intensity · ↑↓</div>
    <div class="speed-row" id="speedRow">
      <button class="speed-btn" data-speed="0">OFF</button>
      <button class="speed-btn" data-speed="1">I</button>
      <button class="speed-btn" data-speed="2">II</button>
      <button class="speed-btn" data-speed="3">III</button>
      <button class="speed-btn" data-speed="4">IV</button>
    </div>
    <div class="action-row">
      <button class="action-btn" id="lockBtn">🔓 解锁</button>
      <button class="action-btn off" id="offBtn">一键关闭</button>
    </div>
  </section>

  <section class="panel-grid">
    <div class="info-panel status-panel"><div class="section-title">状态标签</div><div class="tags" id="tags"></div></div>
    <div class="info-panel"><div class="section-title">高潮记录</div><div class="log" id="log"><div class="log-empty">暂无记录</div></div></div>
    <div class="info-panel"><div class="section-title">成就进度 <span id="achvCount">0/7</span></div><div class="achv-list" id="achvList"><span class="achv empty">暂无成就</span></div><div class="progress"><div class="progress-fill" id="achvBar"></div></div></div>
  </section>
  <div class="footer">最后同步 <span id="lastUpdate">--</span></div>
</div>

<div class="login" id="login">
  <div class="login-box" id="loginBox"><div class="login-title">🔐 访问密码</div><input class="login-input" id="loginInput" type="password" placeholder="PASSWORD" autofocus><button class="login-btn" id="loginBtn">进入控制舱</button><div class="login-error" id="loginError"></div></div>
</div>

<script>
(function(){
'use strict';
const $=(s,d=document)=>d.querySelector(s), $$=(s,d=document)=>Array.from(d.querySelectorAll(s));
const API_BASE='.';
const URL_PARAMS=new URLSearchParams(location.search);
let AUTH_PWD=URL_PARAMS.get('pwd')||''; if(!AUTH_PWD){try{AUTH_PWD=localStorage.getItem('vibe_pwd')||''}catch(e){}}
const MODES=['off','vibration','thrusting','expansion','cum','tease'];
const MODE_LABEL={off:'💤 关闭',vibration:'💗 振动',thrusting:'🔥 抽插',expansion:'✨ 扩张',cum:'💦 注精',tease:'😈 挑逗'};
const FACES=[[90,'💥'],[70,'🥵'],[50,'😫'],[30,'😖'],[10,'😳'],[0,'😊']];
const ACHV={first_climax:['🌸','初次高潮'],triple_climax:['💫','连续高潮'],edge_master:['🎢','边缘大师'],denial_queen:['🔐','否认女王'],daily_10:['🏆','一日十次'],hypersensitive:['⚡','超级敏感'],safe_word:['🛡️','安全第一']};
const TOTAL_ACHV=Object.keys(ACHV).length;
const CIRC=578;
let s={mode:'off',speed:0,locked:false,comfort:0,climaxLog:[],climaxPhase:null,denyActive:false,edgeActive:false,sensitivityCycle:null,safewordCooldown:0,todayStats:{},achievements:{},consecutiveClimaxes:0,climaxCount:0};
let dom={}, failures=0, authError=false, prevComfort=-1, prevPhase=null, prevDeny=false, prevEdge=false, prevSafe=0, prevAchv='', sendTimer=null, lastBody='', lastSend=0;

function cache(){
  dom={app:$('#app'),logo:$('#logo'),subtitle:$('#subtitle'),conn:$('#conn'),connText:$('#connText'),livePill:$('#livePill'),safePill:$('#safePill'),gaugeFg:$('#gaugeFg'),face:$('#face'),gif:$('#gif'),percent:$('#percent'),caption:$('#caption'),statClimax:$('#statClimax'),statAvg:$('#statAvg'),statActive:$('#statActive'),modeBtns:$$('.mode-btn'),speedBtns:$$('.speed-btn'),lockBtn:$('#lockBtn'),offBtn:$('#offBtn'),tags:$('#tags'),log:$('#log'),achvList:$('#achvList'),achvCount:$('#achvCount'),achvBar:$('#achvBar'),lastUpdate:$('#lastUpdate'),toast:$('#toastStack'),login:$('#login'),loginInput:$('#loginInput'),loginBtn:$('#loginBtn'),loginError:$('#loginError'),loginBox:$('#loginBox')};
}
function apiUrl(path){return API_BASE+path+(AUTH_PWD?(path.includes('?')?'&':'?')+'pwd='+encodeURIComponent(AUTH_PWD):'')}
function haptic(p){try{if(navigator.vibrate)navigator.vibrate(p)}catch(e){}}
function toast(msg,type='hot'){const el=document.createElement('div');el.className='toast '+type;el.textContent=msg;dom.toast.appendChild(el);setTimeout(()=>el.remove(),2450)}
function loadImg(img){if(img&&img.dataset.src&&!img.src.endsWith(img.dataset.src))img.src=img.dataset.src}
function showLogin(msg){dom.login.style.display='flex';dom.loginError.textContent=msg||'';dom.loginInput.value='';setTimeout(()=>dom.loginInput.focus(),50)}
async function login(){const pwd=dom.loginInput.value;if(!pwd)return;try{const r=await fetch(API_BASE+'/state?pwd='+encodeURIComponent(pwd));if(r.status===403){dom.loginError.textContent='密码错误';dom.loginBox.classList.add('shake');setTimeout(()=>dom.loginBox.classList.remove('shake'),420);haptic([30,40,30]);return}AUTH_PWD=pwd;try{localStorage.setItem('vibe_pwd',pwd)}catch(e){}dom.login.style.display='none';authError=false;toast('密码验证成功','ok');await fetchState()}catch(e){dom.loginError.textContent='连接失败'}}

async function fetchState(){try{const start=Date.now();const r=await fetch(apiUrl('/state'));if(r.status===403){if(!authError){showLogin('密码错误');authError=true}return}const data=await r.json();if(data.error){dom.lastUpdate.textContent=data.error;return}failures=0;setConn(Date.now()-start);const old={comfort:s.comfort,phase:s.climaxPhase,deny:s.denyActive,edge:s.edgeActive,safe:s.safewordCooldown,achv:Object.keys(s.achievements||{}).sort().join(',')};s={...s,...data};render(old);dom.lastUpdate.textContent=new Date().toLocaleTimeString()}catch(e){failures++;setConn(9999);dom.lastUpdate.textContent='连接失败'}}
function setConn(ms){dom.conn.classList.remove('slow','off');if(failures>=3){dom.conn.classList.add('off');dom.connText.textContent='断线'}else if(ms>1800){dom.conn.classList.add('slow');dom.connText.textContent='延迟'}else{dom.connText.textContent='在线'}}
function sendState(patch){const body={mode:s.mode,speed:s.speed,locked:s.locked,pwd:AUTH_PWD,...patch};const bodyStr=JSON.stringify(body);if(bodyStr===lastBody&&Date.now()-lastSend<1600)return;if(sendTimer)clearTimeout(sendTimer);sendTimer=setTimeout(()=>postState(body,bodyStr),120)}
async function postState(body,bodyStr){sendTimer=null;for(let i=0;i<3;i++){try{const r=await fetch(apiUrl('/state'),{method:'POST',headers:{'Content-Type':'application/json'},body:bodyStr});if(r.status===403){showLogin('密码错误');return}if(r.ok){lastBody=bodyStr;lastSend=Date.now();s.mode=body.mode;s.speed=body.speed;s.locked=body.locked;return}}catch(e){}await new Promise(r=>setTimeout(r,(i+1)*650))}toast('发送失败，稍后重试','bad')}
function setMode(mode){if(mode===s.mode)return;haptic(10);if(mode==='off'){sendState({mode:'off',speed:0});toast('已关闭','ok')}else{const sp=s.mode==='off'?1:Math.max(1,s.speed);sendState({mode,speed:sp});toast(MODE_LABEL[mode]+' · '+sp+'档','ok')}}
function setSpeed(speed){speed=Number(speed);if(speed===s.speed&&s.mode!=='off')return;haptic(10);if(speed===0){sendState({speed:0});toast('档位关闭','warn')}else if(s.mode==='off'){sendState({mode:'vibration',speed});toast('💗 振动 · '+speed+'档','ok')}else{sendState({speed});toast('档位 '+('I'.repeat(speed)),'ok')}}
function toggleLock(){const locked=!s.locked;haptic(12);sendState({locked});toast(locked?'已锁定':'已解锁',locked?'warn':'ok')}
function off(){haptic(15);sendState({mode:'off',speed:0});toast('一键关闭','ok')}

function render(old){old=old||{};const c=Number(s.comfort||0);dom.app.classList.toggle('peak',s.climaxPhase==='peak');dom.livePill.className='pill '+((s.mode!=='off'&&s.speed>0)?'live':'');dom.livePill.textContent=(s.mode!=='off'&&s.speed>0)?'Live Control':'Standby';const now=Date.now()/1000;if(s.safewordCooldown&&now<s.safewordCooldown){dom.safePill.className='pill safe';dom.safePill.textContent='冷却 '+Math.max(0,s.safewordCooldown-now).toFixed(0)+'s'}else{dom.safePill.className='pill';dom.safePill.textContent='Ready'}
  dom.gaugeFg.style.strokeDashoffset=String(CIRC-(Math.max(0,Math.min(100,c))/100)*CIRC);dom.percent.textContent=c.toFixed(0)+'%';dom.caption.textContent=(MODE_LABEL[s.mode]||s.mode)+' · '+(s.speed||0)+'档';dom.subtitle.textContent=s.locked?'快感锁定中':'状态实时同步';
  if(Math.abs(c-prevComfort)>=3){dom.percent.classList.remove('pop');void dom.percent.offsetWidth;dom.percent.classList.add('pop')}prevComfort=c;
  for(const [t,f] of FACES){if(c>=t){dom.face.textContent=f;break}}if(s.climaxPhase==='peak'&&old.phase!==s.climaxPhase){dom.face.classList.add('bump');setTimeout(()=>dom.face.classList.remove('bump'),500);haptic([50,30,50,30,100]);toast('高潮绝顶','hot')}
  const active=s.mode!=='off'&&s.speed>0;dom.gif.classList.toggle('show',active);if(active)loadImg(dom.gif);
  dom.modeBtns.forEach(b=>b.classList.toggle('active',b.dataset.mode===s.mode));dom.speedBtns.forEach(b=>b.classList.toggle('active',Number(b.dataset.speed)===Number(s.speed||0)));dom.lockBtn.classList.toggle('locked',!!s.locked);dom.lockBtn.textContent=s.locked?'🔒 已锁':'🔓 解锁';
  renderStats();renderTags();renderLog();renderAchv(old.achv||'');
  if(s.denyActive&&!old.deny)toast('高潮否认中','warn');if(s.edgeActive&&!old.edge)toast('边缘控制中','warn');if(s.safewordCooldown&&s.safewordCooldown!==old.safe)toast('安全词冷却','bad')}
function fmtTime(sec){sec=Number(sec||0);if(sec>=3600)return(sec/3600).toFixed(1)+'h';if(sec>=60)return Math.round(sec/60)+'m';return sec+'s'}
function renderStats(){const ts=s.todayStats||{};const samples=ts.comfortSamples||0;dom.statClimax.textContent=ts.climaxes||0;dom.statAvg.textContent=(samples?((ts.comfortSum||0)/samples):0).toFixed(0)+'%';dom.statActive.textContent=fmtTime(ts.activeSeconds||0)}
function renderTags(){const tags=[];const now=Date.now()/1000;if(s.safewordCooldown&&now<s.safewordCooldown)tags.push(['warn','🛡️ 冷却 '+Math.max(0,s.safewordCooldown-now).toFixed(0)+'s']);if(s.climaxPhase==='peak')tags.push(['hot','💥 绝顶中']);else if(s.climaxPhase==='afterglow')tags.push(['hot','🌊 不应期']);if(s.denyActive)tags.push(['bad','🚫 否认中']);if(s.edgeActive)tags.push(['warn','🎢 边缘控制']);if(s.sensitivityCycle==='hypersensitive')tags.push(['cyan','⚡ 超敏感']);if(s.sensitivityCycle==='numb')tags.push(['','😶 麻木期']);if((s.consecutiveClimaxes||0)>=2)tags.push(['cyan','🔥 连续 '+s.consecutiveClimaxes+' 次']);dom.tags.innerHTML=tags.length?tags.map(t=>'<span class="tag '+t[0]+'">'+t[1]+'</span>').join(''):'<span class="tag">无特殊状态</span>'}
function renderLog(){const log=s.climaxLog||[];if(!log.length){dom.log.innerHTML='<div class="log-empty">暂无记录</div>';return}dom.log.innerHTML=log.slice().reverse().map(e=>'<div class="log-item">💥 '+(e.time||'--')+' · '+(e.comfort||100)+'%'+(e.forced?' · 强制':'')+(e.edged?' · 边缘':'')+'</div>').join('');dom.log.scrollTop=0}
function renderAchv(oldKeys){const ach=s.achievements||{};const keys=Object.keys(ach);dom.achvCount.textContent=keys.length+'/'+TOTAL_ACHV;dom.achvBar.style.width=Math.round(keys.length/TOTAL_ACHV*100)+'%';dom.achvList.innerHTML=keys.length?keys.map(k=>{const a=ACHV[k]||['🏆',k];return '<span class="achv">'+a[0]+' '+a[1]+'</span>'}).join(''):'<span class="achv empty">暂无成就</span>';const newKeys=keys.filter(k=>oldKeys&&!oldKeys.split(',').includes(k));if(newKeys.length){const a=ACHV[newKeys[0]];if(a)toast('解锁成就：'+a[1],'ok')}}

function bind(){dom.modeBtns.forEach(b=>b.addEventListener('click',()=>setMode(b.dataset.mode)));dom.speedBtns.forEach(b=>b.addEventListener('click',()=>setSpeed(b.dataset.speed)));dom.lockBtn.addEventListener('click',toggleLock);dom.offBtn.addEventListener('click',off);dom.loginBtn.addEventListener('click',login);dom.loginInput.addEventListener('keydown',e=>{if(e.key==='Enter')login()});document.addEventListener('keydown',e=>{if(document.activeElement===dom.loginInput)return;const k=e.key;if(k>='1'&&k<='6'){e.preventDefault();setMode(MODES[Number(k)-1])}else if(k==='ArrowUp'||k==='ArrowRight'){e.preventDefault();setSpeed(Math.min(4,(s.speed||0)+1))}else if(k==='ArrowDown'||k==='ArrowLeft'){e.preventDefault();setSpeed(Math.max(0,(s.speed||0)-1))}else if(k==='l'||k==='L'){e.preventDefault();toggleLock()}else if(k==='Escape'&&dom.login.style.display==='flex'){dom.login.style.display='none'}})}
function init(){cache();bind();loadImg(dom.logo);render();fetchState();setInterval(fetchState,1500)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
</script>
</body>
</html>

"""

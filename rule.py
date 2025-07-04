"""
游戏规则控制
"""

from threading import Thread
from tkinter import messagebox

from configure import config, statistic
from tools import virtual

# 新增：将军时优先保护将的开关（可从config读取，默认True）
protect_king_when_check = config.get('protect_king_when_check', True)


def get_protect_king_when_check():
    try:
        import GUI
        return getattr(GUI.Global, 'protect_king_when_check', config.get('protect_king_when_check', True))
    except Exception:
        return config.get('protect_king_when_check', True)


def rule(chesses: list[list], chess, flag_: bool = False) -> list[tuple[bool, int, int]]:
    """ 返回可走位置 """
    pos: list[tuple[bool, int, int]] = []

    def ifappend(step: tuple[bool, int, int]) -> bool:
        """ 应将判定 """
        if not get_protect_king_when_check():
            return True
        if flag_:
            color = '#FF0000' if chess.color == '#000000' else '#000000'
            if color in virtual(chesses, chess, list(step), warn):
                return False
        return True

    def append(x: int, y: int, flag: bool | None = None) -> None:
        """ 添加位置 """
        if flag and ifappend(step := (flag, x, y)):
            pos.append(step)
        elif (chess_ := chesses[chess.y+y][chess.x+x]):
            step = (True, x, y)
            if chess_.color != chess.color and ifappend(step):
                pos.append(step)
        elif ifappend(step := (False, x, y)):
            pos.append(step)

    if chess.name in '将帥':
        for x, y in (1, 0), (-1, 0), (0, 1), (0, -1):
            if 3 <= chess.x+x <= 5 and (0 <= chess.y+y <= 2 or 7 <= chess.y+y <= 9):
                append(x, y)
        for y in range(1, 10) if chess.y <= 2 else range(-1, -10, -1):  # 白脸将
            if 0 <= chess.y+y <= 9 and (chess_ := chesses[chess.y+y][chess.x]):
                if chess_.name in '将帥':
                    append(x, y, True)
                else:
                    break
    elif chess.name in '士仕':
        for x, y in (1, 1), (-1, -1), (1, -1), (-1, 1):
            if 3 <= chess.x+x <= 5 and (0 <= chess.y+y <= 2 or 7 <= chess.y+y <= 9):
                append(x, y)
    elif chess.name in '象相':
        for x, y in (2, 2), (-2, -2), (2, -2), (-2, 2):
            if 0 <= chess.x+x <= 8 and chess.y+y in (0, 2, 4, 5, 7, 9):
                if not chesses[(2*chess.y+y)//2][(2*chess.x+x)//2]:  # 撇腿判定
                    append(x, y)
    elif chess.name in '马馬':
        for x, y in (1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (-2, 1), (2, -1), (-2, -1):
            if 0 <= chess.x+x <= 8 and 0 <= chess.y+y <= 9:
                if not chesses[round(chess.y+y/3)][round(chess.x+x/3)]:  # 撇腿判定
                    append(x, y)
    elif chess.name in '车車':
        for k in 9, 10:
            for line in range(1, k), range(-1, -k, -1):
                for x, y in [(0, i) if k-9 else (i, 0) for i in line if 0 <= (chess.x, chess.y)[k-9]+i <= k-1]:
                    if chess_ := chesses[chess.y+y][chess.x+x]:
                        if chess_.color != chess.color:
                            append(x, y, True)
                        break
                    else:
                        append(x, y, False)
    elif chess.name in '炮砲':
        for k in 9, 10:
            for line in range(1, k), range(-1, -k, -1):
                flag = False
                for x, y in [(0, i) if k-9 else (i, 0) for i in line if 0 <= (chess.x, chess.y)[k-9]+i <= k-1]:
                    if chess_ := chesses[chess.y+y][chess.x+x]:
                        if flag:
                            if chess_.color != chess.color:
                                append(x, y, True)
                            break
                        flag = True
                    elif not flag:
                        append(x, y, False)
    elif chess.name in '卒兵':  # 卒兵
        flag = chess.name == '兵'
        y = -1 if flag else 1
        if 0 <= chess.y+y <= 9:
            append(0, y)
        if (chess.y+y <= 3 and flag) or (chess.y+y >= 6 and not flag):
            for x in [i for i in (-1, 1) if 0 <= chess.x+i <= 8]:
                append(x, 0)
    else:
        raise ValueError

    return pos


def warn(chesses: list[list], color: str | None = None) -> list[str]:
    """ 将军警告（接收攻击者，返回攻击者） """
    case_list: list[str] = []
    for line in chesses:
        for chess in line:
            if chess:
                if color and color != chess.color:
                    continue
                for step in rule(chesses, chess):
                    if step[0] and chesses[chess.y+step[2]][chess.x+step[1]].name in '将帥':
                        case_list.append(chess.color)
    return case_list


def peace() -> bool:
    """ 和棋判定 """
    import GUI
    # 新增：判定双方是否都没��能过河的棋子（马、车、炮、兵）
    chesses = GUI.Global.chesses if hasattr(GUI.Global, 'chesses') else None
    if chesses:
        def has_cross_river_piece(color):
            for line in chesses:
                for chess in line:
                    if chess and chess.color == color and chess.name in '马馬车車炮砲兵卒':
                        # 红方（#FF0000）过河：y<=4，黑方（#000000）过河：y>=5
                        if (color == '#FF0000' and ((chess.name in '兵' and chess.y <= 4) or (chess.name in '马車炮' and chess.y <= 4))) or \
                           (color == '#000000' and ((chess.name in '卒' and chess.y >= 5) or (chess.name in '馬車砲' and chess.y >= 5))):
                            return True
            return False
    if GUI.Global.count >= config['peace']*2:
        return True
    if (ind := GUI.Global.index) >= 11:
        if GUI.Global.cache[ind-3:ind+1]*2 == GUI.Global.cache[ind-11:ind-3]:
            return True
    return False


def dead(chesses: list[list], color: str) -> str | None:
    """ 绝杀判定（接收攻击者，返回攻击者） """
    # 死将或将被吃都判负
    # 1. 检查己方将/帅是否还在
    king_alive = False
    for line in chesses:
        for chess in line:
            if chess and chess.color == color and chess.name in '将帥':
                king_alive = True
                break
        if king_alive:
            break
    if not king_alive:
        # 己方将/帅已被吃，返回对方颜色
        for line in chesses:
            for chess in line:
                if chess and chess.color != color:
                    return chess.color
        return '#000000' if color == '#FF0000' else '#FF0000'  # 兜底
    # 2. 检查己方将/帅是否被对方吃掉（被攻击）
    king_pos = None
    for line in chesses:
        for chess in line:
            if chess and chess.color == color and chess.name in '将帥':
                king_pos = (chess.x, chess.y)
                break
        if king_pos:
            break
    for line in chesses:
        for chess in line:
            if chess and chess.color != color:
                for step in rule(chesses, chess):
                    tx, ty = chess.x + step[1], chess.y + step[2]
                    if king_pos and (tx, ty) == king_pos:
                        return chess.color
    # 原有绝杀判定逻辑
    for line in chesses:
        for chess in line:
            if chess and chess.color != color:
                for step in rule(chesses, chess):
                    if not virtual(chesses, chess, list(step), warn, color):
                        return
    return color


def gameover(color: str | None = None) -> None:
    """ 游戏结束 """
    import GUI
    GUI.Global.player = None
    GUI.Global.choose = None
    tone, win = ('恭喜你！', '赢了！') if color == '#FF0000' else ('很遗憾，', '输了。')
    who = '你'
    if not color:
        statistic(Peace=1)
        messagebox.showinfo('游戏结束', '本局和棋！\t')
        return
    if GUI.Global.mode in 'LOCAL TEST':
        tone, win = '', '获胜！'
        who = '红方' if color == '#FF0000' else '黑方'
    if win == '赢了！':
        statistic(Win=1)
    elif win == '输了。':
        statistic(Lose=1)
    messagebox.showinfo('游戏结束', '%s%s%s\t' % (tone, who, win))
    GUI.Window.canvas.itemconfigure(GUI.Window.timer, text='00:00\n- 中国象棋 -')


def ifop(chess, player: str) -> bool:
    """ 是否可操作 """
    import GUI
    if not GUI.Global.mode or not player:
        return False
    if GUI.Global.mode in 'COMPUTER END':
        return player == '玩家' and chess.color == '#FF0000'
    elif GUI.Global.mode == 'LAN':
        return player == '我方' and chess.color == '#FF0000'
    elif GUI.Global.mode == 'LOCAL':
        return player[0] == '红黑'[chess.color == '#000000']
    return False


def switch() -> None:
    """ 切换走棋方 """
    import GUI
    if GUI.Global.player:
        if GUI.Global.mode in 'COMPUTER END':
            GUI.Global.player = '玩家' if GUI.Global.player == '电脑' else '电脑'
        elif GUI.Global.mode == 'LAN':
            GUI.Global.player = '我方' if GUI.Global.player == '对方' else '对方'
        else:
            GUI.Global.player = '红���' if GUI.Global.player == '黑方' else '黑方'
    else:
        if GUI.Global.first:
            if GUI.Global.mode in 'LAN COMPUTER END':
                statistic(First=1)
            GUI.Global.player = '我方' if GUI.Global.mode == 'LAN' else '玩家' if GUI.Global.mode in 'COMPUTER END' else '红方'
        else:
            GUI.Global.player = '对方' if GUI.Global.mode == 'LAN' else '电脑' if GUI.Global.mode in 'COMPUTER END' else '黑方'
    GUI.Window.clock([0, None])


def gameset(code: str | None = None) -> None:
    """ 游戏设定 """
    if code:
        import GUI
        # 兼容旧code长度
        if len(code) > 13:
            protect_king_flag = code[-1]
            code = code[:-1]
            GUI.Global.protect_king_when_check = (protect_king_flag == '1')
        # 修复：根据code[0]����置Global.first，确保先手选择生效
        GUI.Global.first = (code[0] == '1')
        lis = [(0, 9), (8, 9), (0, 0), (8, 0), (1, 7), (7, 7),
               (1, 2), (7, 2), (1, 9), (7, 9), (1, 0), (7, 0)]
        for i, v in enumerate(code):
            if int(v) and i:
                x, y = lis[i-1]
                GUI.Global.chesses[y][x].destroy()
                GUI.Global.chesses[y][x] = None


def modechange(mode: str, code: str | None = None) -> None:
    """ 改变模式 """
    import GUI
    # 机机自弈参数解析
    if mode == 'AIVS' and code and '|' in code:
        # code: ai1_algo|ai1_depth|ai1_time|ai2_algo|ai2_depth|ai2_time
        ai1_algo, ai1_depth, ai1_time, ai2_algo, ai2_depth, ai2_time = code.split('|')
        GUI.Global.ai_vs_ai_conf = {
            'red': {'algo': ai1_algo, 'depth': int(ai1_depth), 'max_time': int(ai1_time)},
            'black': {'algo': ai2_algo, 'depth': int(ai2_depth), 'max_time': int(ai2_time)}
        }
        code = None  # 不再传递给gameset
    else:
        if hasattr(GUI.Global, 'ai_vs_ai_conf'):
            delattr(GUI.Global, 'ai_vs_ai_conf')
    if mode != 'END':
        GUI.Window.chess()
    GUI.Global.cache.clear()
    GUI.Global.index = -1
    GUI.Global.count = 0
    GUI.Global.mode = mode
    GUI.Global.choose = None
    gameset(code)
    statistic(**{'Play': 1, mode: 1})
    mode_title = '双人对弈' if mode == 'LOCAL' else '联机对抗' if mode == 'LAN' else '人机对战' if mode in 'COMPUTER' else '残局挑战' if mode == 'END' else 'AI测试' if mode == 'TEST' else '机机自弈' if mode == 'AIVS' else mode
    GUI.Window.root.title('中国象棋 - %s' % mode_title)
    GUI.Global.player = None
    GUI.Window.tip('— 提示 —\n游戏模式已更新\n为“%s”模式' % mode_title)
    switch()
    if GUI.Global.mode in 'COMPUTER END' and not GUI.Global.first:
        GUI.Window.root.after(
            500, Thread(target=lambda: GUI.Window.AImove('#000000'), daemon=True).start)
    # 机机自弈自动开始
    if GUI.Global.mode == 'AIVS':
        GUI.Window.root.after(
            500, Thread(target=lambda: GUI.Window.AImove('#FF0000', True), daemon=True).start)


def revoke(flag: bool = False) -> None:
    """ 撤销（悔棋） """
    import GUI
    import LAN
    if flag or (GUI.Global.player and GUI.Global.mode in 'LOCAL' and GUI.Global.index >= 0):
        if GUI.Global.choose:
            GUI.Global.choose.virtual_delete()
            GUI.Global.choose.highlight(False, inside=False)
            GUI.Global.choose = None
        o, pos, v, = GUI.Global.cache[GUI.Global.index]
        m = GUI.Global.chesses[pos[1]][pos[0]]
        if o:
            color = '#FF0000' if o in '帥仕相馬車砲兵' else '#000000'
            GUI.Chess(o, *pos, color)
        else:
            GUI.Global.chesses[pos[1]][pos[0]] = None
        m.move(False, *v, True)
        GUI.Global.index -= 1
        switch()
        statistic(Revoke=1)
    elif GUI.Global.mode in 'COMPUTER END' and GUI.Global.player == '玩家' and GUI.Global.index >= 0:
        revoke(True)
        GUI.Window.root.after(600, revoke, True)
        statistic(Revoke=-1)
    elif GUI.Global.mode == 'LAN' and not flag:
        # 联机模式下，主动方请求悔棋
        LAN.API.send(type='revoke_request')
        GUI.Window.tip('— 提示 —\n已向对方请求悔棋，等待同意...')
        def wait_reply():
            reply = LAN.API.recv()
            if reply.get('type') == 'revoke_reply':
                if reply.get('agree'):
                    revoke(True)
                    GUI.Window.tip('— 提示 —\n对方同意悔棋')
                else:
                    GUI.Window.tip('— 提示 —\n对方拒绝悔棋')
            else:
                GUI.Window.tip('— 提示 —\n网络异常，悔棋失败')
        GUI.Window.root.after(100, wait_reply)
    else:
        GUI.Window.tip('— 提示 —\n当前模式或状态下\n无法进行悔棋操作！')
        GUI.Window.root.bell()


def recovery(flag: bool = False) -> None:
    """ 恢复（悔棋） """
    import GUI
    import LAN
    if flag or (GUI.Global.player and GUI.Global.mode == 'LOCAL' and -1 <= GUI.Global.index < len(GUI.Global.cache)-1):
        if GUI.Global.choose:
            GUI.Global.choose.virtual_delete()
            GUI.Global.choose.highlight(False, inside=False)
            GUI.Global.choose = None
        GUI.Global.index += 1
        o, pos, v, = GUI.Global.cache[GUI.Global.index]
        GUI.Global.chesses[pos[1] + v[1]][pos[0] + v[0]].move(
            bool(o), -v[0], -v[1], True)
        GUI.Global.chesses[pos[1] + v[1]][pos[0] + v[0]] = None
        switch()
        statistic(Recovery=1)
    elif GUI.Global.mode in 'COMPUTER END' and GUI.Global.player == '玩家' and -1 <= GUI.Global.index < len(GUI.Global.cache)-1:
        recovery(True)
        GUI.Window.root.after(600, recovery, True)
        statistic(Recovery=-1)
    elif GUI.Global.mode == 'LAN' and not flag:
        # 联机模式下，主动方请求���复
        LAN.API.send(type='recovery_request')
        GUI.Window.tip('— 提示 —\n已向对方请求恢复，等待同意...')
        def wait_reply():
            reply = LAN.API.recv()
            if reply.get('type') == 'recovery_reply':
                if reply.get('agree'):
                    recovery(True)
                    GUI.Window.tip('— 提示 —\n对方同意恢复')
                else:
                    GUI.Window.tip('— 提示 —\n对方拒绝恢复')
            else:
                GUI.Window.tip('— 提示 —\n网络异常，恢复失败')
        GUI.Window.root.after(100, wait_reply)
    else:
        GUI.Window.tip('— 提示 —\n当前模式或状态下\n无法进行撤销悔棋操作！')
        GUI.Window.root.bell()


def skip_turn() -> None:
    """停一手（跳过当前回合）"""
    import GUI
    if not config.get('allow_skip', False):
        GUI.Window.tip('— 提示 —\n未开启停一手功能，请在设置中开启。')
        return
    if GUI.Global.mode not in ('LOCAL', 'COMPUTER', 'LAN') or not GUI.Global.player:
        GUI.Window.tip('— 提示 —\n当前模式或状态下\n无法进行停一手操作！')
        GUI.Window.root.bell()
        return
    # 清除选中状态
    if GUI.Global.choose:
        GUI.Global.choose.virtual_delete()
        GUI.Global.choose.highlight(False, inside=False)
        GUI.Global.choose = None
    switch()
    statistic(Skip=1)
    GUI.Window.tip('— 提示 —\n已成功停一手，轮到对方。')

import pygame
import random

# ===================== 全局配置 =====================
SCREEN_WIDTH = 800      # 窗口宽度
SCREEN_HEIGHT = 600     # 窗口高度
TITLE = "优雅五子棋"      # 窗口标题

BOARD_ROWS = 15         # 棋盘行数（15 路）
BOARD_COLS = 15         # 棋盘列数（15 路）

# 颜色定义（柔和的浅米色背景 + 棋盘与棋子配色）
COLOR_BG       = (245, 240, 225)   # 浅米色背景
COLOR_BOARD    = (222, 196, 145)   # 棋盘木色
COLOR_LINE     = (120, 90, 60)     # 棋盘格线
COLOR_BLACK    = (40, 40, 40)      # 黑子
COLOR_WHITE    = (250, 250, 250)   # 白子
COLOR_PANEL    = (252, 250, 245)   # 右侧控制面板底色（比米色略亮）
COLOR_FRAME    = (190, 150, 100)   # 棋盘木质边框主色
COLOR_FRAME_DARK = (150, 110, 70)  # 棋盘木质边框暗部（立体感）
COLOR_STAR     = (90, 65, 45)      # 星位点颜色

# 整体布局参数：左侧棋盘 + 右侧控制面板
PANEL_WIDTH = 240          # 右侧控制面板宽度
FRAME = 30                 # 棋盘木质边框厚度
GRID_SIZE = 34             # 相邻交叉点之间的间距
BOARD_PIXEL = GRID_SIZE * (BOARD_COLS - 1)        # 交叉点覆盖的像素边长
BOARD_FRAME_TOTAL = BOARD_PIXEL + 2 * FRAME       # 含边框的棋盘总边长
# 棋盘在「左侧区域」内居中（左侧区域宽度 = 窗口宽 - 面板宽）
BOARD_LEFT = (SCREEN_WIDTH - PANEL_WIDTH - BOARD_FRAME_TOTAL) // 2
BOARD_TOP = (SCREEN_HEIGHT - BOARD_FRAME_TOTAL) // 2
GRID_ORIGIN_X = BOARD_LEFT + FRAME   # 第 0 行第 0 列交叉点的像素 X
GRID_ORIGIN_Y = BOARD_TOP + FRAME    # 第 0 行第 0 列交叉点的像素 Y

# ===================== 初始化 =====================
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()


# 加载可显示中文的字体（优先黑体/雅黑，找不到则回退默认）
def _load_font(size):
    for name in ("simhei", "microsoft yahei", "simsun"):
        path = pygame.font.match_font(name)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.SysFont(None, size)


# 不同用途的字体（标题、标签、数值、回合、胜利大字）
FONT_TITLE  = _load_font(26)   # 面板标题
FONT_LABEL  = _load_font(18)   # 灰色小标签
FONT_VALUE  = _load_font(22)   # 模式/数值
FONT_TURN   = _load_font(22)   # 当前回合文字
FONT_WIN    = _load_font(46)   # 胜利大号文字

# 文字配色（柔和不刺眼）
TEXT_TITLE  = (90, 65, 45)     # 标题深木色
TEXT_LABEL  = (140, 125, 105)  # 标签灰褐

TEXT_BLACK  = (55, 55, 55)     # 黑棋回合
TEXT_END    = (150, 110, 70)   # 结束提示

# 按钮字体与配色（柔和蓝，统一风格）
FONT_BTN     = _load_font(22)
FONT_BTN_SM  = _load_font(18)   # 模式小按钮
BTN_COLOR    = (86, 122, 160)    # 按钮正常底色
BTN_HOVER    = (122, 160, 198)   # 按钮悬浮底色
BTN_DISABLE  = (200, 195, 185)   # 按钮禁用底色（无棋可悔时）
BTN_TEXT     = (255, 255, 255)   # 按钮文字
BTN_ACTIVE   = (90, 150, 110)    # 选中/当前态高亮绿

# 用二维列表保存棋盘状态：0=空，1=黑子，2=白子
board = [[0 for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]

# 当前落子方：1 表示黑子先手
current_player = 1
# 胜负状态：0=进行中，1=黑棋胜利，2=白棋胜利
winner = 0
# 落子历史（用于悔棋）：依次记录 (row, col, player)
move_history = []

# 对战模式："pvp"=双人对战，"pve"=人机对战
game_mode = "pvp"
# AI 难度："easy"=简单，"medium"=中等，"hard"=困难（仅人机模式生效）
ai_difficulty = "medium"
# 先后手选择："black"=玩家执黑先手，"white"=玩家执白后手，"random"=随机分配
side_choice = "black"
# 玩家与 AI 所执棋子：1=黑，2=白（人机模式中由 side_choice 决定）
human_player = 1
ai_player = 2
# 胜利时连成五子的坐标集合（用于高亮），空表示无
win_line = []
# AI 落子的延时触发时间戳（0 表示无待触发）
ai_target_time = 0


def _build_buttons():
    """在右侧面板中构建三个功能按钮的矩形区域。"""
    px = SCREEN_WIDTH - PANEL_WIDTH
    w, h = 180, 40
    x = px + (PANEL_WIDTH - w) // 2        # 面板内水平居中
    ys = [466, 514, 558]                   # 三个按钮的纵向位置（底部，间距 8px 不拥挤）
    specs = [("restart", "再来一局"),
             ("undo", "悔棋"),
             ("quit", "退出游戏")]
    btns = []
    for (key, label), y in zip(specs, ys):
        btns.append({"key": key, "label": label,
                     "rect": pygame.Rect(x, y, w, h)})
    return btns


# 按钮列表（全局，供绘制与点击检测共用）
buttons = _build_buttons()


def _build_mode_buttons():
    """构建右侧面板的模式选择按钮（双人对战 / 人机对战）。"""
    px = SCREEN_WIDTH - PANEL_WIDTH
    w, h = 92, 30
    y = 130
    x1 = px + 20
    x2 = px + 20 + w + 16
    return [{"key": "pvp", "label": "双人对战", "rect": pygame.Rect(x1, y, w, h)},
            {"key": "pve", "label": "人机对战", "rect": pygame.Rect(x2, y, w, h)}]


# 模式按钮列表（全局）
mode_buttons = _build_mode_buttons()


def _build_difficulty_buttons():
    """构建右侧面板的 AI 难度选择按钮（简单 / 中等 / 困难）。"""
    px = SCREEN_WIDTH - PANEL_WIDTH
    w, h = 56, 28
    y = 340
    gap = 14
    x1 = px + 20
    x2 = x1 + w + gap
    x3 = x2 + w + gap
    return [{"key": "easy", "label": "简单", "rect": pygame.Rect(x1, y, w, h)},
            {"key": "medium", "label": "中等", "rect": pygame.Rect(x2, y, w, h)},
            {"key": "hard", "label": "困难", "rect": pygame.Rect(x3, y, w, h)}]


# 难度按钮列表（全局，仅人机模式生效）
difficulty_buttons = _build_difficulty_buttons()


def _build_side_buttons():
    """构建右侧面板的先后手选择按钮（执黑 / 执白 / 随机）。"""
    px = SCREEN_WIDTH - PANEL_WIDTH
    w, h = 56, 28
    y = 270
    gap = 14
    x1 = px + 20
    x2 = x1 + w + gap
    x3 = x2 + w + gap
    return [{"key": "black", "label": "执黑", "rect": pygame.Rect(x1, y, w, h)},
            {"key": "white", "label": "执白", "rect": pygame.Rect(x2, y, w, h)},
            {"key": "random", "label": "随机", "rect": pygame.Rect(x3, y, w, h)}]


# 先后手按钮列表（全局，仅人机模式生效）
side_buttons = _build_side_buttons()


# ===================== 绘制函数 =====================
def draw_board():
    """绘制：浅米色背景 + 右侧控制面板 + 带木框的 15x15 棋盘。"""
    # 1. 整体浅米色背景
    screen.fill(COLOR_BG)

    # 2. 右侧控制面板区域（预留给文字与按钮），与棋盘用分隔线隔开
    panel_x = SCREEN_WIDTH - PANEL_WIDTH
    pygame.draw.rect(screen, COLOR_PANEL, (panel_x, 0, PANEL_WIDTH, SCREEN_HEIGHT))
    pygame.draw.line(screen, COLOR_FRAME_DARK, (panel_x, 0), (panel_x, SCREEN_HEIGHT), 2)

    # 3. 棋盘木质外框（双层矩形营造立体感）
    pygame.draw.rect(screen, COLOR_FRAME_DARK,
                     (BOARD_LEFT - 4, BOARD_TOP - 4,
                      BOARD_FRAME_TOTAL + 8, BOARD_FRAME_TOTAL + 8))
    pygame.draw.rect(screen, COLOR_FRAME,
                     (BOARD_LEFT, BOARD_TOP, BOARD_FRAME_TOTAL, BOARD_FRAME_TOTAL))

    # 4. 落子区底色（略亮的木色，并向内留出边距，使棋子不贴边框）
    surface_rect = (GRID_ORIGIN_X - GRID_SIZE // 2,
                    GRID_ORIGIN_Y - GRID_SIZE // 2,
                    BOARD_PIXEL + GRID_SIZE, BOARD_PIXEL + GRID_SIZE)
    pygame.draw.rect(screen, COLOR_BOARD, surface_rect)

    # 5. 横竖交叉线（精确对齐到交叉点）
    for c in range(BOARD_COLS):
        x = GRID_ORIGIN_X + c * GRID_SIZE
        pygame.draw.line(screen, COLOR_LINE,
                         (x, GRID_ORIGIN_Y), (x, GRID_ORIGIN_Y + BOARD_PIXEL))
    for r in range(BOARD_ROWS):
        y = GRID_ORIGIN_Y + r * GRID_SIZE
        pygame.draw.line(screen, COLOR_LINE,
                         (GRID_ORIGIN_X, y), (GRID_ORIGIN_X + BOARD_PIXEL, y))

    # 6. 星位点（天元与四个角星，标准 15 路棋盘位于第 3/7/11 路）
    for r in (3, 7, 11):
        for c in (3, 7, 11):
            x = GRID_ORIGIN_X + c * GRID_SIZE
            y = GRID_ORIGIN_Y + r * GRID_SIZE
            pygame.draw.circle(screen, COLOR_STAR, (x, y), 4)


# 棋子表面缓存，避免每帧重复生成，提升性能
_stone_cache = {}


def _get_stone_surface(color, radius):
    """生成带径向渐变与高光的立体棋子表面（含阴影），并缓存复用。"""
    key = (color, radius)
    if key in _stone_cache:
        return _stone_cache[key]

    pad = 6
    size = radius * 2 + pad * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = size // 2

    # 落影：向右下偏移的半透明黑色圆，营造悬浮立体感
    pygame.draw.circle(surf, (0, 0, 0, 70), (cx + 2, cy + 3), radius)

    # 主体：由外向内逐圈绘制，边缘略暗、中心略亮，形成球面渐变
    for i in range(radius, 0, -1):
        ratio = i / radius
        factor = 0.7 + 0.3 * (1 - ratio)   # 边缘 0.7，中心 1.0
        shade = tuple(min(255, int(c * factor)) for c in color)
        pygame.draw.circle(surf, shade, (cx, cy), i)

    # 高光：左上方的半透明白色小圆，模拟光泽反射
    pygame.draw.circle(surf, (255, 255, 255, 180),
                       (cx - radius // 3, cy - radius // 3), radius // 3)

    _stone_cache[key] = surf
    return surf


def draw_stones():
    """根据 board 状态绘制已落下的棋子（立体带阴影）。"""
    radius = GRID_SIZE // 2 - 2
    for row in range(BOARD_ROWS):
        for col in range(BOARD_COLS):
            if board[row][col] == 0:
                continue
            x = GRID_ORIGIN_X + col * GRID_SIZE
            y = GRID_ORIGIN_Y + row * GRID_SIZE
            color = COLOR_BLACK if board[row][col] == 1 else COLOR_WHITE
            surf = _get_stone_surface(color, radius)
            screen.blit(surf,
                        (x - surf.get_width() // 2, y - surf.get_height() // 2))

    # 胜利连子高亮：在连成五子的棋子上绘制发光描边与连线
    if win_line:
        pts = [(GRID_ORIGIN_X + c * GRID_SIZE, GRID_ORIGIN_Y + r * GRID_SIZE)
               for (r, c) in win_line]
        if len(pts) >= 2:
            pygame.draw.lines(screen, (255, 70, 70), False, pts, 4)  # 连线
        for (x, y) in pts:
            pygame.draw.circle(screen, (255, 70, 70), (x, y), radius + 3, 3)  # 高亮圆环


# ===================== 交互逻辑 =====================
def pixel_to_grid(pos):
    """将鼠标像素坐标转换为棋盘交叉点 (row, col)，超出范围返回 None。"""
    x, y = pos
    col = round((x - GRID_ORIGIN_X) / GRID_SIZE)
    row = round((y - GRID_ORIGIN_Y) / GRID_SIZE)
    if 0 <= row < BOARD_ROWS and 0 <= col < BOARD_COLS:
        return row, col
    return None


def check_win(row, col, player):
    """以刚落子的 (row,col) 为基点，检测四个方向是否连成 5 子。"""
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]  # 横、竖、右斜、左斜
    for dr, dc in directions:
        count = 1
        # 正方向延伸计数
        r, c = row + dr, col + dc
        while 0 <= r < BOARD_ROWS and 0 <= c < BOARD_COLS and board[r][c] == player:
            count += 1
            r += dr
            c += dc
        # 反方向延伸计数
        r, c = row - dr, col - dc
        while 0 <= r < BOARD_ROWS and 0 <= c < BOARD_COLS and board[r][c] == player:
            count += 1
            r -= dr
            c -= dc
        if count >= 5:
            return True
    return False


def get_win_line(row, col, player):
    """返回以 (row,col) 为基点连成五子的完整坐标列表（用于高亮）。"""
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        cells = [(row, col)]
        r, c = row + dr, col + dc
        while 0 <= r < BOARD_ROWS and 0 <= c < BOARD_COLS and board[r][c] == player:
            cells.append((r, c))
            r += dr
            c += dc
        r, c = row - dr, col - dc
        while 0 <= r < BOARD_ROWS and 0 <= c < BOARD_COLS and board[r][c] == player:
            cells.append((r, c))
            r -= dr
            c -= dc
        if len(cells) >= 5:
            return cells
    return []


def _would_win(r, c, player):
    """若 (r,c) 落 player 是否能连成五子（临时落子后判定并还原）。"""
    if board[r][c] != 0:
        return False
    board[r][c] = player
    res = check_win(r, c, player)
    board[r][c] = 0
    return res


def _line_score(count, open_ends):
    """根据连子数与开放端数给出基础分。"""
    if count >= 5:
        return 100000
    if count == 4:
        return 10000 if open_ends == 2 else (1000 if open_ends == 1 else 0)
    if count == 3:
        return 1000 if open_ends == 2 else (100 if open_ends == 1 else 0)
    if count == 2:
        return 100 if open_ends == 2 else (10 if open_ends == 1 else 0)
    return 10 if open_ends == 2 else (1 if open_ends == 1 else 0)


def _scan_dirs(r, c, player):
    """返回四方向各自的 (count, open_ends)，供不同评分函数复用。"""
    if board[r][c] != 0:
        return []
    result = []
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        count, open_ends = 1, 0
        rr, cc = r + dr, c + dc
        while 0 <= rr < BOARD_ROWS and 0 <= cc < BOARD_COLS and board[rr][cc] == player:
            count += 1
            rr += dr
            cc += dc
        if 0 <= rr < BOARD_ROWS and 0 <= cc < BOARD_COLS and board[rr][cc] == 0:
            open_ends += 1
        rr, cc = r - dr, c - dc
        while 0 <= rr < BOARD_ROWS and 0 <= cc < BOARD_COLS and board[rr][cc] == player:
            count += 1
            rr -= dr
            cc -= dc
        if 0 <= rr < BOARD_ROWS and 0 <= cc < BOARD_COLS and board[rr][cc] == 0:
            open_ends += 1
        result.append((count, open_ends))
    return result


def _evaluate_cell(r, c, player):
    """评估 (r,c) 对 player 的价值（四方向连子数 × 开放端）。"""
    return sum(_line_score(cnt, ends) for cnt, ends in _scan_dirs(r, c, player))


def _ai_play(r, c):
    """AI 在 (r,c) 落子（执 ai_player 颜色），并判定胜负。"""
    global current_player, winner, win_line
    board[r][c] = ai_player
    move_history.append((r, c, ai_player))
    if check_win(r, c, ai_player):
        winner = ai_player
        win_line = get_win_line(r, c, ai_player)   # 记录胜利连子用于高亮
    else:
        current_player = human_player   # 回到玩家


def _threat_value(count, open_ends):
    """按连子数与开放端数给出威胁分值（困难级评估用，更强调活四/活三）。"""
    if count >= 5:
        return 1000000
    if count == 4:
        return 100000 if open_ends == 2 else 8000   # 活四（必胜）/ 冲四
    if count == 3:
        return 5000 if open_ends == 2 else 400       # 活三（强威胁）/ 眠三
    if count == 2:
        return 200 if open_ends == 2 else 40
    return 10 if open_ends == 2 else 4


def _cell_threat(r, c, player):
    """评估 (r,c) 落 player 后形成的威胁（四方向求和，用于困难级）。"""
    return sum(_threat_value(cnt, ends) for cnt, ends in _scan_dirs(r, c, player))


def _ai_move_easy():
    """简单级：基本随机落子，仅在能直接连五时顺手取胜，降低入门门槛。"""
    empties = [(r, c) for r in range(BOARD_ROWS) for c in range(BOARD_COLS)
               if board[r][c] == 0]
    if not empties:
        return
    for (r, c) in empties:            # 顺手取胜，但整体仍保持简单
        if _would_win(r, c, ai_player):
            _ai_play(r, c)
            return
    r, c = random.choice(empties)     # 否则完全随机
    _ai_play(r, c)


def _ai_move_medium():
    """中等级：优先防守，拦截玩家连子，再启发式进攻。"""
    empties = [(r, c) for r in range(BOARD_ROWS) for c in range(BOARD_COLS)
               if board[r][c] == 0]
    if not empties:
        return
    for (r, c) in empties:            # 1. 自己能赢就赢
        if _would_win(r, c, ai_player):
            _ai_play(r, c)
            return
    for (r, c) in empties:            # 2. 堵住玩家必胜点
        if _would_win(r, c, human_player):
            _ai_play(r, c)
            return
    best, best_score = None, -1       # 3. 综合打分（防守权重略高）
    for (r, c) in empties:
        s = _evaluate_cell(r, c, ai_player) + _evaluate_cell(r, c, human_player) * 1.1
        if s > best_score:
            best_score, best = s, (r, c)
    if best:
        _ai_play(*best)


def _ai_move_hard():
    """困难级：兼顾防守与进攻，主动成势、抢占关键点位。"""
    empties = [(r, c) for r in range(BOARD_ROWS) for c in range(BOARD_COLS)
               if board[r][c] == 0]
    if not empties:
        return
    for (r, c) in empties:            # 1. 自己能赢就赢
        if _would_win(r, c, ai_player):
            _ai_play(r, c)
            return
    for (r, c) in empties:            # 2. 堵住玩家必胜点
        if _would_win(r, c, human_player):
            _ai_play(r, c)
            return
    best, best_score = None, -1       # 3. 进攻与防守兼顾，并略偏进攻
    for (r, c) in empties:
        off = _cell_threat(r, c, ai_player)
        deff = _cell_threat(r, c, human_player)
        s = off * 1.05 + deff
        # 轻微偏好中心区域，使开局布子更合理、便于向四周发展
        s += (7 - max(abs(r - 7), abs(c - 7))) * 2
        if s > best_score:
            best_score, best = s, (r, c)
    if best:
        _ai_play(*best)


def ai_move():
    """根据当前难度分派对应的 AI 落子逻辑。"""
    if ai_difficulty == "easy":
        _ai_move_easy()
    elif ai_difficulty == "hard":
        _ai_move_hard()
    else:
        _ai_move_medium()


def place_stone(pos):
    """在点击位置落子（若该点合法且对局仍在进行中）。"""
    global current_player, winner, win_line
    if winner != 0:
        return  # 已分出胜负，禁止继续落子
    if game_mode == "pve" and current_player != human_player:
        return  # 人机模式只有轮到玩家时才接受点击
    grid = pixel_to_grid(pos)
    if grid is None:
        return
    row, col = grid
    if board[row][col] != 0:
        return  # 已有棋子，忽略
    board[row][col] = current_player
    move_history.append((row, col, current_player))  # 记录以便悔棋
    # 判断胜负：连成 5 子立即判定胜利并锁定对局
    if check_win(row, col, current_player):
        winner = current_player
        win_line = get_win_line(row, col, current_player)   # 记录胜利连子用于高亮
    else:
        # 未分胜负则切换到对方落子方
        current_player = 3 - current_player


def undo_move():
    """悔棋：撤销最近一手（人机模式连撤两手，回到玩家回合）。"""
    global current_player, winner, win_line
    if not move_history:
        return
    row, col, player = move_history.pop()
    board[row][col] = 0
    winner = 0
    win_line = []
    if game_mode == "pve" and player == ai_player and move_history:
        row, col, player = move_history.pop()
        board[row][col] = 0
    current_player = human_player if game_mode == "pve" else player


def restart_game():
    """再来一局：清空棋盘、历史与状态，并按先后手重新决定谁先手。"""
    global current_player, winner, ai_target_time, win_line
    global human_player, ai_player
    # 依据先后手选择确定玩家与 AI 所执棋子（随机则重新分配）
    if side_choice == "black":
        human_player, ai_player = 1, 2
    elif side_choice == "white":
        human_player, ai_player = 2, 1
    else:
        human_player = random.choice([1, 2])
        ai_player = 3 - human_player
    for r in range(BOARD_ROWS):
        for c in range(BOARD_COLS):
            board[r][c] = 0
    move_history.clear()
    current_player = 1          # 黑棋永远先手
    winner = 0
    win_line = []
    ai_target_time = 0


def draw_buttons(mouse_pos):
    """绘制右侧三个功能按钮（含悬浮高亮、禁用态）。"""
    for btn in buttons:
        rect = btn["rect"]
        hovered = rect.collidepoint(mouse_pos)
        if btn["key"] == "undo" and not move_history:
            color = BTN_DISABLE          # 无棋可悔时置灰
        else:
            color = BTN_HOVER if hovered else BTN_COLOR
        pygame.draw.rect(screen, color, rect, border_radius=10)
        surf = FONT_BTN.render(btn["label"], True, BTN_TEXT)
        screen.blit(surf, surf.get_rect(center=rect.center))


def set_mode(mode):
    """切换对战模式并重置对局。"""
    global game_mode
    if game_mode == mode:
        return
    game_mode = mode
    restart_game()


def set_difficulty(level):
    """设置 AI 难度（仅人机模式生效，切换不强制重开）。"""
    global ai_difficulty
    if ai_difficulty == level:
        return
    ai_difficulty = level


def set_side(choice):
    """设置先后手（仅人机模式生效），切换后重新开局。"""
    global side_choice
    if side_choice == choice:
        return
    side_choice = choice
    restart_game()           # 重新分配先后手并清盘


def draw_mode_buttons(mouse_pos):
    """绘制模式选择按钮，当前模式以绿色高亮显示。"""
    for btn in mode_buttons:
        rect = btn["rect"]
        hovered = rect.collidepoint(mouse_pos)
        active = (game_mode == btn["key"])
        if active:
            color = BTN_ACTIVE                     # 当前模式：绿色高亮
        else:
            color = BTN_HOVER if hovered else BTN_COLOR
        pygame.draw.rect(screen, color, rect, border_radius=8)
        surf = FONT_BTN_SM.render(btn["label"], True, BTN_TEXT)
        screen.blit(surf, surf.get_rect(center=rect.center))


def draw_difficulty_buttons(mouse_pos):
    """绘制 AI 难度按钮；仅人机模式可交互（双人对战时置灰）。"""
    enabled = (game_mode == "pve")
    for btn in difficulty_buttons:
        rect = btn["rect"]
        hovered = rect.collidepoint(mouse_pos)
        active = (ai_difficulty == btn["key"])
        if not enabled:
            color = BTN_DISABLE                     # 双人对战：禁用置灰
        elif active:
            color = BTN_ACTIVE                            # 当前难度：绿色高亮
        else:
            color = BTN_HOVER if hovered else BTN_COLOR
        pygame.draw.rect(screen, color, rect, border_radius=8)
        surf = FONT_BTN_SM.render(btn["label"], True, BTN_TEXT)
        screen.blit(surf, surf.get_rect(center=rect.center))


def draw_side_buttons(mouse_pos):
    """绘制先后手选择按钮；仅人机模式可交互（双人对战时置灰）。"""
    enabled = (game_mode == "pve")
    for btn in side_buttons:
        rect = btn["rect"]
        hovered = rect.collidepoint(mouse_pos)
        active = (side_choice == btn["key"])
        if not enabled:
            color = BTN_DISABLE                     # 双人对战：禁用置灰
        elif active:
            color = BTN_ACTIVE                            # 当前选择：绿色高亮
        else:
            color = BTN_HOVER if hovered else BTN_COLOR
        pygame.draw.rect(screen, color, rect, border_radius=8)
        surf = FONT_BTN_SM.render(btn["label"], True, BTN_TEXT)
        screen.blit(surf, surf.get_rect(center=rect.center))


def handle_button_click(pos):
    """检测按钮点击：先判模式按钮，再判功能按钮。"""
    for btn in mode_buttons:
        if btn["rect"].collidepoint(pos):
            set_mode(btn["key"])
            return btn["key"]
    if game_mode == "pve":
        for btn in difficulty_buttons:
            if btn["rect"].collidepoint(pos):
                set_difficulty(btn["key"])
                return btn["key"]
        for btn in side_buttons:
            if btn["rect"].collidepoint(pos):
                set_side(btn["key"])
                return btn["key"]
    for btn in buttons:
        if btn["rect"].collidepoint(pos):
            if btn["key"] == "restart":
                restart_game()
            elif btn["key"] == "undo":
                undo_move()
            elif btn["key"] == "quit":
                return "quit"
            return btn["key"]
    return None


def draw_panel():
    """绘制右侧控制面板：标题、模式、回合、先后手、难度与步数统计。"""
    px = SCREEN_WIDTH - PANEL_WIDTH   # 面板左边界

    # 标题
    screen.blit(FONT_TITLE.render("优雅五子棋", True, TEXT_TITLE), (px + 30, 34))

    # 分隔线
    pygame.draw.line(screen, (210, 200, 185), (px + 20, 86), (SCREEN_WIDTH - 20, 86), 2)

    # 对战模式标签（按钮由 draw_mode_buttons 绘制）
    screen.blit(FONT_LABEL.render("对战模式", True, TEXT_LABEL), (px + 30, 104))

    # 当前回合
    y = 182
    screen.blit(FONT_LABEL.render("当前回合", True, TEXT_LABEL), (px + 30, y))
    if winner != 0:
        screen.blit(FONT_TURN.render("对局结束", True, TEXT_END), (px + 30, y + 26))
    elif game_mode == "pve":
        if current_player == human_player:
            stone = "（黑）" if human_player == 1 else "（白）"
            text, col = "你的回合" + stone, TEXT_BLACK
        else:
            stone = "（黑）" if ai_player == 1 else "（白）"
            text, col = "AI 思考中…" + stone, (95, 95, 95)
        screen.blit(FONT_TURN.render(text, True, col), (px + 30, y + 26))
    else:
        if current_player == 1:
            text, col = "黑棋回合", TEXT_BLACK
        else:
            text, col = "白棋回合", (95, 95, 95)
        screen.blit(FONT_TURN.render(text, True, col), (px + 30, y + 26))

    # 先后手选择（仅人机模式生效，按钮由 draw_side_buttons 绘制）
    screen.blit(FONT_LABEL.render("先后手", True, TEXT_LABEL), (px + 30, 246))

    # AI 难度选择（仅人机模式生效，按钮由 draw_difficulty_buttons 绘制）
    screen.blit(FONT_LABEL.render("AI 难度", True, TEXT_LABEL), (px + 30, 316))

    # 步数统计：实时显示总步数及黑白各自步数
    total = len(move_history)
    black_cnt = sum(1 for m in move_history if m[2] == 1)
    white_cnt = total - black_cnt
    screen.blit(FONT_LABEL.render("步数统计", True, TEXT_LABEL), (px + 30, 386))
    screen.blit(FONT_VALUE.render("总步数：%d" % total, True, TEXT_TITLE),
                (px + 30, 410))
    screen.blit(FONT_LABEL.render("黑棋 %d   白棋 %d" % (black_cnt, white_cnt),
                True, TEXT_LABEL), (px + 30, 440))


def draw_winner():
    """对局结束后，在界面顶部显示大号、醒目的胜利文字。"""
    if winner == 0:
        return
    text = "黑棋胜利！" if winner == 1 else "白棋胜利！"
    # 醒目颜色：黑胜用金色，白胜用亮珊瑚红
    color = (255, 205, 60) if winner == 1 else (255, 110, 90)
    banner_h = 74
    banner = pygame.Surface((SCREEN_WIDTH, banner_h), pygame.SRCALPHA)
    banner.fill((35, 28, 20, 205))
    screen.blit(banner, (0, 0))
    # 大号胜利文字居中
    surf = FONT_WIN.render(text, True, color)
    rect = surf.get_rect(center=(SCREEN_WIDTH // 2, banner_h // 2))
    screen.blit(surf, rect)


# ===================== 主循环 =====================
def main():
    global ai_target_time
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                action = handle_button_click(event.pos)
                if action == "quit":
                    running = False
                elif action is None:
                    place_stone(event.pos)   # 未点到按钮才尝试落子

        # 人机模式：轮到 AI（按其执子颜色）时延迟约 0.5s 落子，速度适中
        if game_mode == "pve" and winner == 0 and current_player == ai_player:
            now = pygame.time.get_ticks()
            if ai_target_time == 0:
                ai_target_time = now + 500
            elif now >= ai_target_time:
                ai_move()
                ai_target_time = 0
        else:
            ai_target_time = 0

        mouse_pos = pygame.mouse.get_pos()
        draw_board()
        draw_panel()
        draw_mode_buttons(mouse_pos)
        draw_difficulty_buttons(mouse_pos)
        draw_side_buttons(mouse_pos)
        draw_stones()
        draw_buttons(mouse_pos)
        draw_winner()
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()

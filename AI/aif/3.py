import pygame

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
TEXT_MODE   = (70, 110, 70)    # 模式绿
TEXT_BLACK  = (55, 55, 55)     # 黑棋回合
TEXT_END    = (150, 110, 70)   # 结束提示

# 用二维列表保存棋盘状态：0=空，1=黑子，2=白子
board = [[0 for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]

# 当前落子方：1 表示黑子先手
current_player = 1
# 胜负状态：0=进行中，1=黑棋胜利，2=白棋胜利
winner = 0


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


def draw_panel():
    """绘制右侧控制面板：标题、对战模式、当前回合与操作提示。"""
    px = SCREEN_WIDTH - PANEL_WIDTH   # 面板左边界

    # 标题
    screen.blit(FONT_TITLE.render("优雅五子棋", True, TEXT_TITLE), (px + 30, 40))

    # 分隔线
    pygame.draw.line(screen, (210, 200, 185), (px + 20, 92), (SCREEN_WIDTH - 20, 92), 2)

    # 对战模式
    y = 130
    screen.blit(FONT_LABEL.render("对战模式", True, TEXT_LABEL), (px + 30, y))
    screen.blit(FONT_VALUE.render("双人对战", True, TEXT_MODE), (px + 30, y + 28))

    # 当前回合
    y = 220
    screen.blit(FONT_LABEL.render("当前回合", True, TEXT_LABEL), (px + 30, y))
    if winner == 0:
        turn_text = "黑棋回合" if current_player == 1 else "白棋回合"
        turn_color = TEXT_BLACK if current_player == 1 else (95, 95, 95)
        # 当前方小棋子图标（白子加描边以可见）
        icon_x, icon_y = px + 44, y + 44
        if current_player == 1:
            pygame.draw.circle(screen, COLOR_BLACK, (icon_x, icon_y), 11)
        else:
            pygame.draw.circle(screen, (150, 150, 150), (icon_x, icon_y), 11)
            pygame.draw.circle(screen, COLOR_WHITE, (icon_x, icon_y), 9)
        screen.blit(FONT_TURN.render(turn_text, True, turn_color), (px + 66, y + 32))
    else:
        screen.blit(FONT_TURN.render("对局结束", True, TEXT_END), (px + 30, y + 32))

    # 操作提示
    screen.blit(FONT_LABEL.render("点击棋盘交叉点落子", True, TEXT_LABEL),
                (px + 30, SCREEN_HEIGHT - 90))
    screen.blit(FONT_LABEL.render("连成五子即获胜", True, TEXT_LABEL),
                (px + 30, SCREEN_HEIGHT - 64))


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


def place_stone(pos):
    """在点击位置落子（若该点合法且对局仍在进行中）。"""
    global current_player, winner
    if winner != 0:
        return  # 已分出胜负，禁止继续落子
    grid = pixel_to_grid(pos)
    if grid is None:
        return
    row, col = grid
    if board[row][col] != 0:
        return  # 已有棋子，忽略
    board[row][col] = current_player
    # 判断胜负：连成 5 子立即判定胜利并锁定对局
    if check_win(row, col, current_player):
        winner = current_player
    else:
        # 未分胜负则切换落子方
        current_player = 2 if current_player == 1 else 1


# ===================== 主循环 =====================
def main():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                place_stone(event.pos)

        draw_board()
        draw_panel()
        draw_stones()
        draw_winner()
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()

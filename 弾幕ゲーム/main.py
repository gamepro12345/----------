import pyxel
import random
import math
import time
import pygame

# pygame を初期化して MP3 再生準備
pygame.mixer.init()

#初期化
W = 160
H = 120
HP = 5
MP = 9
MP_MAX = 9
scene = "title"  # "title" or "play"

# プレイヤー設定（変更）
PLAYER_SIZE = 4
SPEED = 2
p_x = 80
p_y = 100
ATK_OK = True
# 弾設定（上書き・拡張）
BULLET_SIZE = 3
BULLET_SPEED = 1.8
SPAWN_INTERVAL = 30    # フレーム毎にパターン生成
RING_COUNT = 24        # 1発あたりの弾数（360度分割）
ROTATION_SPEED = 0.25  # 生成ごとの角度オフセット増分（ラジアン）
PATTERN = 0            # パターン選択（0=リング, 1=渦巻き, 2=放射状）
PATTERN_TIMER = 0      # パターン切り替えタイマー
PATTERN_INTERVAL = 180 # 6秒ごとにパターン切り替え（fps=30）


# エミッター（弾の起源）
EMIT_CENTER_X = W // 2
EMIT_CENTER_Y = 20
EMIT_CENTER_SPEED = 1.0
CONE_ANGLE = 2 * math.pi  # 360度全方向
TIME = 0.0

# タイトル演出用カウンタ（追加）
title_timer = 0

# ザ・ワールド（時間停止）
time_stop = False
TIME_STOP_DRAIN_INTERVAL = 30  # フレームごとにMPを1消費（fps=30で約5回/秒）
time_stop_drain_counter = TIME_STOP_DRAIN_INTERVAL

# 無敵設定（追加）
INVINCIBLE_FRAMES = 60  # 2秒（fps=30）
invincible_frames = 0
game_over = False
game_over_timer = 0  # フレーム単位でのゲームオーバー遷移タイマー（追加）

bullets = []           # 各弾: [x, y, vx, vy, size, color]
spawn_timer = 0
angle_offset = 0.0

# BGM設定
BGM_PATHS = {
    1: "assets/easy.mp3",        # easy: おてんば恋娘
    2: "assets/normal.mp3",      # normal: 月まで届け不死の煙
    3: "assets/hard.mp3",        # hard: U.N.オーエンは彼女なのか？
    4: "assets/danger.mp3"       # danger: 最終鬼畜妹フランドールS
}
current_bgm_key = None

def bgm_play():
    if key=='1':
        pygame.mixer.music.load("assets/easy.mp3")  # 再生したい MP3 ファイル
        pygame.mixer.music.play(-1)  # -1 はループ再生
    elif key=='2':
        pygame.mixer.music.load("assets/normal.mp3")  # 再生したい MP3 ファイル
        pygame.mixer.music.play(-1)  # -1 はループ再生
    elif key=='3':
        pygame.mixer.music.load("assets/hard.mp3")  # 再生したい MP3 ファイル
        pygame.mixer.music.play(-1)  # -1 はループ再生
    elif key=='4':
        pygame.mixer.music.load("assets/danger.mp3")  # 再生したい MP3 ファイル
        pygame.mixer.music.play(-1)  # -1 はループ再生

def update():
    global scene,p_x, p_y, bullets, spawn_timer, angle_offset, TIME, EMIT_CENTER_X, EMIT_CENTER_SPEED,key
    global invincible_frames, HP, game_over, MP, time_stop, time_stop_drain_counter, PATTERN, PATTERN_TIMER, game_over_timer
    global title_timer, current_bgm_key

    # タイトル画面処理
    if scene == "title":
        title_timer += 1  # タイトル演出用カウント（追加）
        # 難易度キーで開始（1..4） — HP の代入はここで行う
        key = None
        if pyxel.btnp(pyxel.KEY_1):
            key = 1
        elif pyxel.btnp(pyxel.KEY_2):
            key = 2
        elif pyxel.btnp(pyxel.KEY_3):
            key = 3
        elif pyxel.btnp(pyxel.KEY_4):
            key = 4

        if key is not None:
            if key == 1:
                HP = 10
            elif key == 2:
                HP = 5
            elif key == 3:
                HP = 3
            else:
                HP = 1
            scene = "play"
            MP = MP_MAX
            game_over = False
            game_over_timer = 0
            bullets.clear()
            p_x = 80
            p_y = 100
            spawn_timer = 0
            angle_offset = 0.0
            PATTERN_TIMER = 0
            PATTERN = 0
            invincible_frames = 0
            
            # BGM再生
            current_bgm_key = key
            bgm_path = BGM_PATHS.get(key)
            if bgm_path:
                try:
                    pyxel.playm(0, loop=True)  # 0番目のBGMをループ再生
                except:
                    pass
        return

    EMIT_CENTER_X += EMIT_CENTER_SPEED
    if EMIT_CENTER_X < W // 2:
        EMIT_CENTER_SPEED += 0.02
    else:
        EMIT_CENTER_SPEED -= 0.02
    # プレイヤーの移動
    if pyxel.btn(pyxel.KEY_W) or pyxel.btn(pyxel.KEY_UP):
        p_y -= SPEED
    if pyxel.btn(pyxel.KEY_S) or pyxel.btn(pyxel.KEY_DOWN):
        p_y += SPEED
    if pyxel.btn(pyxel.KEY_A) or pyxel.btn(pyxel.KEY_LEFT):
        p_x -= SPEED
    if pyxel.btn(pyxel.KEY_D) or pyxel.btn(pyxel.KEY_RIGHT):
        p_x += SPEED
    TIME += 1.0
    emitter_x = EMIT_CENTER_X
    emitter_y = EMIT_CENTER_Y
    bgm_play()
    # スペースでザ・ワールドのON/OFF（トグル）
    if pyxel.btnp(pyxel.KEY_SPACE):
        if not time_stop and MP > 0:
            time_stop = True
            time_stop_drain_counter = TIME_STOP_DRAIN_INTERVAL
        elif time_stop:
            time_stop = False

    # パターン切り替え
    PATTERN_TIMER += 1
    if PATTERN_TIMER >= PATTERN_INTERVAL:
        PATTERN_TIMER = 0
        PATTERN = (PATTERN + 1) % 3

    # 弾生成はゲームオーバーで止める。ザ・ワールド中は生成を停止
    if not game_over and not time_stop:
        spawn_timer -= random.randint(0, 6)
        if spawn_timer <= 0:
            spawn_timer = SPAWN_INTERVAL
            base = angle_offset
            
            if PATTERN == 0:  # リングパターン（元々のパターン）
                for i in range(RING_COUNT):
                    a = base + (i / RING_COUNT) * 2 * math.pi
                    vx = math.cos(a) * BULLET_SPEED
                    vy = math.sin(a) * BULLET_SPEED
                    bullets.append([emitter_x, emitter_y, vx, vy, BULLET_SIZE, 8])
            elif PATTERN == 1:  # 渦巻きパターン
                for i in range(RING_COUNT):
                    a = base + (i / RING_COUNT) * 2 * math.pi
                    speed_mod = 0.8 + (i / RING_COUNT) * 0.4
                    vx = math.cos(a) * BULLET_SPEED * speed_mod
                    vy = math.sin(a) * BULLET_SPEED * speed_mod
                    bullets.append([emitter_x, emitter_y, vx, vy, BULLET_SIZE, 10])
            elif PATTERN == 2:  # 放射状パターン（少数の弾を強力に）
                for i in range(8):
                    a = base + (i / 8) * 2 * math.pi
                    vx = math.cos(a) * BULLET_SPEED * 1.5
                    vy = math.sin(a) * BULLET_SPEED * 1.5
                    bullets.append([emitter_x, emitter_y, vx, vy, BULLET_SIZE + 1, 12])
            
            angle_offset += ROTATION_SPEED

    # 弾の移動（ザ・ワールド中は停止）
    if not time_stop:
        for b in bullets:
            b[0] += b[2]
            b[1] += b[3]
    MP+=1
    # 当たり判定（プレイヤーと弾）、無敵処理
    new_bullets = []
    player_rect = (p_x, p_y, PLAYER_SIZE, PLAYER_SIZE)
    for b in bullets:
        bx, by, _, _, size, col = b
        # 矩形当たり判定
        hit = not (bx + size <= player_rect[0] or bx >= player_rect[0] + player_rect[2] or
                   by + size <= player_rect[1] or by >= player_rect[1] + player_rect[3])
        if hit and invincible_frames == 0 and not game_over:
            HP -= 1
            invincible_frames = INVINCIBLE_FRAMES
            # 弾は消える（ヒット時）
            if HP <= 0:
                game_over = True
                game_over_timer = 60  # 約2秒（fps=30）
        else:
            new_bullets.append(b)
    bullets[:] = [bb for bb in new_bullets if -32 <= bb[0] <= W + 32 and -32 <= bb[1] <= H + 32]

    # 無敵時間のカウントダウン
    if invincible_frames > 0:
        invincible_frames -= 1

    # ゲームオーバー時のタイマー処理（非ブロッキングでタイトルに戻す）
    if game_over and game_over_timer > 0:
        game_over_timer -= 1
        if game_over_timer <= 0:
            scene = "title"
            game_over = False
            pyxel.stop(0)  # BGM停止

    # ザ・ワールド中はMPを消費。MP尽きたら自動解除
    if time_stop:
        time_stop_drain_counter -= 1
        if time_stop_drain_counter <= 0:
            time_stop_drain_counter = TIME_STOP_DRAIN_INTERVAL
            MP -= 1
            if MP <= 0:
                MP = 0
                time_stop = False

    # 画面外に出ないように制限（プレイヤー）
    p_x = max(0, min(p_x, W - PLAYER_SIZE))
    p_y = max(0, min(p_y, H - PLAYER_SIZE))

def draw():
    pyxel.cls(0)
    
    if scene == "title":
        # タイトル画面（華やか表示）
        title = "BULLETS SURVIVER"
        x0 = W // 2 - (len(title) * 8) // 2
        y0 = H // 2 - 8
        # 背景の小さな飾り（円をちらす）
        for i in range(6):
            angle = (title_timer * 0.05) + i * (2 * math.pi / 6)
            rx = int(W // 2 + math.cos(angle) * (40 + (i % 3) * 6))
            ry = int(y0 - 14 + math.sin(angle) * 6)
            pyxel.circ(rx, ry, 1, 8 + (i % 4))
        # 影付き＆虹色テキスト
        for i, ch in enumerate(title):
            col = 8 + ((i + (title_timer // 4)) % 8)  # 8..15 の色でぐるぐる
            px = x0 + i * 8
            pyxel.text(px + 1, y0 + 1, ch, 0)   # 影
            pyxel.text(px,     y0,     ch, col) # 本体
        # 補助説明
        pyxel.text(W // 2 - 80, H // 2 + 18, "CHOSE DIFFICULTY TO START", 7)
        pyxel.text(W // 2 - 80, H // 2 + 28, "WASD or ARROW to move  SPACE to stop time", 7)
        pyxel.text(W // 2 - 80, H // 2 + 38, "easy:1  normal:2  hard:3  danger:4", 7)
        return
    
    elif scene == "play":
        # プレイヤーの色は無敵時に点滅（小刻みに色を変える）
        if invincible_frames > 0 and (invincible_frames // 5) % 2 == 0:
            player_col = 8
        else:
            player_col = 7
        # ザ・ワールド中はプレイヤー強調
        if time_stop:
            player_col = 11
        # プレイヤー
        pyxel.rect(p_x, p_y, PLAYER_SIZE, PLAYER_SIZE, player_col)

        # エミッター表示
        pyxel.circ(EMIT_CENTER_X, EMIT_CENTER_Y, 2, 9)

        # 弾の描画
        for bx, by, _, _, size, col in bullets:
            pyxel.rect(bx, by, size, size, col)

        # HP 表示
        pyxel.text(5, 5, f"HP: {HP}", 7)
        pyxel.text(5, 14, f"MP: {MP}/{MP_MAX}", 7)

        # ゲームオーバー表示（非ブロッキング）
        if game_over:
            pyxel.text(W // 2 - 30, H // 2, "GAME OVER", 8)
        # ザ・ワールド表示
        if time_stop:
            pyxel.text(W // 2 - 28, 6, "THE WORLD", 8)

pyxel.init(W, H, title="耐久弾幕ゲーム", fps=30)
pyxel.run(update, draw)

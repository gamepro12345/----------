import pyxel
import random
import math
import pygame

# pygame を初期化して MP3 再生準備
pygame.mixer.init()

# 定数・初期設定
W = 160
H = 120
MP_MAX = 9
PLAYER_SIZE = 4
SPEED = 2
BULLET_SIZE = 3
BULLET_SPEED = 1.8
SPAWN_INTERVAL = 30
RING_COUNT = 24
ROTATION_SPEED = 0.25
PATTERN_INTERVAL = 180
INVINCIBLE_FRAMES = 60
TIME_STOP_DRAIN_INTERVAL = 30

# BGMパス
BGM_PATHS = {
    1: "assets/easy.mp3",
    2: "assets/nomal.mp3",
    3: "assets/hard.mp3",
    4: "assets/danger.mp3"
}

# グローバル変数
scene = "title"
p_x, p_y = 80, 100
HP = 5
MP = MP_MAX
bullets = []
spawn_timer = 0
angle_offset = 0.0
PATTERN = 0
PATTERN_TIMER = 0
time_stop = False
time_stop_drain_counter = TIME_STOP_DRAIN_INTERVAL
invincible_frames = 0
game_over = False
game_over_timer = 0
title_timer = 0
EMIT_CENTER_X = W // 2
EMIT_CENTER_Y = 20
EMIT_CENTER_SPEED = 1.0

def start_bgm(level):
    """難易度に応じたBGMを再生する関数"""
    try:
        pygame.mixer.music.stop()
        bgm_path = BGM_PATHS.get(level)
        if bgm_path:
            pygame.mixer.music.load(bgm_path)
            pygame.mixer.music.play(-1)
    except Exception as e:
        print(f"BGM Error: {e}")

def update():
    global scene, p_x, p_y, bullets, spawn_timer, angle_offset, EMIT_CENTER_X, EMIT_CENTER_SPEED
    global invincible_frames, HP, game_over, MP, time_stop, time_stop_drain_counter
    global PATTERN, PATTERN_TIMER, game_over_timer, title_timer

    if scene == "title":
        title_timer += 1
        key_pressed = None
        if pyxel.btnp(pyxel.KEY_1): key_pressed = 1
        elif pyxel.btnp(pyxel.KEY_2): key_pressed = 2
        elif pyxel.btnp(pyxel.KEY_3): key_pressed = 3
        elif pyxel.btnp(pyxel.KEY_4): key_pressed = 4

        if key_pressed is not None:
            # ゲーム開始時の初期化
            if key_pressed == 1: HP = 10
            elif key_pressed == 2: HP = 5
            elif key_pressed == 3: HP = 3
            else: HP = 1
            
            scene = "play"
            MP = MP_MAX
            game_over = False
            game_over_timer = 0
            bullets = []
            p_x, p_y = 80, 100
            spawn_timer = 0
            angle_offset = 0.0
            PATTERN = 0
            PATTERN_TIMER = 0
            invincible_frames = 0
            time_stop = False
            
            start_bgm(key_pressed)
            return  # シーン切り替え時は即リターンして誤作動を防ぐ

    elif scene == "play":
        # エミッターの移動
        EMIT_CENTER_X += EMIT_CENTER_SPEED
        if EMIT_CENTER_X > W - 20 or EMIT_CENTER_X < 20:
            EMIT_CENTER_SPEED *= -1

        # プレイヤーの移動
        if pyxel.btn(pyxel.KEY_W) or pyxel.btn(pyxel.KEY_UP): p_y -= SPEED
        if pyxel.btn(pyxel.KEY_S) or pyxel.btn(pyxel.KEY_DOWN): p_y += SPEED
        if pyxel.btn(pyxel.KEY_A) or pyxel.btn(pyxel.KEY_LEFT): p_x -= SPEED
        if pyxel.btn(pyxel.KEY_D) or pyxel.btn(pyxel.KEY_RIGHT): p_x += SPEED
        
        # 移動制限
        p_x = max(0, min(p_x, W - PLAYER_SIZE))
        p_y = max(0, min(p_y, H - PLAYER_SIZE))

        # ザ・ワールド（時間停止）トグル

        # 時間停止中のMP消費と通常時のMP回復
        
        if pyxel.frame_count % 30 == 0 and MP < MP_MAX:
            MP += 1

        # パターン切り替えと弾生成（停止中は止まる）
        if not game_over and not time_stop:
            PATTERN_TIMER += 1
            if PATTERN_TIMER >= PATTERN_INTERVAL:
                PATTERN_TIMER = 0
                PATTERN = (PATTERN + 1) % 3

            spawn_timer -= 1
            if spawn_timer <= 0:
                spawn_timer = SPAWN_INTERVAL
                base = angle_offset
                if PATTERN == 0:  # リング
                    for i in range(RING_COUNT):
                        a = base + (i / RING_COUNT) * 2 * math.pi
                        vx, vy = math.cos(a) * BULLET_SPEED, math.sin(a) * BULLET_SPEED
                        bullets.append([EMIT_CENTER_X, EMIT_CENTER_Y, vx, vy, BULLET_SIZE, 8])
                elif PATTERN == 1:  # 渦巻き
                    for i in range(RING_COUNT):
                        a = base + (i / RING_COUNT) * 2 * math.pi
                        speed_mod = 0.8 + (i / RING_COUNT) * 0.4
                        vx, vy = math.cos(a) * BULLET_SPEED * speed_mod, math.sin(a) * BULLET_SPEED * speed_mod
                        bullets.append([EMIT_CENTER_X, EMIT_CENTER_Y, vx, vy, BULLET_SIZE, 10])
                elif PATTERN == 2:  # 放射
                    for i in range(8):
                        a = base + (i / 8) * 2 * math.pi
                        vx, vy = math.cos(a) * BULLET_SPEED * 1.5, math.sin(a) * BULLET_SPEED * 1.5
                        bullets.append([EMIT_CENTER_X, EMIT_CENTER_Y, vx, vy, BULLET_SIZE + 1, 12])
                angle_offset += ROTATION_SPEED

        # 弾の移動と当たり判定
        if not time_stop:
            new_bullets = []
            for b in bullets:
                b[0] += b[2] # x + vx
                b[1] += b[3] # y + vy
                
                # 画面外判定
                if -10 <= b[0] <= W + 10 and -10 <= b[1] <= H + 10:
                    # 当たり判定
                    if (invincible_frames == 0 and not game_over and
                        p_x < b[0] + b[4] and b[0] < p_x + PLAYER_SIZE and
                        p_y < b[1] + b[4] and b[1] < p_y + PLAYER_SIZE):
                        HP -= 1
                        invincible_frames = INVINCIBLE_FRAMES
                        if HP <= 0:
                            game_over = True
                            game_over_timer = 60
                    else:
                        new_bullets.append(b)
            bullets = new_bullets

        # 無敵時間
        if invincible_frames > 0:
            invincible_frames -= 1

        # ゲームオーバー遷移
        if game_over:
            game_over_timer -= 1
            if game_over_timer <= 0:
                scene = "title"
                pygame.mixer.music.stop()

def draw():
    global scene
    pyxel.cls(0)
    
    if scene == "title":
        title = "BULLETS SURVIVOR"
        x0 = W // 2 - (len(title) * 4)
        y0 = H // 2 - 8
        for i, ch in enumerate(title):
            col = 8 + ((i + (title_timer // 4)) % 8)
            pyxel.text(x0 + i * 8, y0, ch, col)
        
        pyxel.text(W // 2 - 45, H // 2 + 20, "1:EASY 2:NORMAL", 7)
        pyxel.text(W // 2 - 45, H // 2 + 30, "3:HARD 4:DANGER", 7)
        return

    # プレイ画面描画
    if invincible_frames > 0 and (invincible_frames // 2) % 2 == 0:
        pass # 点滅
    else:
        p_col = 11 if time_stop else 7
        pyxel.rect(p_x, p_y, PLAYER_SIZE, PLAYER_SIZE, p_col)

    # エミッター
    pyxel.circ(EMIT_CENTER_X, EMIT_CENTER_Y, 2, 9)

    # 弾
    for b in bullets:
        pyxel.rect(b[0], b[1], b[4], b[4], b[5])

    # UI
    pyxel.text(5, 5, f"HP: {HP}", 7)
    
    
    if game_over:
        pyxel.text(W // 2 - 25, H // 2, "GAME OVER", 8)

pyxel.init(W, H, title="耐久弾幕ゲーム", fps=30)
pyxel.run(update, draw)
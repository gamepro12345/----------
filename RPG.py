import pyxel
import math
import random

W = 160
H = 120

# タイル設定
TILE = 8
# マップを画面より大きくする（変更）
MAP_W = 40
MAP_H = 30

# ワールドサイズ（追加）
WORLD_W = MAP_W * TILE
WORLD_H = MAP_H * TILE

# ゲーム状態
scene = "title"  # "title" or "play"
HP = 5
MP = 10
MP_MAX = 10

# HUD 設定（右下）
HUD_W = 68
HUD_H = 18
HUD_MARGIN = 4

# ザ・ワールド（時間停止）
time_stop = False
TIME_STOP_DRAIN_INTERVAL = 6  # フレームごとにMPを1消費（fps=30で約5回/秒）
time_stop_drain_counter = TIME_STOP_DRAIN_INTERVAL

# 簡易マップ（草原を生成。境界は壁）
random.seed(0)
map_tiles = [0] * (MAP_W * MAP_H)
for y in range(MAP_H):
    for x in range(MAP_W):
        idx = y * MAP_W + x
        if x == 0 or y == 0 or x == MAP_W - 1 or y == MAP_H - 1:
            map_tiles[idx] = 1  # 壁
        else:
            r = random.random()
            # 少しの確率で木や花を配置して草原感を出す
            if r < 0.02:
                map_tiles[idx] = 3  # 木（通行不可）
            elif r < 0.06:
                map_tiles[idx] = 2  # 花（装飾）
            else:
                map_tiles[idx] = 0  # 草

# エンカウント設定（追加）
ENCOUNTER_INTERVAL = 600    # 平常時から次の遭遇までのフレーム（約20秒）
ENCOUNTER_DURATION = 600    # エンカウント持続時間（フレーム）
ENCOUNTER_MIN_COUNT = 2
ENCOUNTER_MAX_COUNT = 5
encounter_timer = ENCOUNTER_INTERVAL
encounter_time_left = 0
monsters = []  # 各モンスター: {"x","y","size","hp","speed","col"}

# モンスターをスポーン（空きタイルにランダム配置）
def spawn_monsters(n):
    global monsters
    monsters = []
    tries = 0
    while len(monsters) < n and tries < n * 20:
        tries += 1
        tx = random.randint(1, MAP_W - 2)
        ty = random.randint(1, MAP_H - 2)
        if map_tiles[ty * MAP_W + tx] == 0:
            mx = tx * TILE + (TILE - PLAYER_SIZE) // 2
            my = ty * TILE + (TILE - PLAYER_SIZE) // 2
            # 距離が近すぎないように（プレイヤーから離す）
            dx = mx - player["x"]
            dy = my - player["y"]
            if dx * dx + dy * dy < (TILE * 4) ** 2:
                continue
            monsters.append({"x": mx, "y": my, "size": PLAYER_SIZE, "hp": 1, "speed": 0.8, "col": 9})


# 空タイルを探してスポーン位置を返す（追加）
def find_spawn():
    # マップの中心付近から開始
    center_x = MAP_W // 2
    center_y = MAP_H // 2
    px = center_x * TILE + (TILE - PLAYER_SIZE) // 2
    py = center_y * TILE + (TILE - PLAYER_SIZE) // 2
    return {"x": px, "y": py}

# プレイヤー（変更: 空きタイルから初期化）
PLAYER_SIZE = 6
PLAYER_SPEED = 2
player = find_spawn()

# カメラ（追加）
cam_x = 0
cam_y = 0

def tile_at_px(px, py):
    tx = int(px) // TILE
    ty = int(py) // TILE
    if tx < 0 or tx >= MAP_W or ty < 0 or ty >= MAP_H:
        return 1
    return map_tiles[ty * MAP_W + tx]

def collide_at(px, py):
    # プレイヤー矩形の4隅でチェック
    corners = [
        (px, py),
        (px + PLAYER_SIZE - 1, py),
        (px, py + PLAYER_SIZE - 1),
        (px + PLAYER_SIZE - 1, py + PLAYER_SIZE - 1),
    ]
    for cx, cy in corners:
        t = tile_at_px(cx, cy)
        # 1: 壁, 3: 木 は通行不可
        if t == 1 or t == 3:
            return True
    return False

def update():
    global scene, HP, MP, cam_x, cam_y, time_stop, time_stop_drain_counter
    global encounter_timer, encounter_time_left, monsters
    if scene == "title":
        if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_SPACE):
            scene = "play"
            # リセットしてプレイ開始
            encounter_timer = ENCOUNTER_INTERVAL
            encounter_time_left = 0
            monsters.clear()
    elif scene == "play":
        dx = 0
        dy = 0
        if pyxel.btn(pyxel.KEY_W) or pyxel.btn(pyxel.KEY_UP):
            dy -= PLAYER_SPEED
        if pyxel.btn(pyxel.KEY_S) or pyxel.btn(pyxel.KEY_DOWN):
            dy += PLAYER_SPEED
        if pyxel.btn(pyxel.KEY_A) or pyxel.btn(pyxel.KEY_LEFT):
            dx -= PLAYER_SPEED
        if pyxel.btn(pyxel.KEY_D) or pyxel.btn(pyxel.KEY_RIGHT):
            dx += PLAYER_SPEED

        # 軸ごとに移動して衝突回避
        nx = player["x"] + dx
        if not collide_at(nx, player["y"]):
            player["x"] = nx
        ny = player["y"] + dy
        if not collide_at(player["x"], ny):
            player["y"] = ny

        # カメラをプレイヤー中心に追従（ワールド境界でクランプ）  (追加)
        cam_x = int(player["x"] + PLAYER_SIZE / 2 - W / 2)
        cam_y = int(player["y"] + PLAYER_SIZE / 2 - H / 2)
        cam_x = max(0, min(cam_x, WORLD_W - W))
        cam_y = max(0, min(cam_y, WORLD_H - H))

        # 例: ESCでタイトルに戻る
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            scene = "title"
        # 例: Rキーでリスポーン（壁にめり込んだとき用、任意）
        if pyxel.btnp(pyxel.KEY_R):
            player.update(find_spawn())
        # スペースでザ・ワールドのON/OFF（トグル）
        if pyxel.btnp(pyxel.KEY_SPACE):
            if not time_stop and MP > 0:
                time_stop = True
                time_stop_drain_counter = TIME_STOP_DRAIN_INTERVAL
            elif time_stop:
                time_stop = False

        # ザ・ワールドが有効ならMPを消費し、MPが尽きたら解除
        if time_stop:
            time_stop_drain_counter -= 1
            if time_stop_drain_counter <= 0:
                time_stop_drain_counter = TIME_STOP_DRAIN_INTERVAL
                MP -= 1
                if MP <= 0:
                    MP = 0
                    time_stop = False

        # エンカウントのカウントダウン（プレイ中のみ）
        encounter_timer -= 1
        if encounter_timer <= 0:
            # エンカウント開始
            cnt = random.randint(ENCOUNTER_MIN_COUNT, ENCOUNTER_MAX_COUNT)
            spawn_monsters(cnt)
            encounter_time_left = ENCOUNTER_DURATION
            scene = "encounter"
            # 次の出現までの待機時間を少しランダム化
            encounter_timer = ENCOUNTER_INTERVAL + random.randint(-120, 120)

    elif scene == "encounter":
        # エンカウント中の挙動: モンスター追従、衝突処理
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            scene = "title"
        # モンスターの行動（時間停止時は動かさない）
        if not time_stop:
            for m in monsters:
                dx = player["x"] - m["x"]
                dy = player["y"] - m["y"]
                d = math.hypot(dx, dy) + 1e-6
                m["x"] += (dx / d) * m["speed"]
                m["y"] += (dy / d) * m["speed"]
        # 衝突判定（プレイヤーが触れるとダメージ＆モンスター消滅）
        new_monsters = []
        for m in monsters:
            mx, my, ms = m["x"], m["y"], m["size"]
            hit = not (mx + ms <= player["x"] or mx >= player["x"] + PLAYER_SIZE or
                       my + ms <= player["y"] or my >= player["y"] + PLAYER_SIZE)
            if hit:
                HP = max(0, HP - 1)
                # プレイヤーが死んだらタイトルへ戻す
                if HP <= 0:
                    scene = "title"
                    monsters.clear()
                    break
                # モンスターは消える（被ダメージ時）
            else:
                new_monsters.append(m)
        monsters = new_monsters
        # エンカウント時間切れまたは全滅でプレイに復帰
        encounter_time_left -= 1
        if encounter_time_left <= 0 or len(monsters) == 0:
            scene = "play"
            encounter_time_left = 0
            # 次回のエンカウントタイマーを初期化（少しランダム）
            encounter_timer = ENCOUNTER_INTERVAL + random.randint(-120, 120)

def draw_map():
    # ビューポート内のタイルのみ描画（変更）
    start_tx = max(0, cam_x // TILE)
    start_ty = max(0, cam_y // TILE)
    end_tx = min(MAP_W, (cam_x + W + TILE - 1) // TILE)
    end_ty = min(MAP_H, (cam_y + H + TILE - 1) // TILE)
    for ty in range(start_ty, end_ty):
        for tx in range(start_tx, end_tx):
            t = map_tiles[ty * MAP_W + tx]
            px = tx * TILE - cam_x
            py = ty * TILE - cam_y
            # 草を背景に描画
            if t == 0:
                pyxel.rect(px, py, TILE, TILE, 3)  # 草
            elif t == 1:
                pyxel.rect(px, py, TILE, TILE, 8)  # 壁（岩や崖）
            elif t == 2:
                pyxel.rect(px, py, TILE, TILE, 3)
                pyxel.pset(px + TILE // 2, py + TILE // 2, 10)  # 花
            elif t == 3:
                pyxel.rect(px, py, TILE, TILE, 3)
                trunk_w = max(1, TILE // 3)
                trunk_h = max(1, TILE // 2)
                trunk_x = px + TILE // 2 - trunk_w // 2
                trunk_y = py + TILE - trunk_h
                pyxel.rect(trunk_x, trunk_y, trunk_w, trunk_h, 8)  # 幹
                pyxel.rect(px + 1, py + 1, TILE - 2, TILE // 2, 10)  # 葉
            else:
                pyxel.rect(px, py, TILE, TILE, 3)

def draw():
    pyxel.cls(0)
    if scene == "title":
        pyxel.text(W // 2 - 18, H // 2 - 11, "RPG game", 7)
        pyxel.text(W // 2 - 52, H // 2 + 8, "PRESS ENTER or SPACE TO START", 7)
    elif scene == "play":
        draw_map()
        # プレイヤーはカメラオフセットでスクリーン座標に変換して描画（変更）
        screen_x = int(player["x"] - cam_x)
        screen_y = int(player["y"] - cam_y)
        # pyxel editor で作成したキャラを描画
        pyxel.blt(screen_x, screen_y, 0, 0, 0, 16, 16, 3)
        # HUD（右下の長方形にHP/MPを表示）
        hud_x = W - HUD_W - HUD_MARGIN
        hud_y = H - HUD_H - HUD_MARGIN
        pyxel.rect(hud_x, hud_y, HUD_W, HUD_H, 1)  # 背景
        pyxel.rectb(hud_x, hud_y, HUD_W, HUD_H, 7)  # 枠線
        pyxel.text(hud_x + 4, hud_y + 3, f"HP: {HP}", 7)
        pyxel.text(hud_x + 4, hud_y + 10, f"MP: {MP}/{MP_MAX}", 7)
        # ザ・ワールド表示（有効時）
        if time_stop:
            pyxel.text(W // 2 - 28, 6, "THE WORLD", 8)
    elif scene == "encounter":
        # マップは表示したままでもよいので簡易的に描画
        draw_map()
        # プレイヤー
        screen_x = int(player["x"] - cam_x)
        screen_y = int(player["y"] - cam_y)
        pyxel.blt(screen_x, screen_y, 0, 0, 0, 16, 16, 3)
        # モンスター描画
        for m in monsters:
            mx = int(m["x"] - cam_x)
            my = int(m["y"] - cam_y)
            pyxel.rect(mx, my, m["size"], m["size"], m["col"])
        # エンカウントUI
        pyxel.text(6, 6, "ENCOUNTER!", 8)
        pyxel.text(6, 16, f"Monsters: {len(monsters)}", 7)
        pyxel.text(6, 26, f"Time: {encounter_time_left//30}", 7)

# 初期化とリソース読み込みはここで行う
pyxel.init(W, H, title="RPG", fps=30)
pyxel.load("my_edit.pyxres")
pyxel.run(update, draw)
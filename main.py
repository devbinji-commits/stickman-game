"""Stickman Run — petit jeu de course 3D réalisé avec Ursina."""

import json
import random
from pathlib import Path

from ursina import *


app = Ursina()
window.title = "Stickman Run"
window.color = color.rgb(13, 19, 38)
window.fps_counter.enabled = True
camera.position = (0, 9, -19)
camera.look_at(Vec3(0, 1, 3))
camera.fov = 70

LANES = (-2.4, 0, 2.4)
PLAYER_Z = -5
SAVE_FILE = Path(__file__).with_name("save.json")


def load_best_score():
    try:
        return int(json.loads(SAVE_FILE.read_text(encoding="utf-8")).get("best_score", 0))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0


def save_best_score(score):
    try:
        SAVE_FILE.write_text(json.dumps({"best_score": score}, indent=2), encoding="utf-8")
    except OSError:
        pass


# Décor fixe : piste, lignes de voie et silhouettes de bâtiments.
Entity(model="cube", position=(0, -0.25, 9), scale=(10, 0.5, 65), color=color.rgb(35, 43, 62))
for lane_edge in (-1.2, 1.2):
    Entity(model="cube", position=(lane_edge, 0.015, 9), scale=(0.045, 0.025, 65), color=color.rgb(105, 117, 143))
Entity(model="cube", position=(0, -0.55, 9), scale=(200, 0.1, 200), color=color.rgb(17, 24, 42))

for i in range(18):
    side = -1 if i % 2 == 0 else 1
    z = i * 5 - 8
    height = random.uniform(3.5, 9)
    building = Entity(
        model="cube",
        position=(side * random.uniform(7, 11), height / 2 - 0.2, z),
        scale=(random.uniform(2, 4), height, random.uniform(2, 4)),
        color=color.rgb(25, 34, 57),
    )
    building.collider = None


# Le personnage est construit avec des formes Ursina, sans images externes.
player = Entity(position=(LANES[1], 0, PLAYER_Z))
Entity(model="sphere", parent=player, position=(0, 2.15, 0), scale=0.58, color=color.rgb(245, 194, 66))
Entity(model="cube", parent=player, position=(0, 1.25, 0), scale=(0.42, 1.15, 0.3), color=color.rgb(235, 239, 247))
left_arm = Entity(model="cube", parent=player, position=(-0.34, 1.35, 0), scale=(0.16, 0.9, 0.18), color=color.rgb(235, 239, 247))
right_arm = Entity(model="cube", parent=player, position=(0.34, 1.35, 0), scale=(0.16, 0.9, 0.18), color=color.rgb(235, 239, 247))
left_leg = Entity(model="cube", parent=player, position=(-0.15, 0.45, 0), scale=(0.18, 0.85, 0.2), color=color.rgb(90, 190, 255))
right_leg = Entity(model="cube", parent=player, position=(0.15, 0.45, 0), scale=(0.18, 0.85, 0.2), color=color.rgb(90, 190, 255))

score_text = Text(text="Score : 0", position=(-0.86, 0.45), scale=1.4, color=color.white)
best_text = Text(text=f"Record : {load_best_score()}", position=(-0.86, 0.40), scale=1, color=color.rgb(185, 202, 230))
help_text = Text(text="← / → ou A / D : changer de voie     ESPACE : sauter", origin=(0, 0), position=(0, -0.46), scale=0.9, color=color.white)
message = Text(text="", origin=(0, 0), position=(0, 0.16), scale=2.2, color=color.white)

obstacles = []
playing = False
lane_index = 1
jump_velocity = 0
elapsed = 0
spawn_timer = 0
speed = 12
score = 0
best_score = load_best_score()


def set_overlay(title, subtitle, button_label, action):
    global overlay_title, overlay_subtitle, overlay_button
    overlay_title = Text(text=title, origin=(0, 0), position=(0, 0.22), scale=2.5, color=color.rgb(245, 194, 66))
    overlay_subtitle = Text(text=subtitle, origin=(0, 0), position=(0, 0.08), scale=1, color=color.white)
    overlay_button = Button(text=button_label, scale=(0.24, 0.075), position=(0, -0.08), color=color.rgb(58, 112, 190), on_click=action)


def clear_overlay():
    for name in ("overlay_title", "overlay_subtitle", "overlay_button"):
        element = globals().get(name)
        if element:
            destroy(element)


def start_game():
    global playing, lane_index, jump_velocity, elapsed, spawn_timer, speed, score
    clear_overlay()
    for obstacle in obstacles:
        destroy(obstacle)
    obstacles.clear()
    lane_index = 1
    player.x = LANES[lane_index]
    player.y = 0
    jump_velocity = 0
    elapsed = 0
    spawn_timer = 0.7
    speed = 12
    score = 0
    score_text.text = "Score : 0"
    message.text = ""
    help_text.enabled = True
    playing = True


def end_game():
    global playing, best_score
    playing = False
    help_text.enabled = False
    if score > best_score:
        best_score = score
        save_best_score(best_score)
        best_text.text = f"Nouveau record : {best_score}"
    else:
        best_text.text = f"Record : {best_score}"
    set_overlay("Fin de la partie", f"Score : {score}   •   Record : {best_score}", "Rejouer", start_game)


def spawn_obstacle():
    lane = random.randrange(len(LANES))
    obstacle = Entity(
        model="cube",
        position=(LANES[lane], 0.72, 29),
        scale=(1.15, 1.45, 0.9),
        color=color.rgb(236, 83, 91),
    )
    obstacle.lane_index = lane
    obstacles.append(obstacle)


def input(key):
    global lane_index, jump_velocity
    if key == "escape":
        application.quit()
    if not playing:
        return
    if key in ("left arrow", "a"):
        lane_index = max(0, lane_index - 1)
    elif key in ("right arrow", "d"):
        lane_index = min(len(LANES) - 1, lane_index + 1)
    elif key in ("space", "up arrow", "w") and player.y <= 0.01:
        jump_velocity = 9.5
    player.x = LANES[lane_index]


def update():
    global elapsed, spawn_timer, speed, score, jump_velocity
    if not playing:
        return

    dt = time.dt
    elapsed += dt
    speed = min(24, 12 + elapsed * 0.25)
    score = int(elapsed * 10)
    score_text.text = f"Score : {score}"

    # Saut avec gravité et animation de course.
    if player.y > 0 or jump_velocity > 0:
        jump_velocity -= 24 * dt
        player.y = max(0, player.y + jump_velocity * dt)
        if player.y == 0:
            jump_velocity = 0
    swing = math.sin(elapsed * 13) * 28
    left_arm.rotation_z = swing
    right_arm.rotation_z = -swing
    left_leg.rotation_z = -swing * 0.7
    right_leg.rotation_z = swing * 0.7

    spawn_timer -= dt
    if spawn_timer <= 0:
        spawn_obstacle()
        spawn_timer = random.uniform(1.0, 1.5) * max(0.65, 12 / speed)

    for obstacle in obstacles[:]:
        obstacle.z -= speed * dt
        if obstacle.z < PLAYER_Z + 0.65 and obstacle.z > PLAYER_Z - 0.4:
            if obstacle.lane_index == lane_index and player.y < 1.05:
                end_game()
                return
        if obstacle.z < -12:
            obstacles.remove(obstacle)
            destroy(obstacle)


help_text.enabled = False
set_overlay("Stickman Run", "Évite les obstacles et cours le plus longtemps possible !", "Jouer", start_game)
app.run()

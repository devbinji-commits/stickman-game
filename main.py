"""Stickman Arena — jeu de combat local en 2.5D, créé avec Ursina."""

import json
import math
import random
from pathlib import Path

from ursina import *


app = Ursina()
window.title = "Stickman Arena"
window.color = color.rgb(20, 25, 42)
window.fps_counter.enabled = True
camera.position = (0, 5.2, -19)
camera.look_at(Vec3(0, 2.2, 0))
camera.fov = 55

ARENA_LIMIT = 7.3
SAVE_PATH = Path(__file__).with_name("save.json")

# Décor de l'arène
Entity(model="cube", position=(0, -0.3, 0), scale=(18, 0.6, 8), color=color.rgb(48, 57, 78))
Entity(model="cube", position=(0, 0.03, 0), scale=(15, 0.035, 6), color=color.rgb(66, 75, 96))
for x in (-7.8, 7.8):
    Entity(model="cube", position=(x, 1, 0), scale=(0.25, 2, 6), color=color.rgb(112, 124, 151))
for x in range(-7, 8, 2):
    Entity(model="cube", position=(x, 0.06, 0), scale=(0.035, 0.02, 5.7), color=color.rgb(88, 98, 120))
Entity(model="cube", position=(0, 4.4, 4.5), scale=(22, 9, 0.2), color=color.rgb(27, 34, 54))
for i in range(10):
    Entity(model="sphere", position=(-8.7 + i * 1.93, 2.2 + (i % 3) * .55, 4.25), scale=(.3, .3, .15), color=color.rgb(80, 110, 158))


def limb_between(entity, start, end, thickness, tint):
    """Place un cylindre vertical entre deux articulations (coordonnées locales)."""
    delta = end - start
    length = max(delta.length(), 0.001)
    entity.position = (start + end) / 2
    entity.scale = (thickness, length, thickness)
    entity.rotation_z = math.degrees(math.atan2(-delta.x, delta.y))
    entity.color = tint


class Fighter:
    """Personnage stickman articulé, entièrement dessiné avec des formes Ursina."""

    def __init__(self, x, shirt, pants, skin, is_player=False):
        self.root = Entity(position=(x, 0, 0))
        self.shirt = shirt
        self.pants = pants
        self.skin = skin
        self.is_player = is_player
        self.health = 100
        self.facing = 1 if is_player else -1
        self.velocity_y = 0
        self.attack_timer = 0
        self.attack_cooldown = 0
        self.hit_flash = 0
        self.walk_time = 0
        self.blocking = False

        self.torso = Entity(model="cube", parent=self.root, position=(0, 1.83, 0), scale=(.47, .83, .3), color=shirt)
        self.head = Entity(model="sphere", parent=self.root, position=(0, 2.55, 0), scale=(.54, .58, .48), color=skin)
        # Yeux tournés vers la caméra, avec une pupille pour donner une expression.
        for eye_x in (-.15, .15):
            Entity(model="sphere", parent=self.root, position=(eye_x, 2.61, -.222), scale=(.075, .09, .04), color=color.white)
            Entity(model="sphere", parent=self.root, position=(eye_x, 2.61, -.257), scale=(.035, .05, .025), color=color.black)
        self.arm_l = Entity(model="cylinder", parent=self.root, color=shirt)
        self.arm_r = Entity(model="cylinder", parent=self.root, color=shirt)
        self.leg_l = Entity(model="cylinder", parent=self.root, color=pants)
        self.leg_r = Entity(model="cylinder", parent=self.root, color=pants)
        self.hand_l = Entity(model="sphere", parent=self.root, scale=.2, color=skin)
        self.hand_r = Entity(model="sphere", parent=self.root, scale=.2, color=skin)
        self.foot_l = Entity(model="cube", parent=self.root, scale=(.36, .16, .32), color=pants)
        self.foot_r = Entity(model="cube", parent=self.root, scale=(.36, .16, .32), color=pants)
        self.update_pose(0)

    @property
    def x(self):
        return self.root.x

    @x.setter
    def x(self, value):
        self.root.x = value

    @property
    def y(self):
        return self.root.y

    @y.setter
    def y(self, value):
        self.root.y = value

    def update_pose(self, dt):
        if dt:
            self.walk_time += dt * (12 if abs(getattr(self, "move_amount", 0)) > .01 else 3)
        stride = math.sin(self.walk_time) * .38 if self.y < .05 else 0
        crouch = -.15 if self.blocking else 0
        attack = self.attack_timer > 0

        shoulder_l = Vec3(-.25, 2.12 + crouch, 0)
        shoulder_r = Vec3(.25, 2.12 + crouch, 0)
        hip_l = Vec3(-.13, 1.38, 0)
        hip_r = Vec3(.13, 1.38, 0)
        if attack:
            fist_x = self.facing * .95
            fist = Vec3(fist_x, 2.03, -.02)
            mid = Vec3(self.facing * .5, 2.1, 0)
            arm_start = shoulder_r if self.facing > 0 else shoulder_l
            arm_entity = self.arm_r if self.facing > 0 else self.arm_l
            hand_entity = self.hand_r if self.facing > 0 else self.hand_l
            limb_between(arm_entity, arm_start, mid, .19, self.shirt)
            limb_between(self.arm_l if arm_entity is self.arm_r else self.arm_r,
                         shoulder_l if arm_entity is self.arm_r else shoulder_r,
                         Vec3(-self.facing * .43, 1.88 + crouch, 0), .16, self.shirt)
            hand_entity.position = fist
            self.hand_l.position = Vec3(-self.facing * .48, 1.83 + crouch, 0) if hand_entity is self.hand_r else fist
            self.hand_r.position = Vec3(-self.facing * .48, 1.83 + crouch, 0) if hand_entity is self.hand_l else fist
        else:
            left_hand = Vec3(-.48 + stride * .35, 1.6 + crouch, 0)
            right_hand = Vec3(.48 - stride * .35, 1.6 + crouch, 0)
            limb_between(self.arm_l, shoulder_l, left_hand, .16, self.shirt)
            limb_between(self.arm_r, shoulder_r, right_hand, .16, self.shirt)
            self.hand_l.position = left_hand
            self.hand_r.position = right_hand

        knee_l = Vec3(-.18 + stride, .72, 0)
        knee_r = Vec3(.18 - stride, .72, 0)
        ankle_l = Vec3(-.2 - stride * .6, .16, 0)
        ankle_r = Vec3(.2 + stride * .6, .16, 0)
        limb_between(self.leg_l, hip_l, knee_l, .17, self.pants)
        limb_between(self.leg_r, hip_r, knee_r, .17, self.pants)
        limb_between(self.leg_l, knee_l, ankle_l, .14, self.pants)
        limb_between(self.leg_r, knee_r, ankle_r, .14, self.pants)
        self.foot_l.position = ankle_l + Vec3(self.facing * .1, -.06, 0)
        self.foot_r.position = ankle_r + Vec3(self.facing * .1, -.06, 0)
        self.torso.y = 1.83 + crouch
        self.head.y = 2.55 + crouch
        self.torso.color = color.white if self.hit_flash > 0 else self.shirt


player = Fighter(-3.2, color.rgb(57, 160, 255), color.rgb(34, 65, 138), color.rgb(245, 190, 145), True)
enemy = Fighter(3.2, color.rgb(244, 79, 91), color.rgb(129, 39, 61), color.rgb(220, 164, 120))

player_name = Text("JOUEUR", parent=camera.ui, position=(-.55, .4), origin=(0, 0), scale=1.2, color=color.rgb(93, 185, 255))
enemy_name = Text("ADVERSAIRE", parent=camera.ui, position=(.25, .4), origin=(0, 0), scale=1.2, color=color.rgb(255, 112, 119))
player_bar_bg = Entity(parent=camera.ui, model="quad", position=(-.38, .35), scale=(.42, .035), color=color.rgb(66, 73, 91))
enemy_bar_bg = Entity(parent=camera.ui, model="quad", position=(.38, .35), scale=(.42, .035), color=color.rgb(66, 73, 91))
player_bar = Entity(parent=camera.ui, model="quad", position=(-.38, .35, -.01), scale=(.42, .025), color=color.rgb(70, 220, 125))
enemy_bar = Entity(parent=camera.ui, model="quad", position=(.38, .35, -.01), scale=(.42, .025), color=color.rgb(255, 85, 95))
score_label = Text("Victoires : 0", parent=camera.ui, position=(-.86, .46), scale=1, color=color.white)
help_label = Text("A / D ou ← / → : bouger     ESPACE : sauter     J : frapper     K : bloquer", parent=camera.ui,
                  origin=(0, 0), position=(0, -.46), scale=.85, color=color.white)
message = Text("", parent=camera.ui, origin=(0, 0), position=(0, .08), scale=2.2, color=color.rgb(255, 218, 91))

wins = 0
round_over = False
round_timer = 0

def update_health_bars():
    player_bar.scale_x = .42 * max(0, player.health) / 100
    enemy_bar.scale_x = .42 * max(0, enemy.health) / 100
    player_bar.x = -.59 + player_bar.scale_x / 2
    enemy_bar.x = .17 + enemy_bar.scale_x / 2


def attack(attacker, target):
    if attacker.attack_cooldown > 0 or round_over:
        return
    attacker.attack_timer = .24
    attacker.attack_cooldown = .62
    # La frappe touche uniquement à courte distance et si les personnages se font face.
    gap = abs(attacker.x - target.x)
    target_is_forward = (target.x - attacker.x) * attacker.facing > 0
    if gap < 2.15 and target_is_forward and target.y < 1.15:
        if target.blocking:
            damage = 4
        else:
            damage = random.randint(10, 16)
        target.health = max(0, target.health - damage)
        target.hit_flash = .12
        target.x = clamp(target.x + attacker.facing * .28, -ARENA_LIMIT, ARENA_LIMIT)
        update_health_bars()
        if target.health <= 0:
            finish_round(attacker is player)


def finish_round(player_won):
    global round_over, round_timer, wins
    round_over = True
    round_timer = 2.2
    if player_won:
        wins += 1
        score_label.text = f"Victoires : {wins}"
        message.text = "VICTOIRE !"
        message.color = color.rgb(255, 218, 91)
    else:
        message.text = "DÉFAITE !"
        message.color = color.rgb(255, 112, 119)


def reset_round():
    global round_over, round_timer
    player.health = enemy.health = 100
    player.x, enemy.x = -3.2, 3.2
    player.y = enemy.y = 0
    player.velocity_y = enemy.velocity_y = 0
    player.blocking = enemy.blocking = False
    player.attack_timer = enemy.attack_timer = 0
    message.text = ""
    round_over = False
    round_timer = 0
    update_health_bars()


def input(key):
    if key == "escape":
        application.quit()
    if round_over:
        return
    if key in ("j", "f"):
        attack(player, enemy)
    if key == "space" and player.y <= .01:
        player.velocity_y = 8.5
    if key in ("k", "shift"):
        player.blocking = True


def update():
    global round_timer
    dt = time.dt
    if round_over:
        round_timer -= dt
        if round_timer <= 0:
            reset_round()
        return

    # Déplacement du joueur
    move = held_keys["d"] + held_keys["right arrow"] - held_keys["a"] - held_keys["left arrow"]
    player.move_amount = move
    if move:
        player.x = clamp(player.x + move * 6 * dt, -ARENA_LIMIT, ARENA_LIMIT)
        player.facing = 1 if move > 0 else -1
    player.blocking = held_keys["k"] or held_keys["shift"]

    # Adversaire contrôlé par une IA légère : il s'approche et attaque à portée.
    distance = abs(player.x - enemy.x)
    enemy.facing = -1 if enemy.x > player.x else 1
    enemy.move_amount = 0
    if distance > 1.55:
        enemy.move_amount = 1
        enemy.x += enemy.facing * 2.35 * dt
    elif enemy.attack_cooldown <= 0:
        attack(enemy, player)

    for fighter in (player, enemy):
        fighter.attack_timer = max(0, fighter.attack_timer - dt)
        fighter.attack_cooldown = max(0, fighter.attack_cooldown - dt)
        fighter.hit_flash = max(0, fighter.hit_flash - dt)
        if fighter.y > 0 or fighter.velocity_y > 0:
            fighter.velocity_y -= 22 * dt
            fighter.y = max(0, fighter.y + fighter.velocity_y * dt)
            if fighter.y == 0:
                fighter.velocity_y = 0
        fighter.update_pose(dt)

    # Empêche les deux combattants de se traverser.
    if abs(player.x - enemy.x) < 1.0:
        direction = 1 if player.x < enemy.x else -1
        player.x -= direction * .025
        enemy.x += direction * .025


update_health_bars()
app.run()

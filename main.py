"""Stickman Arena — combat cartoon 2.5D avec Ursina, sans Pygame."""

import math
import random

from ursina import *

app = Ursina()
window.title = "Stickman Arena"
window.color = color.rgb(16, 20, 36)
window.fps_counter.enabled = True
camera.position = (0, 5.2, -19)
camera.look_at(Vec3(0, 2.05, 0))
camera.fov = 53

ARENA_LIMIT = 7.1

# Arène colorée avec éclairage doux.
AmbientLight(color=color.rgba(175, 185, 210, 255))
DirectionalLight(y=8, z=-5, rotation=(35, -30, 0), color=color.rgba(255, 246, 224, 255))
Entity(model="cube", position=(0, -.38, 0), scale=(18, .7, 8), color=color.rgb(35, 42, 61))
Entity(model="cube", position=(0, -.015, 0), scale=(15, .035, 6), color=color.rgb(62, 70, 91))
for x in (-7.8, 7.8):
    Entity(model="cube", position=(x, 1, 0), scale=(.22, 2, 6), color=color.rgb(112, 124, 151))
for x in range(-7, 8, 2):
    Entity(model="cube", position=(x, .012, 0), scale=(.025, .02, 5.7), color=color.rgb(99, 108, 130))
Entity(model="cube", position=(0, 4.2, 4.5), scale=(22, 9, .2), color=color.rgb(26, 31, 51))
for i in range(10):
    Entity(model="sphere", position=(-8.7 + i * 1.93, 2.1 + (i % 3) * .5, 4.25), scale=(.27, .27, .14), color=color.rgb(86, 108, 151))


def set_segment(part, start, end, thickness):
    delta = end - start
    part.position = (start + end) / 2
    part.scale = (thickness, max(delta.length() / 2, .01), thickness)
    part.rotation_z = math.degrees(math.atan2(-delta.x, delta.y))


class Fighter:
    """Personnage cartoon aux formes rondes et aux membres colorés articulés."""

    def __init__(self, x, main_color, player=False):
        self.root = Entity(position=(x, 0, 0))
        self.main_color = main_color
        self.player = player
        self.health = 100
        self.facing = 1 if player else -1
        self.velocity_y = 0
        self.attack_timer = 0
        self.attack_cooldown = 0
        self.hit_flash = 0
        self.walk_time = 0
        self.blocking = False
        self.move_amount = 0

        outline = color.rgb(28, 29, 43)
        # Tête ronde surdimensionnée, petit corps « capsule » et couleurs franches.
        self.head_outline = Entity(model="sphere", parent=self.root, position=(0, 2.45, 0), scale=(.73, .75, .58), color=outline)
        self.head = Entity(model="sphere", parent=self.root, position=(0, 2.47, -.035), scale=(.64, .66, .57), color=main_color)
        # Visage simple et lisible, comme un personnage de jeu d'arcade.
        self.eye_l = Entity(model="sphere", parent=self.root, position=(-.17, 2.53, -.53), scale=(.09, .11, .045), color=color.white)
        self.eye_r = Entity(model="sphere", parent=self.root, position=(.17, 2.53, -.53), scale=(.09, .11, .045), color=color.white)
        self.pupil_l = Entity(model="sphere", parent=self.root, position=(-.14, 2.52, -.568), scale=(.045, .06, .025), color=outline)
        self.pupil_r = Entity(model="sphere", parent=self.root, position=(.20, 2.52, -.568), scale=(.045, .06, .025), color=outline)
        self.mouth = Entity(model="cube", parent=self.root, position=(.02, 2.29, -.55), scale=(.16, .035, .025), color=outline)

        self.torso_outline = Entity(model="sphere", parent=self.root, position=(0, 1.45, 0), scale=(.62, .92, .48), color=outline)
        self.torso = Entity(model="sphere", parent=self.root, position=(0, 1.48, -.04), scale=(.53, .83, .48), color=main_color)
        self.belt = Entity(model="cube", parent=self.root, position=(0, .98, -.28), scale=(.52, .13, .07), color=color.rgb(255, 218, 91))

        # Chaque membre comprend un contour sombre et un segment coloré.
        self.parts = {}
        for name in ("arm_l1", "arm_l2", "arm_r1", "arm_r2", "leg_l1", "leg_l2", "leg_r1", "leg_r2"):
            self.parts[name + "_outline"] = Entity(model="cylinder", parent=self.root, color=outline)
            self.parts[name] = Entity(model="cylinder", parent=self.root, color=main_color)
        self.joints = [Entity(model="sphere", parent=self.root, scale=.23, color=main_color) for _ in range(6)]
        self.hands = [Entity(model="sphere", parent=self.root, scale=(.25, .24, .24), color=main_color) for _ in range(2)]
        self.feet = [Entity(model="sphere", parent=self.root, scale=(.36, .19, .3), color=outline) for _ in range(2)]
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

    def limb(self, name, start, end, thickness):
        set_segment(self.parts[name + "_outline"], start, end, thickness * 1.42)
        set_segment(self.parts[name], start, end, thickness)

    def update_pose(self, dt):
        if dt:
            self.walk_time += dt * (11 if abs(self.move_amount) > .01 else 2.5)
        stride = math.sin(self.walk_time) * .34 if self.y < .05 else 0
        shoulder_l, shoulder_r = Vec3(-.34, 1.95, 0), Vec3(.34, 1.95, 0)
        hip_l, hip_r = Vec3(-.2, 1.02, 0), Vec3(.2, 1.02, 0)
        knee_l, knee_r = Vec3(-.2 + stride, .58, 0), Vec3(.2 - stride, .58, 0)
        ankle_l, ankle_r = Vec3(-.2 - stride * .55, .16, 0), Vec3(.2 + stride * .55, .16, 0)

        if self.attack_timer > 0:
            fist = Vec3(self.facing * 1.02, 1.98, -.05)
            elbow = Vec3(self.facing * .59, 2.03, 0)
            resting_elbow = Vec3(-self.facing * .42, 1.72, 0)
            resting_hand = Vec3(-self.facing * .5, 1.45, 0)
            if self.facing > 0:
                arms = ((shoulder_l, resting_elbow, resting_hand), (shoulder_r, elbow, fist))
            else:
                arms = ((shoulder_l, elbow, fist), (shoulder_r, resting_elbow, resting_hand))
        elif self.blocking:
            arms = ((shoulder_l, Vec3(-.38, 2.18, 0), Vec3(-.12, 2.37, -.08)),
                    (shoulder_r, Vec3(.38, 2.18, 0), Vec3(.12, 2.37, -.08)))
        else:
            arms = ((shoulder_l, Vec3(-.48 + stride * .2, 1.64, 0), Vec3(-.52 + stride * .3, 1.34, 0)),
                    (shoulder_r, Vec3(.48 - stride * .2, 1.64, 0), Vec3(.52 - stride * .3, 1.34, 0)))

        for side, (shoulder, elbow, hand) in zip(("l", "r"), arms):
            self.limb(f"arm_{side}1", shoulder, elbow, .16)
            self.limb(f"arm_{side}2", elbow, hand, .14)
            self.hands[0 if side == "l" else 1].position = hand
        for side, hip, knee, ankle in (("l", hip_l, knee_l, ankle_l), ("r", hip_r, knee_r, ankle_r)):
            self.limb(f"leg_{side}1", hip, knee, .18)
            self.limb(f"leg_{side}2", knee, ankle, .15)

        for joint, point in zip(self.joints, (shoulder_l, shoulder_r, hip_l, hip_r, knee_l, knee_r)):
            joint.position = point
        self.feet[0].position = ankle_l + Vec3(self.facing * .1, -.02, -.02)
        self.feet[1].position = ankle_r + Vec3(self.facing * .1, -.02, -.02)
        if self.hit_flash > 0:
            self.head.color = self.torso.color = color.white
        else:
            self.head.color = self.torso.color = self.main_color
        self.head.y = 2.47 + (.025 * math.sin(self.walk_time * 2) if self.move_amount else 0)


player = Fighter(-3.2, color.rgb(43, 171, 255), True)
enemy = Fighter(3.2, color.rgb(255, 76, 100))

Text("JOUEUR", parent=camera.ui, position=(-.69, .405), scale=1, color=color.rgb(105, 199, 255))
Text("ADVERSAIRE", parent=camera.ui, position=(.38, .405), scale=1, color=color.rgb(255, 117, 127))
Entity(parent=camera.ui, model="quad", position=(-.39, .365), scale=(.43, .035), color=color.rgb(60, 67, 83))
Entity(parent=camera.ui, model="quad", position=(.39, .365), scale=(.43, .035), color=color.rgb(60, 67, 83))
player_bar = Entity(parent=camera.ui, model="quad", position=(-.39, .365, -.01), scale=(.43, .025), color=color.rgb(71, 225, 133))
enemy_bar = Entity(parent=camera.ui, model="quad", position=(.39, .365, -.01), scale=(.43, .025), color=color.rgb(255, 75, 93))
score_label = Text("Victoires : 0", parent=camera.ui, position=(-.86, .46), scale=.9, color=color.white)
Text("A / D ou ← / → : bouger     ESPACE : sauter     J : frapper     K : bloquer", parent=camera.ui,
     origin=(0, 0), position=(0, -.46), scale=.8, color=color.white)
message = Text("", parent=camera.ui, origin=(0, 0), position=(0, .08), scale=2.2, color=color.rgb(255, 218, 91))

wins = 0
round_over = False
round_timer = 0


def update_health_bars():
    player_bar.scale_x = .43 * max(0, player.health) / 100
    enemy_bar.scale_x = .43 * max(0, enemy.health) / 100
    player_bar.x = -.605 + player_bar.scale_x / 2
    enemy_bar.x = .175 + enemy_bar.scale_x / 2


def attack(attacker, target):
    if attacker.attack_cooldown > 0 or round_over:
        return
    attacker.attack_timer = .28
    attacker.attack_cooldown = .58
    gap = abs(attacker.x - target.x)
    if gap < 2.05 and (target.x - attacker.x) * attacker.facing > 0 and target.y < 1.1:
        target.health = max(0, target.health - (4 if target.blocking else random.randint(10, 15)))
        target.hit_flash = .16
        target.x = clamp(target.x + attacker.facing * .3, -ARENA_LIMIT, ARENA_LIMIT)
        update_health_bars()
        if target.health <= 0:
            finish_round(attacker is player)


def finish_round(player_won):
    global round_over, round_timer, wins
    round_over, round_timer = True, 2.1
    message.text = "VICTOIRE !" if player_won else "DÉFAITE !"
    message.color = color.rgb(255, 218, 91) if player_won else color.rgb(255, 112, 119)
    if player_won:
        wins += 1
        score_label.text = f"Victoires : {wins}"


def reset_round():
    global round_over, round_timer
    player.health = enemy.health = 100
    player.x, enemy.x = -3.2, 3.2
    player.y = enemy.y = 0
    player.velocity_y = enemy.velocity_y = 0
    player.blocking = enemy.blocking = False
    player.attack_timer = enemy.attack_timer = 0
    message.text = ""
    round_over, round_timer = False, 0
    update_health_bars()


def input(key):
    if key == "escape":
        application.quit()
    if round_over:
        return
    if key in ("j", "f"):
        attack(player, enemy)
    elif key == "space" and player.y <= .01:
        player.velocity_y = 8.5


def update():
    global round_timer
    dt = time.dt
    if round_over:
        round_timer -= dt
        if round_timer <= 0:
            reset_round()
        return

    move = held_keys["d"] + held_keys["right arrow"] - held_keys["a"] - held_keys["left arrow"]
    player.move_amount = move
    if move:
        player.x = clamp(player.x + move * 6 * dt, -ARENA_LIMIT, ARENA_LIMIT)
        player.facing = 1 if move > 0 else -1
    player.blocking = bool(held_keys["k"] or held_keys["shift"])

    distance = abs(player.x - enemy.x)
    enemy.facing = -1 if enemy.x > player.x else 1
    enemy.move_amount = 0
    if distance > 1.5:
        enemy.move_amount = 1
        enemy.x += enemy.facing * 2.3 * dt
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

    if abs(player.x - enemy.x) < 1.0:
        direction = 1 if player.x < enemy.x else -1
        player.x -= direction * .025
        enemy.x += direction * .025


update_health_bars()
app.run()

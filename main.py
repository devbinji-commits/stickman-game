"""Stickman Arena — combat 2.5D avec combattants articulés, réalisé avec Ursina."""

import math
import random

from ursina import *


app = Ursina()
window.title = "Stickman Arena"
window.color = color.rgb(13, 17, 31)
window.fps_counter.enabled = True
camera.position = (0, 5.2, -19)
camera.look_at(Vec3(0, 2.15, 0))
camera.fov = 53

ARENA_LIMIT = 7.1

# Éclairage et décor : l'arène reste lisible même avec des couleurs sombres.
AmbientLight(color=color.rgba(150, 165, 205, 255))
DirectionalLight(y=8, z=-5, rotation=(35, -30, 0), color=color.rgba(255, 242, 220, 255))
Entity(model="cube", position=(0, -.38, 0), scale=(18, .7, 8), color=color.rgb(35, 42, 61))
Entity(model="cube", position=(0, -.015, 0), scale=(15, .035, 6), color=color.rgb(56, 65, 87))
for x in (-7.8, 7.8):
    Entity(model="cube", position=(x, 1, 0), scale=(.22, 2, 6), color=color.rgb(107, 120, 151))
for x in range(-7, 8, 2):
    Entity(model="cube", position=(x, .012, 0), scale=(.025, .02, 5.7), color=color.rgb(83, 94, 120))
Entity(model="cube", position=(0, 4.2, 4.5), scale=(22, 9, .2), color=color.rgb(22, 28, 47))
for i in range(10):
    Entity(model="sphere", position=(-8.7 + i * 1.93, 2.1 + (i % 3) * .5, 4.25), scale=(.27, .27, .14), color=color.rgb(77, 104, 151))


def place_limb(part, start, end, thickness):
    """Place un segment cylindrique entre deux points locaux du personnage."""
    delta = end - start
    length = max(delta.length(), .001)
    part.position = (start + end) / 2
    # Le cylindre Ursina mesure deux unités de haut à l'échelle 1.
    part.scale = (thickness, length / 2, thickness)
    part.rotation_z = math.degrees(math.atan2(-delta.x, delta.y))


class Fighter:
    """Stickman stylisé avec segments articulés, accessoires et animations."""

    def __init__(self, x, accent, pants, skin, player=False):
        self.root = Entity(position=(x, 0, 0))
        self.accent, self.pants, self.skin = accent, pants, skin
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

        ink = color.rgb(24, 27, 38)
        # Tête cerclée, visage et bandeau coloré : silhouette plus expressive.
        self.head_outline = Entity(model="sphere", parent=self.root, position=(0, 2.52, 0), scale=(.61, .65, .52), color=ink)
        self.head = Entity(model="sphere", parent=self.root, position=(0, 2.53, -.035), scale=(.49, .53, .47), color=skin)
        self.band = Entity(model="cube", parent=self.root, position=(0, 2.77, -.285), scale=(.72, .12, .07), color=accent)
        for eye_x in (-.15, .15):
            Entity(model="sphere", parent=self.root, position=(eye_x, 2.55, -.267), scale=(.07, .085, .035), color=ink)
        self.torso = Entity(model="cylinder", parent=self.root, position=(0, 1.8, 0), scale=(.31, .45, .31), color=ink)
        self.chest = Entity(model="cube", parent=self.root, position=(0, 1.92, -.17), scale=(.35, .39, .07), color=accent)
        self.belt = Entity(model="cube", parent=self.root, position=(0, 1.43, -.02), scale=(.39, .11, .33), color=color.rgb(229, 197, 118))

        self.arm_l1 = self.segment(ink); self.arm_l2 = self.segment(ink)
        self.arm_r1 = self.segment(ink); self.arm_r2 = self.segment(ink)
        self.leg_l1 = self.segment(ink); self.leg_l2 = self.segment(ink)
        self.leg_r1 = self.segment(ink); self.leg_r2 = self.segment(ink)
        self.joints = [Entity(model="sphere", parent=self.root, scale=.18, color=ink) for _ in range(6)]
        self.glove_l = Entity(model="sphere", parent=self.root, scale=(.23, .22, .2), color=accent)
        self.glove_r = Entity(model="sphere", parent=self.root, scale=(.23, .22, .2), color=accent)
        self.boot_l = Entity(model="cube", parent=self.root, scale=(.38, .17, .32), color=pants)
        self.boot_r = Entity(model="cube", parent=self.root, scale=(.38, .17, .32), color=pants)
        self.update_pose(0)

    def segment(self, tint):
        return Entity(model="cylinder", parent=self.root, color=tint)

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
            self.walk_time += dt * (11 if abs(self.move_amount) > .01 else 3)
        stride = math.sin(self.walk_time) * .34 if self.y < .05 else 0
        bend = -.12 if self.blocking else 0
        shoulder_l, shoulder_r = Vec3(-.25, 2.12 + bend, 0), Vec3(.25, 2.12 + bend, 0)
        hip_l, hip_r = Vec3(-.14, 1.42, 0), Vec3(.14, 1.42, 0)
        knee_l, knee_r = Vec3(-.18 + stride, .77, 0), Vec3(.18 - stride, .77, 0)
        ankle_l, ankle_r = Vec3(-.2 - stride * .58, .17, 0), Vec3(.2 + stride * .58, .17, 0)

        if self.attack_timer > 0:
            fist = Vec3(self.facing * 1.03, 2.02, -.03)
            elbow = Vec3(self.facing * .55, 2.13, 0)
            idle_hand = Vec3(-self.facing * .5, 1.8 + bend, 0)
            idle_elbow = Vec3(-self.facing * .42, 1.97 + bend, 0)
            if self.facing > 0:
                arm_points = ((shoulder_l, idle_elbow, idle_hand), (shoulder_r, elbow, fist))
            else:
                arm_points = ((shoulder_l, elbow, fist), (shoulder_r, idle_elbow, idle_hand))
        elif self.blocking:
            arm_points = ((shoulder_l, Vec3(-.25, 2.35, 0), Vec3(-.12, 2.47, -.08)),
                          (shoulder_r, Vec3(.25, 2.35, 0), Vec3(.12, 2.47, -.08)))
        else:
            arm_points = ((shoulder_l, Vec3(-.43 + stride * .25, 1.86, 0), Vec3(-.5 + stride * .35, 1.58, 0)),
                          (shoulder_r, Vec3(.43 - stride * .25, 1.86, 0), Vec3(.5 - stride * .35, 1.58, 0)))

        for seg, (start, elbow, hand) in zip((self.arm_l1, self.arm_l2, self.arm_r1, self.arm_r2),
                                              (arm_points[0][0:2], arm_points[0][1:3], arm_points[1][0:2], arm_points[1][1:3])):
            place_limb(seg, start, elbow, .095) if seg in (self.arm_l1, self.arm_r1) else place_limb(seg, elbow, hand, .085)
        self.glove_l.position = arm_points[0][2]
        self.glove_r.position = arm_points[1][2]

        for seg, start, end in ((self.leg_l1, hip_l, knee_l), (self.leg_l2, knee_l, ankle_l),
                                (self.leg_r1, hip_r, knee_r), (self.leg_r2, knee_r, ankle_r)):
            place_limb(seg, start, end, .105 if seg in (self.leg_l1, self.leg_r1) else .09)
        self.boot_l.position = ankle_l + Vec3(self.facing * .12, -.04, 0)
        self.boot_r.position = ankle_r + Vec3(self.facing * .12, -.04, 0)
        points = (shoulder_l, shoulder_r, hip_l, hip_r, knee_l, knee_r)
        for joint, point in zip(self.joints, points):
            joint.position = point
        self.torso.color = color.white if self.hit_flash > 0 else color.rgb(24, 27, 38)
        self.chest.color = color.white if self.hit_flash > 0 else self.accent
        self.band.color = color.white if self.hit_flash > 0 else self.accent


player = Fighter(-3.2, color.rgb(45, 170, 255), color.rgb(32, 54, 112), color.rgb(246, 194, 150), True)
enemy = Fighter(3.2, color.rgb(255, 72, 91), color.rgb(112, 31, 57), color.rgb(219, 160, 119))

Text("JOUEUR", parent=camera.ui, position=(-.69, .405), scale=1, color=color.rgb(105, 199, 255))
Text("ADVERSAIRE", parent=camera.ui, position=(.38, .405), scale=1, color=color.rgb(255, 117, 127))
Entity(parent=camera.ui, model="quad", position=(-.39, .365), scale=(.43, .035), color=color.rgb(60, 67, 83))
Entity(parent=camera.ui, model="quad", position=(.39, .365), scale=(.43, .035), color=color.rgb(60, 67, 83))
player_bar = Entity(parent=camera.ui, model="quad", position=(-.39, .365, -.01), scale=(.43, .025), color=color.rgb(71, 225, 133))
enemy_bar = Entity(parent=camera.ui, model="quad", position=(.39, .365, -.01), scale=(.43, .025), color=color.rgb(255, 75, 93))
score_label = Text("Victoires : 0", parent=camera.ui, position=(-.86, .46), scale=.9, color=color.white)
help_label = Text("A / D ou ← / → : bouger     ESPACE : sauter     J : frapper     K : bloquer", parent=camera.ui,
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

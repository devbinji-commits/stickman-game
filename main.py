"""Stickman Arena — jeu de combat cartoon local réalisé avec Ursina."""

import math
import random

from ursina import *


app = Ursina()
window.title = "Stickman Arena"
window.color = color.rgb(18, 22, 40)
window.fps_counter.enabled = True
camera.position = (0, 5.2, -19)
camera.look_at(Vec3(0, 2.0, 0))
camera.fov = 53

ARENA_LIMIT = 7.0
PALETTES = [
    ("AZUR", color.rgb(45, 165, 255)),
    ("CORAIL", color.rgb(255, 75, 96)),
    ("SOLEIL", color.rgb(255, 190, 45)),
    ("VIOLET", color.rgb(174, 100, 255)),
    ("MENTHE", color.rgb(60, 220, 150)),
]

# Petite arène stylisée. Les combattants sont des formes 3D originales, sans images externes.
AmbientLight(color=color.rgba(175, 185, 210, 255))
DirectionalLight(y=8, z=-5, rotation=(35, -30, 0), color=color.rgba(255, 246, 224, 255))
world_entities = []

def world_entity(**kwargs):
    entity = Entity(**kwargs)
    world_entities.append(entity)
    return entity

world_entity(model="cube", position=(0, -.38, 0), scale=(18, .7, 8), color=color.rgb(35, 42, 61))
world_entity(model="cube", position=(0, -.015, 0), scale=(15, .035, 6), color=color.rgb(62, 70, 91))
for x in (-7.8, 7.8):
    world_entity(model="cube", position=(x, 1, 0), scale=(.22, 2, 6), color=color.rgb(112, 124, 151))
for x in range(-7, 8, 2):
    world_entity(model="cube", position=(x, .012, 0), scale=(.025, .02, 5.7), color=color.rgb(99, 108, 130))
world_entity(model="cube", position=(0, 4.2, 4.5), scale=(22, 9, .2), color=color.rgb(26, 31, 51))
for i in range(10):
    world_entity(model="sphere", position=(-8.7 + i * 1.93, 2.1 + (i % 3) * .5, 4.25), scale=(.27, .27, .14), color=color.rgb(86, 108, 151))


def set_segment(part, start, end, thickness):
    delta = end - start
    part.position = (start + end) / 2
    part.scale = (thickness, max(delta.length() / 2, .01), thickness)
    part.rotation_z = math.degrees(math.atan2(-delta.x, delta.y))


class Fighter:
    """Combattant cartoon compact, avec tête expressive et membres articulés."""

    def __init__(self, x, palette_index, player_number):
        self.root = Entity(position=(x, 0, 0))
        self.palette_index = palette_index
        self.player_number = player_number
        self.health = 100
        self.facing = 1 if player_number == 1 else -1
        self.velocity_y = 0
        self.attack_timer = 0
        self.attack_cooldown = 0
        self.hit_flash = 0
        self.walk_time = 0
        self.blocking = False
        self.move_amount = 0
        self.setup_model()
        self.set_palette(palette_index)
        self.update_pose(0)

    def setup_model(self):
        outline = color.rgb(29, 29, 43)
        self.head_outline = Entity(model="sphere", parent=self.root, position=(0, 2.45, 0), scale=(.73, .75, .58), color=outline)
        self.head = Entity(model="sphere", parent=self.root, position=(0, 2.47, -.035), scale=(.64, .66, .57))
        self.eye_l = Entity(model="sphere", parent=self.root, position=(-.17, 2.53, -.53), scale=(.09, .11, .045), color=color.white)
        self.eye_r = Entity(model="sphere", parent=self.root, position=(.17, 2.53, -.53), scale=(.09, .11, .045), color=color.white)
        self.pupil_l = Entity(model="sphere", parent=self.root, position=(-.14, 2.52, -.568), scale=(.045, .06, .025), color=outline)
        self.pupil_r = Entity(model="sphere", parent=self.root, position=(.20, 2.52, -.568), scale=(.045, .06, .025), color=outline)
        self.mouth = Entity(model="cube", parent=self.root, position=(.02, 2.29, -.55), scale=(.16, .035, .025), color=outline)
        self.torso_outline = Entity(model="sphere", parent=self.root, position=(0, 1.45, 0), scale=(.62, .92, .48), color=outline)
        self.torso = Entity(model="sphere", parent=self.root, position=(0, 1.48, -.04), scale=(.53, .83, .48))
        self.belt = Entity(model="cube", parent=self.root, position=(0, .98, -.28), scale=(.52, .13, .07), color=color.rgb(255, 218, 91))
        self.limbs = {}
        for name in ("arm_l1", "arm_l2", "arm_r1", "arm_r2", "leg_l1", "leg_l2", "leg_r1", "leg_r2"):
            self.limbs[name + "_outline"] = Entity(model="cylinder", parent=self.root, color=outline)
            self.limbs[name] = Entity(model="cylinder", parent=self.root)
        self.joints = [Entity(model="sphere", parent=self.root, scale=.23, color=outline) for _ in range(6)]
        self.hands = [Entity(model="sphere", parent=self.root, scale=(.25, .24, .24)) for _ in range(2)]
        self.feet = [Entity(model="sphere", parent=self.root, scale=(.36, .19, .3), color=outline) for _ in range(2)]

    def set_palette(self, index):
        self.palette_index = index % len(PALETTES)
        self.accent = PALETTES[self.palette_index][1]
        self.head.color = self.torso.color = self.accent
        for part in self.limbs.values():
            if not part.name.endswith("_outline"):
                part.color = self.accent
        for joint in self.joints + self.hands:
            joint.color = self.accent

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
        set_segment(self.limbs[name + "_outline"], start, end, thickness * 1.42)
        set_segment(self.limbs[name], start, end, thickness)

    def update_pose(self, dt):
        if dt:
            self.walk_time += dt * (11 if abs(self.move_amount) > .01 else 2.5)
        stride = math.sin(self.walk_time) * .34 if self.y < .05 else 0
        shoulder_l, shoulder_r = Vec3(-.34, 1.95, 0), Vec3(.34, 1.95, 0)
        hip_l, hip_r = Vec3(-.2, 1.02, 0), Vec3(.2, 1.02, 0)
        knee_l, knee_r = Vec3(-.2 + stride, .58, 0), Vec3(.2 - stride, .58, 0)
        ankle_l, ankle_r = Vec3(-.2 - stride * .55, .16, 0), Vec3(.2 + stride * .55, .16, 0)
        if self.attack_timer > 0:
            fist, elbow = Vec3(self.facing * 1.02, 1.98, -.05), Vec3(self.facing * .59, 2.03, 0)
            other_elbow, other_hand = Vec3(-self.facing * .42, 1.72, 0), Vec3(-self.facing * .5, 1.45, 0)
            arms = ((shoulder_l, elbow, fist), (shoulder_r, other_elbow, other_hand)) if self.facing < 0 else ((shoulder_l, other_elbow, other_hand), (shoulder_r, elbow, fist))
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
        self.head.color = self.torso.color = color.white if self.hit_flash > 0 else self.accent
        self.head.y = 2.47 + (.025 * math.sin(self.walk_time * 2) if self.move_amount else 0)


fighters = []
player = enemy = None
palette_choices = [0, 1]
selected_mode = "bot"
state = "menu"
round_over = False
round_timer = 0
scores = [0, 0]
ui_items = []


def clear_ui():
    for item in ui_items:
        destroy(item)
    ui_items.clear()


def ui_text(text, position, scale=1, tint=color.white, origin=(0, 0)):
    item = Text(text=text, parent=camera.ui, position=position, origin=origin, scale=scale, color=tint)
    ui_items.append(item)
    return item


def ui_button(text, position, callback, tint=color.rgb(48, 132, 210), scale=(.28, .075)):
    item = Button(text=text, parent=camera.ui, position=position, scale=scale, color=tint,
                  highlight_color=color.rgb(95, 170, 235), pressed_color=color.rgb(35, 95, 165), on_click=callback)
    ui_items.append(item)
    return item


def show_menu():
    global state
    state = "menu"
    clear_ui()
    ui_text("STICKMAN", (0, .29), 3.3, color.rgb(255, 207, 72))
    ui_text("ARENA", (0, .16), 2.6, color.white)
    ui_text("Un petit jeu de combat cartoon", (0, .06), 1.05, color.rgb(203, 213, 232))
    ui_button("JOUER", (0, -.12), show_mode, color.rgb(51, 151, 225), (.27, .085))
    ui_text("Combat inspiré des jeux de party — personnages originaux", (0, -.31), .75, color.rgb(165, 178, 204))


def show_mode():
    global state
    state = "mode"
    clear_ui()
    ui_text("CHOISIS TA PARTIE", (0, .29), 2.0, color.rgb(255, 207, 72))
    ui_text("Comment veux-tu jouer ?", (0, .16), 1.05, color.white)
    ui_button("SOLO  •  contre l'ordinateur", (0, .015), choose_bot, color.rgb(43, 139, 218), (.43, .085))
    ui_button("DUO  •  deux joueurs", (0, -.105), choose_local, color.rgb(224, 91, 112), (.43, .085))
    ui_button("RETOUR", (0, -.28), show_menu, color.rgb(79, 86, 107), (.22, .065))


def choose_bot():
    global selected_mode
    selected_mode = "bot"
    show_character_select()


def choose_local():
    global selected_mode
    selected_mode = "local"
    show_character_select()


def show_character_select():
    global state
    state = "select"
    clear_ui()
    ui_text("CHOISIS TES COMBATTANTS", (0, .32), 1.8, color.rgb(255, 207, 72))
    ui_text("Joueur 1", (-.43, .21), 1.1, PALETTES[palette_choices[0]][1])
    ui_text("Joueur 2" if selected_mode == "local" else "Adversaire", (.43, .21), 1.1, PALETTES[palette_choices[1]][1])
    ui_button("◀", (-.55, .08), lambda: change_palette(0, -1), color.rgb(60, 70, 95), (.1, .07))
    ui_button("▶", (-.31, .08), lambda: change_palette(0, 1), color.rgb(60, 70, 95), (.1, .07))
    ui_button("◀", (.31, .08), lambda: change_palette(1, -1), color.rgb(60, 70, 95), (.1, .07))
    ui_button("▶", (.55, .08), lambda: change_palette(1, 1), color.rgb(60, 70, 95), (.1, .07))
    ui_text(PALETTES[palette_choices[0]][0], (-.43, -.01), .9, PALETTES[palette_choices[0]][1])
    ui_text(PALETTES[palette_choices[1]][0], (.43, -.01), .9, PALETTES[palette_choices[1]][1])
    ui_button("COMBATTRE !", (0, -.16), start_match, color.rgb(57, 185, 121), (.31, .085))
    ui_button("RETOUR", (0, -.30), show_mode, color.rgb(79, 86, 107), (.2, .06))


def change_palette(index, direction):
    palette_choices[index] = (palette_choices[index] + direction) % len(PALETTES)
    show_character_select()


def create_fighters():
    global player, enemy, fighters
    for fighter in fighters:
        destroy(fighter.root)
    player = Fighter(-3.2, palette_choices[0], 1)
    enemy = Fighter(3.2, palette_choices[1], 2)
    fighters = [player, enemy]


def start_match():
    global state, scores, round_over, round_timer
    create_fighters()
    scores = [0, 0]
    round_over, round_timer = False, 0
    state = "battle"
    show_battle_ui()
    reset_round()


def show_battle_ui():
    clear_ui()
    ui_text("JOUEUR 1", (-.67, .43), .9, PALETTES[palette_choices[0]][1])
    ui_text("JOUEUR 2" if selected_mode == "local" else "ORDINATEUR", (.36, .43), .9, PALETTES[palette_choices[1]][1])
    ui_text("", (0, .36), 1.25, color.white)
    # Texte du score gardé accessible pour mise à jour.
    score_ui = ui_text("0     —     0", (0, .36), 1.25, color.white)
    global score_label
    score_label = score_ui
    Entity(parent=camera.ui, model="quad", position=(-.39, .31), scale=(.38, .025), color=color.rgb(60, 67, 83))
    Entity(parent=camera.ui, model="quad", position=(.39, .31), scale=(.38, .025), color=color.rgb(60, 67, 83))
    global player_bar, enemy_bar
    player_bar = Entity(parent=camera.ui, model="quad", position=(-.39, .31, -.01), scale=(.38, .018), color=color.rgb(71, 225, 133))
    enemy_bar = Entity(parent=camera.ui, model="quad", position=(.39, .31, -.01), scale=(.38, .018), color=color.rgb(255, 75, 93))
    ui_text("P1 : A/D bouger • W sauter • F frapper • G bloquer", (-.49, -.45), .66, color.rgb(218, 226, 242))
    ui_text("P2 : ←/→ bouger • ↑ sauter • / frapper • Maj droite bloquer" if selected_mode == "local" else "ESPACE : pause du combat", (.48, -.45), .66, color.rgb(218, 226, 242))
    global message_label
    message_label = ui_text("", (0, .08), 2.0, color.rgb(255, 218, 91))


def update_health_bars():
    if not player_bar or not enemy_bar:
        return
    player_bar.scale_x = .38 * max(0, player.health) / 100
    enemy_bar.scale_x = .38 * max(0, enemy.health) / 100
    player_bar.x = -.58 + player_bar.scale_x / 2
    enemy_bar.x = .20 + enemy_bar.scale_x / 2


player_bar = enemy_bar = None
score_label = message_label = None


def reset_round():
    global round_over, round_timer
    player.health = enemy.health = 100
    player.x, enemy.x = -3.2, 3.2
    player.y = enemy.y = 0
    player.velocity_y = enemy.velocity_y = 0
    player.attack_timer = enemy.attack_timer = 0
    player.attack_cooldown = enemy.attack_cooldown = 0
    player.blocking = enemy.blocking = False
    round_over, round_timer = False, 0
    message_label.text = "" if message_label else ""
    update_health_bars()


def finish_round(winner):
    global round_over, round_timer
    if round_over:
        return
    scores[winner - 1] += 1
    score_label.text = f"{scores[0]}     —     {scores[1]}"
    round_over, round_timer = True, 2.0
    message_label.text = "POINT POUR JOUEUR 1 !" if winner == 1 else ("POINT POUR JOUEUR 2 !" if selected_mode == "local" else "L'ORDINATEUR MARQUE !")
    message_label.color = PALETTES[palette_choices[winner - 1]][1]


def attack(attacker, target):
    if attacker.attack_cooldown > 0 or round_over:
        return
    attacker.attack_timer, attacker.attack_cooldown = .28, .55
    gap = abs(attacker.x - target.x)
    if gap < 2.0 and (target.x - attacker.x) * attacker.facing > 0 and target.y < 1.1:
        target.health = max(0, target.health - (4 if target.blocking else random.randint(10, 15)))
        target.hit_flash = .16
        target.x = clamp(target.x + attacker.facing * .28, -ARENA_LIMIT, ARENA_LIMIT)
        update_health_bars()
        if target.health <= 0:
            finish_round(attacker.player_number)


def handle_controls(fighter, move, jump_key, block, attack_key, dt):
    fighter.move_amount = move
    if move:
        fighter.x = clamp(fighter.x + move * 6 * dt, -ARENA_LIMIT, ARENA_LIMIT)
        fighter.facing = 1 if move > 0 else -1
    fighter.blocking = bool(block)
    if jump_key and fighter.y <= .01:
        fighter.velocity_y = 8.5
    if attack_key:
        attack(fighter, enemy if fighter is player else player)


def input(key):
    if key == "escape":
        if state == "battle":
            show_menu()
        else:
            application.quit()
    if state != "battle" or round_over:
        return
    if key in ("f",):
        attack(player, enemy)
    if selected_mode == "local" and key in ("/", "slash"):
        attack(enemy, player)
    if key == "w" and player.y <= .01:
        player.velocity_y = 8.5
    if selected_mode == "local" and key == "up arrow" and enemy.y <= .01:
        enemy.velocity_y = 8.5


def update():
    global round_timer
    dt = time.dt
    if state == "battle" and round_over:
        round_timer -= dt
        if round_timer <= 0:
            reset_round()
        return

    if state == "battle":
        p1_move = held_keys["d"] + held_keys["right arrow"] - held_keys["a"] - held_keys["left arrow"]
        player.move_amount = p1_move
        if p1_move:
            player.x = clamp(player.x + p1_move * 6 * dt, -ARENA_LIMIT, ARENA_LIMIT)
            player.facing = 1 if p1_move > 0 else -1
        player.blocking = bool(held_keys["g"])

        if selected_mode == "local":
            p2_move = held_keys["right arrow"] - held_keys["left arrow"]
            enemy.move_amount = p2_move
            if p2_move:
                enemy.x = clamp(enemy.x + p2_move * 6 * dt, -ARENA_LIMIT, ARENA_LIMIT)
                enemy.facing = 1 if p2_move > 0 else -1
            enemy.blocking = bool(held_keys["right shift"])
        else:
            distance = abs(player.x - enemy.x)
            enemy.facing = -1 if enemy.x > player.x else 1
            enemy.move_amount = 0
            if distance > 1.55:
                enemy.move_amount = 1
                enemy.x += enemy.facing * 2.3 * dt
            elif enemy.attack_cooldown <= 0:
                attack(enemy, player)

        for fighter in fighters:
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
    else:
        # Animation douce des personnages de présentation dans les menus.
        for fighter in fighters:
            fighter.update_pose(dt)


create_fighters()
show_menu()
app.run()

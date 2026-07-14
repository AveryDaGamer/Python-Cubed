# game.py
import pygame
import random

# --- arena (1.25x the original 800x600) ---
SCREEN_W = 1000
SCREEN_H = 750
GROUND_Y = 562       # y-coordinate of the floor line
P1_START_X = 250
P2_START_X = 750

ROUNDS_TO_WIN = 2    # best of 3
KO_FREEZE = 120      # frames the "K.O." message stays up before the next round (2s)
COUNTDOWN_FRAMES = 180  # 3... 2... 1... before each round (3s)
FIGHT_FLASH = 45     # frames "FIGHT!" stays on screen once the round starts

BODY_WIDTH = 170
STAND_HEIGHT = 270
CROUCH_HEIGHT = 140  # short enough that a standing punch whiffs over your head

# --- attack numbers ---
LIGHT_DAMAGE = 10    # fast poke
HEAVY_DAMAGE = 22    # slow but big, and its hitbox reaches low enough to catch crouchers
SPECIAL_DAMAGE = 25  # the projectile
BLOCK_DIVISOR = 5    # blocked hits deal 1/5 damage ("chip" damage)

# --- dodge numbers ---
DODGE_FRAMES = 14    # you are invincible for this many frames
DODGE_SPEED = 12     # pixels per frame while dodging
DODGE_COOLDOWN = 50  # frames before you can dodge again

# --- special meter ---
METER_MAX = 100      # special fires only on a full bar (and empties it)
METER_ON_HIT = 15    # gained for landing a hit
METER_ON_HURT = 10   # gained for taking a hit
METER_ON_BLOCK = 5   # both sides gain a little when a hit is blocked

# --- CPU difficulty levels ---
# reaction:    frames between decisions (lower = faster thinker)
# defend:      chance to react when the opponent swings
# proj_defend: chance to react to an incoming fireball
# attack:      chance to attack when in range
# heavy_mix:   how often an attack is the heavy instead of the jab
# special:     chance to spend a full meter at range
# dash_in:     chance to dodge-dash toward a far opponent to close distance
# punish:      chance to strike while the opponent is stuck in attack cooldown
# idle:        chance to hesitate and do nothing
# jump:        chance of a random hop
AI_LEVELS = {
    'easy': {
        'reaction': 24, 'defend': 0.25, 'proj_defend': 0.35, 'attack': 0.5,
        'heavy_mix': 0.25, 'special': 0.35, 'dash_in': 0.0, 'punish': 0.1,
        'idle': 0.25, 'jump': 0.12,
    },
    'medium': {
        'reaction': 15, 'defend': 0.55, 'proj_defend': 0.7, 'attack': 0.7,
        'heavy_mix': 0.35, 'special': 0.6, 'dash_in': 0.12, 'punish': 0.45,
        'idle': 0.08, 'jump': 0.06,
    },
    'hard': {
        'reaction': 8, 'defend': 0.85, 'proj_defend': 0.92, 'attack': 0.9,
        'heavy_mix': 0.4, 'special': 0.9, 'dash_in': 0.3, 'punish': 0.9,
        'idle': 0.0, 'jump': 0.03,
    },
}


class Projectile(pygame.sprite.Sprite):
    """The special attack: an energy ball that flies across the screen."""
    SPEED = 9

    def __init__(self, owner, x, y, direction):
        super().__init__()
        self.owner = owner
        self.direction = direction
        self.evaded = False  # so a dodged ball only counts once in the stats
        self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (80, 255, 120), (20, 20), 20)
        pygame.draw.circle(self.image, (255, 255, 255), (20, 20), 20, 3)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.rect.x += self.SPEED * self.direction
        if self.rect.right < 0 or self.rect.left > SCREEN_W:
            self.kill()


class Player(pygame.sprite.Sprite):
    def __init__(self, x, color, controls):
        super().__init__()
        self.is_ai = False
        self.target = None          # the opponent, set for AI players
        self.projectile_group = None  # set in run_game so the AI can see fireballs
        self.ai_params = AI_LEVELS['medium']
        self.ai_decision_timer = 0
        self.ai_move = 0            # -1 left, 0 stand, 1 right
        self.ai_wants_punch = False
        self.ai_wants_heavy = False
        self.ai_wants_special = False
        self.ai_wants_block = False
        self.ai_wants_crouch = False
        self.ai_wants_dodge = False
        self.ai_wants_jump = False
        self.color = color
        self.image = pygame.Surface((BODY_WIDTH, STAND_HEIGHT))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.midbottom = (x, GROUND_Y)
        self.speed = 5
        self.vel_y = 0
        self.on_ground = True
        self.controls = controls
        self.max_health = 100
        self.health = 100
        self.facing = 1          # 1 = facing right, -1 = facing left
        self.attacking = 0       # frames remaining in the current attack
        self.attack_cooldown = 0 # frames until you can attack again
        self.attack_cooldown_max = 25  # length of the current cooldown, for the HUD bar
        self.attack_type = 'light'
        self.attack_damage = LIGHT_DAMAGE
        self.has_hit = False     # whether this attack already landed
        self.crouching = False
        self.blocking = False
        self.dodging = 0         # frames remaining in the current dodge (invincible)
        self.dodge_cooldown = 0
        self.dodge_dir = 1
        self.meter = 0           # special meter, 0..METER_MAX
        self.fire_special = False  # flag picked up by the main loop to spawn the ball
        # remember last frame's buttons so dodge/special fire once per press
        self.prev_dodge = False
        self.prev_special = False
        self.evade_counted = True  # so a dodged swing only counts once in the stats
        # match-long stats for the victory screen (NOT reset between rounds)
        self.stats = {
            'light': 0,    # light attacks thrown
            'heavy': 0,    # heavy attacks thrown
            'special': 0,  # specials fired
            'hits': 0,     # attacks that landed clean
            'damage': 0,   # total damage dealt (including chip)
            'blocked': 0,  # incoming hits this player blocked
            'dodged': 0,   # incoming attacks this player dodged with i-frames
        }

    def reset(self, x):
        """Put the fighter back to its starting state for a new round."""
        self.rect.size = (BODY_WIDTH, STAND_HEIGHT)
        self.rect.midbottom = (x, GROUND_Y)
        self.health = self.max_health
        self.vel_y = 0
        self.on_ground = True
        self.attacking = 0
        self.attack_cooldown = 0
        self.has_hit = False
        self.crouching = False
        self.blocking = False
        self.dodging = 0
        self.dodge_cooldown = 0
        self.meter = 0
        self.fire_special = False
        self.prev_dodge = False
        self.prev_special = False
        self.ai_decision_timer = 0
        self.ai_move = 0
        self.ai_wants_punch = False
        self.ai_wants_heavy = False
        self.ai_wants_special = False
        self.ai_wants_block = False
        self.ai_wants_crouch = False
        self.ai_wants_dodge = False
        self.ai_wants_jump = False
        self.update_image()

    def get_human_inputs(self):
        keys = pygame.key.get_pressed()
        return {name: keys[key] for name, key in self.controls.items()}

    def get_ai_inputs(self):
        p = self.ai_params
        # only re-decide every few frames = the CPU's "reaction time"
        self.ai_decision_timer -= 1
        if self.ai_decision_timer <= 0:
            self.ai_decision_timer = p['reaction']
            self.ai_move = 0
            self.ai_wants_punch = False
            self.ai_wants_heavy = False
            self.ai_wants_special = False
            self.ai_wants_block = False
            self.ai_wants_crouch = False
            self.ai_wants_dodge = False

            distance = self.target.rect.centerx - self.rect.centerx
            gap = abs(distance)
            toward = 1 if distance > 0 else -1
            # center-to-center: bodies are 170 wide, so touching == 170 apart,
            # and the fist reaches out to about 250. 220 sits between the two.
            punch_range = 220

            # is a fireball flying toward us?
            threat_ball = None
            if self.projectile_group:
                for proj in self.projectile_group:
                    if proj.owner is self:
                        continue
                    g = self.rect.centerx - proj.rect.centerx
                    approaching = (g > 0) == (proj.direction > 0)
                    if approaching and abs(g) < 300:
                        threat_ball = proj
                        break

            if threat_ball and random.random() < p['proj_defend']:
                # a high ball can be ducked; a low one must be rolled through or blocked
                ball_is_high = threat_ball.rect.bottom <= GROUND_Y - CROUCH_HEIGHT
                if ball_is_high and random.random() < 0.6:
                    self.ai_wants_crouch = True
                elif self.dodge_cooldown == 0 and random.random() < 0.5:
                    self.ai_wants_dodge = True
                else:
                    self.ai_wants_block = True
            elif self.target.attacking > 0 and gap < 320 and random.random() < p['defend']:
                # the opponent is mid-swing: pick the right defense
                if (self.target.attack_type == 'light' and not self.target.crouching
                        and random.random() < 0.5):
                    self.ai_wants_crouch = True   # slip under the high jab
                elif self.dodge_cooldown == 0 and random.random() < 0.4:
                    self.ai_wants_dodge = True    # roll through with i-frames
                else:
                    self.ai_wants_block = True    # eat chip instead of the full hit
            elif not self.target.on_ground and gap < 260 and random.random() < p['attack']:
                self.ai_wants_heavy = True        # anti-air: swat jumpers with the big one
            elif (self.target.attack_cooldown > 12 and gap <= punch_range
                    and random.random() < p['punish']):
                # they just swung and are stuck in cooldown: free hit
                if random.random() < 0.6:
                    self.ai_wants_heavy = True
                else:
                    self.ai_wants_punch = True
            elif self.meter >= METER_MAX and gap > 280 and random.random() < p['special']:
                self.ai_wants_special = True      # full bar and out of reach: fireball
            elif gap > punch_range:
                if random.random() < p['idle']:
                    pass                          # hesitate (mostly the easy CPU)
                elif (gap > 320 and self.dodge_cooldown == 0
                        and random.random() < p['dash_in']):
                    self.ai_move = toward         # held direction steers the dodge...
                    self.ai_wants_dodge = True    # ...into a quick dash toward you
                else:
                    self.ai_move = toward
            else:
                # in range: mix up lights and heavies, sometimes guard or back off
                roll = random.random()
                if roll < p['attack']:
                    if random.random() < p['heavy_mix']:
                        self.ai_wants_heavy = True
                    else:
                        self.ai_wants_punch = True
                elif roll < p['attack'] + 0.15:
                    self.ai_wants_block = True
                else:
                    self.ai_move = -toward        # retreat
            # occasional random hop to stay unpredictable
            self.ai_wants_jump = random.random() < p['jump']

        return {
            'left': self.ai_move == -1,
            'right': self.ai_move == 1,
            'jump': self.ai_wants_jump,
            'crouch': self.ai_wants_crouch,
            'punch': self.ai_wants_punch,
            'heavy': self.ai_wants_heavy,
            'special': self.ai_wants_special,
            'block': self.ai_wants_block,
            'dodge': self.ai_wants_dodge,
        }

    def start_attack(self, kind):
        if kind == 'heavy':
            self.attacking = 14       # heavy is "out" longer...
            self.attack_cooldown = 50 # ...and locks you out longer
            self.attack_damage = HEAVY_DAMAGE
        else:
            self.attacking = 10
            self.attack_cooldown = 25
            self.attack_damage = LIGHT_DAMAGE
        self.attack_cooldown_max = self.attack_cooldown
        self.attack_type = kind
        self.has_hit = False
        self.evade_counted = False
        self.stats[kind] += 1

    def update(self):
        inputs = self.get_ai_inputs() if self.is_ai else self.get_human_inputs()

        # dodge and special only trigger on a fresh press, not while held
        dodge_pressed = inputs['dodge'] and not self.prev_dodge
        special_pressed = inputs['special'] and not self.prev_special
        self.prev_dodge = inputs['dodge']
        self.prev_special = inputs['special']

        if self.attacking > 0:
            self.attacking -= 1
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.dodge_cooldown > 0:
            self.dodge_cooldown -= 1

        if self.dodging > 0:
            # mid-dodge: committed to the roll, invincible, no other actions
            self.dodging -= 1
            self.rect.x += self.dodge_dir * DODGE_SPEED
            self.crouching = False
            self.blocking = False
        else:
            self.crouching = inputs['crouch'] and self.on_ground
            self.blocking = inputs['block'] and self.on_ground and self.attacking == 0

            # walking and jumping only while standing free (not crouched/blocking)
            if not self.crouching and not self.blocking:
                if inputs['left']:
                    self.rect.x -= self.speed
                if inputs['right']:
                    self.rect.x += self.speed
                if inputs['jump'] and self.on_ground:
                    self.vel_y = -15
                    self.on_ground = False

            # dodge: a quick dash with invincibility frames (ground only)
            if dodge_pressed and self.on_ground and self.dodge_cooldown == 0 and self.attacking == 0:
                self.dodging = DODGE_FRAMES
                self.dodge_cooldown = DODGE_COOLDOWN
                if inputs['left']:
                    self.dodge_dir = -1
                elif inputs['right']:
                    self.dodge_dir = 1
                else:
                    self.dodge_dir = -self.facing  # no direction held: hop away
                self.crouching = False
                self.blocking = False
                self.rect.x += self.dodge_dir * DODGE_SPEED  # dash starts this frame

            # attacks (crouching attacks come out low; you can't attack while blocking)
            if not self.blocking and self.attack_cooldown == 0:
                if inputs['punch']:
                    self.start_attack('light')
                elif inputs['heavy']:
                    self.start_attack('heavy')
                elif special_pressed and self.meter >= METER_MAX:
                    self.meter = 0
                    self.fire_special = True  # main loop spawns the projectile
                    self.stats['special'] += 1

        self.vel_y += 0.8
        self.rect.y += self.vel_y

        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.vel_y = 0
            self.on_ground = True

        # shrink / grow the body when crouch state changes, keeping feet planted
        target_h = CROUCH_HEIGHT if self.crouching else STAND_HEIGHT
        if self.rect.height != target_h:
            feet = self.rect.midbottom
            self.rect.size = (BODY_WIDTH, target_h)
            self.rect.midbottom = feet

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_W:
            self.rect.right = SCREEN_W

        self.update_image()

    def update_image(self):
        """Rebuild the body surface so crouch / block / dodge are visible."""
        self.image = pygame.Surface(self.rect.size)
        self.image.fill(self.color)
        if self.blocking:
            # white shield strip on the side facing the opponent
            x = self.rect.width - 12 if self.facing == 1 else 0
            pygame.draw.rect(self.image, (255, 255, 255), (x, 0, 12, self.rect.height))
        # ghost while dodging = the invincibility frames
        self.image.set_alpha(110 if self.dodging > 0 else 255)

    def get_hitbox(self):
        if self.attacking <= 0:
            return None
        if self.attack_type == 'heavy':
            # big and tall: reaches low enough to catch a crouching opponent
            w, h = 100, 120
            y = self.rect.top + 60
        else:
            # quick jab at head height: a crouching opponent slips under it
            w, h = 80, 40
            y = self.rect.top + 90
        if self.facing == 1:
            return pygame.Rect(self.rect.right, y, w, h)
        else:
            return pygame.Rect(self.rect.left - w, y, w, h)


def apply_hit(attacker, defender, damage):
    """Deal damage, respecting dodges and blocks.
    Returns True if the attack made contact (clean hit OR blocked)."""
    if defender.dodging > 0:
        return False  # invincibility frames: the attack whiffs right through

    if defender.blocking:
        chip = max(1, damage // BLOCK_DIVISOR)
        attacker.stats['damage'] += min(chip, defender.health)
        defender.stats['blocked'] += 1
        defender.health = max(0, defender.health - chip)
        defender.meter = min(METER_MAX, defender.meter + METER_ON_BLOCK)
        attacker.meter = min(METER_MAX, attacker.meter + METER_ON_BLOCK)
        # shove the blocker back a step
        push = 14 if defender.rect.centerx >= attacker.rect.centerx else -14
        defender.rect.x += push
        if defender.rect.left < 0:
            defender.rect.left = 0
        if defender.rect.right > SCREEN_W:
            defender.rect.right = SCREEN_W
    else:
        attacker.stats['damage'] += min(damage, defender.health)
        attacker.stats['hits'] += 1
        defender.health = max(0, defender.health - damage)
        defender.meter = min(METER_MAX, defender.meter + METER_ON_HURT)
        attacker.meter = min(METER_MAX, attacker.meter + METER_ON_HIT)
    return True


def resolve_player_collision(p1, p2):
    if not p1.rect.colliderect(p2.rect):
        return

    if p1.rect.centerx < p2.rect.centerx:
        overlap = p1.rect.right - p2.rect.left
        p1.rect.x -= overlap // 2
        p2.rect.x += overlap - overlap // 2
    else:
        overlap = p2.rect.right - p1.rect.left
        p2.rect.x -= overlap // 2
        p1.rect.x += overlap - overlap // 2

    for p in (p1, p2):
        if p.rect.left < 0:
            p.rect.left = 0
        if p.rect.right > SCREEN_W:
            p.rect.right = SCREEN_W


def draw_skill_bar(surface, skill_font, x, y, w, h, label, ratio, from_right):
    """One cooldown pill: fills back up as the skill recovers, green when ready."""
    ready = ratio >= 1
    pygame.draw.rect(surface, (35, 35, 50), (x, y, w, h))
    fill = int(w * min(ratio, 1))
    color = (90, 200, 110) if ready else (105, 105, 130)
    fill_x = x + w - fill if from_right else x
    pygame.draw.rect(surface, color, (fill_x, y, fill, h))
    pygame.draw.rect(surface, (255, 255, 255), (x, y, w, h), 1)
    text = skill_font.render(label, True, (255, 255, 255))
    surface.blit(text, text.get_rect(center=(x + w // 2, y + h // 2)))


def draw_hud(surface, p1, p2, score, font, skill_font):
    BAR_WIDTH = 300
    BAR_HEIGHT = 25
    METER_HEIGHT = 12
    MARGIN = 20
    Y = 20
    METER_Y = Y + BAR_HEIGHT + 6

    # Player 1 bar (drains toward the left)
    p1_ratio = max(p1.health, 0) / p1.max_health
    pygame.draw.rect(surface, (150, 30, 30), (MARGIN, Y, BAR_WIDTH, BAR_HEIGHT))
    p1_fill = int(BAR_WIDTH * p1_ratio)
    pygame.draw.rect(surface, (230, 200, 50),
                     (MARGIN + BAR_WIDTH - p1_fill, Y, p1_fill, BAR_HEIGHT))
    pygame.draw.rect(surface, (255, 255, 255), (MARGIN, Y, BAR_WIDTH, BAR_HEIGHT), 2)

    # Player 2 bar (mirrored, drains toward the right)
    p2_ratio = max(p2.health, 0) / p2.max_health
    p2_x = SCREEN_W - MARGIN - BAR_WIDTH
    pygame.draw.rect(surface, (150, 30, 30), (p2_x, Y, BAR_WIDTH, BAR_HEIGHT))
    p2_fill = int(BAR_WIDTH * p2_ratio)
    pygame.draw.rect(surface, (230, 200, 50), (p2_x, Y, p2_fill, BAR_HEIGHT))
    pygame.draw.rect(surface, (255, 255, 255), (p2_x, Y, BAR_WIDTH, BAR_HEIGHT), 2)

    # Special meters under the health bars (gold when full = special ready)
    for x, player, from_right in ((MARGIN, p1, False), (p2_x, p2, True)):
        ratio = player.meter / METER_MAX
        fill = int(BAR_WIDTH * ratio)
        color = (230, 200, 50) if player.meter >= METER_MAX else (80, 160, 255)
        pygame.draw.rect(surface, (40, 40, 60), (x, METER_Y, BAR_WIDTH, METER_HEIGHT))
        fill_x = x + BAR_WIDTH - fill if from_right else x
        pygame.draw.rect(surface, color, (fill_x, METER_Y, fill, METER_HEIGHT))
        pygame.draw.rect(surface, (255, 255, 255), (x, METER_Y, BAR_WIDTH, METER_HEIGHT), 1)

    # Cooldown bars: attack + dodge readiness (mirrored so ATTACK sits outermost)
    COOL_Y = METER_Y + METER_HEIGHT + 6
    COOL_H = 18
    COOL_W = 145  # two bars + 10px gap == BAR_WIDTH, lining up with the bars above
    for x0, player, from_right in ((MARGIN, p1, False), (p2_x, p2, True)):
        atk = 1.0 if player.attack_cooldown == 0 else \
            1 - player.attack_cooldown / player.attack_cooldown_max
        dodge = 1.0 if player.dodge_cooldown == 0 else \
            1 - player.dodge_cooldown / DODGE_COOLDOWN
        bars = [("ATTACK", atk), ("DODGE", dodge)]
        if from_right:
            bars.reverse()
        for i, (label, ratio) in enumerate(bars):
            draw_skill_bar(surface, skill_font, x0 + i * (COOL_W + 10), COOL_Y,
                           COOL_W, COOL_H, label, ratio, from_right)

    # Score in the middle
    score_text = font.render(f"{score[0]} - {score[1]}", True, (255, 255, 255))
    score_rect = score_text.get_rect(center=(SCREEN_W // 2, Y + BAR_HEIGHT // 2))
    surface.blit(score_text, score_rect)


def draw_banner(surface, big_font, small_font, main_text, sub_text=""):
    """Big centred message (K.O., winner, countdown) with an optional line underneath."""
    text = big_font.render(main_text, True, (230, 200, 50))
    rect = text.get_rect(center=(SCREEN_W // 2, 275))

    # dark strip behind the text so it stays readable over the fighters
    strip = pygame.Rect(0, rect.top - 20, SCREEN_W, rect.height + 40)
    shade = pygame.Surface((strip.width, strip.height))
    shade.set_alpha(180)
    shade.fill((0, 0, 0))
    surface.blit(shade, strip.topleft)

    surface.blit(text, rect)
    if sub_text:
        sub = small_font.render(sub_text, True, (255, 255, 255))
        surface.blit(sub, sub.get_rect(center=(SCREEN_W // 2, rect.bottom + 40)))


def draw_stone_button(surface, text, rect, mouse_pos, font):
    """Sandstone-block button matching the desert theme (shared with the menu)."""
    hovered = rect.collidepoint(mouse_pos)
    base = (172, 120, 78) if hovered else (128, 88, 58)   # sun-lit vs shaded stone
    pygame.draw.rect(surface, base, rect, border_radius=10)
    if hovered:
        # warm inner glow, like sunlight catching the block
        pygame.draw.rect(surface, (235, 195, 140), rect.inflate(-8, -8), 2, border_radius=8)
    pygame.draw.rect(surface, (62, 40, 28), rect, 3, border_radius=10)  # dark mortar edge
    label = font.render(text, True, (255, 238, 205))
    surface.blit(label, label.get_rect(center=rect.center))


def draw_pause_menu(surface, big_font, font, resume_btn, quit_btn, mouse_pos):
    shade = pygame.Surface((SCREEN_W, SCREEN_H))
    shade.set_alpha(170)
    shade.fill((20, 12, 8))
    surface.blit(shade, (0, 0))
    title = big_font.render("PAUSED", True, (230, 200, 50))
    surface.blit(title, title.get_rect(center=(SCREEN_W // 2, 210)))
    hint = font.render("ESC also resumes the fight", True, (255, 238, 205))
    surface.blit(hint, hint.get_rect(center=(SCREEN_W // 2, 550)))
    draw_stone_button(surface, "Resume", resume_btn, mouse_pos, font)
    draw_stone_button(surface, "Quit Match", quit_btn, mouse_pos, font)


def draw_victory_screen(surface, big_font, font, stat_font,
                        winner_name, score, p1, p2, p1_name, p2_name):
    """End-of-match screen: who won plus the full stat sheet for both fighters."""
    shade = pygame.Surface((SCREEN_W, SCREEN_H))
    shade.set_alpha(215)
    shade.fill((20, 12, 8))
    surface.blit(shade, (0, 0))

    title = big_font.render(f"{winner_name} WINS!", True, (230, 200, 50))
    surface.blit(title, title.get_rect(center=(SCREEN_W // 2, 110)))
    final = font.render(f"Final score   {score[0]} - {score[1]}", True, (255, 238, 205))
    surface.blit(final, final.get_rect(center=(SCREEN_W // 2, 185)))

    # column headers, tinted to match each fighter
    head1 = font.render(p1_name, True, (100, 160, 255))
    head2 = font.render(p2_name, True, (255, 100, 100))
    surface.blit(head1, head1.get_rect(center=(SCREEN_W // 2 - 260, 255)))
    surface.blit(head2, head2.get_rect(center=(SCREEN_W // 2 + 260, 255)))

    rows = [
        ("Light attacks thrown", 'light'),
        ("Heavy attacks thrown", 'heavy'),
        ("Specials fired", 'special'),
        ("Hits landed", 'hits'),
        ("Damage dealt", 'damage'),
        ("Attacks blocked", 'blocked'),
        ("Attacks dodged", 'dodged'),
    ]
    for i, (label, key) in enumerate(rows):
        y = 315 + i * 44
        lab = stat_font.render(label, True, (230, 200, 50))
        v1 = stat_font.render(str(p1.stats[key]), True, (255, 238, 205))
        v2 = stat_font.render(str(p2.stats[key]), True, (255, 238, 205))
        surface.blit(lab, lab.get_rect(center=(SCREEN_W // 2, y)))
        surface.blit(v1, v1.get_rect(center=(SCREEN_W // 2 - 260, y)))
        surface.blit(v2, v2.get_rect(center=(SCREEN_W // 2 + 260, y)))

    footer = font.render("Press any key to return to the menu", True, (255, 238, 205))
    surface.blit(footer, footer.get_rect(center=(SCREEN_W // 2, SCREEN_H - 55)))


def run_game(screen, mode="multi", difficulty="medium"):
    font = pygame.font.Font(None, 48)
    big_font = pygame.font.Font(None, 120)
    skill_font = pygame.font.Font(None, 20)
    stat_font = pygame.font.Font(None, 34)
    score = [0, 0]

    resume_btn = pygame.Rect(SCREEN_W // 2 - 150, 310, 300, 60)
    quit_btn = pygame.Rect(SCREEN_W // 2 - 150, 400, 300, 60)

    # what each fighter is called in the K.O. / winner messages
    p1_name = "PLAYER 1"
    p2_name = f"CPU ({difficulty.upper()})" if mode == "single" else "PLAYER 2"

    p1_controls = {
        'left': pygame.K_a, 'right': pygame.K_d, 'jump': pygame.K_w, 'crouch': pygame.K_s,
        'punch': pygame.K_q, 'heavy': pygame.K_e, 'special': pygame.K_r,
        'block': pygame.K_f, 'dodge': pygame.K_LSHIFT,
    }
    p2_controls = {
        'left': pygame.K_j, 'right': pygame.K_l, 'jump': pygame.K_i, 'crouch': pygame.K_k,
        'punch': pygame.K_u, 'heavy': pygame.K_o, 'special': pygame.K_p,
        'block': pygame.K_SEMICOLON, 'dodge': pygame.K_RSHIFT,
    }

    player1 = Player(P1_START_X, (0, 100, 255), p1_controls)
    player2 = Player(P2_START_X, (255, 60, 60), p2_controls)

    projectiles = pygame.sprite.Group()
    player1.projectile_group = projectiles
    player2.projectile_group = projectiles

    if mode == "single":
        player2.is_ai = True
        player2.target = player1
        player2.ai_params = AI_LEVELS[difficulty]

    all_sprites = pygame.sprite.Group()
    all_sprites.add(player1, player2)

    clock = pygame.time.Clock()

    # "countdown" -> "fighting" -> "ko" -> next round countdown, or -> "match_over";
    # ESC drops into "paused" from any of the action states and back out again
    state = "countdown"
    prev_state = "countdown"  # what to resume into when unpausing
    countdown_timer = COUNTDOWN_FRAMES
    fight_flash = 0      # frames left of the "FIGHT!" flash
    ko_timer = 0         # frames left in the K.O. freeze
    banner = ""          # big message shown during "ko"
    banner_sub = ""
    winner_name = ""

    while True:  # Main Loop
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if state == "paused":
                        state = prev_state       # resume the fight
                    elif state == "match_over":
                        return "menu"
                    else:
                        prev_state = state       # freeze everything
                        state = "paused"
                elif state == "match_over":
                    return "menu"  # any key after the match ends
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state == "paused":
                    if resume_btn.collidepoint(mouse_pos):
                        state = prev_state
                    elif quit_btn.collidepoint(mouse_pos):
                        return "menu"
                elif state == "match_over":
                    return "menu"

        if state == "countdown":
            # fighters stand frozen while the numbers tick down
            countdown_timer -= 1
            if countdown_timer <= 0:
                state = "fighting"
                fight_flash = FIGHT_FLASH

        elif state == "fighting":
            if fight_flash > 0:
                fight_flash -= 1
            all_sprites.update()

            # spawn any specials that were triggered this frame
            for p in (player1, player2):
                if p.fire_special:
                    p.fire_special = False
                    x = p.rect.centerx + p.facing * (p.rect.width // 2 + 24)
                    y = p.rect.top + 110  # chest height: crouchers can duck a standing fireball
                    projectiles.add(Projectile(p, x, y, p.facing))
            projectiles.update()

            # dodging players roll straight through the opponent
            if player1.dodging <= 0 and player2.dodging <= 0:
                resolve_player_collision(player1, player2)

            # players always face each other
            player1.facing = 1 if player2.rect.centerx >= player1.rect.centerx else -1
            player2.facing = 1 if player1.rect.centerx >= player2.rect.centerx else -1

            # melee hit detection
            for attacker, defender in ((player1, player2), (player2, player1)):
                hitbox = attacker.get_hitbox()
                if hitbox and not attacker.has_hit and hitbox.colliderect(defender.rect):
                    if apply_hit(attacker, defender, attacker.attack_damage):
                        attacker.has_hit = True
                    elif not attacker.evade_counted:
                        # the swing passed through i-frames: one dodge on the stat sheet
                        defender.stats['dodged'] += 1
                        attacker.evade_counted = True

            # projectile hit detection
            for proj in projectiles:
                defender = player2 if proj.owner is player1 else player1
                if proj.rect.colliderect(defender.rect):
                    if apply_hit(proj.owner, defender, SPECIAL_DAMAGE):
                        proj.kill()  # dodged balls fly right through instead
                    elif not proj.evaded:
                        defender.stats['dodged'] += 1
                        proj.evaded = True

            # --- K.O. check: did anyone run out of health this frame? ---
            p1_down = player1.health <= 0
            p2_down = player2.health <= 0
            if p1_down or p2_down:
                if p1_down and p2_down:
                    # both dropped on the same frame: nobody scores
                    banner, banner_sub = "DOUBLE K.O.", "No point awarded"
                elif p2_down:
                    score[0] += 1
                    banner, banner_sub = "K.O.", f"{p1_name} wins the round"
                else:
                    score[1] += 1
                    banner, banner_sub = "K.O.", f"{p2_name} wins the round"
                state = "ko"
                ko_timer = KO_FREEZE

        elif state == "ko":
            ko_timer -= 1
            if ko_timer <= 0:
                if score[0] >= ROUNDS_TO_WIN or score[1] >= ROUNDS_TO_WIN:
                    winner_name = p1_name if score[0] > score[1] else p2_name
                    state = "match_over"
                else:
                    player1.reset(P1_START_X)
                    player2.reset(P2_START_X)
                    projectiles.empty()
                    state = "countdown"
                    countdown_timer = COUNTDOWN_FRAMES

        # --- drawing ---
        screen.fill((30, 30, 30))
        pygame.draw.rect(screen, (60, 45, 30), (0, GROUND_Y, SCREEN_W, SCREEN_H - GROUND_Y))
        pygame.draw.line(screen, (200, 200, 200), (0, GROUND_Y), (SCREEN_W, GROUND_Y), 3)
        all_sprites.draw(screen)
        projectiles.draw(screen)

        # draw attack hitboxes (white fists, orange heavies)
        for p in (player1, player2):
            hb = p.get_hitbox()
            if hb:
                color = (255, 160, 40) if p.attack_type == 'heavy' else (255, 255, 255)
                pygame.draw.rect(screen, color, hb)

        draw_hud(screen, player1, player2, score, font, skill_font)
        if state == "ko":
            draw_banner(screen, big_font, font, banner, banner_sub)
        elif state == "match_over":
            draw_victory_screen(screen, big_font, font, stat_font, winner_name,
                                score, player1, player2, p1_name, p2_name)
        elif state == "paused":
            draw_pause_menu(screen, big_font, font, resume_btn, quit_btn, mouse_pos)
        elif state == "countdown":
            number = countdown_timer // 60 + 1  # 3, 2, 1
            round_number = score[0] + score[1] + 1
            draw_banner(screen, big_font, font, str(number), f"Round {round_number}")
        elif fight_flash > 0:
            # quick "FIGHT!" flash right as the round starts (no dark strip:
            # the fighters are already moving underneath)
            text = big_font.render("FIGHT!", True, (230, 200, 50))
            screen.blit(text, text.get_rect(center=(SCREEN_W // 2, 275)))

        pygame.display.update()
        clock.tick(60)

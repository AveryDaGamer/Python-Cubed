import pygame
pygame.init()

font = pygame.font.Font(None, 48)
score = [0, 0]  # rounds won: [player1, player2]
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("My First Pygame")
GROUND_Y = 450  # y-coordinate of the floor line (150px above the bottom of a 600px window)

class Player(pygame.sprite.Sprite):
    def __init__(self, x, color, controls):
        super().__init__()
        self.image = pygame.Surface((170, 270))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.midbottom = (x, GROUND_Y)
        self.speed = 5
        self.vel_y = 0
        self.on_ground = True
        self.controls = controls  # dict: {'left': key, 'right': key, 'jump': key}
        self.max_health = 100
        self.health = 100
        self.facing = 1          # 1 = facing right, -1 = facing left
        self.attacking = 0       # frames remaining in the current punch
        self.attack_cooldown = 0 # frames until you can punch again
        self.has_hit = False     # whether this punch already landed
    def update(self):
        keys = pygame.key.get_pressed()
        if keys[self.controls['left']]:
            self.rect.x -= self.speed
        if keys[self.controls['right']]:
            self.rect.x += self.speed
    
        if keys[self.controls['jump']] and self.on_ground:
            self.vel_y = -15
            self.on_ground = False
        # count down attack timers
        if self.attacking > 0:
            self.attacking -= 1
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        # start a punch
        if keys[self.controls['punch']] and self.attack_cooldown == 0:
            self.attacking = 10       # punch is "out" for 10 frames
            self.attack_cooldown = 25 # can't punch again for 25 frames total
            self.has_hit = False
        self.vel_y += 0.8
        self.rect.y += self.vel_y

        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.vel_y = 0
            self.on_ground = True

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > 800:
            self.rect.right = 800
    def get_hitbox(self):
            if self.attacking <= 0:
                return None
            w, h = 80, 40   # sized for your 170x270 players
            if self.facing == 1:
                return pygame.Rect(self.rect.right, self.rect.top + 90, w, h)
            else:
                return pygame.Rect(self.rect.left - w, self.rect.top + 90, w, h)
p1_controls = {'left': pygame.K_a, 'right': pygame.K_d, 'jump': pygame.K_w, 'punch': pygame.K_q}
p2_controls = {'left': pygame.K_j, 'right': pygame.K_l, 'jump': pygame.K_i, 'punch': pygame.K_u}

player1 = Player(200, (0, 100, 255), p1_controls)   # blue, starts left
player2 = Player(600, (255, 60, 60), p2_controls)   # red, starts right

all_sprites = pygame.sprite.Group()
all_sprites.add(player1, player2)



clock = pygame.time.Clock()
def resolve_player_collision(p1, p2):
    if not p1.rect.colliderect(p2.rect):
        return

    # how much they overlap horizontally
    if p1.rect.centerx < p2.rect.centerx:
        overlap = p1.rect.right - p2.rect.left
        p1.rect.x -= overlap // 2
        p2.rect.x += overlap - overlap // 2
    else:
        overlap = p2.rect.right - p1.rect.left
        p2.rect.x -= overlap // 2
        p1.rect.x += overlap - overlap // 2

    # don't let the pushback shove anyone off-screen
    for p in (p1, p2):
        if p.rect.left < 0:
            p.rect.left = 0
        if p.rect.right > 800:
            p.rect.right = 800

def draw_hud(surface, p1, p2, score):
    BAR_WIDTH = 300
    BAR_HEIGHT = 25
    MARGIN = 20
    Y = 20

    # --- Player 1 bar (left side, drains toward the left) ---
    p1_ratio = max(p1.health, 0) / p1.max_health
    # background (red = lost health)
    pygame.draw.rect(surface, (150, 30, 30), (MARGIN, Y, BAR_WIDTH, BAR_HEIGHT))
    # foreground (yellow = remaining), anchored to the RIGHT edge so it drains inward like SF
    p1_fill = int(BAR_WIDTH * p1_ratio)
    pygame.draw.rect(surface, (230, 200, 50),
                     (MARGIN + BAR_WIDTH - p1_fill, Y, p1_fill, BAR_HEIGHT))
    # border
    pygame.draw.rect(surface, (255, 255, 255), (MARGIN, Y, BAR_WIDTH, BAR_HEIGHT), 2)

    # --- Player 2 bar (right side, mirrored: drains toward the right) ---
    p2_ratio = max(p2.health, 0) / p2.max_health
    p2_x = 800 - MARGIN - BAR_WIDTH
    pygame.draw.rect(surface, (150, 30, 30), (p2_x, Y, BAR_WIDTH, BAR_HEIGHT))
    p2_fill = int(BAR_WIDTH * p2_ratio)
    pygame.draw.rect(surface, (230, 200, 50), (p2_x, Y, p2_fill, BAR_HEIGHT))
    pygame.draw.rect(surface, (255, 255, 255), (p2_x, Y, BAR_WIDTH, BAR_HEIGHT), 2)

    # --- Score in the middle ---
    score_text = font.render(f"{score[0]} - {score[1]}", True, (255, 255, 255))
    score_rect = score_text.get_rect(center=(400, Y + BAR_HEIGHT // 2))
    surface.blit(score_text, score_rect)


running = True
while running:  # Main Loop
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    all_sprites.update()
    resolve_player_collision(player1, player2)

    # players always face each other
    player1.facing = 1 if player2.rect.centerx >= player1.rect.centerx else -1
    player2.facing = 1 if player1.rect.centerx >= player2.rect.centerx else -1

    # hit detection
    for attacker, defender in ((player1, player2), (player2, player1)):
        hitbox = attacker.get_hitbox()
        if hitbox and not attacker.has_hit and hitbox.colliderect(defender.rect):
            defender.health -= 10
            attacker.has_hit = True

    # --- drawing ---
    screen.fill((30, 30, 30))
    pygame.draw.rect(screen, (60, 45, 30), (0, GROUND_Y, 800, 600 - GROUND_Y))  # dirt/floor area
    pygame.draw.line(screen, (200, 200, 200), (0, GROUND_Y), (800, GROUND_Y), 3)  # horizon line
    all_sprites.draw(screen)

    # draw punch hitboxes (the visible "fists")
    for p in (player1, player2):
        hb = p.get_hitbox()
        if hb:
            pygame.draw.rect(screen, (255, 255, 255), hb)

    draw_hud(screen, player1, player2, score)  # HUD drawn last so it is always on top
    pygame.display.update()
    clock.tick(60)

pygame.quit()

pygame.quit()

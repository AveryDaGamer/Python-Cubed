import pygame
pygame.init()

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

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[self.controls['left']]:
            self.rect.x -= self.speed
        if keys[self.controls['right']]:
            self.rect.x += self.speed

        if keys[self.controls['jump']] and self.on_ground:
            self.vel_y = -15
            self.on_ground = False

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

p1_controls = {'left': pygame.K_a, 'right': pygame.K_d, 'jump': pygame.K_w}
p2_controls = {'left': pygame.K_j, 'right': pygame.K_l, 'jump': pygame.K_i}

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
running = True
while running: #Main Loop
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                print("Space was pressed")

    all_sprites.update()
    resolve_player_collision(player1, player2)

    
    screen.fill((30, 30, 30))
    pygame.draw.rect(screen, (60, 45, 30), (0, GROUND_Y, 800, 600 - GROUND_Y))  # dirt/floor area
    pygame.draw.line(screen, (200, 200, 200), (0, GROUND_Y), (800, GROUND_Y), 3)  # horizon line
    all_sprites.draw(screen)
    pygame.display.update()
    clock.tick(60)

pygame.quit()
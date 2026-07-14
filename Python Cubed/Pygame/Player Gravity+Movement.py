import pygame
pygame.init()

screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("My First Pygame")
GROUND_Y = 450  # y-coordinate of the floor line (150px above the bottom of a 600px window)

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((50, 80))  # taller, more fighter-shaped
        self.image.fill((0, 100, 255))
        self.rect = self.image.get_rect()
        self.rect.midbottom = (400, GROUND_Y)  # standing on the floor
        self.speed = 5
        self.vel_y = 0
        self.on_ground = True

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed

        # jump
        if keys[pygame.K_UP] and self.on_ground:
            self.vel_y = -15
            self.on_ground = False

        # gravity
        self.vel_y += 0.8
        self.rect.y += self.vel_y

        # land on the floor
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.vel_y = 0
            self.on_ground = True

        # keep inside the screen horizontally
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > 800:
            self.rect.right = 800


player = Player()
all_sprites = pygame.sprite.Group()
all_sprites.add(player)

clock = pygame.time.Clock()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                print("Space was pressed")

    all_sprites.update()

    
    screen.fill((30, 30, 30))
    pygame.draw.rect(screen, (60, 45, 30), (0, GROUND_Y, 800, 600 - GROUND_Y))  # dirt/floor area
    pygame.draw.line(screen, (200, 200, 200), (0, GROUND_Y), (800, GROUND_Y), 3)  # horizon line
    all_sprites.draw(screen)
    pygame.display.update()
    clock.tick(60)

pygame.quit()
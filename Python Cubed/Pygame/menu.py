# main.py
import pygame
import game

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Street Fighter")
clock = pygame.time.Clock()

title_font = pygame.font.Font(None, 90)
button_font = pygame.font.Font(None, 50)
small_font = pygame.font.Font(None, 36)


def draw_button(surface, text, rect, mouse_pos):
    hovered = rect.collidepoint(mouse_pos)
    color = (90, 90, 140) if hovered else (60, 60, 90)
    pygame.draw.rect(surface, color, rect, border_radius=8)
    pygame.draw.rect(surface, (255, 255, 255), rect, 2, border_radius=8)
    label = button_font.render(text, True, (255, 255, 255))
    surface.blit(label, label.get_rect(center=rect.center))


def menu_screen():
    single_btn = pygame.Rect(250, 220, 300, 60)
    multi_btn = pygame.Rect(250, 310, 300, 60)
    credits_btn = pygame.Rect(250, 400, 300, 60)

    while True:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if single_btn.collidepoint(mouse_pos):
                    return "single"
                if multi_btn.collidepoint(mouse_pos):
                    return "multi"
                if credits_btn.collidepoint(mouse_pos):
                    return "credits"

        screen.fill((25, 25, 40))
        title = title_font.render("STREET FIGHTER", True, (230, 200, 50))
        screen.blit(title, title.get_rect(center=(400, 120)))

        draw_button(screen, "Single Player", single_btn, mouse_pos)
        draw_button(screen, "Multiplayer", multi_btn, mouse_pos)
        draw_button(screen, "Credits", credits_btn, mouse_pos)

        pygame.display.update()
        clock.tick(60)


def credits_screen():
    back_btn = pygame.Rect(300, 480, 200, 60)
    lines = [
        "Made by: YOUR NAME",
        "Built with Python + Pygame",
        "P1: WASD + Q      P2: IJKL + U",
        "ESC during a match returns to this menu",
    ]

    while True:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_btn.collidepoint(mouse_pos):
                    return "menu"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "menu"

        screen.fill((25, 25, 40))
        title = title_font.render("CREDITS", True, (230, 200, 50))
        screen.blit(title, title.get_rect(center=(400, 100)))
        for i, line in enumerate(lines):
            text = small_font.render(line, True, (255, 255, 255))
            screen.blit(text, text.get_rect(center=(400, 210 + i * 50)))

        draw_button(screen, "Back", back_btn, mouse_pos)
        pygame.display.update()
        clock.tick(60)


# --- state machine: routes between screens ---
state = "menu"
while state != "quit":
    if state == "menu":
        state = menu_screen()
    elif state == "credits":
        state = credits_screen()
    elif state in ("single", "multi"):
        state = game.run_game(screen, mode=state)

pygame.quit()

# main.py
import os
import pygame
import game

pygame.init()
screen = pygame.display.set_mode((game.SCREEN_W, game.SCREEN_H))
pygame.display.set_caption("Street Fighter")
clock = pygame.time.Clock()

CENTER_X = game.SCREEN_W // 2

title_font = pygame.font.Font(None, 90)
button_font = pygame.font.Font(None, 50)
small_font = pygame.font.Font(None, 36)
controls_font = pygame.font.Font(None, 32)

# desert-arch background for the menu screens (falls back to a flat color)
_bg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "menu_bg.png")
try:
    MENU_BG = pygame.image.load(_bg_path).convert()
    MENU_BG = pygame.transform.smoothscale(MENU_BG, (game.SCREEN_W, game.SCREEN_H))
except (pygame.error, FileNotFoundError):
    MENU_BG = None


def draw_background(darken=90):
    """Menu backdrop: the desert image with a dark tint so text stays readable."""
    if MENU_BG:
        screen.blit(MENU_BG, (0, 0))
        if darken:
            shade = pygame.Surface((game.SCREEN_W, game.SCREEN_H))
            shade.set_alpha(darken)
            shade.fill((42, 22, 12))  # warm dusk shadow instead of flat black
            screen.blit(shade, (0, 0))
    else:
        screen.fill((84, 54, 38))  # sandstone fallback if the image is missing


def draw_button(surface, text, rect, mouse_pos):
    """Sandstone-block buttons to match the desert arch background."""
    game.draw_stone_button(surface, text, rect, mouse_pos, button_font)


def menu_screen():
    single_btn = pygame.Rect(CENTER_X - 150, 230, 300, 60)
    multi_btn = pygame.Rect(CENTER_X - 150, 320, 300, 60)
    controls_btn = pygame.Rect(CENTER_X - 150, 410, 300, 60)
    credits_btn = pygame.Rect(CENTER_X - 150, 500, 300, 60)
    exit_btn = pygame.Rect(CENTER_X - 150, 590, 300, 60)

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
                if controls_btn.collidepoint(mouse_pos):
                    return "controls"
                if credits_btn.collidepoint(mouse_pos):
                    return "credits"
                if exit_btn.collidepoint(mouse_pos):
                    return "exit_confirm"

        draw_background(darken=60)
        title = title_font.render("STREET FIGHTER", True, (230, 200, 50))
        screen.blit(title, title.get_rect(center=(CENTER_X, 130)))

        draw_button(screen, "Single Player", single_btn, mouse_pos)
        draw_button(screen, "Multiplayer", multi_btn, mouse_pos)
        draw_button(screen, "Controls", controls_btn, mouse_pos)
        draw_button(screen, "Credits", credits_btn, mouse_pos)
        draw_button(screen, "Exit", exit_btn, mouse_pos)

        pygame.display.update()
        clock.tick(60)


def exit_confirm_screen():
    """Safety net: make sure the player really meant to close the game."""
    yes_btn = pygame.Rect(CENTER_X - 150, 340, 300, 60)
    no_btn = pygame.Rect(CENTER_X - 150, 430, 300, 60)

    while True:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if yes_btn.collidepoint(mouse_pos):
                    return "quit"
                if no_btn.collidepoint(mouse_pos):
                    return "menu"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "menu"

        draw_background(darken=130)
        title = title_font.render("EXIT GAME", True, (230, 200, 50))
        screen.blit(title, title.get_rect(center=(CENTER_X, 170)))
        question = small_font.render("Are you sure you want to leave?", True, (255, 238, 205))
        screen.blit(question, question.get_rect(center=(CENTER_X, 260)))

        draw_button(screen, "Yes, exit", yes_btn, mouse_pos)
        draw_button(screen, "No, stay", no_btn, mouse_pos)

        pygame.display.update()
        clock.tick(60)


def difficulty_screen():
    """Pick the CPU level for single player."""
    easy_btn = pygame.Rect(CENTER_X - 150, 250, 300, 60)
    medium_btn = pygame.Rect(CENTER_X - 150, 340, 300, 60)
    hard_btn = pygame.Rect(CENTER_X - 150, 430, 300, 60)
    back_btn = pygame.Rect(CENTER_X - 100, 550, 200, 60)

    while True:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if easy_btn.collidepoint(mouse_pos):
                    return "easy"
                if medium_btn.collidepoint(mouse_pos):
                    return "medium"
                if hard_btn.collidepoint(mouse_pos):
                    return "hard"
                if back_btn.collidepoint(mouse_pos):
                    return "menu"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "menu"

        draw_background(darken=110)
        title = title_font.render("SINGLE PLAYER", True, (230, 200, 50))
        screen.blit(title, title.get_rect(center=(CENTER_X, 120)))
        sub = small_font.render("Choose your opponent", True, (255, 238, 205))
        screen.blit(sub, sub.get_rect(center=(CENTER_X, 190)))

        draw_button(screen, "Easy", easy_btn, mouse_pos)
        draw_button(screen, "Medium", medium_btn, mouse_pos)
        draw_button(screen, "Hard", hard_btn, mouse_pos)
        draw_button(screen, "Back", back_btn, mouse_pos)

        pygame.display.update()
        clock.tick(60)


def controls_screen():
    back_btn = pygame.Rect(CENTER_X - 100, 640, 200, 60)
    rows = [
        ("Move", "A / D", "J / L"),
        ("Jump", "W", "I"),
        ("Crouch (hold)", "S", "K"),
        ("Punch", "Q", "U"),
        ("Heavy", "E", "O"),
        ("Special", "R", "P"),
        ("Block (hold)", "F", ";"),
        ("Dodge", "L Shift", "R Shift"),
    ]
    tips = [
        "Block cuts damage to 1/5  -  dodge has invincibility frames",
        "Crouch ducks under punches and high fireballs",
        "Land hits to fill your meter - a full bar unlocks the special",
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

        draw_background(darken=170)
        title = title_font.render("CONTROLS", True, (230, 200, 50))
        screen.blit(title, title.get_rect(center=(CENTER_X, 90)))

        # column headers, tinted to match each fighter
        p1_head = small_font.render("PLAYER 1", True, (100, 160, 255))
        p2_head = small_font.render("PLAYER 2", True, (255, 100, 100))
        screen.blit(p1_head, p1_head.get_rect(center=(CENTER_X - 220, 165)))
        screen.blit(p2_head, p2_head.get_rect(center=(CENTER_X + 220, 165)))

        for i, (action, p1_key, p2_key) in enumerate(rows):
            y = 215 + i * 38
            label = controls_font.render(action, True, (230, 200, 50))
            k1 = controls_font.render(p1_key, True, (255, 238, 205))
            k2 = controls_font.render(p2_key, True, (255, 238, 205))
            screen.blit(label, label.get_rect(center=(CENTER_X, y)))
            screen.blit(k1, k1.get_rect(center=(CENTER_X - 220, y)))
            screen.blit(k2, k2.get_rect(center=(CENTER_X + 220, y)))

        for i, tip in enumerate(tips):
            text = controls_font.render(tip, True, (230, 205, 170))
            screen.blit(text, text.get_rect(center=(CENTER_X, 540 + i * 32)))

        draw_button(screen, "Back", back_btn, mouse_pos)
        pygame.display.update()
        clock.tick(60)


def credits_screen():
    back_btn = pygame.Rect(CENTER_X - 100, 600, 200, 60)
    lines = [
        "Made by: Kalel, Avery, and Justin",
        "Built with Python + Pygame",
        "See the Controls screen for the full move list",
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

        draw_background(darken=140)
        title = title_font.render("CREDITS", True, (230, 200, 50))
        screen.blit(title, title.get_rect(center=(CENTER_X, 120)))
        for i, line in enumerate(lines):
            text = small_font.render(line, True, (255, 238, 205))
            screen.blit(text, text.get_rect(center=(CENTER_X, 260 + i * 55)))

        draw_button(screen, "Back", back_btn, mouse_pos)
        pygame.display.update()
        clock.tick(60)


# --- state machine: routes between screens ---
state = "menu"
while state != "quit":
    if state == "menu":
        state = menu_screen()
    elif state == "controls":
        state = controls_screen()
    elif state == "credits":
        state = credits_screen()
    elif state == "exit_confirm":
        state = exit_confirm_screen()  # -> "quit" or back to "menu"
    elif state == "single":
        state = difficulty_screen()  # -> "easy" / "medium" / "hard" / "menu"
    elif state in ("easy", "medium", "hard"):
        state = game.run_game(screen, mode="single", difficulty=state)
    elif state == "multi":
        state = game.run_game(screen, mode="multi")

pygame.quit()

# main.py
import pygame, sys, random, os

# ---- Config ----
SCREEN_WIDTH = 288
SCREEN_HEIGHT = 512
FPS = 120

# Paths
ASSETS = os.path.join(os.path.dirname(__file__), "assets")
SOUNDS = os.path.join(os.path.dirname(__file__), "sound")

# ---- Init ----
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Bird")
clock = pygame.time.Clock()

# ---- Load assets ----
def load_image(name, folder=ASSETS):
    path = os.path.join(folder, name)
    return pygame.image.load(path).convert_alpha()

bg_surface = load_image("background-day.png")      # 288x512
floor_surface = load_image("base.png")             # floor image (will be tiled)
pipe_surface = load_image("pipe-green.png")        # pipe image
message_surface = None
try:
    message_surface = load_image("message.png")    # optional title message
except Exception:
    message_surface = None

# Bird frames (animation)
bird_down = load_image("bluebird-downflap.png")
bird_mid = load_image("bluebird-midflap.png")
bird_up = load_image("bluebird-upflap.png")
bird_frames = [bird_down, bird_mid, bird_up]
bird_index = 0
bird_surface = bird_frames[bird_index]
bird_rect = bird_surface.get_rect(center=(50, SCREEN_HEIGHT // 2))

# Sounds (optional, game runs without them if missing)
def load_sound(name):
    try:
        return pygame.mixer.Sound(os.path.join(SOUNDS, name))
    except Exception:
        return None

flap_sound = load_sound("sfx_wing.wav")
death_sound = load_sound("sfx_hit.wav")
score_sound = load_sound("sfx_point.wav")

# ---- Game variables ----
gravity = 0.05
bird_movement = 0
start = False       # False -> show title / game over screen
floor_x_pos = 0

pipe_list = []
PIPE_HEIGHTS = [200, 250, 300, 350, 400]
SPAWNPIPE = pygame.USEREVENT + 1
pygame.time.set_timer(SPAWNPIPE, 1500)   # spawn every 1500ms (tweakable)

BIRDFLAP = pygame.USEREVENT
pygame.time.set_timer(BIRDFLAP, 200)

score = 0
high_score = 0
can_score = True

# ---- Functions ----
def draw_floor():
    # draw floor twice for seamless scrolling
    screen.blit(floor_surface, (floor_x_pos, SCREEN_HEIGHT - floor_surface.get_height()))
    screen.blit(floor_surface, (floor_x_pos + SCREEN_WIDTH, SCREEN_HEIGHT - floor_surface.get_height()))

def create_pipe():
    # choose a random center for the bottom pipe
    height = random.choice(PIPE_HEIGHTS)
    gap = 100  # space between top and bottom pipes (tweakable)
    bottom_pipe = pipe_surface.get_rect(midtop=(SCREEN_WIDTH + 50, height))
    top_pipe = pipe_surface.get_rect(midbottom=(SCREEN_WIDTH + 50, height - gap))
    return bottom_pipe, top_pipe

def move_pipes(pipes):
    for p in pipes:
        p.centerx -= 2
    visible = [p for p in pipes if p.right > -50]
    return visible

def draw_pipes(pipes):
    for pipe in pipes:
        if pipe.bottom >= SCREEN_HEIGHT:
            # bottom pipe
            screen.blit(pipe_surface, pipe)
        else:
            # top pipe: flip vertical
            flip = pygame.transform.flip(pipe_surface, False, True)
            screen.blit(flip, pipe)

def check_collision(pipes):
    global can_score
    for pipe in pipes:
        if bird_rect.colliderect(pipe):
            can_score = True
            if death_sound:
                death_sound.play()
            return False
    if bird_rect.top <= -50 or bird_rect.bottom >= SCREEN_HEIGHT - floor_surface.get_height() + 10:
        can_score = True
        if death_sound:
            death_sound.play()
        return False
    return True

def rotate_bird(bird_surf):
    # rotate a bit depending on movement
    new_bird = pygame.transform.rotozoom(bird_surf, -bird_movement * 3, 1)
    return new_bird

# Score display
game_font = pygame.font.Font(None, 32)

def score_display(current_score, highscore):
    score_surf = game_font.render(str(current_score), True, (255, 255, 255))
    score_rect = score_surf.get_rect(center=(SCREEN_WIDTH // 2, 50))
    screen.blit(score_surf, score_rect)

    # if game over show high score too
    hs_surf = game_font.render(f"Highscore {highscore}", True, (255,255,255))
    hs_rect = hs_surf.get_rect(center=(SCREEN_WIDTH // 2, 80))
    screen.blit(hs_surf, hs_rect)

def pipe_score_check():
    global score, can_score
    if pipe_list:
        for pipe in pipe_list:
            # when a bottom pipe passes the bird
            if 95 < pipe.centerx < 105 and can_score and pipe.bottom >= SCREEN_HEIGHT:
                score += 1
                can_score = False
                if score_sound:
                    score_sound.play()
            if pipe.centerx < 0 and not can_score:
                can_score = True

# Bird animation helper
def bird_animation():
    new_bird = bird_frames[bird_index]
    new_rect = new_bird.get_rect(center=(50, bird_rect.centery))
    return new_bird, new_rect

# ---- Main loop ----
running = True
while running:
    clock.tick(FPS)
    clicked = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                clicked = True
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                clicked = True

        if event.type == BIRDFLAP:
            # change bird index for animation
            if bird_index < 2:
                bird_index += 1
            else:
                bird_index = 0
            bird_surface, bird_rect = bird_animation()

        if event.type == SPAWNPIPE and start:
            b, t = create_pipe()
            pipe_list.extend([b, t])

    # Input handling
    if clicked:
        if not start:
            # start or restart
            pipe_list.clear()
            bird_rect.center = (50, SCREEN_HEIGHT // 2)
            bird_movement = 0
            score = 0
            start = True
        else:
            bird_movement = -2.1  # jump strength
            if flap_sound:
                flap_sound.play()

    # Background
    screen.blit(bg_surface, (0, 0))

    # Game logic if started
    if start:
        # Bird physics
        bird_movement += gravity
        bird_rect.centery += bird_movement
        # rotate and draw bird
        rotated = rotate_bird(bird_surface)
        screen.blit(rotated, bird_rect)

        # Move & draw pipes
        pipe_list = move_pipes(pipe_list)
        draw_pipes(pipe_list)

        # Check collision
        start = check_collision(pipe_list)

        # Score check
        pipe_score_check()

    else:
        # show title / message
        if message_surface:
            msg_rect = message_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            screen.blit(message_surface, msg_rect)
        else:
            # fallback text
            FONT_PATH = os.path.join(ASSETS, "04B_19.TTF")
            game_font = pygame.font.Font(FONT_PATH, 32)
            title_surf = title_font.render("Flappy Bird - Press SPACE or Click", True, (255,255,255))
            title_rect = title_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            screen.blit(title_surf, title_rect)

        # show bird idle (no gravity)
        screen.blit(bird_surface, bird_rect)

    # Move floor
    floor_x_pos -= 1
    draw_floor()
    if floor_x_pos <= -SCREEN_WIDTH:
        floor_x_pos = 0

    # When game end, update high score
    if not start and score > 0:
        if score > high_score:
            high_score = score

    # Display scores
    score_display(score, high_score)

    pygame.display.update()

pygame.quit()
sys.exit()

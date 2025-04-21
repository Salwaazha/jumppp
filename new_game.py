import pygame
import random
import os
from pygame import mixer

# Inisialisasi modul
mixer.init() #untuk suara
pygame.init() #untuk game

# Ukuran layar game
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600

# Membuat jendela game 
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Go Go Jump')
icon = pygame.image.load('img/walking1_0.png')
pygame.display.set_icon(icon)

# Set frame rate
clock = pygame.time.Clock()
FPS = 60

# Suara dan musik 
pygame.mixer.music.load('img/Fun Background.mp3')
pygame.mixer.music.set_volume(0.9)
pygame.mixer.music.play(-1, 0.0) #-1 berarti lagi terulang terus-menerus
jump_fx = pygame.mixer.Sound('img/jump.mp3')
jump_fx.set_volume(1)
death_fx = pygame.mixer.Sound('img/death.mp3')
death_fx.set_volume(1)

# Game variables
SCROLL_THRESH = 200 #batas atas layar (scroll)
GRAVITY = 1 #percepatan turun
MAX_PLATFORMS = 10 #jumlah maks. platform dilayar (jumlah kayu)
scroll = 0 #Nilai akan bertambah jika Jumpy menyentuh scroll tresh (platform & musuh ikut bergeser)
bg_scroll = 0 
game_over = False
score = 0
fade_counter = 0 #transisi layar ketika game mati 

# Menampilkan skor
if os.path.exists('score.txt'):
    with open('score.txt', 'r') as file:
        high_score = int(file.read())
else: 
    high_score = 0

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Fonts
font_small = pygame.font.SysFont('Lucida Sans', 20)
font_big = pygame.font.SysFont('Lucida Sans', 24)

# Import gambar
jumpy_image = pygame.image.load('img/zaizai.png').convert_alpha()
bg_image = pygame.image.load('img/bg.png').convert_alpha()
platform_image = pygame.image.load('img/wood.png').convert_alpha()
bird_sheet_img = pygame.image.load('img/bird.png').convert_alpha()

# Menampilkan teks dilayar
def draw_text(text, font, text_col, x, y): #didalam kurung = parameter
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

# Menampilkan skor
def draw_panel():
    draw_text('SCORE: ' + str(score), font_small, WHITE, 0, 0)

# Menampilkan bg
def draw_bg(bg_scroll):
    screen.blit(bg_image, (0, bg_scroll))
    screen.blit(bg_image, (0, bg_scroll - SCREEN_HEIGHT))

#Kelas Character (inheritance)
class Character: #superclass
    def __init__(self, x, y, image, width, height): #init = constructor, fungsi otomatis jalan saat objek dibuat
        self.image = pygame.transform.scale(image, (width, height))
        self.rect = pygame.Rect(x, y, width, height) #rect = posisi
        self.vel_y = 0 #kecepatan jatuh
        self.flip = False #aarah hadap
        self.width = width    
        self.height = height 
        #x, y, image, width, height = data member
        #deklarasi objek = variabel dalam class
        
    def apply_gravity(self):
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), (self.rect.x - 12, self.rect.y - 5))

# Kelas Player
class Player(Character):
    def __init__(self, x, y): #setup awal player
        print('Constructor Execute Kelas Player')
        super().__init__(x, y, jumpy_image, 65, 65)  # Pakai super() untuk ambil init dari Character
    
    def move(self): 
        global scroll
        dx = 0
        dy = 0
        
        # Arah
        key = pygame.key.get_pressed()
        if key[pygame.K_a]:
            dx = -10
            self.flip = False
        if key[pygame.K_d]:
            dx = 10
            self.flip = True
        
        # Gravity
        self.vel_y += GRAVITY
        dy += self.vel_y
        
        # Batas layar kiri-kanan player
        if self.rect.left + dx < 0:
            dx = -self.rect.left
        if self.rect.right + dx > SCREEN_WIDTH:
            dx = SCREEN_WIDTH - self.rect.right

        # Ceck tabrakan
        for platform in platform_group:
            if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                if self.rect.bottom < platform.rect.centery:
                    if self.vel_y > 0:
                        self.rect.bottom = platform.rect.top
                        dy = 0
                        self.vel_y = -20
                        jump_fx.play()

        # Scroll ketika player naik
        if self.rect.top <= SCROLL_THRESH:
            if self.vel_y < 0:
                scroll = -dy

        # Update posisi
        self.rect.x += dx
        self.rect.y += dy + scroll

        # Mendeteksi saat nabrak musuh
        self.mask = pygame.mask.from_surface(self.image)

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), (self.rect.x - 12, self.rect.y - 5))
    
    def __del__(self): #dipanggil otomatis saat objek player dihapus (misal saat restart game)
        print('Destructor Execute Kelas Player')
 
# Platform class
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, moving):
        print('Constructor Execute Kelas Platform')
        super().__init__()
        self.image = pygame.transform.scale(platform_image, (width, 10))
        self.moving = moving
        self.move_counter = random.randint(0, 50)
        self.direction = random.choice([-1, 1])
        self.speed = random.randint(1, 2)
        self.rect = self.image.get_rect(topleft=(x, y))

    def update(self, scroll):
        if self.moving:
            self.move_counter += 1
            self.rect.x += self.direction * self.speed
        
        if self.move_counter >= 100 or self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
            self.direction *= -1
            self.move_counter = 0
        
        self.rect.y += scroll

        if self.rect.top > SCREEN_HEIGHT:
            self.kill()
            
    def __del__(self):
        print('Disructor Execute Kelas Platform')

class SpriteSheet(): #memotong bagian gambar menjadi frame frame animasi
    def __init__(self, image):
        print('Constructor Execute Kelas SpriteSheet')
        self.sheet = image

    def get_image(self, frame, width, height, scale, colour):
        image = pygame.Surface((width, height)).convert_alpha()
        image.blit(self.sheet, (0, 0), ((frame * width), 0, width, height))
        image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        image.set_colorkey(colour)
        return image

    def __del__(self): 
        print('Distructor Execute Kelas SpriteSheet')

class Enemy(pygame.sprite.Sprite): #subclass dari pygame sprite
    def __init__(self, SCREEN_WIDTH, y, sprite_sheet, scale):
        print('Constructor Execute Kelas Enemy')
        super().__init__()
        self.animation_list = [] #list gambar animasi burung
        self.frame_index = 0 #frame animasi yang sedang dipakai
        self.update_time = pygame.time.get_ticks() #waktu terakhir animasi di update
        self.direction = random.choice([-1, 1]) #arah gerak (-1) kekiri, (1) kekanan
        self.flip = self.direction == 1

        # Load image
        animation_steps = 8  
        for animation in range(animation_steps):
            image = sprite_sheet.get_image(animation, 30, 30, scale, (0, 0, 0))
            image = pygame.transform.flip(image, self.flip, False)
            image.set_colorkey((0, 0, 0))
            self.animation_list.append(image)
        
        self.image = self.animation_list[self.frame_index]
        self.rect = self.image.get_rect(topleft=(0 if self.direction == 1 else SCREEN_WIDTH, y))
      
    def update(self, scroll, SCREEN_WIDTH):
        ANIMATION_COOLDOWN = 50
        self.image = self.animation_list[self.frame_index]
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index = (self.frame_index + 1) % len(self.animation_list)

        self.rect.x += self.direction * 2
        self.rect.y += scroll
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

    def __del__(self):
        print('Distructor Execute Kelas Enemy')



# Player instance
jumpy = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)

# Create sprite groups
platform_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()

# Create starting platform
platform = Platform(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 50, 80, False)
platform_group.add(platform)

bird_sheet = SpriteSheet(bird_sheet_img)

# Game loop
run = True
while run:
    clock.tick(FPS)
    
    if not game_over:
        jumpy.move()
        bg_scroll += scroll
        if bg_scroll >= SCREEN_HEIGHT:
            bg_scroll = 0
        draw_bg(bg_scroll)

        # Generate platforms
        if len(platform_group) < MAX_PLATFORMS:
            p_w = random.randint(40, 60)
            p_x = random.randint(0, SCREEN_WIDTH - p_w)
            p_y = platform.rect.y - random.randint(80, 120)
            p_moving = score > 1000 and random.choice([True, False])
            platform = Platform(p_x, p_y, p_w, p_moving)
            platform_group.add(platform)

        # Update platforms
        platform_group.update(scroll)

        # Generate enemies
        if len(enemy_group) == 0 and score > 2000:
            enemy = Enemy(SCREEN_WIDTH, 95, bird_sheet, 1.5)
            enemy_group.add(enemy)
        
        # Update enemies
        enemy_group.update(scroll, SCREEN_WIDTH)

        # Update score
        if scroll > 0:
            score += scroll

        # Draw high score line
        pygame.draw.line(screen, WHITE, (0, score - high_score + SCROLL_THRESH), (SCREEN_WIDTH, score - high_score + SCROLL_THRESH), 3)
        draw_text('HIGH SCORE', font_small, WHITE, SCREEN_WIDTH - 130, score - high_score + SCROLL_THRESH)

        # Draw sprites
        platform_group.draw(screen)
        enemy_group.draw(screen)
        jumpy.draw()
        
        # Draw panel
        draw_panel() 

        # Check game over
        if jumpy.rect.top > SCREEN_HEIGHT or pygame.sprite.spritecollide(jumpy, enemy_group, False, pygame.sprite.collide_mask):
            game_over = True
            death_fx.play()
    
    else:
        if fade_counter < SCREEN_WIDTH:
            fade_counter += 5
            for y in range(0, 6, 2):
                pygame.draw.rect(screen, BLACK, (0, y * 100, fade_counter, 100))
                pygame.draw.rect(screen, BLACK, (SCREEN_WIDTH - fade_counter, (y + 1) * 100, SCREEN_WIDTH, 100))
        else:
            draw_text('GAME OVER!', font_big, WHITE, 130, 200)
            draw_text('SCORE: ' + str(score), font_big, WHITE, 130, 250)
            draw_text('PRESS SPACE TO PLAY AGAIN', font_big, WHITE, 40, 300)
            if score > high_score:
                high_score = score
                with open('score.txt', 'w') as file:
                    file.write(str(high_score))
            key = pygame.key.get_pressed()
            if key[pygame.K_SPACE]:
                # Reset variables
                game_over = False
                score = 0
                scroll = 0
                fade_counter = 0
                jumpy.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150)
                enemy_group.empty()
                platform_group.empty()
                platform = Platform(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 50, 100, False)
                platform_group.add(platform)

    # Event handler
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if score > high_score:
                high_score = score
                with open('score.txt', 'w') as file:
                    file.write(str(high_score))
            run = False
    
    # Update display
    pygame.display.update()

pygame.quit()   
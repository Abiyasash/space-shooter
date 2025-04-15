import pygame
from os.path import join
from random import randint, uniform


class Player(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.original_image = pygame.image.load(
            join('images', 'player.png')
        ).convert_alpha()
        self.image = self.original_image
        self.rect = self.image.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT - 200))
        self.direction = pygame.Vector2()
        self.speed = 300

        self.lasers = 1
        self.can_shoot = False
        self.laser_shoot_time = 0
        self.cooldown_duration = 400

        self.mask = pygame.mask.from_surface(self.image)

        self.flashing = False
        self.flash_start_time = 0
        self.flash_duration = 1000
        self.flash_interval = 100
        self.last_flash_time = 0
        self.mask_image = self.mask.to_surface(
            setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0)
        )
        self.gold_flash_image = self.mask.to_surface(
            setcolor=(255, 215, 0, 255), unsetcolor=(0, 0, 0, 0)
        )

        self.invicible = False
        self.upgrading = False

    def laser_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.laser_shoot_time >= self.cooldown_duration:
                self.can_shoot = True

    def damage_flashing(self):
        current_time = pygame.time.get_ticks()

        if self.flashing:
            if current_time - self.flash_start_time >= self.flash_duration:
                self.flashing = False
                self.invicible = False
                self.upgrading = False
                self.image = self.original_image
            elif current_time - self.last_flash_time >= self.flash_interval:
                self.last_flash_time = current_time
                if self.upgrading:
                    self.image = (
                        self.original_image
                        if self.image == self.gold_flash_image
                        else self.gold_flash_image
                    )
                else:
                    self.image = (
                        self.original_image
                        if self.image == self.mask_image
                        else self.mask_image
                    )

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(
            keys[pygame.K_a] or keys[pygame.K_LEFT]
        )
        self.direction.y = int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(
            keys[pygame.K_w] or keys[pygame.K_UP]
        )
        self.direction = (
            self.direction.normalize() if self.direction else self.direction
        )
        self.rect.center += self.direction * self.speed * dt

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WINDOW_WIDTH:
            self.rect.right = WINDOW_WIDTH
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > WINDOW_HEIGHT:
            self.rect.bottom = WINDOW_HEIGHT

        recent_keys = pygame.key.get_just_pressed()
        if game_active and recent_keys[pygame.K_SPACE] and self.can_shoot:
            for _ in range(int(self.lasers)):
                Laser(laser_surf, self.rect.midtop, (all_sprites, laser_sprites))
                laser_sound.play()
            self.can_shoot = False
            self.laser_shoot_time = pygame.time.get_ticks()

        self.laser_timer()
        self.damage_flashing()


class Star(pygame.sprite.Sprite):
    def __init__(self, groups, surf):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(
            center=(randint(0, WINDOW_WIDTH), randint(0, WINDOW_HEIGHT))
        )


class Laser(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(midbottom=pos)
        self.speed = 800

    def update(self, dt):
        self.rect.centery -= self.speed * dt
        if self.rect.bottom < 0:
            self.kill()


class Meteor(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.original_surf = surf
        self.image = surf
        self.rect = self.image.get_frect(center=pos)
        self.start_time = pygame.time.get_ticks()
        self.lifetime = 3000
        self.direction = pygame.Vector2(uniform(-0.5, 0.5), 1)
        self.speed = randint(400, 500)
        self.rotation = 0
        self.rotation_speed = randint(40, 80)

    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt
        if pygame.time.get_ticks() - self.start_time >= self.lifetime:
            self.kill()

        self.rotation += self.rotation_speed * dt
        self.image = pygame.transform.rotozoom(self.original_surf, self.rotation, 1)
        self.rect = self.image.get_frect(center=self.rect.center)


class AnimatedExplosion(pygame.sprite.Sprite):
    def __init__(self, frames, pos, groups):
        super().__init__(groups)
        self.frames = frames
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_frect(center=pos)

    def update(self, dt):
        self.frame_index += 20 * dt
        if self.frame_index < len(self.frames):
            self.image = self.frames[int(self.frame_index)]
        else:
            self.kill()


def collisions():
    global running, player, score, lives, damage_event

    if not player.invicible:
        collision_sprites = pygame.sprite.spritecollide(
            player, meteor_sprites, True, pygame.sprite.collide_mask
        )
        if collision_sprites:
            lives -= 1
            if lives == 0:
                pygame.event.post(pygame.event.Event(game_over_event))
            else:
                damage_sound.play()
                player.flashing = True
                player.invicible = True
                player.flash_start_time = pygame.time.get_ticks()
                player.last_flash_time = player.flash_start_time

    for laser in laser_sprites:
        collided_sprites = pygame.sprite.spritecollide(laser, meteor_sprites, True)
        if collided_sprites:
            laser.kill()
            score += 1
            AnimatedExplosion(explosion_frames, laser.rect.midtop, all_sprites)
            explosion_sound.play()


def display_score():
    global score
    text_surf = font.render(str(score), True, (240, 240, 240))
    text_rect = text_surf.get_frect(midbottom=(WINDOW_WIDTH / 2, WINDOW_HEIGHT - 50))
    display_surface.blit(text_surf, text_rect)
    pygame.draw.rect(
        display_surface, (240, 240, 240), text_rect.inflate(20, 16).move(0, -8), 5, 10
    )


def display_waves():
    global wave
    text_surf = font.render(f'Wave: {wave}', True, (240, 240, 240))
    text_rect = text_surf.get_frect(midtop=(WINDOW_WIDTH - 1180, WINDOW_HEIGHT - 700))
    display_surface.blit(text_surf, text_rect)


def display_lives():
    global lives
    text_surf = font.render(f'Lives: {lives}', True, (240, 240, 240))
    text_rect = text_surf.get_frect(midtop=(WINDOW_WIDTH - 100, WINDOW_HEIGHT - 700))
    display_surface.blit(text_surf, text_rect)


def display_msg():
    global game_active

    msg = (
        f'Game Over!\nScore: {score}\nPress any button to play again.'
        if not game_active
        else 'Space Shooter\n\nPress any button to begin.'
    )

    game_music.stop()
    game_over_text = font.render(msg, True, (240, 240, 240))
    game_over_rect = game_over_text.get_frect(
        center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
    )
    display_surface.blit(game_over_text, game_over_rect)


def increase_wave():
    global player, wave, meteor_event, meteor_spawn_interval, score
    wave_sound.play()

    speed_factor = 1.1487
    cooldown_factor = 0.8706
    meteor_spawn_factor = 0.794328

    if score < 100:
        player.speed = 300 * (speed_factor**wave)
        player.lasers += 0.5
        player.cooldown_duration = 400 * (cooldown_factor**wave)
    else:
        player.speed = 600
        player.lasers = 3
        player.cooldown_duration = 200

    meteor_spawn_interval = 200 * (meteor_spawn_factor**wave)
    meteor_spawn_interval = max(20, int(meteor_spawn_interval))

    pygame.time.set_timer(meteor_event, meteor_spawn_interval)

    player.invicible = True
    player.flashing = True
    player.upgrading = True
    player.flash_start_time = pygame.time.get_ticks()
    player.last_flash_time = player.flash_start_time

    wave += 1

pygame.init()
WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Space Shooter')
running = True
game_active = True
game_just_started = True
score = 0
lives = 5
last_upgraded_score = 0
wave = 1
clock = pygame.time.Clock()

star_surf = pygame.image.load(join('images', 'star.png')).convert_alpha()
meteor_surf = pygame.image.load(join('images', 'meteor.png')).convert_alpha()
laser_surf = pygame.image.load(join('images', 'laser.png')).convert_alpha()
font = pygame.font.Font(join('images', 'Oxanium-Bold.ttf'), 40)
explosion_frames = [
    pygame.image.load(join('images', 'explosion', f'{i}.png')).convert_alpha()
    for i in range(21)
]

laser_sound = pygame.mixer.Sound(join('audio', 'laser.wav'))
laser_sound.set_volume(0.4)

explosion_sound = pygame.mixer.Sound(join('audio', 'explosion.wav'))
explosion_sound.set_volume(0.6)

damage_sound = pygame.mixer.Sound(join('audio', 'damage.ogg'))
damage_sound.set_volume(0.6)

wave_sound = pygame.mixer.Sound(join('audio', 'upgrade.mp3'))
wave_sound.set_volume(1)

game_music = pygame.mixer.Sound(join('audio', 'game_music.wav'))
game_music.set_volume(0.8)

all_sprites = pygame.sprite.Group()
meteor_sprites = pygame.sprite.Group()
laser_sprites = pygame.sprite.Group()
for i in range(30):
    Star(all_sprites, star_surf)
player = Player(all_sprites)

meteor_event = pygame.event.custom_type()
meteor_spawn_interval = 200
pygame.time.set_timer(meteor_event, meteor_spawn_interval)

game_over_event = pygame.event.custom_type()

while running:
    dt = clock.tick() / 1000
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if game_active and event.type == meteor_event:
            x, y = randint(0, WINDOW_WIDTH), randint(-200, -100)
            Meteor(meteor_surf, (x, y), (all_sprites, meteor_sprites))
        if event.type == game_over_event:
            game_active = False
        if (not game_active or game_just_started) and event.type == pygame.KEYDOWN:
            running = True
            game_active = True
            game_just_started = False
            score = 0
            lives = 5
            last_upgraded_score = 0
            wave = 1

            meteor_spawn_interval = 200

            pygame.time.set_timer(meteor_event, meteor_spawn_interval)

            game_music.play(loops=-1)
            all_sprites = pygame.sprite.Group()
            meteor_sprites = pygame.sprite.Group()
            laser_sprites = pygame.sprite.Group()
            for i in range(30):
                Star(all_sprites, star_surf)
            player = Player(all_sprites)

    display_surface.fill('#3a2e3f')

    if game_just_started:
        display_msg()

    else:
        if game_active:
            all_sprites.update(dt)
            collisions()
            display_score()
            display_waves()
            display_lives()
            if (
                score % 20 == 0
                and score != 0
                and score <= 200
                and score != last_upgraded_score
            ):
                increase_wave()
                last_upgraded_score = score
            all_sprites.draw(display_surface)

        else:
            game_music.stop()
            display_msg()

    pygame.display.update()

pygame.quit()

import pygame
from .player import Player
from .obstacle import Obstacle

# Game Engine

WHITE = (255, 255, 255)
BROWN = (120, 80, 40)
DARK_GREEN = (30, 100, 30)
DARK_OVERLAY = (20, 25, 35)


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.ground_y = height - 40

        self.player = Player(80, self.ground_y)

        self.speed = 6.0
        self.speed_increase_per_frame = 0.003
        self.max_speed = 14.0

        # Difficulty settings: starting speed and spawn interval.
        self.difficulties = {
            "Easy": (5.0, 85),
            "Medium": (6.0, 70),
            "Hard": (8.0, 55),
        }
        self.difficulty = "Medium"
        self.spawn_interval = 70

        self._spawn_timer = 0
        self.obstacles = []

        self.distance = 0
        self.score = 0
        self.font = pygame.font.SysFont("Arial", 30)
        self.game_over_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.message_font = pygame.font.SysFont("Arial", 24)
        self.game_over = False

        # Basic sound effects.
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            self.jump_sound = self._make_sound(600, 0.10)
            self.score_sound = self._make_sound(900, 0.08)
            self.game_over_sound = self._make_sound(150, 0.25)
        except pygame.error:
            self.jump_sound = None
            self.score_sound = None
            self.game_over_sound = None

    def _make_sound(self, frequency, duration):
        # Generate a simple tone without needing external sound files.
        import math
        sample_rate = 44100
        samples = int(sample_rate * duration)
        buffer = bytearray()

        for i in range(samples):
            value = int(
                32767
                * 0.25
                * math.sin(2 * math.pi * frequency * i / sample_rate)
            )
            buffer.append(value & 255)
            buffer.append((value >> 8) & 255)

        return pygame.mixer.Sound(buffer=bytes(buffer))

    def reset(self, difficulty=None):
        if difficulty is not None:
            self.difficulty = difficulty

        start_speed, self.spawn_interval = self.difficulties[self.difficulty]

        self.player = Player(80, self.ground_y)
        self.speed = start_speed
        self._spawn_timer = 0
        self.obstacles = []
        self.distance = 0
        self.score = 0
        self.game_over = False

    def handle_event(self, event):
        # Ignore gameplay input after the game has ended.
        if self.game_over:
            return

        if event.type == pygame.KEYDOWN and event.key in (
            pygame.K_SPACE,
            pygame.K_UP,
            pygame.K_w,
        ):
            self.player.jump()
            if self.jump_sound:
                self.jump_sound.play()

    def handle_input(self):
        # Jumping is handled by the KEYDOWN event.
        pass

    def update(self):
        if self.game_over:
            return

        # Increase speed gradually, but never exceed the maximum.
        self.speed = min(
            self.speed + self.speed_increase_per_frame,
            self.max_speed,
        )

        self.player.update()

        self._spawn_timer += 1
        if self._spawn_timer >= self.spawn_interval:
            self._spawn_timer = 0
            self.obstacles.append(
                Obstacle(self.width, self.ground_y, self.speed)
            )

        # Keep both old and new obstacle rectangles so a fast obstacle
        # cannot pass through the player between frames.
        player_rect = self.player.rect()
        previous_rects = {}

        for obstacle in self.obstacles:
            previous_rects[id(obstacle)] = obstacle.rect().copy()
            obstacle.speed = self.speed
            obstacle.move()

        for obstacle in self.obstacles:
            old_rect = previous_rects[id(obstacle)]
            new_rect = obstacle.rect()

            # Original collision check plus the swept rectangle.
            # The swept rectangle covers the obstacle's entire path.
            swept_rect = old_rect.union(new_rect)

            if swept_rect.colliderect(player_rect):
                self.game_over = True
                print("GAME OVER")
                print(f"Final Score: {self.score}")
                if self.game_over_sound:
                    self.game_over_sound.play()
                return

        # Award one point when an obstacle has fully passed the player.
        for obstacle in self.obstacles:
            if (
                not obstacle.scored
                and obstacle.x + obstacle.width < self.player.x
            ):
                obstacle.scored = True
                self.score += 1
                if self.score_sound:
                    self.score_sound.play()

        self.obstacles = [
            obstacle for obstacle in self.obstacles
            if not obstacle.off_screen()
        ]
        self.distance += self.speed

    def render(self, screen):
        pygame.draw.line(
            screen,
            BROWN,
            (0, self.ground_y),
            (self.width, self.ground_y),
            4,
        )

        pygame.draw.rect(screen, WHITE, self.player.rect())
        for obstacle in self.obstacles:
            pygame.draw.rect(screen, DARK_GREEN, obstacle.rect())

        score_text = self.font.render(
            f"Score: {self.score}", True, (0, 0, 0)
        )
        screen.blit(score_text, (10, 10))

        if self.game_over:
            overlay = pygame.Surface(
                (self.width, self.height),
                pygame.SRCALPHA,
            )
            overlay.fill((*DARK_OVERLAY, 190))
            screen.blit(overlay, (0, 0))

            title = self.game_over_font.render(
                "GAME OVER", True, (255, 255, 255)
            )
            final_score = self.font.render(
                f"Final Score: {self.score}", True, (255, 255, 255)
            )
            instruction = self.message_font.render(
                "R: Replay   1: Easy   2: Medium   3: Hard   Q/ESC: Exit",
                True,
                (220, 220, 220),
            )

            screen.blit(
                title,
                title.get_rect(
                    center=(self.width // 2, self.height // 2 - 65)
                ),
            )
            screen.blit(
                final_score,
                final_score.get_rect(
                    center=(self.width // 2, self.height // 2)
                ),
            )
            screen.blit(
                instruction,
                instruction.get_rect(
                    center=(self.width // 2, self.height // 2 + 50)
                ),
            )

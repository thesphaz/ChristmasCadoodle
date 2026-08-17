"""
🎄 Christmas Toy Tycoon - A Sidescroller Tycoon Game 🎄

Help Santa's toy factory workers produce toys before Christmas!
- Manage your toy factory on a conveyor belt
- Hire workers and upgrade equipment
- Race against the clock to fulfill orders
- Reach profit targets and unlock new toy types
"""

import pygame
import random
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
FPS = 60
FONT_SMALL = pygame.font.Font(None, 24)
FONT_MEDIUM = pygame.font.Font(None, 32)
FONT_LARGE = pygame.font.Font(None, 48)

# Colors
COLOR_BG = (20, 30, 60)
COLOR_CONVEYOR = (100, 100, 120)
COLOR_TEXT = (255, 255, 255)
COLOR_MONEY = (0, 255, 0)
COLOR_DANGER = (255, 50, 50)
COLOR_BUTTON = (50, 150, 255)
COLOR_BUTTON_HOVER = (100, 200, 255)


class ToyType(Enum):
    WOODEN_BLOCK = {"name": "Wooden Block", "base_value": 5, "production_time": 30, "color": (180, 140, 80)}
    DOLL = {"name": "Doll", "base_value": 15, "production_time": 60, "color": (255, 180, 200)}
    TRAIN = {"name": "Train", "base_value": 25, "production_time": 90, "color": (255, 100, 50)}
    ROBOT = {"name": "Robot", "base_value": 40, "production_time": 120, "color": (200, 200, 200)}


@dataclass
class Button:
    x: int
    y: int
    width: int
    height: int
    text: str
    cost: int = 0
    
    def draw(self, screen, font, is_hovering=False):
        color = COLOR_BUTTON_HOVER if is_hovering else COLOR_BUTTON
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, COLOR_TEXT, (self.x, self.y, self.width, self.height), 2)
        
        text_surf = font.render(self.text, True, COLOR_TEXT)
        text_rect = text_surf.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
        screen.blit(text_surf, text_rect)
        
        if self.cost > 0:
            cost_text = font.render(f"${self.cost}", True, COLOR_MONEY)
            screen.blit(cost_text, (self.x + 5, self.y + self.height - 20))
    
    def is_clicked(self, pos):
        return (self.x <= pos[0] <= self.x + self.width and 
                self.y <= pos[1] <= self.y + self.height)


class Toy:
    def __init__(self, toy_type: ToyType, x: float):
        self.type = toy_type
        self.x = x
        self.y = SCREEN_HEIGHT // 2
        self.progress = 0  # 0-1, completion percentage
        self.value = toy_type.value["base_value"]
        self.size = 15
    
    def update(self, speed=1.0):
        """Move toy along conveyor and progress production"""
        self.x += speed
        self.progress = min(1.0, self.progress + 0.005)
    
    def draw(self, screen):
        color = self.type.value["color"]
        # Draw toy
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size)
        
        # Draw progress bar
        if self.progress < 1.0:
            bar_width = 30
            bar_height = 5
            pygame.draw.rect(screen, (50, 50, 50), (self.x - bar_width // 2, self.y - 25, bar_width, bar_height))
            pygame.draw.rect(screen, COLOR_MONEY, 
                           (self.x - bar_width // 2, self.y - 25, bar_width * self.progress, bar_height))
    
    def is_complete(self):
        return self.progress >= 1.0


class Worker:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 30
        self.speed = 1.5
        self.working_on: Optional[Toy] = None
        self.idle_timer = 0
    
    def update(self, toys: List[Toy]):
        """AI: Find nearest incomplete toy"""
        if self.working_on is None or self.working_on.progress >= 1.0:
            # Find nearest incomplete toy
            incomplete_toys = [t for t in toys if not t.is_complete()]
            if incomplete_toys:
                self.working_on = min(incomplete_toys, 
                                     key=lambda t: abs(t.x - self.x))
            else:
                self.idle_timer += 1
        
        # Move towards toy
        if self.working_on:
            target_x = self.working_on.x
            if abs(self.x - target_x) > 5:
                self.x += (target_x - self.x) * 0.05
            else:
                self.working_on.progress += 0.01
    
    def draw(self, screen):
        # Draw worker body
        pygame.draw.rect(screen, (100, 200, 100), 
                        (self.x - self.width // 2, self.y - self.height // 2, 
                         self.width, self.height))
        # Draw head
        pygame.draw.circle(screen, (220, 180, 140), (int(self.x), int(self.y - 20)), 8)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("🎄 Christmas Toy Tycoon 🎄")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Game state
        self.money = 100
        self.score = 0
        self.level = 1
        self.days_until_christmas = 25
        self.toys: List[Toy] = []
        self.workers: List[Worker] = []
        self.conveyor_speed = 2.0
        
        # Orders
        self.current_order = random.choice(list(ToyType))
        self.orders_fulfilled = 0
        self.order_quantity = 10
        self.order_progress = 0
        
        # UI Buttons
        self.buttons = [
            Button(20, 20, 140, 40, "Hire Worker ($50)", cost=50),
            Button(180, 20, 140, 40, "Speed Up ($30)", cost=30),
            Button(340, 20, 140, 40, "New Toy Type ($100)", cost=100),
            Button(500, 20, 140, 40, "Upgrade Factory ($200)", cost=200),
        ]
        
        # Spawn initial workers
        self.hire_worker()
    
    def hire_worker(self):
        """Spawn a new worker"""
        y = SCREEN_HEIGHT // 2 + random.randint(-40, 40)
        self.workers.append(Worker(random.randint(100, 400), y))
    
    def speed_up_conveyor(self):
        """Increase production speed"""
        self.conveyor_speed *= 1.2
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                
                # Check button clicks
                if self.buttons[0].is_clicked(pos) and self.money >= 50:  # Hire
                    self.money -= 50
                    self.hire_worker()
                elif self.buttons[1].is_clicked(pos) and self.money >= 30:  # Speed
                    self.money -= 30
                    self.speed_up_conveyor()
                elif self.buttons[2].is_clicked(pos) and self.money >= 100:  # New toy
                    self.money -= 100
                    self.current_order = random.choice(list(ToyType))
                    self.order_progress = 0
                elif self.buttons[3].is_clicked(pos) and self.money >= 200:  # Upgrade
                    self.money -= 200
                    self.level += 1
                    self.conveyor_speed += 1.0
    
    def update(self):
        # Spawn new toys
        if random.random() < 0.02 and len(self.toys) < 30:
            self.toys.append(Toy(self.current_order, -20))
        
        # Update toys
        for toy in self.toys[:]:
            toy.update(self.conveyor_speed)
            if toy.is_complete() and toy.x < SCREEN_WIDTH - 50:
                self.money += toy.value
                self.score += toy.value
                self.order_progress += 1
                self.toys.remove(toy)
            elif toy.x > SCREEN_WIDTH + 50:
                self.toys.remove(toy)
        
        # Update workers
        for worker in self.workers:
            worker.update(self.toys)
        
        # Check order completion
        if self.order_progress >= self.order_quantity:
            self.orders_fulfilled += 1
            self.money += 50  # Bonus
            self.current_order = random.choice(list(ToyType))
            self.order_progress = 0
            self.order_quantity = max(10, 10 + self.orders_fulfilled)
        
        # Decrease days
        self.days_until_christmas = max(0, 25 - self.orders_fulfilled // 5)
        
        # Game over condition
        if self.days_until_christmas == 0 and self.order_progress < self.order_quantity:
            self.running = False
    
    def draw(self):
        self.screen.fill(COLOR_BG)
        
        # Draw conveyor belt
        pygame.draw.rect(self.screen, COLOR_CONVEYOR, 
                        (0, SCREEN_HEIGHT // 2 - 30, SCREEN_WIDTH, 60))
        
        # Draw belt pattern
        for i in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(self.screen, (70, 70, 90), 
                           (i, SCREEN_HEIGHT // 2 - 30), 
                           (i, SCREEN_HEIGHT // 2 + 30), 2)
        
        # Draw toys
        for toy in self.toys:
            toy.draw(self.screen)
        
        # Draw workers
        for worker in self.workers:
            worker.draw(self.screen)
        
        # Draw UI
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            is_hovering = button.is_clicked(mouse_pos)
            button.draw(self.screen, FONT_SMALL, is_hovering)
        
        # Draw stats
        stats_y = 80
        money_text = FONT_MEDIUM.render(f"💰 ${self.money}", True, COLOR_MONEY)
        self.screen.blit(money_text, (20, stats_y))
        
        score_text = FONT_MEDIUM.render(f"Score: {self.score}", True, COLOR_TEXT)
        self.screen.blit(score_text, (20, stats_y + 40))
        
        level_text = FONT_MEDIUM.render(f"Level: {self.level}", True, COLOR_TEXT)
        self.screen.blit(level_text, (20, stats_y + 80))
        
        # Draw current order
        order_text = f"Order: {self.order_quantity - self.order_progress} {self.current_order.value['name']}s left"
        order_surf = FONT_SMALL.render(order_text, True, COLOR_TEXT)
        self.screen.blit(order_surf, (SCREEN_WIDTH - 300, 20))
        
        # Draw Christmas countdown
        christmas_text = FONT_SMALL.render(f"Days until Christmas: {self.days_until_christmas}", 
                                          True, COLOR_DANGER if self.days_until_christmas < 5 else COLOR_TEXT)
        self.screen.blit(christmas_text, (SCREEN_WIDTH - 300, 50))
        
        # Draw workers count
        workers_text = FONT_SMALL.render(f"Workers: {len(self.workers)}", True, COLOR_TEXT)
        self.screen.blit(workers_text, (SCREEN_WIDTH - 300, 80))
        
        # Draw speed
        speed_text = FONT_SMALL.render(f"Speed: {self.conveyor_speed:.1f}x", True, COLOR_TEXT)
        self.screen.blit(speed_text, (SCREEN_WIDTH - 300, 110))
        
        pygame.display.flip()
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()

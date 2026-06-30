import random
import tkinter as tk
from dataclasses import dataclass


CELL_SIZE = 24
GRID_WIDTH = 24
GRID_HEIGHT = 18
START_DELAY_MS = 120
MIN_DELAY_MS = 55
SPEED_STEP_MS = 4

BG_COLOR = "#101820"
GRID_COLOR = "#17242f"
SNAKE_HEAD_COLOR = "#7ddf64"
SNAKE_BODY_COLOR = "#39a852"
FOOD_COLOR = "#ff4d5a"
TEXT_COLOR = "#f7f7f2"
MUTED_TEXT_COLOR = "#9fb3c8"


@dataclass(frozen=True)
class Point:
    x: int
    y: int


class SnakeGame:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("贪吃蛇")
        self.root.resizable(False, False)

        self.width = GRID_WIDTH * CELL_SIZE
        self.height = GRID_HEIGHT * CELL_SIZE

        self.score_var = tk.StringVar()
        self.status_var = tk.StringVar()

        self.header = tk.Frame(root, bg=BG_COLOR, padx=12, pady=10)
        self.header.pack(fill=tk.X)

        self.score_label = tk.Label(
            self.header,
            textvariable=self.score_var,
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            font=("Helvetica", 16, "bold"),
        )
        self.score_label.pack(side=tk.LEFT)

        self.status_label = tk.Label(
            self.header,
            textvariable=self.status_var,
            bg=BG_COLOR,
            fg=MUTED_TEXT_COLOR,
            font=("Helvetica", 11),
        )
        self.status_label.pack(side=tk.RIGHT)

        self.canvas = tk.Canvas(
            root,
            width=self.width,
            height=self.height,
            bg=BG_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack()

        self.root.bind("<Up>", lambda _: self.change_direction(Point(0, -1)))
        self.root.bind("<Down>", lambda _: self.change_direction(Point(0, 1)))
        self.root.bind("<Left>", lambda _: self.change_direction(Point(-1, 0)))
        self.root.bind("<Right>", lambda _: self.change_direction(Point(1, 0)))
        self.root.bind("w", lambda _: self.change_direction(Point(0, -1)))
        self.root.bind("s", lambda _: self.change_direction(Point(0, 1)))
        self.root.bind("a", lambda _: self.change_direction(Point(-1, 0)))
        self.root.bind("d", lambda _: self.change_direction(Point(1, 0)))
        self.root.bind("<space>", lambda _: self.toggle_pause())
        self.root.bind("r", lambda _: self.reset())
        self.root.bind("R", lambda _: self.reset())

        self.snake: list[Point] = []
        self.direction = Point(1, 0)
        self.pending_direction = self.direction
        self.food = Point(0, 0)
        self.score = 0
        self.delay_ms = START_DELAY_MS
        self.paused = False
        self.game_over = False
        self.after_id: str | None = None

        self.reset()

    def reset(self) -> None:
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        center = Point(GRID_WIDTH // 2, GRID_HEIGHT // 2)
        self.snake = [
            center,
            Point(center.x - 1, center.y),
            Point(center.x - 2, center.y),
        ]
        self.direction = Point(1, 0)
        self.pending_direction = self.direction
        self.score = 0
        self.delay_ms = START_DELAY_MS
        self.paused = False
        self.game_over = False
        self.food = self.random_food()

        self.update_labels()
        self.draw()
        self.schedule_next_tick()

    def random_food(self) -> Point:
        occupied = set(self.snake)
        free_cells = [
            Point(x, y)
            for x in range(GRID_WIDTH)
            for y in range(GRID_HEIGHT)
            if Point(x, y) not in occupied
        ]
        return random.choice(free_cells)

    def change_direction(self, new_direction: Point) -> None:
        if self.game_over:
            return

        opposite = Point(-self.direction.x, -self.direction.y)
        if new_direction != opposite:
            self.pending_direction = new_direction

    def toggle_pause(self) -> None:
        if self.game_over:
            return

        self.paused = not self.paused
        self.update_labels()
        if not self.paused:
            self.schedule_next_tick()

    def schedule_next_tick(self) -> None:
        if not self.paused and not self.game_over:
            self.after_id = self.root.after(self.delay_ms, self.tick)

    def tick(self) -> None:
        self.after_id = None
        self.direction = self.pending_direction

        head = self.snake[0]
        new_head = Point(head.x + self.direction.x, head.y + self.direction.y)

        if self.hit_wall(new_head) or new_head in self.snake:
            self.end_game()
            return

        self.snake.insert(0, new_head)

        if new_head == self.food:
            self.score += 1
            self.delay_ms = max(MIN_DELAY_MS, self.delay_ms - SPEED_STEP_MS)
            self.food = self.random_food()
        else:
            self.snake.pop()

        self.update_labels()
        self.draw()
        self.schedule_next_tick()

    def hit_wall(self, point: Point) -> bool:
        return (
            point.x < 0
            or point.x >= GRID_WIDTH
            or point.y < 0
            or point.y >= GRID_HEIGHT
        )

    def end_game(self) -> None:
        self.game_over = True
        self.update_labels()
        self.draw()
        self.canvas.create_text(
            self.width // 2,
            self.height // 2,
            text="游戏结束",
            fill=TEXT_COLOR,
            font=("Helvetica", 32, "bold"),
        )
        self.canvas.create_text(
            self.width // 2,
            self.height // 2 + 42,
            text="按 R 重新开始",
            fill=MUTED_TEXT_COLOR,
            font=("Helvetica", 15),
        )

    def update_labels(self) -> None:
        self.score_var.set(f"得分: {self.score}")
        if self.game_over:
            self.status_var.set("R 重新开始")
        elif self.paused:
            self.status_var.set("已暂停 | 空格继续")
        else:
            self.status_var.set("方向键/WASD 移动 | 空格暂停")

    def draw(self) -> None:
        self.canvas.delete("all")
        self.draw_grid()
        self.draw_food()
        self.draw_snake()

    def draw_grid(self) -> None:
        for x in range(0, self.width, CELL_SIZE):
            self.canvas.create_line(x, 0, x, self.height, fill=GRID_COLOR)
        for y in range(0, self.height, CELL_SIZE):
            self.canvas.create_line(0, y, self.width, y, fill=GRID_COLOR)

    def draw_food(self) -> None:
        pad = 4
        self.draw_cell(self.food, FOOD_COLOR, pad)

    def draw_snake(self) -> None:
        for index, point in enumerate(self.snake):
            color = SNAKE_HEAD_COLOR if index == 0 else SNAKE_BODY_COLOR
            self.draw_cell(point, color, 2)

    def draw_cell(self, point: Point, color: str, padding: int) -> None:
        x1 = point.x * CELL_SIZE + padding
        y1 = point.y * CELL_SIZE + padding
        x2 = (point.x + 1) * CELL_SIZE - padding
        y2 = (point.y + 1) * CELL_SIZE - padding
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")


def main() -> None:
    root = tk.Tk()
    SnakeGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()

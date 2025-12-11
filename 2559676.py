# student_last_3 = 676
import random
from time import sleep
from graphix import Circle, GraphixObject, Point, Text, Window, Polygon, Rectangle

PATCH_SIZE = 100

type Tile = list[GraphixObject]


# region inputs
def get_size_input() -> int:
    while True:
        num = input("Enter patch size (5, 7, 9): ")
        if not num.isdigit():
            print("Invalid input, please enter a single whole number")
            continue

        num = int(num)

        if num not in [5, 7, 9]:
            print("Invalid number, please enter either '5', '7', '9'")
            continue

        return num


def get_colour_input() -> str:
    valid_colours: list[str] = ["red", "green", "blue", "pink", "orange", "purple"]

    while True:
        colour: str = input("Enter patch colour: ").lower()

        if colour in valid_colours:
            return colour

        print(f"Invalid input, please enter a valid colour {valid_colours}")


def get_colour_inputs() -> list[str]:
    colours: list[str] = []

    while len(colours) < 3:
        colour = get_colour_input()
        if colour in colours:
            print("Colour already present, please choose a unique colour")
            continue

        colours.append(colour)

    return colours


def get_shuffle_inputs() -> int:
    while True:
        num = input("How many shuffle moves should be made to shuffle the tiles: ")
        if not num.isdigit():
            print("Invalid input, please enter a whole number")
            continue

        num = int(num)

        return num


# region plain
def draw_plain(win: Window, x: int, y: int, colour: str) -> list[Rectangle]:
    rect = Rectangle(Point(x, y), Point(x + PATCH_SIZE, y + PATCH_SIZE))
    rect.fill_colour = colour
    rect.outline_colour = colour
    rect.draw(win)
    return [rect]


# region penultimate patch
def patch_penultimate_shape_points(x: int, y: int) -> list[Point]:
    points = [(0, 10), (10, 0), (20, 10), (20, 20), (10, 10), (0, 20)]

    return [Point(x + dx, y + dy) for dx, dy in points]


def patch_penultimate_shape(x: int, y: int, colour: str, fill: bool) -> Polygon:
    poly = Polygon(patch_penultimate_shape_points(x, y))
    poly.outline_colour = colour
    if fill:
        poly.fill_colour = colour
    return poly


def patch_penultimate_line_points(x: int, y: int) -> list[Point]:
    points: list[tuple[int, int]] = [
        # top path
        (0, 10),
        (10, 0),
        (20, 10),
        (30, 0),
        (40, 10),
        (50, 0),
        (60, 10),
        (70, 0),
        (80, 10),
        (90, 0),
        (100, 10),
        # return path
        (100, 20),
        (90, 10),
        (80, 20),
        (70, 10),
        (60, 20),
        (50, 10),
        (40, 20),
        (30, 10),
        (20, 20),
        (10, 10),
        (0, 20),
    ]

    return [Point(x + dx, y + dy) for dx, dy in points]


def patch_penultimate_line(x: int, y: int, colour: str) -> Polygon:
    poly = Polygon(patch_penultimate_line_points(x, y))
    poly.outline_colour = colour
    poly.fill_colour = colour
    return poly


def is_fill(y_end: int, i: int, j: int) -> bool:
    is_border_row = i in (0, y_end)
    is_middle_allowed = j not in (1, 3)

    return is_border_row or is_middle_allowed


def draw_patch_penultimate(win: Window, x0: int, y0: int, colour: str):
    step = 20
    rows = PATCH_SIZE // step
    y_fill_end = rows - 1
    x_positions = range(x0, x0 + PATCH_SIZE, step)

    patch_objs: list[GraphixObject] = []

    line = patch_penultimate_line(x0, y0, colour)
    line.draw(win)
    patch_objs.append(line)

    for i, y in enumerate(range(y0 + step, y0 + PATCH_SIZE - step, step)):
        for j, x in enumerate(x_positions):
            poly = patch_penultimate_shape(x, y, colour, is_fill(y_fill_end, i, j))
            poly.draw(win)
            patch_objs.append(poly)

    line = patch_penultimate_line(x0, y0 + PATCH_SIZE - step, colour)
    line.draw(win)
    patch_objs.append(line)

    return patch_objs


# region final patch
def draw_patch_final(win: Window, x: int, y: int, colour: str):
    patch_objs: list[Circle] = []

    for i in range(10, 101, 10):
        circle = Circle(Point(50 + x, (100 - i // 2) + y), i // 2)
        circle.outline_colour = colour
        circle.draw(win)
        patch_objs.append(circle)

    return patch_objs


# region antepenultimate
def window(size: int) -> Window:
    return Window("up2559676", PATCH_SIZE * size, PATCH_SIZE * size)


def patch_colour(x: int, y: int, size: int, colours: list[str]) -> str:
    total = x + y
    if total < size - PATCH_SIZE:
        return colours[0]
    if total >= size:
        return colours[2]
    return colours[1]


def draw_patch(win: Window, x: int, y: int, colour: str) -> Tile:
    is_left = x == 0
    is_last = x == win.width - PATCH_SIZE
    is_middle = x == PATCH_SIZE * 2 and y >= PATCH_SIZE * 2
    is_corner = is_left and y == win.height - PATCH_SIZE

    if is_last or is_middle or is_corner:
        return list(draw_patch_final(win, x, y, colour))
    elif is_left or y == 0:
        return draw_patch_penultimate(win, x, y, colour)
    else:
        return list(draw_plain(win, x, y, colour))


def draw_patchs(win: Window, colours: list[str]) -> list[Tile]:
    win_objs: list[Tile] = []

    width = win.width
    height = win.height

    for y in range(0, height, PATCH_SIZE):
        for x in range(0, width, PATCH_SIZE):
            patch_objs = draw_patch(win, x, y, patch_colour(x, y, width, colours))
            win_objs.append(patch_objs)

    return win_objs


# region sliding puzzle game
def undraw_last(tiles: list[Tile]):
    last_tile = tiles[-1]
    for obj in last_tile:
        obj.undraw()
    tiles[-1].clear()


def find_neighbours(size: int, index: int) -> list[int]:
    neighbours: list[int] = []

    row = index // size
    col = index % size

    if row > 0:
        neighbours.append(index - size)

    if row < size - 1:
        neighbours.append(index + size)

    if col > 0:
        neighbours.append(index - 1)

    if col < size - 1:
        neighbours.append(index + 1)

    return neighbours


def compute_direction(size: int, from_index: int, to_index: int) -> tuple[int, int]:
    diff = to_index - from_index

    if diff == -size:
        return (-1, 0)
    if diff == size:
        return (1, 0)
    if diff == -1:
        return (0, -1)
    if diff == 1:
        return (0, 1)

    raise ValueError("Indices are not neighbours")


def animate_move(tile: Tile, dr: int, dc: int, *, step: int = 5) -> None:
    frames = 100 // step

    # Normalise direction
    step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
    step_c = 0 if dc == 0 else (1 if dc > 0 else -1)

    for _ in range(frames):
        for obj in tile:
            obj.move(step_c * step, step_r * step)
        sleep(1 / frames)


def shuffle_tile(tiles: list[Tile], size: int, blank_index: int) -> int:
    options = find_neighbours(size, blank_index)
    move_index = random.choice(options)

    dr, dc = compute_direction(size, move_index, blank_index)
    animate_move(tiles[move_index], dr, dc)

    tiles[blank_index], tiles[move_index] = tiles[move_index], tiles[blank_index]
    return move_index


def shuffle_tiles(tiles: list[Tile], size: int, blank_pos: int, moves: int) -> int:
    for _ in range(moves):
        blank_pos = shuffle_tile(tiles, size, blank_pos)
    return blank_pos


def get_clicked_tile_index(size: int, mouse: Point) -> int:
    row = int(mouse.y // 100)
    col = int(mouse.x // 100)

    return row * size + col


def play_sliding_puzzle(
    win: Window,
    size: int,
    colours: list[str],
    original_sig: str,
    tiles: list[Tile],
    blank_index: int,
):
    while True:
        mouse = win.get_mouse()
        clicked_index = get_clicked_tile_index(size, mouse)

        neighbours = find_neighbours(size, clicked_index)
        if blank_index not in neighbours:
            continue

        dr, dc = compute_direction(size, clicked_index, blank_index)
        animate_move(tiles[clicked_index], dr, dc)

        tiles[blank_index], tiles[clicked_index] = (
            tiles[clicked_index],
            tiles[blank_index],
        )

        blank_index = clicked_index

        if is_solved(colours, original_sig, tiles):
            return


def tile_signiture(tiles: list[Tile], colours: list[str]) -> str:
    signature_string = ""

    for tile in tiles:
        if len(tile) == 0:
            signature_string += " "
            continue

        child_obj = tile[0]
        # Design Index (0-5)
        # 0: Rect Solid, 1: Rect Outline
        # 2: Circ Solid, 3: Circ Outline
        # 4: Line Solid, 5: Line Outline

        type_idx = 0
        if isinstance(child_obj, Rectangle):
            type_idx = 0 if child_obj.fill_colour else 1
        elif isinstance(child_obj, Circle):
            type_idx = 2 if child_obj.fill_colour else 3
        elif isinstance(child_obj, Polygon):
            type_idx = 4 if child_obj.fill_colour else 5
        else:
            raise ValueError(f"Invalid tile: {tile}")

        # Color Index (0-2)
        color_idx = colours.index(child_obj.outline_colour)

        # Convert idxs into a ASCII Character
        unique_id = (type_idx * 3) + color_idx
        signature_string += chr(65 + unique_id)

    return signature_string


def is_solved(colours: list[str], original_sig: str, tiles: list[Tile]) -> bool:
    return original_sig[:-1] == tile_signiture(tiles[:-1], colours)


def ask_play_again(win: Window) -> bool:
    rect = Rectangle(Point(0, 0), Point(win.width, win.height))
    rect.fill_colour = "black"
    rect.draw(win)

    centre_x = win.width // 2
    centre_y = win.height // 2

    msg = Text(Point(centre_x, centre_y), "Well done!\nPlay again? (y/n)")
    msg.fill_colour = "white"
    msg.size = 32
    msg.draw(win)

    while True:
        key = win.get_key().lower()

        if key == "y":
            msg.undraw()
            rect.undraw()
            return True
        if key == "n":
            msg.undraw()
            rect.undraw()
            return False


def main():
    size = get_size_input()
    colours = get_colour_inputs()

    win = window(size)

    tiles: list[Tile] = draw_patchs(win, colours)
    original_signiture = tile_signiture(tiles, colours)

    win.get_mouse()

    # region Challenge
    undraw_last(tiles)

    while True:
        num_shuffle = get_shuffle_inputs()

        blank_index = shuffle_tiles(tiles, size, (size**2 - 1), num_shuffle)
        play_sliding_puzzle(win, size, colours, original_signiture, tiles, blank_index)
        if not ask_play_again(win):
            break


main()

import pygame
import sys
import enum
import abc
import random


class PlayerType(abc.ABC):
    @abc.abstractmethod
    def move_made(self):
        pass


class HumanPlayer(PlayerType):
    def __init__(self):
        self._move = False
        self.state = self.state_1
        self.start_pos = None
        self.end_pos = None

    def reset_data(self):
        self._move = False
        self.state = self.state_1
        self.start_pos = None
        self.end_pos = None

    def move_made(self):
        if not self._move:
            return None
        else:
            return True

    def on_event(self, event, logic, graphics, screen, player):
        self.state(event, logic, graphics, screen, player)

    def state_1(self, event, logic, graphics, screen, player):
        if event.type == pygame.MOUSEBUTTONUP:
            mouse_click = pygame.mouse.get_pos()
            if graphics.rect_at(mouse_click):
                self.start_pos = graphics.rect_at(mouse_click)
                if logic.player_owns_square(player, self.start_pos):
                    self.state = self.state_2
        
    def state_2(self, event, logic, graphics, screen, player):
        graphics.highlight_piece(screen, self.start_pos, logic.is_king(self.start_pos, player), player)
        if event.type == pygame.MOUSEBUTTONUP:
            mouse_click = pygame.mouse.get_pos()
            if graphics.rect_at(mouse_click) is not None:
                board_pos = graphics.rect_at(mouse_click)
                if self.start_pos == board_pos:
                    self.state = self.state_1
                if logic.is_legal(self.start_pos, board_pos) and not self.state == self.state_1:
                    self.end_pos = board_pos
                    logic.perform_move(self.start_pos, self.end_pos)

                    if logic.check_for_jump(self.end_pos) and logic.take_made:
                        self.start_pos = self.end_pos
                        self.state = self.jump_state
                    else:
                        self._move = True

    def jump_state(self, event, logic, graphics, screen, player):
        graphics.highlight_piece(screen, self.start_pos, logic.is_king(self.start_pos, player), player)
        if event.type == pygame.MOUSEBUTTONUP:
            mouse_click = pygame.mouse.get_pos()
            board_pos = graphics.rect_at(mouse_click)
            if graphics.rect_at(mouse_click) is not None:
                board_pos = graphics.rect_at(mouse_click)
            if logic.is_legal(self.start_pos, board_pos):
                self.end_pos = board_pos
                logic.perform_move(self.start_pos, self.end_pos)
                if logic.check_for_jump(self.end_pos) and logic.take_made:
                    self.start_pos = self.end_pos
                    self.state = self.jump_state
                else:
                    self._move = True


class RandomPlayer(PlayerType):
    def __init__(self):
        self._move_made = False
        self.state = self.state_1
        self._legal_moves = None
        self._move = None
        self._start_pos = None
        self._end_pos = None

    def move_made(self):
        if self._move:
            return self._move_made

    def begin_move(self, logic, graphics, screen, player):
        self.state(logic, graphics, screen, player)

    def state_1(self, logic, graphics, screen, player):
        self._legal_moves = logic.get_moves(player)
        number = random.randint(0, len(self._legal_moves) - 1)
        self._move = (self._legal_moves[number])
        self._start_pos = self._move[0]
        self._end_pos = self._move[1]
        self.state = self.state_2

    def state_2(self, logic, graphics, screen, player):
        graphics.highlight_piece(player, self._move[0], logic.is_king(self._move[0], player), screen)
        logic.check_for_take(self._start_pos, self._end_pos)
        logic.perform_move(self._start_pos, self._end_pos)
        self._move_made = True

    def jump_state(self, logic, graphics, screen, player):
        pass

    def reset_data(self):
        self._move_made = False
        self.state = self.state_1
        self._legal_moves = None
        self._move = None
        self._start_pos = None
        self._end_pos = None


class MiniMaxPlayer(PlayerType):
    def move_made(self):
        pass


class CellValue(enum.Enum):
    EMPTY = 0
    BLACK = 1
    RED = 2
    INVALID = 3
    BLACK_KING = 4
    RED_KING = 5


class Player(enum.Enum):
    BLACK = 0
    RED = 1


class PlayerRole(enum.Enum):
    HUMAN = 0
    AI = 1


class GraphicalBoard:
    def __init__(self):
        cell_size = 111
        self.img_background = pygame.image.load('graphics/game_board.png')
        self.squares = {}
        self.img_black_normal = pygame.image.load('graphics/black_normal.png')
        self.img_black_normal_selected = pygame.image.load('graphics/black_normal_selected.png')
        self.img_black_king = pygame.image.load('graphics/black_king.png')
        self.img_red_normal = pygame.image.load('graphics/red_normal.png')
        self.img_red_king = pygame.image.load('graphics/red_king.png')

        # Graphical board rectangles
        img_width, img_height = self.img_red_normal.get_size()
        shift_x = (cell_size - img_width) / 2
        shift_y = (cell_size - img_height) / 2
        for y in range(8):
            top_pos = 2 + y * cell_size + shift_y
            for x in range(8):
                left_pos = 2 + x * cell_size + shift_x
                if x % 2 != y % 2:
                    space = pygame.Rect(left_pos, top_pos, cell_size, cell_size)
                    self.squares[(x, y)] = space

    # If the given permission collides with a rectangle, return the position of the rectangle.
    def rect_at(self, screen_pos):
        for pos, square in self.squares.items():
            if square.collidepoint(screen_pos):
                return pos
        return None

    def draw_pieces(self, screen, logical_board):
        for pos, square_graphic in self.squares.items():
            square_logic = logical_board.value_at(pos)
            img = None
            if square_logic == CellValue.BLACK:
                img = self.img_black_normal
            elif square_logic == CellValue.RED:
                img = self.img_red_normal
            elif square_logic == CellValue.BLACK_KING:
                img = self.img_black_king
            elif square_logic == CellValue.RED_KING:
                img = self.img_red_king
            if img is not None:
                screen.blit(img, square_graphic)

    # Highlight a piece if a player has one selected
    def highlight_piece(self, screen, pos, is_king, player):
        if player == Player.BLACK:
            if is_king:
                img = pygame.image.load('graphics/black_king_selected.png')
            else:
                img = pygame.image.load('graphics/black_normal_selected.png')
            square_graphic = self.squares[pos]
            screen.blit(img, square_graphic)
        else:
            if is_king:
                img = pygame.image.load('graphics/red_king_selected.png')
            else:
                img = pygame.image.load('graphics/red_normal_selected.png')
            square_graphic = self.squares[pos]
            screen.blit(img, square_graphic)

    def draw_board(self, screen):
        screen.blit(self.img_background, (0, 0))


class GameLogic:
    def __init__(self):
        self.graphics = GraphicalBoard()
        self.board = []
        self.player_turn = Player.BLACK
        self.take_at = None
        self.take_made = False
        self.take_position = None

        # Logical Board
        for y in range(8):
            row = []
            for x in range(8):
                if x % 2 != y % 2:
                    if y < 3:
                        row.append(CellValue.BLACK)
                    elif y < 5:
                        row.append(CellValue.EMPTY)
                    else:
                        row.append(CellValue.RED)
                else:
                    row.append(CellValue.INVALID)
            self.board.append(row)

    def player_owns_square(self, player, pos):
        if player == Player.BLACK:
            if self.value_at(pos) == CellValue.BLACK or self.value_at(pos) == CellValue.BLACK_KING:
                return True
        else:
            if self.value_at(pos) == CellValue.RED or self.value_at(pos) == CellValue.RED_KING:
                return True
        return False

    # Get the value of a position on the board
    def value_at(self, pos):
        if pos is not None:
            x, y = pos
            if y > 7 or y < 0:
                return None
            if x > 7 or x < 0:
                return None
            return self.board[y][x]

    # Set the value at a position on the board
    def set_value_at(self, pos, value):
        if pos is not None:
            x, y = pos
            self.board[y][x] = value

    # Check if a piece at a specific position is a king piece
    def is_king(self, pos, player):
        if player == Player.BLACK:
            if self.value_at(pos) == CellValue.BLACK_KING:
                return True
        else:
            if self.value_at(pos) == CellValue.RED_KING:
                return True
        return False

    # Make a piece a king piece if the piece has moved to the other end of the board.
    def make_king(self, end_pos):
        x_1, y_1 = end_pos
        if self.player_turn == Player.BLACK:
            if y_1 >= 7:
                self.set_value_at(end_pos, CellValue.BLACK_KING)
        if self.player_turn == Player.RED:
            if y_1 <= 0:
                self.set_value_at(end_pos, CellValue.RED_KING)

    # Return the player who turn it is next
    def next_player(self):
        if self.player_turn == Player.BLACK:
            return Player.RED
        else:
            return Player.BLACK

    def change_player(self, player):
        self.player_turn = player

    # Return the direction that each player is moving in the y-axis
    def player_direction(self, player):
        if player == Player.BLACK:
            return 1
        else:
            return -1

    def check_for_take(self, start_pos, end_pos):
        x_0, y_0 = start_pos
        x_1, y_1 = end_pos
        dy = y_1 - y_0
        front_right = (x_0 + 1, y_0 + 1)
        front_left = (x_0 - 1, y_0 + 1)
        back_right = (x_0 + 1, y_0 - 1)
        back_left = (x_0 - 1, y_0 - 1)
        if dy == 2 or dy == -2:
            if x_1 > x_0 and y_1 > y_0:
                if self.player_owns_square(self.next_player(), front_right):
                    self.take_at = front_right
                    return self.take_at
            if x_1 < x_0 and y_1 > y_0:
                if self.player_owns_square(self.next_player(), front_left):
                    self.take_at = front_left
                    return self.take_at
            if x_1 > x_0 and y_1 < y_0:
                if self.player_owns_square(self.next_player(), back_right):
                    self.take_at = back_right
                    return self.take_at
            if x_1 < x_0 and y_1 < y_0:
                if self.player_owns_square(self.next_player(), back_left):
                    self.take_at = back_left
                    return self.take_at
        return None

    # Check that the desired move is a legal one
    def is_legal(self, start_pos, end_pos):
        x_0, y_0 = start_pos
        x_1, y_1 = end_pos
        dx = x_1 - x_0
        dy = y_1 - y_0
        if x_1 > 7 or x_1 < 0:
            return False
        if y_1 > 7 or y_1 < 0:
            return False
        self.take_at = None
        if start_pos == end_pos:
            return False
        if self.player_owns_square(self.player_turn, end_pos) or self.player_owns_square(self.next_player(), end_pos):
            return False
        if self.value_at(start_pos) == CellValue.BLACK\
                or self.value_at(start_pos) == CellValue.RED:
            if dy * self.player_direction(self.player_turn) < 0:
                return False
        if dy > 2 or dy < -2:
            return False
        if self.check_for_take(start_pos, end_pos):
            return True
        if dx > 1 or dx < -1:
            return False
        if dy > 1 or dy < -1:
            return False
        return True

    def perform_move(self, start_pos, end_pos):
        self.set_value_at(end_pos, self.value_at(start_pos))
        self.set_value_at(start_pos, CellValue.EMPTY)
        self.make_king(end_pos)

        if self.take_at is not None:
            self.set_value_at(self.take_at, CellValue.EMPTY)
            self.set_take_made(True)
            self.take_position = end_pos

    # Check if a jump can be made after a take
    def check_for_jump(self, start_pos):
        x_0, y_0 = start_pos
        front_right = (x_0 + 2, y_0 + 2)
        front_left = (x_0 - 2, y_0 + 2)
        back_right = (x_0 + 2, y_0 - 2)
        back_left = (x_0 - 2, y_0 - 2)

        if self.is_legal(start_pos, front_right):
            if self.check_for_take(start_pos, front_right):
                return True
        if self.is_legal(start_pos, front_left):
            if self.check_for_take(start_pos, front_left):
                return True
        if self.is_legal(start_pos, back_right):
            if self.check_for_take(start_pos, back_right):
                return True
        if self.is_legal(start_pos, back_left):
            if self.check_for_take(start_pos, back_left):
                return True
        return False

    def set_take_made(self, is_take_made):
        self.take_made = is_take_made

    def get_moves(self, player):
        legal_moves = []
        y_index = 0
        x_index = 0
        for row in self.board:
            for space in row:

                front_right = (x_index + 1, y_index + 1)
                front_left = (x_index - 1, y_index + 1)
                back_right = (x_index + 1, y_index - 1)
                back_left = (x_index - 1, y_index - 1)

                take_front_right = (x_index + 2, y_index + 2)
                take_front_left = (x_index - 2, y_index + 2)
                take_back_right = (x_index + 2, y_index - 2)
                take_back_left = (x_index - 2, y_index - 2)

                if player == Player.RED:
                    if space == CellValue.RED or space == CellValue.RED_KING:
                        start_pos = (x_index, y_index)
                        if self.is_legal(start_pos, front_right):
                            legal_moves.append((start_pos, front_right))
                        if self.is_legal(start_pos, front_left):
                            legal_moves.append((start_pos, front_left))
                        if self.is_legal(start_pos, back_right):
                            legal_moves.append((start_pos, back_right))
                        if self.is_legal(start_pos, back_left):
                            legal_moves.append((start_pos, back_left))

                        if self.is_legal(start_pos, take_front_right):
                            legal_moves.append((start_pos, take_front_right))
                        if self.is_legal(start_pos, take_front_left):
                            legal_moves.append((start_pos, take_front_left))
                        if self.is_legal(start_pos, take_back_right):
                            legal_moves.append((start_pos, take_back_right))
                        if self.is_legal(start_pos, take_back_left):
                            legal_moves.append((start_pos, take_back_left))
                else:
                    if space == CellValue.BLACK or space == CellValue.BLACK_KING:
                        start_pos = (x_index, y_index)
                        if self.is_legal(start_pos, front_right):
                            legal_moves.append((start_pos, front_right))
                        if self.is_legal(start_pos, front_left):
                            legal_moves.append((start_pos, front_left))
                        if self.is_legal(start_pos, back_right):
                            legal_moves.append((start_pos, back_right))
                        if self.is_legal(start_pos, back_left):
                            legal_moves.append((start_pos, back_left))

                        if self.is_legal(start_pos, take_front_right):
                            legal_moves.append((start_pos, take_front_right))
                        if self.is_legal(start_pos, take_front_left):
                            legal_moves.append((start_pos, take_front_left))
                        if self.is_legal(start_pos, take_back_right):
                            legal_moves.append((start_pos, take_back_right))
                        if self.is_legal(start_pos, take_back_left):
                            legal_moves.append((start_pos, take_back_left))

                x_index += 1
            y_index += 1
            x_index = 0
        return legal_moves

    def game_over(self):
        black_pieces = 0
        red_pieces = 0
        for rows in self.board:
            for space in rows:
                if space == CellValue.BLACK or space == CellValue.BLACK_KING:
                    black_pieces += 1
        for rows in self.board:
            for space in rows:
                if space == CellValue.RED or space == CellValue.RED_KING:
                    red_pieces += 1
        if black_pieces == 0 or red_pieces == 0:
            pass


class GameState:
    def __init__(self):
        self.player_1_role = PlayerRole.AI
        self.player_2_role = PlayerRole.HUMAN
        self.human_player = HumanPlayer()
        self.human_player_2 = HumanPlayer()
        self.ai_player_1 = RandomPlayer()
        self.ai_player_2 = RandomPlayer()
        self.resolution = 900
        self.cell_size = 111
        self.screen = pygame.display.set_mode((self.resolution, self.resolution))
        self.logic = GameLogic()
        self.graphics = GraphicalBoard()
        self.state = self.player_1_turn

    # State 1 for the player turn (Player has to select a piece)
    def player_1_turn(self, event):
        if self.player_1_role == PlayerRole.HUMAN:
            self.human_player.on_event(event, self.logic, self.graphics, self.screen, self.logic.player_turn)
            move_made = self.human_player.move_made()
            if move_made:
                self.human_player.reset_data()
                self.logic.set_take_made(False)
                self.logic.change_player(self.logic.next_player())
                self.state = self.player_2_turn
        else:
            self.ai_player_1.begin_move(self.logic, self.graphics, self.logic.player_turn, self.screen)
            move_made = self.ai_player_1.move_made()
            if move_made:
                self.logic.set_take_made(False)
                self.logic.change_player(self.logic.next_player())
                self.state = self.player_2_turn
                self.ai_player_1.reset_data()

    def player_2_turn(self, event):
        if self.player_2_role == PlayerRole.HUMAN:
            self.human_player_2.on_event(event, self.logic, self.graphics, self.screen, self.logic.player_turn)
            move_made = self.human_player_2.move_made()
            if move_made:
                self.human_player_2.reset_data()
                self.logic.set_take_made(False)
                self.logic.change_player(self.logic.next_player())
                self.state = self.player_1_turn
        else:
            self.ai_player_2.begin_move(self.logic, self.graphics, self.logic.player_turn, self.screen)
            move_made = self.ai_player_2.move_made()
            if move_made:
                self.logic.set_take_made(False)
                self.logic.change_player(self.logic.next_player())
                self.state = self.player_1_turn
                self.ai_player_2.reset_data()


def main():
    pygame.init()
    clock = pygame.time.Clock()
    game = GameState()
    graphics = GraphicalBoard()
    screen_update = pygame.USEREVENT
    pygame.time.set_timer(screen_update, 100)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            graphics.draw_board(game.screen)
            graphics.draw_pieces(game.screen, game.logic)
            game.state(event)

        pygame.display.update()
        clock.tick(60)


if __name__ == '__main__':
    main()

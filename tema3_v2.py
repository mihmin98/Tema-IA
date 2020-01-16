#!/usr/bin/env python3

from operator import add as op_add
import copy
import argparse
import time
import psutil
import memory_profiler
import pygame
import sys

parser = argparse.ArgumentParser()
parser.add_argument('-gui', default=False, required=False, action='store_true')
parser.add_argument('-diff', default=2)


def get_enemy(player):
    if player == 'a':
        return 'n'
    return 'a'


def draw_board(display, board):
    width_grid = height_grid = 100
    rects = []

    for i in range(8):
        for j in range(8):
            rect = pygame.Rect(i * (width_grid+1), j *
                               (height_grid+1), width_grid, height_grid)
            rects.append(rect)

            pygame.draw.rect(display, (255, 255, 255), rect)

            val = board.get_val(i, j)
            if val == 'a':
                pygame.draw.circle(display, (0, 0, 0),
                                   rect.center, width_grid // 2 - 2, 4)
            elif val == 'n':
                pygame.draw.circle(display, (0, 0, 0),
                                   rect.center, width_grid // 2 - 2)

    pygame.display.flip()
    return rects


class Game:
    MIN_PLAYER = None
    MAX_PLAYER = None

    def __init__(self):
        self.board = self.new_board()
        self.set_val(3, 3, 'a')
        self.set_val(3, 4, 'n')
        self.set_val(4, 3, 'n')
        self.set_val(4, 4, 'a')

    def __str__(self):
        string = '   a b c d e f g h\n'
        string += '  ' + '-' * 16 + '\n'
        for i in range(8):
            string += str(i) + ' |'
            for j in range(8):
                string += self.get_val(i, j) + ' '
            string += '\n'

        return string

    def new_board(self):
        return ['#'] * 64

    def get_val(self, i, j):
        if 0 <= i <= 7 and 0 <= j <= 7:
            return self.board[i*8 + j]
        return None

    def set_val(self, i, j, val):
        if 0 <= i <= 7 and 0 <= j <= 7:
            self.board[i*8 + j] = val
        else:
            return None

    def get_distance(self, pos_1, pos_2):
        # Line
        if pos_1[0] == pos_2[0]:
            return abs(pos_2[1] - pos_1[1])

        # Column
        if pos_1[1] == pos_2[1]:
            return abs(pos_2[0] - pos_1[0])

        # Diagonal; Does not matter what subtraction we do
        return abs(pos_2[0] - pos_1[0])

    def get_moves(self, player):
        '''
        Returns a list of all the valid moves
        '''
        enemy_val = get_enemy(player)

        # A valid move must be adjacent to an enemy piece

        # Get all enemies
        enemies = []
        for i in range(8):
            for j in range(8):
                if self.get_val(i, j) == enemy_val:
                    enemies.append((i, j))

        # For all enemies get empty adjacent positions
        possible_moves = []
        for enemy in enemies:
            i = enemy[0]
            j = enemy[1]
            # Top Left
            if self.get_val(i-1, j-1) == '#' and (i-1, j-1) not in possible_moves:
                possible_moves.append((i-1, j-1))
            # Top
            if self.get_val(i-1, j) == '#' and (i-1, j) not in possible_moves:
                possible_moves.append((i-1, j))
            # Top Right
            if self.get_val(i-1, j+1) == '#' and (i-1, j+1) not in possible_moves:
                possible_moves.append((i-1, j+1))
            # Left
            if self.get_val(i, j-1) == '#' and (i, j-1) not in possible_moves:
                possible_moves.append((i, j-1))
            # Right
            if self.get_val(i, j+1) == '#' and (i, j+1) not in possible_moves:
                possible_moves.append((i, j+1))
            # Bot Left
            if self.get_val(i+1, j-1) == '#' and (i+1, j-1) not in possible_moves:
                possible_moves.append((i+1, j-1))
            # Bot
            if self.get_val(i+1, j) == '#' and (i+1, j) not in possible_moves:
                possible_moves.append((i+1, j))
            # Bot Right
            if self.get_val(i+1, j+1) == '#' and (i+1, j+1) not in possible_moves:
                possible_moves.append((i+1, j+1))

        # Check if moves are valid
        valid_moves = []
        for move in possible_moves:
            valid, junk = self.valid_move(move, player)
            if valid and move not in valid_moves:
                valid_moves.append(move)

        return valid_moves

    def valid_move(self, piece, player):
        '''
        Returns True if a piece can be placed on the given position.
        Also if i can be placed, returns the position of the furthest valid ally (to form a line)
        '''
        # Move on all 8 axis
        # If you find an empty space or reach the end of the board, then abandon that axis
        # I think this should look like bf
        # Maybe this function should return the farthest valid allied piece, if there is any
        # Tuple: (pos, direction, enemies)
        enemy = get_enemy(player)
        max_piece = None
        max_enemies = 0
        valid = False
        queue = []
        # Top Left
        queue.append((piece, (-1, -1), 0))
        # Top
        queue.append((piece, (-1, 0), 0))
        # Top Right
        queue.append((piece, (-1, 1), 0))
        # Left
        queue.append((piece, (0, -1), 0))
        # Right
        queue.append((piece, (0, 1), 0))
        # Bot Left
        queue.append((piece, (1, -1), 0))
        # Bot
        queue.append((piece, (1, 0), 0))
        # Bot Right
        queue.append((piece, (1, 1), 0))

        while len(queue) > 0:
            curr = queue.pop(0)
            curr_pos = curr[0]
            curr_enemies = curr[2]
            # If we are on the starting piece, then increment with direction and continue
            if curr_pos == piece:
                curr_pos = tuple(map(op_add, curr[0], curr[1]))

            curr_pos_val = self.get_val(curr_pos[0], curr_pos[1])

            # Check if out of bounds or empty space
            if curr_pos_val == None or curr_pos_val == '#':
                continue

            # Check if curr_pos is a player piece, if it is make the move valid and check if that is the best distance
            elif curr_pos_val == player and curr_enemies > 0:
                valid = True
                if max_piece == None or curr_enemies > max_enemies:
                    max_piece = curr_pos
                    max_enemies = curr_enemies

            # Check if curr_pos is an enemy piece, if it is increment the position
            elif curr_pos_val == enemy:
                curr_enemies += 1
                new_pos = tuple(map(op_add, curr[0], curr[1]))
                queue.append((new_pos, curr[1], curr_enemies))

        return valid, max_piece

    def move(self, start, dest, player):
        '''
        Sets all the pieces in a line from start to dest to the value of the start
        '''
        #player = self.get_val(start[0], start[1])
        curr_pos = start

        step_i = 1
        if start[0] > dest[0]:
            step_i = -1
        elif start[0] == dest[0]:
            step_i = 0

        step_j = 1
        if start[1] > dest[1]:
            step_j = -1
        elif start[1] == dest[1]:
            step_j = 0

        while(curr_pos != dest):
            #curr_pos[0] += step_i
            #curr_pos[1] += step_j
            self.set_val(curr_pos[0], curr_pos[1], player)
            curr_pos = tuple(map(op_add, curr_pos, (step_i, step_j)))

        self.set_val(curr_pos[0], curr_pos[1], player)

    def final(self):
        '''
        If there are no more moves for both players, returns True. Else returns False
        '''
        return len(self.get_moves('a')) == 0 and len(self.get_moves('n')) == 0

    def count_pieces(self):
        '''
        Returns the number of white and black pieces
        '''
        num_a = 0
        num_n = 0
        for i in range(8):
            for j in range(8):
                val = self.get_val(i, j)
                if val == 'a':
                    num_a += 1
                elif val == 'n':
                    num_n += 1

        return num_a, num_n

    def get_winner(self):
        '''
        Returns the winner. If the game has not ended it returns None
        '''
        if not self.final():
            return None
        num_a, num_n = self.count_pieces()

        if num_a > num_n:
            return 'a'
        elif num_n > num_a:
            return 'n'
        else:
            return 'tie'

    def estimate_score(self, depth):
        final = self.final()
        score_max = 0
        score_min = 0
        if Game.MAX_PLAYER == 'a':
            score_max, score_min = self.count_pieces()
        else:
            score_min, score_max = self.count_pieces()

        # If game has ended
        if final:
            # If MAX wins
            if score_max > score_min:
                return 100 + depth
            # If MIN wins
            elif score_min > score_max:
                return -100 + depth
            # If TIE
            else:
                return 0
        else:
            return score_max - score_min


class State:
    def __init__(self, board, curr_player, depth, score=None):
        self.board = board
        self.curr_player = curr_player
        self.depth = depth
        self.score = score
        self.chosen_state = None

    def get_moves(self):
        enemy = get_enemy(self.curr_player)
        moves = self.board.get_moves(self.curr_player)

        move_states = []
        for move in moves:
            new_board = copy.deepcopy(self.board)
            junk, dest = new_board.valid_move(move, self.curr_player)
            new_board.move(move, dest, self.curr_player)
            move_states.append(State(new_board, enemy, self.depth-1))

        return move_states


def min_max(state):
    if state.depth == 0 or state.board.final() or len(state.get_moves()) == 0:
        state.score = state.board.estimate_score(state.depth)
        return state

    state.moves = state.get_moves()

    moves_score = [min_max(state) for state in state.moves]

    if state.curr_player == Game.MAX_PLAYER:
        state.chosen_state = max(moves_score, key=lambda x: x.score)
    else:
        state.chosen_state = min(moves_score, key=lambda x: x.score)

    state.score = state.chosen_state.score
    return state


def alpha_beta(alpha, beta, state):
    '''
    ceva debug stuff

    print(alpha, beta, state.depth)
    if alpha == 0 and beta == 2 and state.depth == 2:
        print('crash')
        print(state.curr_player)
        print(state.board)
        print('moves', len(state.get_moves()))
    '''

    if state.depth == 0 or state.board.final() or len(state.get_moves()) == 0:
        state.score = state.board.estimate_score(state.depth)
        return state

    if alpha > beta:
        return state

    state.moves = state.get_moves()

    if state.curr_player == Game.MAX_PLAYER:
        curr_score = float('-inf')

        for move in state.moves:
            new_state = alpha_beta(alpha, beta, move)
            if curr_score < new_state.score:
                state.chosen_state = new_state
                curr_score = new_state.score

            if alpha < new_state.score:
                alpha = new_state.score
                if alpha >= beta:
                    break

    elif state.curr_player == Game.MIN_PLAYER:
        curr_score = float('inf')

        for move in state.moves:
            new_state = alpha_beta(alpha, beta, move)

            if curr_score > new_state.score:
                state.chosen_state = new_state
                curr_score = new_state.score

            if beta > new_state.score:
                beta = new_state.score
                if alpha >= beta:
                    break

    state.score = state.chosen_state.score

    return state


def play_game(algo, player, depth, gui):
    enemy = get_enemy(player)

    Game.MIN_PLAYER = player
    Game.MAX_PLAYER = enemy
    board = Game()

    print('\nInitial:')
    print(str(board))

    state = State(board, 'n', depth)

    if gui:
        # Init pygame
        pygame.init()
        pygame.display.set_caption('Reversi')
        display = pygame.display.set_mode(size=(810, 810))

        rectangles = draw_board(display, board)
    while True:
        if state.curr_player == Game.MIN_PLAYER:
            # Player turn
            print('Player turn')
            valid_moves = state.board.get_moves(Game.MIN_PLAYER)
            print('valid moves:', len(valid_moves))
            for move in valid_moves:
                print(chr(move[1] + ord('a')), move[0])
            if len(valid_moves) == 0:
                print('No valid moves')
            else:
                while True:
                    if gui:
                        # Go through events
                        valid_move = False
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()

                            elif event.type == pygame.MOUSEBUTTONDOWN:
                                pos = pygame.mouse.get_pos()

                                for rect in range(len(rectangles)):
                                    if rectangles[rect].collidepoint(pos):
                                        line = rect // 8
                                        col = rect % 8

                                        if (line, col) in valid_moves:
                                            valid_move = True
                                            break

                        if valid_move:
                            break

                    else:
                        # If not GUI
                        try:
                            player_input = input('\n> ')
                            col = player_input[0].lower()
                            line = int(player_input[1])

                            if 0 <= line <= 7 and 'a' <= col <= 'h':
                                # Transformam coloana in nr
                                col = ord(col) - ord('a')
                                if (line, col) in valid_moves:
                                    # Valid move
                                    break
                                else:
                                    # Invalid move
                                    print('Invalid move')
                            else:
                                print('Invalid input')

                        except Exception as e:
                            print('error %s\n' % e)

                junk, dest = state.board.valid_move(
                    (line, col), Game.MIN_PLAYER)
                print('move:', (line, col), dest)
                state.board.move((line, col), dest, Game.MIN_PLAYER)

        else:
            # CPU turn
            print('CPU turn')
            valid_moves = state.board.get_moves(Game.MAX_PLAYER)
            if len(valid_moves) == 0:
                print('No valid moves')
            else:
                t1 = time.time()

                new_state = None
                mem_usage = None
                if algo == 'minmax':
                    mem_usage, new_state = memory_profiler.memory_usage(
                        (min_max, [state]), retval=True, max_usage=True)
                else:
                    mem_usage, new_state = memory_profiler.memory_usage(
                        (alpha_beta, [-500, 500, state]), retval=True, max_usage=True)

                state.board = new_state.chosen_state.board

                t2 = time.time()
                dt = t2-t1
                print('Time to move:', round(dt * 1000), 'ms')

                if mem_usage != None:
                    print('Mem Usage:', mem_usage[0], 'MiB\n')

        # Print board, check winner and change player
        print(str(state.board))
        draw_board(display, state.board)
        num_a, num_n = state.board.count_pieces()
        print('White pieces:', num_a, '\nBlack pieces:', num_n, '\n')
        winner = state.board.get_winner()
        if winner != None:
            if winner == 'a':
                print('White has won')
            elif winner == 'b':
                print('Black has won')
            else:
                print('Tie')
            break
        state.curr_player = get_enemy(state.curr_player)


if __name__ == "__main__":
    args = parser.parse_args()

    while True:
        algo = input('1. Min Max\n2. Alpha Beta\n\n> ')
        if algo == '1':
            algo = 'minmax'
            break
        elif algo == '2':
            algo = 'alphabeta'
            break
        else:
            print('Invalid answer')

    while True:
        player = input('1. White\n2. Black\n\n> ')
        if player == '1':
            player = 'a'
            break
        elif player == '2':
            player = 'n'
            break
        else:
            print('Invalid answer')

    play_game(algo, player, int(args.diff), bool(args.gui))

try:
    from pynput import keyboard
except ImportError:
    print("Missing dependency: pynput. Run: pip install pynput")
    raise SystemExit(1)

import json
import platform
import random
import sys
import time
import os
from collections import Counter

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

COINS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'coins.json')
DECK_SIZE = 53
DEFAULT_BALANCE = 100

# Source: Idea Inspiration: https://codereview.stackexchange.com/questions/82103/ascii-fication-of-playing-cards

# Single source of truth for hand multipliers.
# Both the display art and evaluate_hand() read from this dict.
PAYTABLE = {
    "Royal Flush": 100,
    "Five of a Kind": 50,
    "Straight Flush": 20,
    "Four of a Kind": 10,
    "Full House": 5,
    "Flush": 4,
    "Straight": 3,
    "Three of a Kind": 1,
    "Two Pair": 1,
    "One Pair": 0,
    "High Card": 0,
}

# Layout rows for the payout art: [(left_display, left_key, right_display, right_key), ...]
# None on the right side means a single-column row.
_PAYOUT_ROWS = [
    ("Royal Flush",     "Royal Flush",     "Flush",           "Flush"),
    ("Five of a Kind",  "Five of a Kind",  "Straight",        "Straight"),
    ("Straight Flush",  "Straight Flush",  "Three of a Kind", "Three of a Kind"),
    ("Four of a Kind",  "Four of a Kind",  "Two Pair",        "Two Pair"),
    ("Full House",      "Full House",      None,              None),
]


def _build_payout_art():
    W = 65
    lines = ['┏' + " Joker's Wild ".center(W, '━') + '┓']
    lines.append('┃' + ' ' * W + '┃')
    for ld, lk, rd, rk in _PAYOUT_ROWS:
        left = f"  {ld:<23}x {PAYTABLE[lk]}"
        if rd is None:
            lines.append('┃' + left.ljust(W) + '┃')
        else:
            right = f"{rd:<18}x {PAYTABLE[rk]}"
            lines.append('┃' + f"{left:<35}{right}".ljust(W) + '┃')
    lines.append('┃' + ' ' * W + '┃')
    lines.append('┡' + '━' * W + '┩')
    return '\n'.join(lines)


payout = _build_payout_art()

# Suit symbols indexed 0=Spades, 1=Diamonds, 2=Hearts, 3=Clubs, 4=Joker #1, 5=Joker #2
_SUIT_SYMBOLS = ['♠', '♦', '♥', '♣', '§']


class bcolors:
    BLUE   = '\033[94m'
    GREEN  = '\033[92m'
    ORANGE = '\033[93m'
    RED    = '\033[91m'
    GREY   = '\033[90m'
    ENDC   = '\033[0m'
    BOLD   = '\033[1m'
    UNDERLINE = '\033[4m'


def _value_str(value):
    mapping = {1: 'A', 11: 'J', 12: 'Q', 13: 'K', 14: 'Joker'}
    return mapping.get(value, str(value))


def evaluate_hand(hand):
    """Classify a 5-card poker hand. Joker (value=14) is wild.
    Returns (hand_name, multiplier).
    """
    joker_count = sum(1 for v, _ in hand if v == 14)
    regular     = [(v, s) for v, s in hand if v != 14]
    values      = [v for v, _ in regular]
    suits       = [s for _, s in regular]

    val_counts = Counter(values)
    counts = sorted(val_counts.values(), reverse=True)

    # Add wild jokers to the best grouping
    if joker_count:
        if counts:
            counts[0] += joker_count
        else:
            counts = [joker_count]

    top    = counts[0] if counts else 0
    second = counts[1] if len(counts) > 1 else 0

    # Flush: all non-joker cards share one suit, jokers fill the rest
    is_flush = len(set(suits)) <= 1 and (len(suits) + joker_count == 5)

    # Straight: works for both A-low (A=1) and A-high (A=14)
    def _straight_ok(vals, wilds):
        if not vals:
            return wilds >= 5
        unique = sorted(set(vals))
        span   = unique[-1] - unique[0]
        gaps   = span - (len(unique) - 1)
        return span <= 4 and gaps <= wilds

    def has_straight():
        if _straight_ok(values, joker_count):
            return True
        if 1 in values:
            high = [14 if v == 1 else v for v in values]
            return _straight_ok(high, joker_count)
        return False

    is_straight = has_straight()

    # Royal Flush: A-high straight flush (A, 10, J, Q, K)
    def is_royal():
        if not is_flush or not is_straight:
            return False
        if 1 not in values:
            return False
        non_ace_max = max((v for v in values if v != 1), default=0)
        return non_ace_max >= 10

    # Classify hand
    if top == 5:
        name = "Five of a Kind"
    elif is_flush and is_straight:
        if is_royal():
            name = "Royal Flush"
        else:
            name = "Straight Flush"
    elif top == 4:
        name = "Four of a Kind"
    elif top == 3 and second == 2:
        name = "Full House"
    elif is_flush:
        name = "Flush"
    elif is_straight:
        name = "Straight"
    elif top == 3:
        name = "Three of a Kind"
    elif top == 2 and second == 2:
        name = "Two Pair"
    elif top == 2:
        name = "One Pair"
    else:
        name = "High Card"

    return name, PAYTABLE.get(name, 0)


class Cards:
    MARGIN_LEFT    = '  '
    MARGIN_BETWEEN = '  '

    def __init__(self, NR_OF_CARDS):
        self.NR_OF_CARDS = NR_OF_CARDS

    def create_cards(self, n, used_cards=None):
        """Draw n unique cards from the deck.
        Returns (front_ascii_cards, hand, used_cards).
          front_ascii_cards: {card_index: [9 line strings]}
          hand:              [(value, suit_idx), ...]
          used_cards:        set of (value, suit_idx) already dealt
        """
        if used_cards is None:
            used_cards = set()
        hand             = []
        front_ascii_cards = {}

        for i in range(n):
            value, suit_idx = self._draw_card(used_cards)
            hand.append((value, suit_idx))
            front_ascii_cards[i] = self._make_card_lines(value, suit_idx)

        return front_ascii_cards, hand, used_cards

    def _make_card_lines(self, value, suit_idx):
        v     = _value_str(value)
        suit  = _SUIT_SYMBOLS[suit_idx]
        inner = 9
        return [
            '╔═════════╗',
            '║' + v.ljust(inner)    + '║',
            '║' + ' ' * inner       + '║',
            '║' + ' ' * inner       + '║',
            '║' + suit.center(inner) + '║',
            '║' + ' ' * inner       + '║',
            '║' + ' ' * inner       + '║',
            '║' + v.rjust(inner)    + '║',
            '╚═════════╝',
        ]

    def _draw_card(self, used_cards):
        """Draw one unique card from the deck, add it to used_cards, return (value, suit_idx)."""
        while True:
            r = random.randint(1, DECK_SIZE)
            if r == 1:
                value, suit_idx = 14, 4
            else:
                value    = random.randint(1, 13)
                suit_idx = random.randint(0, 3)
            if (value, suit_idx) not in used_cards:
                used_cards.add((value, suit_idx))
                return value, suit_idx

    def _partial_color_line(self, card_line, row, value, suit_idx):
        """Color only the inner content (not borders) on rows with value/suit."""
        if row in (1, 4, 7):
            if value == 14:
                color = bcolors.ORANGE
            elif suit_idx in (1, 2):   # Diamonds, Hearts
                color = bcolors.RED
            else:                      # Spades, Clubs
                color = bcolors.GREY
            return card_line[0] + color + card_line[1:-1] + bcolors.ENDC + card_line[-1]
        return card_line


class Dealer(Cards):
    """Handles dealing and displaying the cards."""

    MARGIN_HITME = ' ' * 11
    _BACK_CARD = [
        '╔═════════╗',
        '║' + bcolors.RED + '░░░░░░░░░' + bcolors.ENDC + '║',
        '║' + bcolors.RED + '░░░░░░░░░' + bcolors.ENDC + '║',
        '║' + bcolors.RED + '░░░░X░░░░' + bcolors.ENDC + '║',
        '║' + bcolors.RED + '░░░░X░░░░' + bcolors.ENDC + '║',
        '║' + bcolors.RED + '░░░░X░░░░' + bcolors.ENDC + '║',
        '║' + bcolors.RED + '░░░░░░░░░' + bcolors.ENDC + '║',
        '║' + bcolors.RED + '░░░░░░░░░' + bcolors.ENDC + '║',
        '╚═════════╝',
    ]

    def __init__(self, NR_OF_CARDS):
        super().__init__(NR_OF_CARDS)

    def shuffles(self, front_ascii_cards, hand):
        """Interleave card rows into 9 display strings with partial coloring."""
        the_flop = []
        for row in range(9):
            parts = []
            for i in range(self.NR_OF_CARDS):
                parts.append(self._partial_color_line(front_ascii_cards[i][row], row, *hand[i]))
            the_flop.append(self.MARGIN_BETWEEN.join(parts))
        return the_flop

    def deals_cards(self, the_flop, NR_OF_CARDS):
        """Animate card backs one-by-one, then reveal the hand."""
        M = self.MARGIN_HITME
        hit_me = (
            f'\n{M}' + bcolors.RED +
            f'\n{M}██╗  ██╗██╗████████╗    ███╗   ███╗███████╗'
            f'\n{M}██║  ██║██║╚══██╔══╝    ████╗ ████║██╔════╝'
            f'\n{M}███████║██║   ██║       ██╔████╔██║█████╗  '
            f'\n{M}██╔══██║██║   ██║       ██║╚██╔╝██║██╔══╝  '
            f'\n{M}██║  ██║██║   ██║       ██║ ╚═╝ ██║███████╗'
            f'\n{M}╚═╝  ╚═╝╚═╝   ╚═╝       ╚═╝     ╚═╝╚══════╝' +
            bcolors.ENDC +
            f'\n\n{M}    ' + bcolors.UNDERLINE + 'Press Enter' + bcolors.ENDC
        )

        input(hit_me)

        for nr in range(1, NR_OF_CARDS + 1):
            time.sleep(0.09)
            sys_clear(OnScreen=payout)
            for row_line in self._BACK_CARD:
                print(self.MARGIN_LEFT + self.MARGIN_BETWEEN.join([row_line] * nr))

        time.sleep(2)
        sys_clear(OnScreen=payout)
        for line in the_flop:
            print(self.MARGIN_LEFT + line)
        time.sleep(1.5)

    def deals_replacement(self, new_ascii, new_hand, selected, NR_OF_CARDS):
        """Animate replacement: card backs on swapped positions, then reveal all."""
        sys_clear(OnScreen=payout)
        for row in range(9):
            parts = []
            for i in range(NR_OF_CARDS):
                if i in selected:
                    parts.append(self._BACK_CARD[row])
                else:
                    parts.append(self._partial_color_line(new_ascii[i][row], row, *new_hand[i]))
            print(self.MARGIN_LEFT + self.MARGIN_BETWEEN.join(parts))
        time.sleep(1.5)

        # Frame 2: reveal all cards face-up
        sys_clear(OnScreen=payout)
        for line in self.shuffles(new_ascii, new_hand):
            print(self.MARGIN_LEFT + line)
        time.sleep(1.5)


class Select(Cards):
    """Handles player card selection and replacement."""

    def __init__(self, front_ascii_cards, hand, NR_OF_CARDS, used_cards):
        super().__init__(NR_OF_CARDS)
        self.front_ascii_cards = front_ascii_cards
        self.hand              = hand
        self.used_cards        = used_cards

    def highlight_card(self):
        """Let the player choose cards to replace.
        Arrow keys navigate; Space toggles selection; Enter confirms.
        Returns a set of card indices selected for replacement.
        """
        state = {'cursor': 0, 'selected': set()}

        def redraw():
            sys_clear(OnScreen=payout)
            for line in self._build_display(state['cursor'], state['selected']):
                print(self.MARGIN_LEFT + line)
            print(
                f"\n  {bcolors.BLUE}←/→{bcolors.ENDC} navigate  "
                f"{bcolors.ORANGE}Space{bcolors.ENDC} select/deselect  "
                f"{bcolors.GREEN}Enter{bcolors.ENDC} confirm draw"
            )

        def on_key(key):
            if key == keyboard.Key.right:
                state['cursor'] = min(self.NR_OF_CARDS - 1, state['cursor'] + 1)
            elif key == keyboard.Key.left:
                state['cursor'] = max(0, state['cursor'] - 1)
            elif key == keyboard.Key.space:
                c = state['cursor']
                if c in state['selected']:
                    state['selected'].discard(c)
                else:
                    state['selected'].add(c)
            elif key == keyboard.Key.enter:
                return False   # stops the listener
            else:
                return         # ignore all other keys
            redraw()

        redraw()
        try:
            with keyboard.Listener(on_press=on_key, suppress=True) as listener:
                listener.join()
        except (OSError, RuntimeError):
            print(f"\n  {bcolors.RED}Keyboard input failed — keeping current hand.{bcolors.ENDC}")

        return state['selected']

    def _build_display(self, cursor, selected):
        """Return 10 strings: 9 card rows + 1 marker row."""
        lines = []
        for row in range(9):
            parts = []
            for i in range(self.NR_OF_CARDS):
                card_line = self.front_ascii_cards[i][row]
                if i in selected:
                    parts.append(bcolors.ORANGE + card_line + bcolors.ENDC)
                elif i == cursor:
                    parts.append(bcolors.BLUE + card_line + bcolors.ENDC)
                else:
                    parts.append(self._partial_color_line(card_line, row, *self.hand[i]))
            lines.append(self.MARGIN_BETWEEN.join(parts))

        # Marker row beneath the cards
        markers = []
        for i in range(self.NR_OF_CARDS):
            if i in selected and i == cursor:
                markers.append(bcolors.BLUE + bcolors.BOLD + '[SWAP]'.center(11) + bcolors.ENDC)
            elif i in selected:
                markers.append(bcolors.ORANGE + bcolors.BOLD + '[SWAP]'.center(11) + bcolors.ENDC)
            elif i == cursor:
                markers.append(bcolors.BLUE + '[  ]'.center(11) + bcolors.ENDC)
            else:
                markers.append(' ' * 11)
        lines.append(self.MARGIN_BETWEEN.join(markers))
        return lines

    def replace_select(self, selected, used_cards):
        """Draw new cards for each selected position.
        Returns (new_hand, new_front_ascii_cards, used_cards).
        """
        new_hand  = list(self.hand)
        new_ascii = dict(self.front_ascii_cards)

        for i in selected:
            value, suit_idx = self._draw_card(used_cards)
            new_hand[i]  = (value, suit_idx)
            new_ascii[i] = self._make_card_lines(value, suit_idx)

        return new_hand, new_ascii, used_cards


class Bet:
    """Tracks balance and handles bet placement and payout."""

    def __init__(self, balance=None):
        self.balance     = balance if balance is not None else self.load_balance()
        self.current_bet = 0

    @staticmethod
    def load_balance():
        try:
            with open(COINS_FILE, 'r') as f:
                data = json.load(f)
            return int(data.get('balance', DEFAULT_BALANCE))
        except (FileNotFoundError, json.JSONDecodeError, ValueError, KeyError):
            return DEFAULT_BALANCE

    @staticmethod
    def save_balance(balance):
        try:
            with open(COINS_FILE, 'w') as f:
                json.dump({'balance': balance}, f)
        except OSError as e:
            print(f"Warning: could not save balance: {e}", file=sys.stderr)

    def place_bet(self, amount):
        """Deduct bet from balance. Returns False if invalid."""
        if amount <= 0 or amount > self.balance:
            return False
        self.current_bet  = amount
        self.balance     -= amount
        self.save_balance(self.balance)
        return True

    def payout(self, multiplier):
        """Add winnings to balance. Returns the amount won."""
        winnings      = self.current_bet * multiplier
        self.balance += winnings
        self.save_balance(self.balance)
        return winnings



def display_result(hand_name, multiplier, winnings, balance):
    """Print a prominent result box after hand evaluation."""
    W = 65
    top    = '┏' + '━' * W + '┓'
    bottom = '┡' + '━' * W + '┩'
    side   = '┃'
    empty  = side + ' ' * W + side

    def center_line(text, raw_len):
        pad = W - raw_len
        left = pad // 2
        right = pad - left
        return side + ' ' * left + text + ' ' * right + side

    hand_text = bcolors.BOLD + hand_name.upper() + bcolors.ENDC
    hand_raw  = len(hand_name)

    if winnings > 0:
        win_str  = f"+{winnings} coins (x{multiplier})"
        win_text = bcolors.GREEN + win_str + bcolors.ENDC
        win_raw  = len(win_str)
    else:
        win_str  = "No Win"
        win_text = bcolors.RED + win_str + bcolors.ENDC
        win_raw  = len(win_str)

    bal_str  = f"Balance: {balance} coins"
    bal_text = bcolors.GREEN + bal_str + bcolors.ENDC
    bal_raw  = len(bal_str)

    print()
    print(top)
    print(empty)
    print(center_line(hand_text, hand_raw))
    print(center_line(win_text, win_raw))
    print(empty)
    print(center_line(bal_text, bal_raw))
    print(empty)
    print(bottom)


def sys_clear(OnScreen=None):
    """Clear the terminal screen across platforms."""
    if 'ipad' in platform.platform().lower():
        try:
            import console
            console.clear()
        except ImportError:
            pass
    elif os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')
    if OnScreen is not None:
        print(OnScreen)

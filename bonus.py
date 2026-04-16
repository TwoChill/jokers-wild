"""Double-or-Nothing bonus round (DQ XI Joker's Wild rules).

Contract: starting winnings in, final winnings out.
  * Pick 1 of 4 face-down cards. Higher than the face-up reference -> double.
  * Tie or lower -> winnings become 0 and the round ends.
  * Player may cash out between rounds (n at the prompt).
  * Capped at MAX_DOUBLES consecutive wins (forced cash-out at the cap).
  * Deck is the standard 52 cards. No joker in Double-or-Nothing.

No balance/persistence side effects live in this module; commit happens in the
caller via Bet.award().
"""

import random
import time

from base import (
    Cards,
    Dealer,
    bcolors,
    _value_str,
    payout,
    sys_clear,
)

try:
    from pynput import keyboard
except ImportError:
    keyboard = None


class DoubleOrNothing:
    MAX_DOUBLES = 8
    CHOICES     = 4

    def __init__(self, winnings, rng=None, pick_strategy=None, continue_strategy=None):
        self.starting_winnings  = winnings
        self.winnings           = winnings
        self._rng               = rng if rng is not None else random.Random()
        self._pick_strategy     = pick_strategy or self._default_pick
        self._continue_strategy = continue_strategy or self._default_continue
        self._cards             = Cards(1 + self.CHOICES)

    def play(self):
        """Run the Double-or-Nothing sequence. Returns final winnings (>= 0)."""
        if self.winnings <= 0:
            return 0

        wins = 0
        while wins < self.MAX_DOUBLES:
            if wins == 0:
                if not self._continue_strategy(self.winnings, first_round=True):
                    return self.winnings
            else:
                if not self._continue_strategy(self.winnings, first_round=False):
                    return self.winnings

            reference, choices = self._draw_round()
            idx = self._pick_strategy(reference, choices)
            if idx is None:
                return self.winnings

            chosen = choices[idx]
            self._render_reveal(reference, choices, idx)

            if chosen[0] > reference[0]:
                self.winnings *= 2
                wins += 1
                self._banner(f"DOUBLED  Winnings: {self.winnings}", bcolors.GREEN)
            else:
                self._banner(
                    f"LOST  Reference was {_value_str(reference[0])}, yours was {_value_str(chosen[0])}",
                    bcolors.RED,
                )
                return 0

        self._banner(f"CAP REACHED  Collecting {self.winnings}", bcolors.ORANGE)
        return self.winnings

    def _draw_round(self):
        """Shuffle a fresh 52-card deck and deal (reference, [choices...])."""
        deck = [(v, s) for v in range(1, 14) for s in range(4)]
        self._rng.shuffle(deck)
        drawn = deck[: 1 + self.CHOICES]
        return drawn[0], drawn[1:]

    # ---- default strategies (interactive) ----

    def _default_continue(self, winnings, first_round):
        prompt = (
            f"\n  Play Double-or-Nothing with {bcolors.GREEN}{winnings}{bcolors.ENDC} coins? [y/n]: "
            if first_round else
            f"\n  Winnings: {bcolors.GREEN}{winnings}{bcolors.ENDC}.  Double again? [y/n]: "
        )
        return input(prompt).strip().lower() == 'y'

    def _default_pick(self, reference, choices):
        if keyboard is None:
            print(f"  {bcolors.RED}pynput unavailable -- collecting current winnings.{bcolors.ENDC}")
            return None

        state = {'cursor': 0, 'confirmed': False}

        def redraw():
            sys_clear(OnScreen=payout)
            print(
                f"\n  Reference (left) vs. your pick (right) -- "
                f"beat the reference to win {bcolors.GREEN}{self.winnings * 2}{bcolors.ENDC} coins.\n"
            )
            self._render_layout(reference, choices, cursor=state['cursor'])
            print(
                f"\n  {bcolors.BLUE}<-/->{bcolors.ENDC} navigate  "
                f"{bcolors.GREEN}Enter{bcolors.ENDC} pick"
            )

        def on_key(key):
            if key == keyboard.Key.right:
                state['cursor'] = min(self.CHOICES - 1, state['cursor'] + 1)
            elif key == keyboard.Key.left:
                state['cursor'] = max(0, state['cursor'] - 1)
            elif key == keyboard.Key.enter:
                state['confirmed'] = True
                return False
            else:
                return
            redraw()

        redraw()
        try:
            with keyboard.Listener(on_press=on_key, suppress=True) as listener:
                listener.join()
        except (OSError, RuntimeError):
            print(f"  {bcolors.RED}Keyboard input failed -- collecting current winnings.{bcolors.ENDC}")
            return None

        return state['cursor'] if state['confirmed'] else None

    # ---- rendering ----

    def _render_layout(self, reference, choices, cursor, reveal_idx=None):
        """Draw: reference card, gap, 4 choice cards (face-down except reveal_idx)."""
        ref_lines = self._cards._make_card_lines(*reference)
        choice_lines = []
        for i, (v, s) in enumerate(choices):
            if reveal_idx is not None and i == reveal_idx:
                choice_lines.append(self._cards._make_card_lines(v, s))
            else:
                choice_lines.append(Dealer._BACK_CARD)

        gap = '     '
        for row in range(9):
            parts = [self._cards._partial_color_line(ref_lines[row], row, *reference), gap]
            for i, lines in enumerate(choice_lines):
                if reveal_idx is not None and i == reveal_idx:
                    parts.append(self._cards._partial_color_line(lines[row], row, *choices[i]))
                elif i == cursor and reveal_idx is None:
                    parts.append(bcolors.BLUE + lines[row] + bcolors.ENDC)
                else:
                    parts.append(lines[row])
            print(Cards.MARGIN_LEFT + Cards.MARGIN_BETWEEN.join(parts))

        markers = [' ' * 11, gap]
        for i in range(self.CHOICES):
            if reveal_idx is not None and i == reveal_idx:
                markers.append(bcolors.ORANGE + bcolors.BOLD + '[PICK]'.center(11) + bcolors.ENDC)
            elif i == cursor and reveal_idx is None:
                markers.append(bcolors.BLUE + '[PICK]'.center(11) + bcolors.ENDC)
            else:
                markers.append(' ' * 11)
        print(Cards.MARGIN_LEFT + Cards.MARGIN_BETWEEN.join(markers))

    def _render_reveal(self, reference, choices, idx):
        sys_clear(OnScreen=payout)
        print(
            f"\n  Reference: {_value_str(reference[0])}   "
            f"Your card: {_value_str(choices[idx][0])}\n"
        )
        self._render_layout(reference, choices, cursor=idx, reveal_idx=idx)
        time.sleep(1.2)

    def _banner(self, text, color):
        print(f"\n  {color}{bcolors.BOLD}{text}{bcolors.ENDC}")
        time.sleep(1.2)

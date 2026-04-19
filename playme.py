import importlib.metadata
import pathlib
import re
import sys


def _check_requirements():
    req = pathlib.Path(__file__).parent / "requirements.txt"
    if not req.exists():
        return
    missing = []
    for line in req.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name = re.split(r"[><=!~\[\s]", line)[0]
        try:
            importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            missing.append(line)
    if missing:
        print("Missing packages:")
        for p in missing:
            print(f"  {p}")
        print("\nInstall with: pip install -r requirements.txt")
        input("\nPress Enter to exit...")
        sys.exit(1)


_check_requirements()


import base as clss
from bonus import DoubleOrNothing


def _prompt_restart(bet):
    """Ask the player whether to restart with a fresh stake. Returns True to continue."""
    print(f"\n  {clss.bcolors.RED}Out of coins.{clss.bcolors.ENDC}")
    restart = input("  Restart with 100? [y/n]: ").strip().lower()
    if restart == 'y':
        bet.balance = clss.DEFAULT_BALANCE
        clss.Bet.save_balance(bet.balance)
        return True
    return False


def main():
    clss.sys_clear(OnScreen=clss.payout)

    NR_OF_CARDS = 5

    bet = clss.Bet()

    while True:
        if bet.balance <= 0:
            if not _prompt_restart(bet):
                break
        clss.sys_clear(OnScreen=clss.payout)
        print(f"  Balance: {clss.bcolors.GREEN}{bet.balance}{clss.bcolors.ENDC} coins\n")

        # Get a valid bet
        while True:
            raw = input(f"  Enter bet (1–{bet.balance}): ").strip()
            try:
                amount = int(raw)
                if bet.place_bet(amount):
                    break
                print(f"  Bet must be between 1 and {bet.balance}.")
            except ValueError:
                print("  Please enter a whole number.")

        # Deal initial hand
        cards  = clss.Cards(NR_OF_CARDS)
        front_ascii_cards, hand, used_cards = cards.create_cards(NR_OF_CARDS)

        dealer   = clss.Dealer(NR_OF_CARDS)
        the_flop = dealer.shuffles(front_ascii_cards, hand)
        dealer.deals_cards(the_flop, NR_OF_CARDS)

        # Player selects cards to replace
        player   = clss.Select(front_ascii_cards, hand, NR_OF_CARDS, used_cards)
        selected = player.highlight_card()

        # Replace selected cards and redisplay
        if selected:
            new_hand, new_ascii, used_cards = player.replace_select(selected, used_cards)
            dealer.deals_replacement(new_ascii, new_hand, selected, NR_OF_CARDS)
        else:
            new_hand, new_ascii = hand, front_ascii_cards
            new_flop = dealer.shuffles(new_ascii, new_hand)
            clss.sys_clear(OnScreen=clss.payout)
            for line in new_flop:
                print(clss.Cards.MARGIN_LEFT + line)

        # Evaluate, optionally play Double-or-Nothing, then commit winnings.
        hand_name, multiplier = clss.evaluate_hand(new_hand)
        winnings = bet.compute_winnings(multiplier)

        if winnings > 0:
            winnings = DoubleOrNothing(winnings).play()

        bet.award(winnings)

        clss.display_result(hand_name, multiplier, winnings, bet.balance)

        if bet.balance <= 0:
            if not _prompt_restart(bet):
                break
            continue

        again = input("\n  Again? [Enter] / q to quit: ").strip().lower()
        if again == 'q':
            print(f"\n  Final balance: {bet.balance} coins. Thanks for playing!")
            break


if __name__ == "__main__":
    main()

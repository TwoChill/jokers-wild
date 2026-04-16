import base as clss


def main():
    clss.sys_clear(OnScreen=clss.payout)

    NR_OF_CARDS = 5

    bet = clss.Bet()

    while True:
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

        # Evaluate and pay out
        hand_name, multiplier = clss.evaluate_hand(new_hand)
        winnings = bet.payout(multiplier)

        clss.display_result(hand_name, multiplier, winnings, bet.balance)

        if bet.balance <= 0:
            print(f"\n  {clss.bcolors.RED}Out of coins.{clss.bcolors.ENDC}")
            restart = input("  Restart with 100? [y/n]: ").strip().lower()
            if restart == 'y':
                bet.balance = clss.DEFAULT_BALANCE
                clss.Bet.save_balance(bet.balance)
                continue
            break

        again = input("\n  Again? [Enter] / q to quit: ").strip().lower()
        if again == 'q':
            print(f"\n  Final balance: {bet.balance} coins. Thanks for playing!")
            break


if __name__ == "__main__":
    main()

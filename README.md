# Joker's Wild

A 5-card draw poker game you play in your terminal. Inspired by the casino minigame from Dragon Quest XI.

You get 5 cards, choose which ones to swap, and try to make the best poker hand you can. The Joker is wild -- it becomes whatever card helps you most.

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━ Joker's Wild ━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                                                 ┃
┃  Royal Flush            x 100     Flush             x 4         ┃
┃  Five of a Kind         x 50      Straight          x 3         ┃
┃  Straight Flush         x 20      Three of a Kind   x 1         ┃
┃  Four of a Kind         x 10      Two Pair          x 1         ┃
┃  Full House             x 5                                     ┃
┃                                                                 ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
```

---

## What you need

1. **Python 3.8 or newer.** If you don't have it yet, download it from [python.org](https://www.python.org/downloads/). During installation on Windows, make sure to check the box that says **"Add Python to PATH"**.

2. **A terminal / command prompt.** Every computer has one:
   - **Windows:** Press `Win + R`, type `cmd`, press Enter.
   - **Mac:** Open Spotlight (`Cmd + Space`), type `Terminal`, press Enter.
   - **Linux:** You probably already know where yours is.

---

## How to install

Open your terminal and run these commands one at a time:

```
git clone https://github.com/Twochill/Jokers_Wild.git
cd Jokers_Wild
pip install pynput
```

If `pip` doesn't work, try `pip3` instead.

Don't have `git`? You can also click the green **Code** button on the GitHub page, choose **Download ZIP**, unzip the folder, and open your terminal inside it.

---

## How to play

From inside the game folder, run:

```
python playme.py
```

(On some systems you may need `python3 playme.py` instead.)

### The flow of a hand

1. **Place your bet.** Type a number and press Enter. You can bet anywhere from 1 coin up to your full balance.

2. **Cards are dealt.** You'll see 5 cards appear on screen. Press Enter to continue.

3. **Pick cards to swap.** Use these keys:
   - **Left / Right arrow keys** -- move the cursor between cards.
   - **Spacebar** -- select (or deselect) a card for swapping. Selected cards show an orange `[SWAP]` marker.
   - **Enter** -- confirm your choices. Selected cards are replaced with new ones from the deck. If you're happy with your hand, just press Enter without selecting anything.

4. **See your result.** The game shows your hand, your winnings, and your updated balance.

5. **Double or Nothing (optional).** After any winning hand you'll be offered a bonus round. One reference card is shown face-up on the left, four face-down cards on the right. Pick one of the four -- if its value is strictly higher than the reference, your winnings double. Tie or lower and you lose all your winnings from this hand. You can keep doubling up to 8 times (256x) or cash out at any prompt by typing `n`. Losing hands skip the offer.

6. **Keep going or quit.** Press Enter to play another hand, or type `q` to quit.

### Winning hands (from best to worst)

| Hand | What it means | Payout |
|------|--------------|--------|
| Royal Flush | A, K, Q, J, 10 -- all the same suit | x 100 |
| Five of a Kind | Four matching cards + the Joker | x 50 |
| Straight Flush | Five cards in a row, all the same suit | x 20 |
| Four of a Kind | Four cards with the same number | x 10 |
| Full House | Three of one number + two of another | x 5 |
| Flush | Five cards of the same suit (any numbers) | x 4 |
| Straight | Five cards in a row (any suits) | x 3 |
| Three of a Kind | Three cards with the same number | x 1 |
| Two Pair | Two different pairs | x 1 |
| One Pair | Two cards with the same number | x 0 |
| High Card | Nothing above | x 0 |

Your payout = your bet multiplied by the number in the Payout column. For example, if you bet 10 coins and get a Flush, you win 10 x 4 = 40 coins back.

One Pair and High Card pay nothing -- you lose your bet. The minimum winning hand is Two Pair.

### The Joker

The deck has 53 cards: the standard 52 plus one Joker. The Joker is **wild** -- it automatically counts as whatever card makes your hand the strongest. You don't have to do anything special; the game figures it out for you.

---

## Your coin balance

- You start with **100 coins**.
- Your balance is saved automatically between sessions in a file called `coins.json` in the game folder.
- If you run out of coins, the game asks if you want to restart with 100.
- To manually reset your balance, just delete `coins.json` and run the game again.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `python` command not found | Try `python3` instead. If that doesn't work, reinstall Python and check "Add to PATH". |
| `pip install pynput` fails | Try `pip3 install pynput` or `python -m pip install pynput`. |
| Cards look broken / garbled | Your terminal doesn't support Unicode box-drawing characters. Try Windows Terminal, iTerm2 (Mac), or any modern terminal emulator. The default `cmd.exe` on older Windows versions may not render correctly. |
| Arrow keys don't work | Make sure you clicked inside the terminal window so it has focus. On some Linux setups, `pynput` needs permission to read keyboard input -- try running with `sudo`. |

---

Part of the **Rise of the Dragon Rider** text-based RPG project.

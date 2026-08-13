# ⛵ Cardboard Regatta: Quick Reference Guide

## ⏱️ Turn Structure
1. **Phase 1: Wind & Forecast Phase** — six steps, **in order**:
   1. **Wind arrives** — move the Wind Marker to last round's Forecast Marker.
   2. **Irons bleed** — any boat head to wind: **-1 Momentum** (min 0).
   3. **Puff** — if the arriving wind is a Puff: **+1 Momentum**, except boats in Irons.
   4. **Shadow** — boats starting in a Wind Shadow have their **cap lowered by 1** (min 1).
   5. **Settle** — every boat above her cap **drops to it**. Irons exempt (she bled at 2).
      *This is the only clamp in the game — never check a cap at any other moment.*
   6. **Forecast** — roll **2d6** for next round, place the Forecast Marker.
   - *The wind springs back*: a shift that would push past the 60 deg limit returns the
     wind to Base instead. Base holds ~half the race; a shift lasts ~3 rounds.
   - *Sail in today's wind, plan for tomorrow's*: all movement this round uses the
     **Wind Marker**. The Forecast Marker only tells you what your heading will be
     worth next round.
   - *Shifts change your Point of Sail for free* — and Point of Sail sets your momentum
     cap, i.e. your action count. Finish the round on the tack the shift will **lift**
     (Close-Hauled -> Broad Reach, 5 cards), not the one it will **head**
     (Close-Hauled -> Irons, 1 card).
2. **Phase 2: Planning Phase**
   - **Read your Momentum tracker: that is how many action cards you play** (min 1, max 6).
   - Play that many Action Cards face-down, in order.
   - Deck is **13 cards**: Trim x5, Head Up x2, Bear Off x2, Luff x2, Tack x1, Gybe x1.
     The Qty is a rule: **one Tack and one Gybe per round, maximum** — you own only one of
     each. All 13 come back in Cleanup. 5 Trims covers any slot count except Momentum 6.
   - *Wind Shadow*: start the round in another boat's downwind **cone** — 1 hex to
     leeward of her plus the 3 hexes across at range 2 — and your **Max Momentum drops by 1**
     for the whole round (min 1); if you are above the new cap, drop to it now. Costs
     you an action card. Does not stack, nothing blocks it, checked once at the start
     of the round only. *Use it on purpose: park upwind of a rival and cover her.*
     The cone is fixed to the WIND, not to the boat — running dead downwind it falls
     **ahead** of her, so downwind the trailing boat blankets the leader.
3. **Phase 3: Movement Phase**
   - **Upwind Rank**: never measured — every hex prints three rank numbers, one per
     wind state, colour-matched to the Compass Rose. Read the one matching the Wind
     Marker; **higher = further upwind**. A step of 2 is one hex straight upwind, so
     adjacent columns differ by 1 and are *never* level. A shift just means reading a
     different colour.
   - **Initiative**: re-read every Action Step — *the furthest boat to windward that
     has not yet moved goes next*. Ties: higher Momentum, then a 1d6 rolled once at the
     start of the phase and kept all round — you keep your *roll*, not your place. Only unmoved boats are compared, so the order within a step is stable.
     A wind shift rotates the upwind axis and can swap the order without anyone moving.
   - Resolve Action 1 for all players in Initiative order, then Action 2, etc.
4. **Phase 4: Cleanup Phase**
   - Retrieve all played cards.

---

## 🌬️ Points of Sail (POS) & Momentum
*Base Wind is North (0°). A **Puff** gives +1 Momentum and +1 cap **for that round only**,
to every boat except one in Irons. No expiry rule needed — next round Settle takes it back.*
*Momentum is your action count, so Max Momentum is also your top speed in hexes per round.*

| POS | Angle | Max Momentum | Notes |
|---|:---:|:---:|---|
| **Irons** | 0° | 1 | Auto -1 Momentum per turn. Cannot play `Trim` or `Head Up`. Exit using `Bear Off` (pivots in place at 0 speed). |
| **Close-Hauled** | 60° / 300° | 4 | 4 hexes/round |
| **Broad Reach** | 120° / 240° | 5 | **5 hexes/round — fastest** |
| **Run** | 180° | 4 | 4 hexes/round |

*Settle to your cap*: in Phase 1, if your Momentum is above the cap for the Point of
Sail you are now on, drop it to the cap. Mid-round it may sit above the cap — you carry
your way through a turn — but `Trim` can never take you above it. **Irons is exempt**:
she bleeds 1 a round instead of dropping straight to 1.

---

## 🃏 Action Cards
*Golden Rule: At Momentum 1+, ALL maneuver cards move you **1 hex forward** before applying rotation or momentum changes!*
*You play one card per point of Momentum, so Momentum gained by `Trim` pays off NEXT round.*

| Card | POS Allowed | Requirements | Effect |
|---|---|---|---|
| **Trim** | Any (except Irons) | None | Move 1 hex forward. **+1 Momentum**. |
| **Head Up** | Any (except Irons) | Momentum 1+ | Move 1 hex forward. Turn 60° towards wind. |
| **Bear Off** | Any (except Run) | None | Move 1 hex forward. Turn 60° away from wind. *(At Momentum 0: pivot in place without moving forward)*. |
| **Tack** | Close-Hauled | Momentum 1+ | Move 1 hex forward. Turn 120° across wind to opposite tack. **-1 Momentum**. |
| **Gybe** | Run | Momentum 1+ | Move 1 hex forward. Flip tack downwind. |
| **Luff** | Close-Hauled, Broad Reach, Irons | None | Move 1 hex forward (if momentum > 0). **-1 Momentum**. |

---

## ⚖️ Right-of-Way (ROW) Rules
*Fouls only occur when two boats attempt to occupy the **exact same hex**.*
*On contact the boats **share the hex** — nobody is pushed back or loses Momentum, and the
Protest card is the whole penalty. Every pair in a pile-up is judged separately (max 1
Protest each per round). Entering an occupied hex on purpose is legal.*

**Bail Out** (boats only — you cannot duck a mark, since stopping does not turn you):
if your revealed card would take you into an occupied hex, discard your
**final** face-down card to stop short — no move, no rotation, Momentum -1, card
set aside. Swapping to a different card does NOT help: every card moves you 1 hex forward
in your current facing first, so they all land on the same hex.
- You cannot bail on your **last card of the round** (nothing left to pay with).
- You cannot bail at **Momentum 0** (no way to spill, and the payment would be free).
- You **may bail more than once** a round if you still have cards to pay with.
- Only the boat arriving **second** gets the choice — the hex must already be occupied.
  Moving first in Initiative order can mean fouling with no chance to duck.

1. **Rule 10 (Starboard vs Port):** **Starboard** tack has ROW over Port tack.
2. **Rule 11 (Overlapped):** **Leeward** boat has ROW; the **Windward** boat keeps clear.
3. **Rule 12 (Clear Astern):** the boat **astern** keeps clear of the boat ahead.
   *Overlap test — check one hex:* boats move 1 hex per step, so a collision is always
   between neighbours. Of the six neighbouring hexes only the one **dead astern** is
   "clear astern"; any other adjacent hex is an **overlap**. (Same-tack boats sailing
   straight never collide — someone has to converge first.)
4. **Rule 13 (Tacking):** Tacking boats have NO ROW and must keep clear.
5. **OCS Boats:** Boats returning to the Pre-Start area after starting early have NO ROW.

*No Rule 14 penalty: the Bail Out is how any boat declines contact, right-of-way boat
included. Right of way does not stop a rival sitting where you wanted to go — making
her spend a card to duck you is a fair exchange, not a foul.*

**Not implemented:** RRS 15 (acquiring ROW), 16 (changing course — the Bail Out covers it),
17 (proper course), 18 (mark-room), 20 (room to tack). **There is no mark-room**: the 3-hex
Zone only decides whether you have *rounded*, and confers no rights. An inside overlap at a
mark buys you nothing — Rules 10-13 apply at a buoy exactly as in open water.

---

## 🚩 Penalties & Marks
- **Rounded a mark?** All three, in order: (1) you came within **3 hexes** (the Zone),
  (2) at some moment inside the Zone the mark was on the required hand (default Port),
  (3) you are now **further away** than the step before. Miss any and nothing is credited.
- **Protest Cards (Max 1 per round)**: You get a Protest card if you violate ROW (cause a
  collision) OR if you **end** an action step on a mark that bounds the leg you are sailing.
- **Clearing a Protest**: Next Planning Phase you play **2 fewer action slots** (minimum 1),
  then discard the card. You know before you commit cards, so plan the short round.
- **Never DSQ**: no disqualification exists. Worst possible score is DNF.
- **Board edge**: you cannot sail off it. Stop in the hex nearest the edge, **Momentum -> 0**,
  and turn to any heading that points back at your mark (not head to wind). The board is
  **21 x 29** with the start line across the middle — at least 4 hexes of clear water
  beyond every mark and line end, or about one round's sailing.
- **Marks**: **entering** a mark's hex hits it — you move 1 hex per card, so there is no
  passing *through* a buoy. Only marks bounding your current leg count. The **Committee
  Boat and Pin are live during the pre-start, Leg 1 and the final leg**, scenery otherwise
  — so you cannot barge between a leeward boat and the committee boat.
- **Split Hexes**: a hex split by a line **always resolves in the boat's favour** — at the
  gun that means Pre-Start (not OCS), at the finish it means Finished. Not opposite rules.
- **Finish Side**: whichever side the *final leg* heads towards. South for Courses 1 and 3
  (downwind finish), North for Course 2 (upwind sprint).
- **Finishing Window**: the race closes **20 rounds after the first boat finishes**. Anyone
  still out is DNF (boats + 1 points — just 1 worse than finishing last).

// Cardboard Regatta — the Quick Reference appendix.
//
// This is a card, not a chapter. It is consulted mid-round with a boat in one
// hand, so it is set denser and unjustified, and every claim is a fact rather
// than an explanation — the reasoning lives in the chapters and is linked to.
//
// Kept in its own module so the appendix can also be built as a standalone
// card without duplicating a word of it.

#import "regatta.typ": sans, mono
#import "rulebook.typ": pal

// --- Card-specific furniture ------------------------------------------------

/// A section bar. Louder than a chapter heading and much tighter, so the eye
/// lands on the right block without reading.
#let ref-head(title) = context {
  let p = pal.get()
  block(width: 100%, above: 10pt, below: 5pt, {
    block(width: 100%, fill: p.ink, inset: (x: 7pt, y: 4pt),
      text(font: sans, size: 9pt, weight: "bold", fill: p.paper,
           tracking: 0.1em)[#upper(title)])
  })
}

/// A single rule of thumb, set apart because it is the one thing on the card a
/// player most often needs and most often forgets.
#let key(body) = context {
  let p = pal.get()
  block(width: 100%, above: 5pt, below: 5pt,
    fill: p.accent.transparentize(93%),
    stroke: (left: 1.6pt + p.accent),
    inset: (x: 7pt, y: 5pt), body)
}

/// The whole appendix, wrapped in its compact treatment.
#let quick-ref(body) = context {
  let p = pal.get()
  // Tuned to land the card on exactly two pages, so it prints as one sheet,
  // double-sided, and lives beside the board instead of inside the book.
  set text(size: 8.3pt)
  set par(justify: false, leading: 0.46em, spacing: 0.52em)
  set list(indent: 4pt, spacing: 0.34em, marker: ([•], [–]))
  set enum(indent: 4pt, spacing: 0.34em)
  set table(inset: (x: 5pt, y: 3.1pt))
  show heading.where(level: 2): it => ref-head(it.body)
  body
}

// --- The card ---------------------------------------------------------------

#let quick-reference = [

== Turn Structure

*Phase 1 — Wind & Forecast.* Six steps, #underline[in order]:

+ *Wind arrives* — move the Wind Marker to last round's Forecast Marker.
+ *Irons bleed* — any boat head to wind: *−1 Momentum* (min 0).
+ *Puff* — if the arriving wind is a Puff: *+1 Momentum*, except boats in Irons.
+ *Shadow* — boats starting in a Wind Shadow have their *cap lowered by 1* (min 1).
+ *Settle* — every boat above her cap *drops to it*. Irons exempt: she bled at step 2.
+ *Forecast* — roll *2d6* for next round, place the Forecast Marker.

#key[
  *Step 5 is the only clamp in the game.* Never check a momentum cap at any other
  moment — not mid-round, not after a card.
]

- *The wind springs back*: a shift that would push past the 60° limit returns the wind
  to Base instead. Base holds about half the race; a shift lasts roughly 3 rounds.
- *Sail in today's wind, plan for tomorrow's*: everything this round resolves against
  the *Wind Marker*. The Forecast Marker only says what your heading will be worth next
  round.
- *Shifts change your Point of Sail for free*, and Point of Sail sets your cap, which is
  your card count. Finish on the tack the shift will *lift* (Close-Hauled ➔ Broad Reach,
  5 cards), not the one it will *head* (Close-Hauled ➔ Irons, 1 card).

*Phase 2 — Planning.*

- *Read your Momentum tracker: that is how many cards you play* (min 1, max 6). Place
  them face-down, in order. *You must fill every slot.*
- Deck is *13 cards*: Trim ×5, Head Up ×2, Bear Off ×2, Luff ×2, Tack ×1, Gybe ×1. The
  quantity is a rule — *one Tack and one Gybe per round, maximum*. All 13 return in
  Cleanup.
- *Wind Shadow*: start the round in another boat's downwind *cone* — 1 hex to leeward
  plus the 3 hexes across at range 2 — and your cap drops by 1 for the whole round
  (min 1). Costs you a card. Does not stack, nothing blocks it, checked once at the
  start of the round only.
- The cone is fixed to the *wind*, not the boat. Running dead downwind it falls *ahead*
  of her — so downwind, the trailing boat blankets the leader. *Use it on purpose.*

*Phase 3 — Movement.*

- *Upwind Rank* is never measured. Every hex prints three rank numbers, one per wind
  state, colour-matched to the Compass Rose. Read the one matching the Wind Marker;
  *higher is further upwind*. A step of 2 is one hex straight upwind, so adjacent
  columns differ by 1 and are *never* level.
- *Initiative*, re-read every Action Step: _the furthest boat to windward that has not
  yet moved goes next._ Ties break on higher Momentum, then a *1d6 rolled once* at the
  start of the phase and kept all round — you keep your *roll*, not your place.
- Resolve Action 1 for every player in Initiative order, then Action 2, and so on.

*Phase 4 — Cleanup.* Retrieve all played cards. Nothing is spent.

== Points of Sail & Momentum

#table(
  columns: 4,
  align: (left, center, center, left),
  [Point of Sail], [Angle], [Cap], [Notes],
  [*Irons*], [0°], [1],
    [Auto −1 Momentum per round. Cannot play `Trim` or `Head Up`. Exit with `Bear Off`, which pivots in place even at Momentum 0.],
  [*Close-Hauled*], [60° / 300°], [4], [4 hexes/round.],
  [*Broad Reach*], [120° / 240°], [5], [*5 hexes/round — the fastest point of sail.*],
  [*Run*], [180°], [4], [4 hexes/round.],
)

- *Settle to your cap*: in Phase 1, if your Momentum is above the cap for the Point of
  Sail you are now on, drop it. Mid-round it may sit above the cap — you carry your way
  through a turn — but `Trim` can never take you above it. *Irons is exempt*: she bleeds
  1 a round instead of dropping straight to 1.
- A *Puff* gives +1 Momentum and +1 cap *for that round only*, to every boat except one
  in Irons. It needs no expiry rule: next round Settle takes it back.
- Momentum is your action count, so the cap is also your top speed in hexes per round.

== Action Cards

#key[
  *The Golden Movement Rule.* At Momentum 1+, *every* card moves you *1 hex forward in
  your current facing* before any rotation or momentum change is applied. So at speed,
  every card in your hand lands you on the same hex — a different card only changes
  which way you point when you get there.
]

#table(
  columns: 4,
  align: (left, left, left, left),
  [Card], [Points of Sail], [Requires], [Effect],
  [*Trim*], [Any except Irons], [None],
    [Move 1 hex. *+1 Momentum* (never above your cap). Moves you even at Momentum 0.],
  [*Head Up*], [Any except Irons], [Momentum 1+],
    [Move 1 hex. Turn 60° towards the wind.],
  [*Bear Off*], [Any except Run], [None],
    [Move 1 hex. Turn 60° away from the wind. _At Momentum 0 she pivots in place._],
  [*Tack*], [Close-Hauled], [Momentum 1+],
    [Move 1 hex. Turn 120° across the wind to the opposite tack. *−1 Momentum.*],
  [*Gybe*], [Run], [Momentum 1+],
    [Move 1 hex. Flip tack. *Facing does not change.*],
  [*Luff*], [Close-Hauled, Broad Reach, Irons], [None],
    [Move 1 hex and *−1 Momentum*. A brake, not a turn. _At Momentum 0 she holds station._],
)

- Momentum gained by `Trim` pays off *next* round: your slot count was fixed when this
  one began.
- An *illegal card* is discarded with no effect — but at Momentum 1+ you still coast one
  hex forward without rotating.

== Right-of-Way

*A foul happens only when two boats occupy the exact same hex.* On contact the boats
*share the hex*: nobody is pushed back, nobody loses Momentum, and the Protest card is
the whole penalty. Every pair in a pile-up is judged separately (max 1 Protest each per
round). Entering an occupied hex on purpose is legal.

+ *Rule 10 — Starboard vs Port.* *Starboard* tack has right of way.
+ *Rule 11 — Overlapped.* The *leeward* boat has right of way; *windward* keeps clear.
+ *Rule 12 — Clear Astern.* The boat *astern* keeps clear of the boat ahead.
+ *Rule 13 — Tacking.* A boat playing `Tack` has *no* right of way.
+ *OCS.* A boat returning to the pre-start side has *no* right of way over anybody.

#key[
  *The overlap test is one hex.* Boats move 1 hex per step, so a collision is always
  between neighbours. Of the six neighbouring hexes only the one *dead astern* is clear
  astern; *any* other adjacent hex is an overlap. Same-tack boats sailing straight never
  collide — somebody has to converge first.
]

*Bail Out.* If your revealed card would take you into an *already occupied* hex, discard
your *final* face-down card to stop short: no move, no rotation, *−1 Momentum*, and the
revealed card is set aside unplayed.

- You *cannot* bail on your last card of the round — nothing left to pay with.
- You *cannot* bail at Momentum 0: no way to spill, and the payment would be free.
- You *may* bail more than once a round, while you still have cards to pay with.
- Only the boat arriving *second* ever gets the choice, since the hex must already be
  occupied. Moving first can mean fouling with no chance to duck.
- You *cannot* bail out of a mark. Stopping does not turn you, and a buoy never moves.

*No Rule 14 penalty:* the Bail Out is how any boat declines contact, the right-of-way
boat included. Right of way does not stop a rival sitting where you wanted to go —
making her spend a card to duck you is a fair exchange, not a foul.

*Not implemented:* RRS 15 (acquiring right of way), 16 (changing course — the Bail Out
covers it), 17 (proper course), 18 (mark-room), 20 (room to tack). *There is no
mark-room*: the 3-hex Zone only decides whether you have _rounded_ and confers no rights.
An inside overlap at a mark buys you nothing.

== Marks, Penalties & the Board

- *Have you rounded?* All three, in order: (1) you came within *3 hexes* — the Zone;
  (2) at some moment inside the Zone the mark lay on the required hand, Port by default;
  (3) you are now *further away* than the step before. Miss any and nothing is credited.
- *Hitting a mark*: *entering* its hex hits it. You move 1 hex per card, so there is no
  passing *through* a buoy. Only marks bounding your current leg count.
- *The line marks* — Committee Boat and Pin — are live during the *pre-start, Leg 1 and
  the final leg*, and scenery otherwise. So you cannot barge between a leeward boat and
  the committee boat.
- *Protest cards*, max *1 per round*: for violating right of way, or for ending an
  Action Step on a live mark.
- *Clearing a Protest*: next Planning Phase you play *2 fewer slots* (minimum 1), then
  discard the card. You know before you commit, so plan the short round.
- *Never DSQ.* No disqualification exists. The worst score on the sheet is DNF.
- *Board edge*: you cannot sail off it. Stop in the hex nearest the edge, *Momentum ➔ 0*,
  and turn to any heading that points back at your mark — never head to wind. The board
  is *21 × 29* with the line across the middle: at least 4 hexes of clear water beyond
  every mark and line end, about one round's sailing.
- *Split hexes* always resolve *in the boat's favour* — at the gun that means Pre-Start
  and not OCS; at the finish it means Finished. Not opposite rules.
- *Finish Side*: whichever side the *final leg* heads towards. South for Courses 1 and 3,
  North for Course 2.
- *Finishing Window*: the race closes *20 rounds after the first boat finishes*. Anyone
  still out is DNF — boats + 1 points, exactly 1 worse than finishing last.
]

# Cardboard Regatta

## Table of Contents
- [Components & Core Concepts](#components--core-concepts)
  - [Components](#components)
  - [Points of Sail & Hex Geometry](#points-of-sail--hex-geometry)
- [Setup & Course Layout](#setup--course-layout)
  - [Race Setup](#race-setup)
  - [Starting Line Layout](#starting-line-layout-flat-topped-hexes)
  - [Sailing Instructions](#sailing-instructions-sailing-the-course)
  - [Example Courses](#example-courses)
  - [Fast-Play Rules](#fast-play-rules-1520-min-sprint)
- [Turn Structure & Gameplay Phases](#turn-structure--gameplay-phases)
  - [Phase 1: Pre-Start Sequence](#phase-1-pre-start-sequence)
  - [Phase 2: Wind Phase (Optional)](#phase-2-wind-phase-optional)
  - [Phase 3: Planning Phase](#phase-3-planning-phase)
  - [Phase 4: Movement Phase](#phase-4-movement-phase)
- [Sailing Tactics & Hazards](#sailing-tactics--hazards)
  - [Wind Shadow](#wind-shadow)
  - [Rounding Marks](#rounding-marks)
  - [Fouling & Right-of-Way (ROW) Rules](#fouling--right-of-way-row-rules)
- [Red Flags & Penalties](#red-flags--penalties)
  - [Incurring a Red Flag](#incurring-a-red-flag)
  - [Clearing a Red Flag](#clearing-a-red-flag)
  - [Disqualification (DSQ) & Leaving the Board](#disqualification-dsq--leaving-the-board)
- [Finishing the Race](#finishing-the-race)
- [Scoring System (RRS Appendix A)](#scoring-system-rrs-appendix-a)
- [Glossary of Nautical & Racing Terms](#glossary-of-nautical--racing-terms)

---

## Components & Core Concepts
> *"The pessimist complains about the wind; the optimist expects it to change; the realist adjusts the sails."* — William Arthur Ward

### Components
- **Hex grid**
- **Boat tokens** for each player (5 tokens per boat, close-hauled [port](#term-port)/[starboard](#term-starboard) on opposite sides)
- **Action deck** for each player
- **Wind deck**
- **Speed Trackers** (Player mats with speed sliders or d6 dice to track speed 0–4)
- **d6 die** (for pre-start turn counter)
- **Red Flag cards** (for tracking penalties)

### Points of Sail & Hex Geometry
Wind direction is set along hex grid axes. The 6 hex directions relative to the wind direction correspond to four [Points of Sail](#term-points-of-sail):

- **[Irons](#term-irons) (0°)**: Pointed directly into the wind (1 hex direction).
- **[Close-Hauled](#term-close-hauled) (60° / 300°)**: Pointed 60° off the wind (2 hex directions).
- **[Broad Reach](#term-broad-reach) (120° / 240°)**: Pointed 120° off the wind (2 hex directions).
- **[Run](#term-run) (180°)**: Pointed directly downwind (1 hex direction).
- **Hex Alignment**: Boat tokens are placed in hexes pointing directly toward one of the 6 flat hex sides (edges).

#### Port vs. Starboard Tack
- **[Starboard Tack](#term-starboard)**: Wind is blowing across the boat's starboard (right) side (facing 60°, 120°, or 180° relative to wind).
- **[Port Tack](#term-port)**: Wind is blowing across the boat's port (left) side (facing 300°, 240°, or 180° relative to wind).
- **Token Flipping**: Flip your boat token to its matching side ([Port](#term-port) or [Starboard](#term-starboard)) whenever your boat changes tacks via a [`Tack`](#term-tack) or [`Gybe`](#term-gybe) maneuver.

> [!TIP]
> **How to Escape Irons:** When your boat is in [Irons](#term-irons) (facing 0° North), you cannot play `Sail` or [`Head Up`](#term-head-up). To get out of Irons, play a **[`Bear Off`](#term-bear-off)** action card (which turns your boat 60° to [Close-Hauled](#term-close-hauled), even at Speed 0). Alternatively, play **[`Luff`](#term-luff)** to spill wind and remain in place until you can bear off.

---

## Setup & Course Layout
> *"To desire nothing beyond what you have is surely the best waypoint on any course."* — Joshua Slocum

### Race Setup
1. Set the **Wind direction marker** pointing straight down the board (North to South / 0° to 180°).
2. Set the **starting line length** to at least equal the number of boats (e.g., if there are 4 boats, use at least 4 hexes between the pin and committee boat).
3. Setup [windward](#term-windward) and [leeward](#term-leeward) [marks](#term-mark) as required by the race course.
4. Use the **boat number cards** to randomly assign boats to players (each boat has a matching maneuver deck).
5. The player assigned **boat #1** is the Starting Player.
6. The starting player places their boat on a hex anywhere in the pre-start area at any [point of sail](#term-points-of-sail) and at any starting speed (from Speed 0 up to the Point of Sail's maximum speed). Then place boat #2, etc. Each subsequent boat must be placed at least 2 hexes away from any previously placed boat.

### Starting Line Layout (Flat-Topped Hexes)
On a flat-topped hex grid, adjacent horizontal hexes are staggered (forming a zig-zag pattern). 

With wind blowing straight down the board (North to South / 0° to 180°), the starting line is defined as follows:
- **[Pin Mark](#term-pin-mark) ([Port](#term-port) / Left End)** and **[Committee Boat](#term-committee-boat) ([Starboard](#term-starboard) / Right End)** are placed in hexes across the board from each other at the same general horizontal rank.
- **The Starting Line**: The imaginary straight line segment connecting the center of the [Pin Mark](#term-pin-mark) hex to the center of the [Committee Boat](#term-committee-boat) hex.
- **Line Boundaries**:
  - **Pre-Start Area**: All hexes lying entirely on the South ([downwind](#term-leeward)) side of the starting line segment.
  - **Course Side**: All hexes lying entirely on the North ([upwind](#term-windward)) side of the starting line segment.
  - **Split Line Hexes**: If a boat is in a hex that is bisected/split by the starting line segment when the start gun fires, roll **1d6**:
    - **1–3**: The boat is on the **Course Side ([OCS](#term-ocs))**.
    - **4–6**: The boat is in the **Pre-Start Area**.
  - **Crossing the Line**: A boat legally starts when its movement path moves from a pre-start hex across the imaginary line segment (between the [Pin Mark](#term-pin-mark) and [Committee Boat](#term-committee-boat)) into a course hex.

### Sailing Instructions (Sailing the Course)
To legally complete a race, boats must follow official Sailing Instructions (RRS Rule 28):

1. **Start Legally**: Pass through the starting line segment from the pre-start area (South) to the course side (North) after the start gun fires (or re-cross legally if [OCS](#term-ocs)).
2. **Mark Rounding Direction (Default: Leave to Port)**: Unless specified otherwise by the course layout, all [marks](#term-mark) must be rounded **leaving the mark to [Port](#term-port) (Left)** (counter-clockwise rounding).
3. **Course Leg Sequence (The String Rule)**: Boats must round each [mark](#term-mark) in the exact sequence specified by the course legs (e.g., Leg 1 ➔ Leg 2 ➔ Leg 3). A boat’s track, if drawn as a string from start to finish, must wrap around the required side of each mark in sequence.
4. **Finish Legally**: Cross the finish line segment between the two finish marks in the direction indicated by the final course leg.

### Example Courses

#### 🏆 Course 1: Standard Windward-Leeward (3 Legs — 30–40 Mins)
*The classic competitive regatta layout testing upwind tacking and downwind tactical positioning.*
- **[Windward Mark](#term-windward)**: Placed 10 hexes upwind (North) of the starting line.
- **[Leeward Mark](#term-leeward)**: Placed 10 hexes downwind (South) of the starting line (below the start line).
- **Leg Sequence**:
  1. **Leg 1 (Upwind)**: Start Line ➔ [Windward Mark](#term-windward) *(round leaving mark to [Port](#term-port) / Left)*.
  2. **Leg 2 (Downwind)**: Windward Mark ➔ [Leeward Mark](#term-leeward) *(round leaving mark to [Port](#term-port) / Left)*.
  3. **Leg 3 (Upwind Sprint)**: Leeward Mark ➔ Finish Line *(Start Line)*.

#### ⚡ Course 2: Beginner Sprint (2 Legs — 15–20 Mins)
*A fast introductory race designed for learning points of sail and maneuver planning.*
- **[Windward Mark](#term-windward)**: Placed 6 hexes upwind (North) of the starting line.
- **Leg Sequence**:
  1. **Leg 1 (Upwind)**: Start Line ➔ [Windward Mark](#term-windward) *(round leaving mark to [Port](#term-port) / Left)*.
  2. **Leg 2 (Downwind Finish)**: Windward Mark ➔ Downwind Finish Line *(Start Line)*.

#### 📐 Course 3: Olympic Triangle (3 Legs — 35–45 Mins)
*An advanced course testing broad reach speed, gybing maneuvers, and mark rounding strategy.*
- **[Windward Mark](#term-windward)**: Placed 8 hexes North (0° upwind) of the starting line.
- **Reach Mark (Wing)**: Placed 6 hexes South-West (240°) from the Windward Mark (left of windward).
- **[Leeward Mark](#term-leeward)**: Placed 6 hexes South-East (120°) from the Reach Mark (directly downwind of the Windward Mark).
- **Leg Sequence**:
  1. **Leg 1 (Upwind)**: Start Line ➔ [Windward Mark](#term-windward) *(leave to [Port](#term-port) / Left)*.
  2. **Leg 2 (Reaching Triangle)**: Windward Mark ➔ Reach Mark *(leave to [Port](#term-port) / Left)* ➔ [Leeward Mark](#term-leeward) *(leave to [Port](#term-port) / Left)*.
  3. **Leg 3 (Upwind Finish)**: Leeward Mark ➔ Finish Line *(Start Line)*.

### Fast-Play Rules (15–20 Min Sprint)
For quick 4-player games that finish in **15 to 20 minutes max**, use these streamlined pacing rules:

1. **Sprint Course (2 Legs)**: Play a 2-leg course (Leg 1 Upwind to a 6-to-8 hex mark ➔ Leg 2 Downwind Finish at the Start Line).
2. **Instant Start**: Skip the 3-turn pre-start countdown. Place all boats in the Pre-Start Area at **Speed 2 or 3** facing their chosen [point of sail](#term-points-of-sail). The start gun fires immediately on **Round 1**.
3. **Simultaneous 45-Second Timer**: Use a 45-second timer during the Planning Phase for all players to select their 4 action cards simultaneously.

---

## Turn Structure & Gameplay Phases
> *"He that will not sail till all dangers are over must never put to sea."* — Thomas Fuller

### Phase 1: Pre-Start Sequence
- After all players have placed their boats, the pre-start sequence begins and lasts for **3 turns**.
- Players maneuver for starting position during these 3 turns using standard Planning and Movement phases.
- Use the included **d6** to count down the 3 pre-start turns (3, 2, 1).
- **On Course Side ([OCS](#term-ocs)) Rule**: At the end of Turn 3 (when the start gun fires), any boat on the course side of the starting line is **[OCS](#term-ocs)**.
  - **Split Hex Determination**: If a boat ends Turn 3 on a hex that is split by the starting line segment, roll **1d6**: on **1–3**, the boat is **[OCS](#term-ocs)**; on **4–6**, the boat counts as **Pre-Start**.
  - An OCS boat must maneuver its token so that it is **entirely on the pre-start side of the starting line** before it can legally cross the start line to begin Leg 1.
  - **OCS [Right-of-Way](#term-right-of-way)**: A boat returning to the pre-start side after starting early ([OCS](#term-ocs)) has **no [Right-of-Way](#term-right-of-way)** and must [keep clear](#term-keep-clear) of all boats that started legally.

### Phase 2: Wind Phase (Optional)
At the start of each round during the weather phase:
1. Move all active Wind cards downwind by one zone. Discard any Wind card pushed out of zones 5 and 6.
2. Draw new Wind cards for zones 1 and 2 from the Wind deck.

#### Wind Card Types & Effects
- **Steady**: No change to wind conditions in this zone.
- **Puff**: Gives +1 Speed to any boat moving through or starting in this zone.
- **Shift (Left)**: Rotates wind direction counter-clockwise by 60° (1 hex side) in this zone.
- **Shift (Right)**: Rotates wind direction clockwise by 60° (1 hex side) in this zone.
- **Puff Shift (Left / Right)**: Combines a Puff (+1 Speed) with a wind shift in the specified direction.

### Phase 3: Planning Phase
- Every round, players receive **4 Action slots** during the planning phase.
- Select 4 action cards from your maneuver deck and place them face-down in order (Action 1, Action 2, Action 3, Action 4).
- Cards feature [Point of Sail](#term-points-of-sail) icons: **Green** for valid points of sail, **Red** for invalid points of sail.

#### Actions Summary
| Action | Qty | Valid Points of Sail (POS) | Requirements & Effects |
|---|---|---|---|
| **[Head Up](#term-head-up)** | x2 | Any except [Irons](#term-irons) | Rotate facing 60° towards the wind (0° North). Requires Speed > 0. |
| **[Bear Off](#term-bear-off)** | x2 | Any except [Run](#term-run) | Rotate facing 60° away from the wind (180° South). (Can be played at Speed 0 to exit [Irons](#term-irons)). |
| **[Tack](#term-tack)** | x1 | [Close-Hauled](#term-close-hauled) | Rotate facing 120° across the wind to the opposite tack. Requires Speed > 1; reduces Speed by 1. |
| **[Gybe](#term-gybe)** | x1 | [Run](#term-run) | Flip tack ([Port](#term-port)/[Starboard](#term-starboard)) while running downwind. |
| **[Luff](#term-luff)** | x2 | [Close-Hauled](#term-close-hauled), [Broad-Reach](#term-broad-reach), or [Irons](#term-irons) | Reduce Speed by 1 without changing facing. (Can be played at Speed 0). |
| **Sail** | x4 | Any except [Irons](#term-irons) | Increase Speed by 1 (up to POS max speed) and move forward 1 hex. |

### Phase 4: Movement Phase

#### Initiative
At the start of the Movement Phase, initiative determines turn order:
1. The player whose boat is furthest **[upwind](#term-windward)** (closest to the wind source) has **Initiative** and acts first.
2. If tied for upwind distance, the boat with **higher Speed** acts first.
3. If still tied, the boat with the **lowest sail number** acts first.

#### Speed & Polar Limits
Each **Sail** action increases Speed by 1 up to the maximum speed for your current [Point of Sail](#term-points-of-sail):

| Point of Sail | Max Speed / Effect |
|---|---|
| **[Close-Hauled](#term-close-hauled)** | 3 |
| **[Broad-Reach](#term-broad-reach)** | 4 |
| **[Run](#term-run)** | 3 |
| **[Irons](#term-irons)** | Speed automatically reduced by 1 at the start of each turn. Cannot play `Sail`. |

#### Action Resolution (Round-Robin)
Movement is executed in 4 **Action Steps** (Action 1 through Action 4):
1. For each Action Step, all players reveal their planned card for that step in Initiative order.
2. Active player executes their card's movement and rotation. **Maneuver Resolution Order**: Move 1 hex forward in your current facing direction first, then apply the card's rotation/heading change.
3. If an action is **illegal** for the current POS or speed state, it is discarded without effect (the boat coasts forward 1 hex if Speed > 0).

#### Round Cleanup
At the end of each round (after Action 4), all players retrieve their played action cards back into their hand for the next round (except any cards set aside to clear a Red Flag).

---

## Sailing Tactics & Hazards
> *"To win a regatta, you must first finish the race."* — Sir Peter Blake

### Wind Shadow
- **[Wind Shadow](#term-wind-shadow) Area**: The 2 hexes directly [downwind](#term-leeward) of any boat (in the direction the wind is blowing, independent of the boat's facing angle).
- **Planning Phase Effect**: If your boat *starts* the Planning Phase in another boat's [Wind Shadow](#term-wind-shadow), its maximum speed for the round is reduced by 1 (minimum max speed 1). You still plan all 4 action cards.
- **Movement Phase Effect**: If your boat *enters* a [Wind Shadow](#term-wind-shadow) during movement, its current Speed is immediately reduced by 1.

### Rounding Marks
- **Ending in a Mark Hex**: If you end an Action Step or turn in a hex containing a [mark](#term-mark), you hit the mark and incur a **Red Flag card**.
- **Passing Through a Mark**: If a boat moves *through* a hex containing a [mark](#term-mark) during an Action Step without ending its turn there, roll **1d6**. On a roll of **1**, the boat hits the mark and incurs a **Red Flag card**.
- **Mark Penalty Limit**: A boat can receive a maximum of 1 Red Flag card per round from any individual mark.

### Fouling & Right-of-Way (ROW) Rules
When two boats enter the same hex or path, [Right-of-Way (ROW)](#term-right-of-way) determines which boat is at fault:
1. **Starboard vs. Port**: A boat on **[Starboard Tack](#term-starboard)** has [ROW](#term-right-of-way) over a boat on **[Port Tack](#term-port)**. The Port tack boat must [keep clear](#term-keep-clear).
2. **Same Tack (Windward vs. Leeward)**: When on the same tack, the **[Leeward](#term-leeward) boat** (further downwind) has [ROW](#term-right-of-way) over the **[Windward](#term-windward) boat** (further upwind). The Windward boat must [keep clear](#term-keep-clear).
3. **Overtaking**: A boat coming from behind ([clear astern](#term-clear-ahead)) must [keep clear](#term-keep-clear) of a boat ahead ([clear ahead](#term-clear-ahead)).
4. **Returning OCS Boat**: A boat returning to the pre-start side after starting early ([OCS](#term-ocs)) has no [Right-of-Way](#term-right-of-way) and must [keep clear](#term-keep-clear) of all boats that started legally.

---

## Red Flags & Penalties
> *"Good judgment comes from experience, and experience comes from bad judgment."* — Mark Twain

### Incurring a Red Flag
A boat takes a **Red Flag card** if it:
- Ends an Action Step or turn in a hex containing a [mark](#term-mark) on the current leg.
- Moves through a mark's hex and rolls a **1** on **1d6**.
- Violates [Right-of-Way](#term-right-of-way) and collides with or forces another boat to alter course into the same hex.

### Clearing a Red Flag
- A player **must clear their Red Flag card as soon as able** (on the very next Planning Phase).
- **Random Discard Procedure**: During the Planning Phase, the player shuffles their maneuver deck face-down and draws **2 random action cards** to set aside for the round (leaving only 2 active action slots to plan for that round).
- Once the round is complete and the Red Flag card is removed, return the 2 discarded cards to the player's maneuver deck.

### Disqualification (DSQ) & Leaving the Board
- A boat holding an uncleared Red Flag card that incurs a **second penalty** is **immediately disqualified**.
- A boat holding an uncleared Red Flag card that crosses the finish line to finish is **immediately disqualified**.
- If a boat moves off the hex grid boundary, it is **immediately disqualified**.

---

## Finishing the Race
> *"It is not the ship so much as the skillful sailing that assures the prosperous voyage."* — George William Curtis

- **Finish Line Layout**: The finish line is the imaginary straight line segment connecting the centers of the two finish line [marks](#term-mark) (such as the [Pin Mark](#term-pin-mark) and [Committee Boat](#term-committee-boat)).
- **Crossing the Finish Line**: A boat finishes the race when its movement path crosses the imaginary finish line segment between the two marks from the course side to the finish side.
- **Split Finish Line Hexes**: If a boat ends an Action Step in a hex that is bisected/split by the finish line segment, roll **1d6**:
  - **1–3**: The boat is determined to still be on the **Course Side** (has not legally finished yet).
  - **4–6**: The boat is determined to be on the **Finish Side** (legally finished!).

---

## Scoring System (RRS Appendix A)
> *"You don't win a regatta in the first race, but you can certainly lose it."* — Dennis Conner

Cardboard Regatta uses the official **Low-Point System** from Appendix A of the *Racing Rules of Sailing*.

### Race Points
In each individual race, boats receive points matching their finishing order:

| Finishing Status | Points Awarded |
|---|---|
| **1st Place** | 1 point |
| **2nd Place** | 2 points |
| **3rd Place** | 3 points |
| **4th Place** | 4 points |
| **Nth Place** | N points |
| **DNF / DSQ / [OCS](#term-ocs)** | Total number of entered boats + 1 point |

* **DNF** (Did Not Finish): Failed to complete all course legs.
* **DSQ** (Disqualified): Crosses the finish line holding a Red Flag card, incurs a 2nd penalty, or leaves the board.
* **[OCS](#term-ocs)** (On Course Side): Fails to re-cross the start line legally after starting early.

### Series Regatta Scoring
- **Series Score**: A boat’s regatta score is the total sum of points across all races in the series.
- **Throwouts (Discards)**: If **4 or more races** are played in a regatta series, each boat discards (excludes) its single worst race score from its total.
- **Winner**: The boat with the **lowest cumulative series score** wins the regatta!

### Tie-Breaking (RRS A8)
If two or more boats are tied in total series points:
1. **Most High Finishes**: The tie is awarded to the boat with the most 1st-place finishes. If still tied, the boat with the most 2nd-place finishes, and so on.
2. **Last Race Standings**: If still tied, the tie is broken by whichever tied boat finished higher in the final race of the series.

---

## Glossary of Nautical & Racing Terms
> *"Beyond the edge of the chart there be dragons, but also the joy of discovery."*

For players new to sailing, here is a quick reference guide to common sailing and racing terms used in Cardboard Regatta:

| Term | Definition |
|---|---|
| <a id="term-port"></a>**Port** | The **left** side of a boat when facing forward towards the bow. |
| <a id="term-starboard"></a>**Starboard** | The **right** side of a boat when facing forward towards the bow. |
| <a id="term-bow"></a>**Bow** | The front end of the boat. |
| <a id="term-stern"></a>**Stern** | The back end of the boat. |
| <a id="term-windward"></a>**Windward** | Upwind; closer to the direction the wind is blowing from (towards North / 0°). |
| <a id="term-leeward"></a>**Leeward** | Downwind; further in the direction the wind is blowing toward (towards South / 180°). |
| <a id="term-points-of-sail"></a>**Points of Sail** | The angle of a boat relative to the wind direction ([Irons](#term-irons), [Close-Hauled](#term-close-hauled), [Broad Reach](#term-broad-reach), [Run](#term-run)). |
| <a id="term-irons"></a>**Irons (Head to Wind)** | Pointed directly into the wind (0°). Speed drops by 1 each turn and you cannot play `Sail`. Play a [`Bear Off`](#term-bear-off) card to turn out of Irons. |
| <a id="term-close-hauled"></a>**Close-Hauled** | Sailing as close to the wind direction as possible (60° / 300°). |
| <a id="term-broad-reach"></a>**Broad Reach** | Sailing diagonally away from the wind direction (120° / 240°). Maximum boat speed (4). |
| <a id="term-run"></a>**Run** | Sailing directly downwind with the wind coming over the stern (180°). |
| <a id="term-tack"></a>**Tack** | Turning the bow (front) of the boat through the wind to change from one side to the other. |
| <a id="term-gybe"></a>**Gybe (Jibe)** | Turning the stern (back) of the boat through the wind while sailing downwind. |
| <a id="term-head-up"></a>**Head Up** | Steering the boat closer toward the wind direction (60° turn). |
| <a id="term-bear-off"></a>**Bear Off (Bear Away)** | Steering the boat further away from the wind direction (60° turn). |
| <a id="term-luff"></a>**Luff** | Easing sails to spill wind and slow down without changing facing direction. |
| <a id="term-right-of-way"></a>**Right-of-Way (ROW)** | The legal entitlement under RRS Part 2 of a boat to hold its position/course. Other boats must *[Keep Clear](#term-keep-clear)*. |
| <a id="term-keep-clear"></a>**Keep Clear** | Steering/positioning your boat so a [Right-of-Way](#term-right-of-way) boat can sail her course without taking avoiding action. |
| <a id="term-clear-ahead"></a>**Clear Ahead / Clear Astern** | A boat is *Clear Astern* when its hull is entirely behind an imaginary line perpendicular to a boat ahead (*Clear Ahead*). |
| <a id="term-mark"></a>**Mark** | An anchored buoy in the water that boats must round during the race. |
| <a id="term-pin-mark"></a>**Pin Mark** | The orange buoy marking the left ([Port](#term-port)) end of the starting line. |
| <a id="term-committee-boat"></a>**Committee Boat** | The official race boat anchored at the right ([Starboard](#term-starboard)) end of the starting line. |
| <a id="term-ocs"></a>**OCS (On Course Side)** | Crossing the starting line onto the course side before the start gun fires (starting early). |
| <a id="term-wind-shadow"></a>**Wind Shadow** | The 2-hex blanketed area downwind of a boat where wind velocity and max speed are reduced. |

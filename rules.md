# Cardboard Regatta v2

## Components
- **Hex grid**
- **Boat tokens** for each player (5 tokens per boat, close-hauled port/starboard on opposite sides)
- **Action deck** for each player
- **Wind deck**
- **d6 die** (for pre-start turn counter)
- **Penalty tokens**

## Points of Sail & Hex Geometry
Wind direction is set along hex grid axes. The 6 hex directions relative to the wind direction correspond to four Points of Sail:

- **Irons (0°)**: Pointed directly into the wind (1 hex direction).
- **Close-Hauled (60° / 300°)**: Pointed 60° off the wind (2 hex directions).
- **Broad Reach (120° / 240°)**: Pointed 120° off the wind (2 hex directions).
- **Run (180°)**: Pointed directly downwind (1 hex direction).

### Port vs. Starboard Tack
- **Starboard Tack**: Wind is blowing across the boat's starboard (right) side (facing 60°, 120°, or 180° relative to wind).
- **Port Tack**: Wind is blowing across the boat's port (left) side (facing 300°, 240°, or 180° relative to wind).

## Setup
1. Set the **Wind direction marker** pointing straight down the board.
2. Set the **starting line length** to at least equal the number of boats (e.g., if there are 4 boats, use at least 4 hexes between the pin and committee boat).
3. Setup **windward and leeward marks** as required by the race course.
4. Use the **boat number cards** to randomly assign boats to players (each boat has a matching maneuver deck).
5. The player assigned **boat #1** is the Starting Player.
6. The starting player places their boat on a hex anywhere in the pre-start area at any point of sail. Then place boat #2, etc. Each subsequent boat must be placed at least 2 hexes away from any previously placed boat.

## Pre-Start
- After all players have placed their boats, the pre-start sequence begins and lasts for **3 turns**.
- Players maneuver for starting position during these 3 turns using standard Planning and Movement phases.
- Use the included **d6** to count down the 3 pre-start turns (3, 2, 1).
- **On Course Side (OCS) Rule**: At the end of Turn 3 (when the start gun fires), any boat on the course side of the starting line is **OCS**. An OCS boat must turn around and re-cross the starting line from the pre-start side before it can legally begin racing.

## Wind Phase (Optional)
At the start of each round during the weather phase:
1. Move all active Wind cards downwind by one zone. Discard any Wind card pushed out of zones 5 and 6.
2. Draw new Wind cards for zones 1 and 2 from the Wind deck.

### Wind Card Types & Effects
- **Steady**: No change to wind conditions in this zone.
- **Puff**: Gives +1 Speed to any boat moving through or starting in this zone.
- **Shift (Left)**: Rotates wind direction counter-clockwise by 60° (1 hex side) in this zone.
- **Shift (Right)**: Rotates wind direction clockwise by 60° (1 hex side) in this zone.
- **Puff Shift (Left / Right)**: Combines a Puff (+1 Speed) with a wind shift in the specified direction.

## Planning Phase
- Every round, players receive **4 Action slots** during the planning phase.
- Select 4 action cards from your maneuver deck and place them face-down in order (Action 1, Action 2, Action 3, Action 4).
- Cards feature Point of Sail icons: **Green** for valid points of sail, **Red** for invalid points of sail.

### Actions Summary
| Action | Qty | Valid Points of Sail (POS) | Requirements & Effects |
|---|---|---|---|
| **Head Up** | x2 | Any except Irons | Rotate facing 60° towards the wind. Requires Speed > 0. |
| **Bear Off** | x2 | Any except Run | Rotate facing 60° away from the wind. (Can be played at Speed 0 to exit Irons). |
| **Tack** | x1 | Close-Hauled | Rotate facing 120° across the wind to the opposite tack. Requires Speed > 1; reduces Speed by 1. |
| **Gybe** | x1 | Run | Flip tack (Port/Starboard) while running downwind. |
| **Luff** | x2 | Close-Hauled, Broad-Reach, or Irons | Reduce Speed by 1 without changing facing. (Can be played at Speed 0). |
| **Sail** | x4 | Any except Irons | Increase Speed by 1 (up to POS max speed) and move forward 1 hex. |

## Movement Phase

### Initiative
At the start of the Movement Phase, initiative determines turn order:
1. The player whose boat is furthest **upwind** (closest to the wind source) has **Initiative** and acts first.
2. If tied for upwind distance, the boat with **higher Speed** acts first.
3. If still tied, the boat with the **lowest sail number** acts first.

### Speed & Polar Limits
Each **Sail** action increases Speed by 1 up to the maximum speed for your current Point of Sail:

| Point of Sail | Max Speed / Effect |
|---|---|
| **Close-Hauled** | 3 |
| **Broad-Reach** | 4 |
| **Run** | 3 |
| **Irons** | Speed automatically reduced by 1 at the start of each turn. Cannot play `Sail`. |

### Action Resolution (Round-Robin)
Movement is executed in 4 **Action Steps** (Action 1 through Action 4):
1. For each Action Step, all players reveal their planned card for that step in Initiative order.
2. Active player executes their card's movement and rotation. If a boat has Speed > 0 and plays a maneuver card, it advances 1 hex in its current facing direction in addition to executing the card's maneuver.
3. If an action is **illegal** for the current POS or speed state, it is discarded without effect (the boat coasts forward 1 hex if Speed > 0).

### "Oh Shit!" Rule
- A player may swap their current planned card for another card in their maneuver deck by **discarding their current planned card plus 1 additional unplayed action card** from their remaining slots for that round.
- If a player does not have at least 1 remaining unplayed action card besides the current slot, they cannot use this rule.

## Rounding Marks
- You may not end your movement in the same hex as a mark.
- Ending movement in a mark's hex counts as touching the mark and incurs a **Penalty**.

## Wind Shadow
- **Wind Shadow Area**: The 2 hexes directly downwind of any boat.
- **Planning Phase Effect**: If your boat *starts* the Planning Phase in another boat's Wind Shadow, you plan 1 less action card (3 actions total for the round).
- **Movement Phase Effect**: If your boat *enters* a Wind Shadow during movement, its current Speed is immediately reduced by 1.

## Fouling & Penalties

### Right-of-Way Rules
When two boats enter the same hex or path, Right-of-Way (ROW) determines which boat is at fault:
1. **Starboard vs. Port**: A boat on **Starboard Tack** has ROW over a boat on **Port Tack**. The Port tack boat must keep clear.
2. **Same Tack (Windward vs. Leeward)**: When on the same tack, the **Leeward boat** (further downwind) has ROW over the **Windward boat** (further upwind). The Windward boat must keep clear.
3. **Overtaking**: A boat coming from behind (clear astern) must keep clear of a boat ahead.

### Incurring a Penalty
A boat receives a **Penalty Token** if it:
- Ends an Action Step in the same hex as a mark on the current leg.
- Violates Right-of-Way and collides with or forces another boat to alter course into the same hex.

### Clearing a Penalty
- To clear a Penalty Token, a player must plan and execute **1 Tack** and **1 Gybe** action card across their action slots.
- When both penalty maneuvers are completed without incurring another penalty, remove the Penalty Token.

### Disqualification (DSQ)
- A boat with an uncleared Penalty Token that incurs a **second penalty** is **immediately disqualified**.
- A boat with an uncleared Penalty Token that crosses the finish line to finish is **immediately disqualified**.

## Leaving the Board
- If a boat moves off the hex grid boundary, it is **immediately disqualified**.

## Scoring
- **Low-Point System** (per *Racing Rules of Sailing, Appendix A*):
  - 1st Place = 1 point, 2nd Place = 2 points, 3rd Place = 3 points, etc.
  - Disqualified (DSQ) or Did Not Finish (DNF) = Number of entries + 1 point.
- The player with the **lowest cumulative score** across all races wins the regatta.

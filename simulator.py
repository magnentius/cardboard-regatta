#!/usr/bin/env python3
"""
Cardboard Regatta - Python Playtest Simulator Engine
=====================================================
A complete, modular simulation engine for testing Cardboard Regatta rules, 
courses, wind shift dynamics, multi-boat right-of-way, multi-lap sailing, 
and game metrics (rounds played, estimated tabletop play time, maneuver stats).

Usage Example:
  python3 simulator.py --boats 4 --wind-shifts --course courses/course1_beginner_sprint.json --laps 1 --est-turn-time 90
"""

import argparse
import json
import os
import random
import time

# -----------------------------------------------------------------------------
# Hex Grid Geometry (Flat-topped Vertical Columns - Axial Coordinates)
# -----------------------------------------------------------------------------
# 0: North (0° / Up), 1: North-East (60°), 2: South-East (120°),
# 3: South (180° / Down), 4: South-West (240°), 5: North-West (300°)
DIRECTIONS = {
    0: (0, -1),   # North / 0°
    1: (1, -1),   # NE / 60°
    2: (1, 0),    # SE / 120°
    3: (0, 1),    # South / 180°
    4: (-1, 1),   # SW / 240°
    5: (-1, 0)    # NW / 300°
}

DIR_NAMES = {
    0: "0° (North)",
    1: "60° (NE)",
    2: "120° (SE)",
    3: "180° (South)",
    4: "240° (SW)",
    5: "300° (NW)"
}

# Cube-coordinate form of each hex direction, used to project a hex onto the wind
# axis. Axial (q, r) -> cube (q, -q-r, r).
CUBE_DIRECTIONS = {d: (v[0], -v[0] - v[1], v[1]) for d, v in DIRECTIONS.items()}

MAX_MOMENTUM = {"Irons": 1, "Close-Hauled": 4, "Broad Reach": 5, "Run": 4}

# Maneuver deck composition (rules.md, Actions Summary). Momentum decides how many
# of these a boat plays in a round.
#
# There are 5 Trims so that a boat can fill every slot she can realistically earn.
# With 4, the padding card forced at 5 slots actively punished the speed the Points
# of Sail table rewards: a Broad Reach boat was pushed off her best point of sail
# (cap 5 -> 4) and a Close-Hauled boat in a puff went straight into Irons. A 6th
# Trim would be dead weight — momentum 6 needs a Broad Reach AND a puff, which is
# under 0.3% of rounds.
DECK = {"Trim": 5, "Head Up": 2, "Bear Off": 2, "Luff": 2, "Tack": 1, "Gybe": 1}

# Preference order for filling slots that no maneuver was planned for: fastest first.
FILLERS = ["Trim", "Head Up", "Bear Off", "Luff"]

# A boat plays one action card per point of momentum, floored at 1 so a stopped boat
# can always Trim to get going again (or Bear Off to pivot out of Irons), and capped
# at 6, the highest momentum any point of sail can reach (Broad Reach in a puff).
MIN_SLOTS, MAX_SLOTS = 1, 6

# How close a boat must get to a mark for a rounding to count (RRS uses a
# 3-boat-length zone).
MARK_ZONE = 3

def slots_for_momentum(momentum):
    """How many action cards a boat plays this round."""
    return max(MIN_SLOTS, min(MAX_SLOTS, momentum))

# How reliably each skill level reads the wind vane before committing its cards.
FORECAST_ATTENTION = {"expert": 1.0, "intermediate": 0.75, "beginner": 0.5, "random": 0.0}

def projected_next_slots(facing, momentum, forecast_wind, forecast_puff=False):
    """Action cards a boat would have next round, once the forecast shift lands.

    This is what the wind vane is for. The physics of the current round always run on
    the current wind, but *where you choose to finish the round* should account for
    the breeze you will wake up in: the same heading can be a Close-Hauled lane now
    and dead Irons — one single action card — after a 60 degree shift.

    Mirrors the order the engine resolves the start of a round: Irons bleeds a point,
    then a puff adds one. Momentum is otherwise carried across a change of point of
    sail — only `Trim` is capped — so this deliberately does not clamp to the cap.
    """
    pos = pos_of_sail_for((facing - forecast_wind) % 6)
    projected = momentum
    if pos == "Irons":
        projected = max(0, projected - 1)
    if forecast_puff:
        projected = min(MAX_MOMENTUM[pos] + 1, projected + 1)
    return slots_for_momentum(projected)

def forecast_pos_of_sail(facing, forecast_wind):
    """The point of sail a heading will become once the forecast shift lands."""
    return pos_of_sail_for((facing - forecast_wind) % 6)

def forecast_vmg(pos, facing, target, forecast_wind):
    """Ground made good towards the target, per hex, once the forecast shift lands.

    Returns hexes closer per hex sailed: +1 for a heading that lays the target, 0 for
    one across it, negative for one away. A heading that becomes Irons is worth
    nothing, since she cannot sail it at all.

    This is what makes a wind shift matter. A shift re-labels which hex headings count
    as close-hauled, so the same heading can be a slow tack before the shift and lay
    the mark outright after it.
    """
    if pos_of_sail_for((facing - forecast_wind) % 6) == "Irons":
        return 0.0
    v = DIRECTIONS[facing]
    nxt = (pos[0] + v[0], pos[1] + v[1])
    return float(get_hex_distance(pos, target) - get_hex_distance(nxt, target))

BOAT_NAMES = [
    ("Red Pearl", "Red"),
    ("Blue Horizon", "Blue"),
    ("Green Wave", "Green"),
    ("Yellow Jacket", "Yellow"),
    ("Purple Comet", "Purple"),
    ("Orange Thunder", "Orange"),
    ("Cyan Breeze", "Cyan"),
    ("Magenta Clipper", "Magenta")
]

def get_hex_distance(p1, p2):
    """Calculates axial hex distance between two (q, r) points."""
    dq = p1[0] - p2[0]
    dr = p1[1] - p2[1]
    return (abs(dq) + abs(dr) + abs(dq + dr)) // 2

# The physical board (rules.md, Components): 21 columns wide by 29 rows tall, with the
# starting line running across the middle. That is a RECTANGLE on the table, which is not
# a constant-r box in axial coordinates — adjacent columns stagger half a hex, so a fixed
# r-range shears into a parallelogram and gives the corners of the board away.
#
# `line_rank` is precisely the visual row (rank 0 is the line, +1 is one hex upwind), so
# the honest test is a column range plus a rank range.
BOARD_COLUMNS = 21          # 10 either side of the centre of the line
BOARD_ROWS = 29             # 14 rows upwind of the line, 14 downwind

def in_bounds(pos, bounds):
    """Is this hex on the board? Columns AND rows, the way a player sees them."""
    return (bounds["q_min"] <= pos[0] <= bounds["q_max"]
            and bounds["rank_min"] <= line_rank(pos) <= bounds["rank_max"])

def get_upwind_rank(pos, wind):
    """Signed projection of a hex onto the wind axis. Higher = further upwind
    (closer to the wind source). Correct for all 6 wind headings, unlike a raw
    r-coordinate comparison, which only tracks 'upwind' while the wind is due North."""
    x, z = pos[0], pos[1]
    y = -x - z
    dx, dy, dz = CUBE_DIRECTIONS[wind]
    return (x * dx + y * dy + z * dz) / 2.0

# The course is laid out against the BASE wind and then stays put; the wind shifts
# around it. So line crossings, OCS and finishes are always judged against base wind,
# while sailing decisions (initiative, right-of-way, leg orientation) use the wind
# blowing right now.
BASE_WIND = 0

def line_rank(pos):
    """How far upwind of the start line's origin a hex sits, in hexes.

    Positive is towards the course side, negative towards the pre-start side, and
    exactly 0 means the hex is bisected by the line itself.
    """
    return get_upwind_rank(pos, BASE_WIND)

SQRT3_2 = 0.8660254037844386

def hex_to_xy(pos):
    """Physical centre of a hex, with north as +y. Used for angular geometry."""
    q, r = pos
    return (SQRT3_2 * q, -(q / 2.0 + r))

def side_of_leg(boat_pos, mark_pos, leg_dir):
    """Which side of the leg's rhumb line the boat is passing the mark on.

    +1 = left of the leg, -1 = right of it, 0 = dead on the line. Leaving a mark to
    port means keeping it on your left, so you pass to the RIGHT of the leg (-1).

    Judged from geometry rather than from where her bow happens to point: on a beat
    she is tacking, so an instantaneous heading test is close to a coin flip.
    """
    bx, by = hex_to_xy(boat_pos)
    mx, my = hex_to_xy(mark_pos)
    lx, ly = hex_to_xy(DIRECTIONS[leg_dir])
    cross = lx * (by - my) - ly * (bx - mx)
    if abs(cross) < 1e-9:
        return 0
    return 1 if cross > 0 else -1

# The wind lives in three states. Internally they are offsets from Base so the
# pendulum logic is readable; on the board they are hex headings.
WIND_OFFSET_TO_DIR = {-1: 5, 0: 0, 1: 1}    # left 300°, base 0°, right 60°
WIND_DIR_TO_OFFSET = {5: -1, 0: 0, 1: 1}

def next_wind(current, roll, hysteresis=True):
    """Where the wind goes next, and whether it arrives as a puff.

    The breeze behaves like a pendulum rather than a random walk: it tends back to
    Base. Without that, the +/-60 degree limit makes the shifted states *stickier*
    than Base — a shift roll into the limit is simply wasted, so the wind sits out
    on a corner about twice as long as it sits square. Two things pull it home:

      * "spring": a shift that would push past the limit springs the wind back to Base
      * "full": as above, and while shifted a roll of 7 also settles it back

    `hysteresis` is False, "spring", or "full".
    """
    off = WIND_DIR_TO_OFFSET[current]
    puff = roll in (2, 12)
    step = -1 if roll <= 4 else (1 if roll >= 10 else 0)

    if step:
        if off == step:
            off = 0 if hysteresis else off   # at the limit: spring home, or waste the roll
        else:
            off += step
    elif hysteresis == "full" and roll == 7 and off != 0:
        off = 0

    return WIND_OFFSET_TO_DIR[off], puff

def describe_wind_change(prev, now, puff):
    """Plain-language summary of a wind roll, for the log."""
    prev_off, now_off = WIND_DIR_TO_OFFSET[prev], WIND_DIR_TO_OFFSET[now]
    if now_off == prev_off:
        text = "STEADY"
    elif now_off == 0:
        text = "WIND RETURNS TO BASE"
    else:
        text = "SHIFT LEFT" if now_off < prev_off else "SHIFT RIGHT"
    return ("PUFF & " + text) if puff else text

def wind_shadow_hexes(pos, wind):
    """The cone of dirty air a boat casts downwind: one hex to leeward, three across
    at range two.

    Measured purely along the wind, independent of which way she is pointing — so this
    is NOT an "astern" shadow. Beating, it happens to fall behind her; running dead
    downwind it falls AHEAD of her, which is why the trailing boat blankets the leader
    on a run.

    A single-file line of two hexes — the original shape — was almost impossible to
    aim. Boats have a rival within 2 hexes on ~41% of rounds, yet only ~4% were ever
    blanketed, because covering someone needed near-exact alignment and any 60 degree
    shift slid the whole thing off her. Spreading with distance is both what real
    dirty air does and what makes the shadow usable on purpose.
    """
    dw = (wind + 3) % 6
    v = DIRECTIONS[dw]
    tip = (pos[0] + v[0], pos[1] + v[1])
    mid = (pos[0] + 2 * v[0], pos[1] + 2 * v[1])
    cone = [tip, mid]
    # The two hexes flanking the mid-point that are still exactly 2 hexes away.
    # Stepping sideways from the mid-point would reach range 3, not 2.
    for side in ((dw + 2) % 6, (dw + 4) % 6):
        sv = DIRECTIONS[side]
        cone.append((mid[0] + sv[0], mid[1] + sv[1]))
    return cone

def pos_of_sail_for(diff):
    """Point of sail from the boat's facing offset relative to the wind."""
    if diff == 0:
        return "Irons"
    if diff in (1, 5):
        return "Close-Hauled"
    if diff in (2, 4):
        return "Broad Reach"
    return "Run"

def tack_for(facing, wind, held_tack):
    """Tack is geometric: which side of the boat the wind crosses.

    With the wind from the North, a boat heading 60° (NE) has her starboard side facing
    SE and her port side facing NW — so the northerly strikes her PORT side and she is on
    port tack. Turned around: close-hauled on starboard tack in a northerly means heading
    NW, which is the standard picture on the water.

    So 60°/120° off the wind is PORT tack and 240°/300° is STARBOARD. (These were
    inverted here and in rules.md; the geometry was always right, only the label was
    wrong, but it reversed every Rule 10 crossing relative to a sailor's instinct.)

    Dead upwind (Irons) and dead downwind (Run) are ambiguous, so the boat holds the tack
    she was last unambiguously on (rules.md, 'Tack State in Irons'). Deriving this every
    time means a wind shift correctly changes which tack a boat is on without her playing
    a card."""
    diff = (facing - wind) % 6
    if diff in (1, 2):
        return "Port"
    if diff in (4, 5):
        return "Starboard"
    return held_tack

def apply_card(pos, facing, speed, held_tack, card, wind, bounds, momentum_penalty=0,
               edge_target=None):
    """Pure resolution of a single action card.

    Shared by the movement engine and the AI plan rollout so the two can never
    disagree about the physics — they previously implemented separate, divergent
    copies of every maneuver.

    `momentum_penalty` is subtracted from the point-of-sail momentum cap for boats
    sailing in another boat's wind shadow (floor of 1). It is applied here rather
    than fixed up front because a boat can change point of sail mid-round.

    `edge_target` is the hex she is sailing towards. If she runs into the board edge
    she stops there with no way on, and swings round to the best heading that points
    at it — otherwise a boat could be left pinned against the wall pointing out to
    sea, with one action slot a round and no way to use it.

    Returns (pos, facing, speed, held_tack, moved, legal, hit_edge).
    """
    diff = (facing - wind) % 6
    pos_of_sail = pos_of_sail_for(diff)

    if card == "Trim":
        legal = pos_of_sail != "Irons"
    elif card == "Head Up":
        legal = pos_of_sail != "Irons" and speed >= 1
    elif card == "Bear Off":
        legal = pos_of_sail != "Run"
    elif card == "Tack":
        legal = pos_of_sail == "Close-Hauled" and speed >= 1
    elif card == "Gybe":
        legal = pos_of_sail == "Run" and speed >= 1
    elif card == "Luff":
        legal = pos_of_sail in ("Close-Hauled", "Broad Reach", "Irons")
    else:
        return pos, facing, speed, held_tack, False, True, False   # unknown card: no effect

    # The Golden Movement Rule: at Momentum 1+ every maneuver card advances 1 hex
    # forward before rotation or momentum changes are applied. An illegal card is
    # discarded but the boat still coasts forward without rotating. Trim is the one
    # card with no momentum requirement, so it is also the way a stopped boat
    # gets going again.
    moved = False
    hit_edge = False
    if speed >= 1 or card == "Trim":
        vec = DIRECTIONS[facing]
        nxt = (pos[0] + vec[0], pos[1] + vec[1])
        if in_bounds(nxt, bounds):
            pos = nxt
            moved = True
        else:
            hit_edge = True

    if not legal:
        # Discarded without effect; the coast above already happened.
        return pos, facing, speed if not hit_edge else 0, held_tack, moved, False, hit_edge

    if card == "Trim":
        speed = min(max(1, MAX_MOMENTUM[pos_of_sail] - momentum_penalty), speed + 1)
    elif card == "Head Up":
        if diff in (1, 2):
            facing = (facing - 1) % 6
        elif diff in (4, 5):
            facing = (facing + 1) % 6
        elif diff == 3:
            # Heading up from dead downwind is ambiguous on the hex grid; she comes
            # up onto the tack she was already sailing. Starboard is 240°/300° off the
            # wind, so from a Run she heads up the +1 way.
            facing = (facing + 1) % 6 if held_tack == "Starboard" else (facing - 1) % 6
    elif card == "Bear Off":
        if diff in (1, 2):
            facing = (facing + 1) % 6
        elif diff in (4, 5):
            facing = (facing - 1) % 6
        elif diff == 0:
            # Bearing away out of Irons, likewise onto the tack she was already on.
            facing = (facing - 1) % 6 if held_tack == "Starboard" else (facing + 1) % 6
    elif card == "Tack":
        facing = (facing + 2) % 6 if diff == 5 else (facing - 2) % 6
        speed = max(0, speed - 1)
    elif card == "Gybe":
        # rules.md gives Gybe no rotation, only "flip tack downwind" (contrast Tack,
        # which explicitly rotates 120°). She stays dead downwind and the boom
        # crosses, so only the tack changes.
        held_tack = "Port" if held_tack == "Starboard" else "Starboard"
    elif card == "Luff":
        speed = max(0, speed - 1)

    if hit_edge:
        speed = 0
        if edge_target is not None:
            # She holds the hex nearest the edge and comes round onto a heading that
            # points at the mark. get_target_bearing already refuses to leave her head
            # to wind, picking the nearer close-hauled tack instead.
            facing = get_target_bearing(pos, edge_target, wind)

    return pos, facing, speed, tack_for(facing, wind, held_tack), moved, True, hit_edge

def get_target_pos(boat, course, is_prestart=False):
    """Single source of truth for the hex a boat is currently sailing towards.

    Used by both the AI plan rollout and the plan scorer. These were previously two
    separate calculations that returned opposite headings once a boat had crossed
    the finish line's latitude, which made boats oscillate and sail off the board.
    """
    if is_prestart:
        return boat.start_berth
    if boat.is_returning_ocs:
        return (course.pin_mark[0] + 1, course.pin_mark[1] + 2)
    if boat.target_mark_idx < len(course.marks):
        mark = course.marks[boat.target_mark_idx]
        if not boat.entered_zone:
            # Sail at the approach waypoint for the whole leg, not just near the mark.
            # Steering at the buoy and bending late measures worse (+30% over the rhumb
            # line versus +23%): arriving already on the correct side avoids the late
            # correction, and a failed correction costs a whole loop back.
            return mark["approach"]
        # She has reached the mark; carry on round to the exit waypoint so she leaves
        # on the correct side rather than U-turning on the near side.
        return mark["exit"]

    # Aim through the finish line. Which side the boat approaches from is fixed by the
    # course — whether the last mark lies upwind or downwind of the line — never by
    # where the boat currently is. That dependency used to make the rollout and the
    # scorer disagree, which sent boats oscillating off the board.
    last_mark_upwind = course.marks[-1]["upwind"] if course.marks else 10
    downwind_finish = last_mark_upwind > 0   # coming down from a windward mark

    # A boat that slipped past the line outside the pin/committee span did not
    # finish, so she has to work back to the course side and cross it properly.
    # Aiming through the middle of the line also pulls her into the span.
    past_the_line = line_rank(boat.pos) < 0 if downwind_finish else line_rank(boat.pos) > 0
    if past_the_line:
        return course.mark_pos(2 if downwind_finish else -2)
    return course.mark_pos(-2 if downwind_finish else 2)

def roll_2d6():
    """Rolls two 6-sided dice."""
    return random.randint(1, 6) + random.randint(1, 6)

def get_target_bearing(from_pos, to_pos, wind=None):
    """Returns the best valid hex direction (0..5) facing towards to_pos from from_pos, avoiding Irons if wind is provided."""
    dq = to_pos[0] - from_pos[0]
    dr = to_pos[1] - from_pos[1]
    
    if dq == 0 and dr == 0:
        return 0
        
    best_dir = 0
    best_dist = float("inf")
    
    for d, vec in DIRECTIONS.items():
        step_pos = (from_pos[0] + vec[0], from_pos[1] + vec[1])
        dist = get_hex_distance(step_pos, to_pos)
        if dist < best_dist:
            best_dist = dist
            best_dir = d
            
    if wind is not None and best_dir == wind:
        # Target is directly upwind. Target the closest Close-Hauled tack instead of Irons.
        tack1 = (wind + 1) % 6
        tack2 = (wind + 5) % 6
        d1 = get_hex_distance((from_pos[0] + DIRECTIONS[tack1][0], from_pos[1] + DIRECTIONS[tack1][1]), to_pos)
        d2 = get_hex_distance((from_pos[0] + DIRECTIONS[tack2][0], from_pos[1] + DIRECTIONS[tack2][1]), to_pos)
        best_dir = tack1 if d1 <= d2 else tack2
        
    return best_dir

# -----------------------------------------------------------------------------
# Course Configuration Loader
# -----------------------------------------------------------------------------
class CourseConfig:
    """Builds a race course around a start line laid perpendicular to the base wind.

    Courses are declared relative to the line rather than as absolute hexes, because
    the line's coordinates depend on the fleet size (length = boats + 2). Each mark
    gives `upwind` (hexes to windward of the line, negative for downwind) and
    `across` (hexes along the line from its centre, positive towards the committee
    boat), which is how the rulebook describes them.
    """

    def __init__(self, filepath, num_boats=4):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Course configuration file not found: {filepath}")

        with open(filepath, "r") as f:
            data = json.load(f)

        self.name = data.get("name", "Custom Course")
        self.line_length = max(2, num_boats + 2)

        # The line runs across the wind, so it zigzags: due west along it alternates
        # NW and SW, which holds the upwind rank constant instead of climbing 0.5 of
        # a hex per step the way a constant-r row does.
        self.committee_boat = (0, 0)
        self.pin_mark = self.along_line(-self.line_length)
        self.finish_pin, self.finish_committee = self.pin_mark, self.committee_boat
        self.line_rank_value = line_rank(self.committee_boat)

        self.marks = []
        for m in data.get("marks", []):
            self.marks.append({
                "id": m["id"],
                "name": m["name"],
                "pos": self.mark_pos(m["upwind"], m.get("across", 0)),
                "upwind": m["upwind"],
                "across": m.get("across", 0),
                "rounding_direction": m.get("rounding_direction", "Port"),
            })

        # Every mark gets two waypoints, which together trace a rounding arc:
        #   approach — off to the side of the INCOMING leg she must pass
        #   exit     — off to the side of the OUTGOING leg she must leave on
        # Leaving a mark to port means keeping it on her left, so on both legs she
        # stays to the right of the rhumb line. Without the exit waypoint a boat
        # simply U-turns on the near side of the mark, which is not a rounding at all
        # — the string never goes round the buoy.
        prev = self.line_centre()
        for i, m in enumerate(self.marks):
            nxt = self.marks[i + 1]["pos"] if i + 1 < len(self.marks) else self.line_centre()
            in_dir = get_target_bearing(prev, m["pos"])
            out_dir = get_target_bearing(m["pos"], nxt)
            port = m["rounding_direction"] == "Port"
            a_off = (in_dir + 1) % 6 if port else (in_dir + 5) % 6
            x_off = (out_dir + 1) % 6 if port else (out_dir + 5) % 6
            av, xv = DIRECTIONS[a_off], DIRECTIONS[x_off]
            m["leg_dir"] = in_dir
            m["approach"] = (m["pos"][0] + 2 * av[0], m["pos"][1] + 2 * av[1])
            m["exit"] = (m["pos"][0] + 2 * xv[0], m["pos"][1] + 2 * xv[1])
            prev = m["pos"]

        # One fixed board holds every course (rules.md, "Room to sail"): 21 columns by 29
        # rows, centred on the middle of the line. The fleet size changes the LENGTH of the
        # line, not the size of the water — eight boats race the same board as two, with
        # less of it to themselves.
        centre_q = self.line_centre()[0]
        half_w = (BOARD_COLUMNS - 1) // 2
        half_h = (BOARD_ROWS - 1) // 2
        self.bounds = {"q_min": centre_q - half_w, "q_max": centre_q + half_w,
                       "rank_min": -half_h, "rank_max": half_h}

        # Every mark must fit, with room to sail round it. This is a rules invariant, not
        # a preference: a course that overflows the board would trap boats against a wall.
        for m in self.marks:
            if not in_bounds(m["pos"], self.bounds):
                raise ValueError(
                    f"Course '{self.name}' does not fit the {BOARD_COLUMNS}x{BOARD_ROWS} "
                    f"board: {m['name']} at {m['pos']} is off the edge with "
                    f"{num_boats} boats.")

    def along_line(self, n):
        """The hex `n` steps along the start line from the committee boat.

        Negative goes towards the pin. Alternating NW/SW (or SE/NE going the other
        way) keeps the line square to the wind; every second hex sits exactly on it.
        """
        q, r = self.committee_boat
        for i in range(abs(n)):
            d = (5 if i % 2 == 0 else 4) if n < 0 else (2 if i % 2 == 0 else 1)
            v = DIRECTIONS[d]
            q, r = q + v[0], r + v[1]
        return (q, r)

    def line_centre(self):
        return self.along_line(-(self.line_length // 2))

    def mark_pos(self, upwind, across=0):
        """A mark `upwind` hexes to windward of the line and `across` hexes along it."""
        base = self.along_line(-(self.line_length // 2) + across)
        v = DIRECTIONS[0]   # due north: +1 upwind rank per hex
        return (base[0] + upwind * v[0], base[1] + upwind * v[1])

    def within_line_span(self, pos):
        """True if a hex lies between the pin and the committee boat, across the line."""
        lo = min(self.pin_mark[0], self.committee_boat[0])
        hi = max(self.pin_mark[0], self.committee_boat[0])
        return lo <= pos[0] <= hi

# -----------------------------------------------------------------------------
# Boat State Representation
# -----------------------------------------------------------------------------
class Boat:
    def __init__(self, boat_id, name, color, start_pos, start_facing, start_speed, skill_level="expert"):
        self.boat_id = boat_id
        self.name = name
        self.color = color
        self.pos = start_pos            # (q, r)
        self.facing = start_facing      # 0..5
        self.speed = start_speed        # 0..4
        # Tack is derived from facing vs. wind (see tack_for); _held_tack only carries
        # her through the two ambiguous headings, Irons and dead downwind.
        self._held_tack = tack_for(start_facing, 0, "Starboard")
        self.tack_side = self._held_tack
        self.skill_level = skill_level  # "expert", "intermediate", "beginner", "random"
        self.start_berth = start_pos       # her assigned berth on the start line
        self.start_slot = 0                # index of that berth along the line
        self.initiative_roll = 0.0         # d6 tie-break, rolled once per round
        self.momentum_penalty = 0          # 1 while blanketed in another boat's wind shadow
        self.closest_to_mark = float("inf")   # nearest she has been on this approach
        self.passed_correct_side = False      # reached the mark on the required hand
        self.entered_zone = False             # has she actually reached the mark
        self.step_start_pos = start_pos    # where she began the current action step
        self.step_start_facing = start_facing  # and which way she was pointing then

        self.current_lap = 1
        self.target_mark_idx = 0        # Index into course marks list
        self.is_returning_ocs = False
        self.finished = False
        self.protests = 0
        self.finish_rank = 0
        self.active_protest = False
        self.history = [start_pos]

    @property
    def momentum(self):
        return self.speed

    @momentum.setter
    def momentum(self, value):
        self.speed = value

    def get_pos_of_sail(self, wind):
        """Returns Point of Sail string based on facing relative to wind."""
        return pos_of_sail_for((self.facing - wind) % 6)

    def get_max_momentum(self, wind):
        """Max momentum for her current Point of Sail, after any wind shadow."""
        return max(1, MAX_MOMENTUM[self.get_pos_of_sail(wind)] - self.momentum_penalty)

    def get_max_speed(self, wind):
        return self.get_max_momentum(wind)

    def get_tack(self, wind):
        """Her tack right now, derived from facing vs. the current wind."""
        return tack_for(self.facing, wind, self._held_tack)

    def update_tack(self, wind):
        """Refreshes the cached tack. Call after any facing change or wind shift."""
        self._held_tack = self.get_tack(wind)
        self.tack_side = self._held_tack
        return self.tack_side

# -----------------------------------------------------------------------------
# Improved Heuristic AI Planner
# -----------------------------------------------------------------------------
class SailingAI:
    @staticmethod
    def _make_plan(slots, steering):
        """Builds a plan of exactly `slots` cards from a steering skeleton of
        (position, card) pairs, filling the remaining slots with the fastest card the
        deck still allows. Returns None if the deck cannot supply it.

        With only 4 Trims in the deck, a boat at momentum 5 or 6 physically cannot
        Trim every slot and gets padded onto steering cards instead.
        """
        plan = [None] * slots
        for p, card in steering:
            if p >= slots or plan[p] is not None:
                return None
            plan[p] = card

        counts = {}
        for card in plan:
            if card:
                counts[card] = counts.get(card, 0) + 1
                if counts[card] > DECK[card]:
                    return None

        for i in range(slots):
            if plan[i] is not None:
                continue
            for filler in FILLERS:
                if counts.get(filler, 0) < DECK[filler]:
                    plan[i] = filler
                    counts[filler] = counts.get(filler, 0) + 1
                    break
            else:
                return None
        return plan

    @staticmethod
    def build_candidate_plans(slots, wide_search, is_prestart):
        """Candidate action plans of exactly `slots` cards, all deck-legal."""
        skeletons = [[]]   # straight line: fill everything with Trim (then padding)

        for card in ("Tack", "Gybe", "Bear Off", "Head Up", "Luff"):
            for p in range(min(slots, 3)):
                skeletons.append([(p, card)])

        if wide_search or slots >= 4:
            pairs = [("Bear Off", "Bear Off"), ("Head Up", "Head Up"),
                     ("Bear Off", "Tack"), ("Tack", "Head Up"),
                     # Already on a Run: Gybe swaps her tack without turning her, so
                     # she needs a Head Up straight after to come up on the new side.
                     ("Gybe", "Head Up")]
            for a, b in pairs:
                for p in range(min(max(slots - 1, 1), 2)):
                    skeletons.append([(p, a), (p + 1, b)])

        if slots >= 3:
            # The gybe-set. Gybe is only legal on a Run, so swinging from one broad
            # reach to the other is Bear Off (down to the Run), Gybe (swap tack), Head
            # Up (onto the new reach) — three cards. Without this skeleton the AI can
            # only manage it across two rounds.
            triples = [("Bear Off", "Gybe", "Head Up"),
                       ("Head Up", "Tack", "Bear Off")]
            for a, b, c in triples:
                for p in range(min(max(slots - 2, 1), 2)):
                    skeletons.append([(p, a), (p + 1, b), (p + 2, c)])

        if is_prestart:
            # Station keeping. Luff is the one card that holds a stopped boat in
            # place, and bleeding momentum also shortens the next round, which is how
            # a boat parks on the line instead of being carried across it.
            for n in range(1, min(slots, DECK["Luff"]) + 1):
                skeletons.append([(i, "Luff") for i in range(n)])

        plans = []
        for skeleton in skeletons:
            plan = SailingAI._make_plan(slots, skeleton)
            if plan is not None and plan not in plans:
                plans.append(plan)
        return plans

    @staticmethod
    def _simulate_plan(plan, boat, wind, course, is_prestart=False, live_marks=frozenset()):
        # Dirty air caps how far Trim can build momentum for the whole round.
        """Rolls a 4-card plan forward one round through the shared physics in
        apply_card, so the AI evaluates plans against exactly the maneuvers the
        engine will execute.

        `live_marks` are the mark hexes that would earn this boat a Protest if she
        entered one. They are counted along the whole path, not just at the end: every
        card moves exactly one hex, so a mark in the middle of a plan is hit just as
        surely as one at the end, and it cannot be ducked with a Bail Out.

        Returns (pos, facing, speed, min_dist_to_target, irons_count, mark_rounded,
        illegal_maneuver_count, mark_hits).
        """
        target_pos = get_target_pos(boat, course, is_prestart)

        curr_pos = boat.pos
        curr_facing = boat.facing
        curr_speed = boat.speed
        curr_tack = boat._held_tack

        min_dist = get_hex_distance(curr_pos, target_pos)
        irons_count = 0
        illegal_maneuver_count = 0
        mark_rounded = False
        mark_hits = 0
        target_idx = boat.target_mark_idx

        for card in plan:
            if (curr_facing - wind) % 6 == 0:
                irons_count += 1

            curr_pos, curr_facing, curr_speed, curr_tack, _moved, legal, hit_edge = apply_card(
                curr_pos, curr_facing, curr_speed, curr_tack, card, wind, course.bounds,
                boat.momentum_penalty, edge_target=target_pos)

            if not legal:
                illegal_maneuver_count += 1
            if hit_edge:
                illegal_maneuver_count += 1

            if curr_pos in live_marks:
                mark_hits += 1

            dist = get_hex_distance(curr_pos, target_pos)
            if dist < min_dist:
                min_dist = dist
            if target_idx < len(course.marks):
                if get_hex_distance(curr_pos, course.marks[target_idx]["pos"]) <= 1:
                    mark_rounded = True

        return (curr_pos, curr_facing, curr_speed, min_dist, irons_count, mark_rounded,
                illegal_maneuver_count, mark_hits)

    @staticmethod
    def plan_round_actions(boat, other_boats, wind, course, slots=4, forecast_wind=None,
                           is_prestart=False, prestart_turns_left=0, forecast_puff=False,
                           live_marks=frozenset()):
        """
        Evaluates candidate action plans for the round and selects the best sequence.
        If is_prestart is True, Expert and Intermediate AI execute a Dip-Start strategy
        (holding just below the line to build speed without crossing OCS).
        """
        # Maneuver legality and movement physics are ALWAYS evaluated against the
        # current wind — the shift on the vane has not arrived yet. The forecast only
        # colours which END STATE is worth having, via projected_next_slots below.
        eval_wind = wind

        # Skill decides how reliably a skipper actually reads the vane before
        # committing cards: expert every round, intermediate 3 in 4, beginner 1 in 2.
        reads_vane = forecast_wind is not None and \
            random.random() < FORECAST_ATTENTION.get(boat.skill_level, 0.0)

        target_pos = get_target_pos(boat, course, is_prestart)
        dist_to_mark = get_hex_distance(boat.pos, target_pos)

        # Calculate current direction difference to target mark
        desired_dir = get_target_bearing(boat.pos, target_pos, eval_wind)
        curr_dir_diff = min((boat.facing - desired_dir) % 6, (desired_dir - boat.facing) % 6)

        candidate_plans = SailingAI.build_candidate_plans(
            slots, is_prestart or dist_to_mark <= 3 or curr_dir_diff >= 2, is_prestart)
        # The fastest plan the deck can supply for this slot count. Past 4 slots it is
        # no longer all-Trim, because only 4 Trims exist.
        straight_line_plan = SailingAI._make_plan(slots, [])

        # Determine Leg Orientation (Upwind vs Downwind) along the wind axis.
        # A raw r-comparison is NOT a measure of upwind progress on this grid: a NW
        # step (300°) gains ground to windward while leaving r unchanged, and a SE
        # step (120°) gives it away. Judging legs by r sent boats reaching sideways
        # for dozens of hexes while the AI believed it was making progress.
        # The two contexts are also mutually exclusive now, so a boat can never have
        # both Tack and Gybe filtered out of her options at the same time.
        boat_rank = get_upwind_rank(boat.pos, eval_wind)
        target_rank = get_upwind_rank(target_pos, eval_wind)
        is_upwind_context = target_rank > boat_rank
        is_downwind_context = not is_upwind_context

        # No leg-orientation filtering. A Tack is only legal Close-Hauled and a Gybe
        # only on a Run, and apply_card already enforces that — illegal plans score
        # +10000 and get dropped below. Filtering on whether the *mark* happens to lie
        # upwind was actively wrong: under a shifted wind a windward mark can read as
        # downwind by rank, which deleted every Tack from the candidate list exactly
        # when the boat needed to tack for lateral separation, and sent her sailing
        # off to the board edge instead.
        filtered_plans = candidate_plans

        scored_plans = []

        for plan in filtered_plans:
            final_pos, final_facing, final_speed, min_dist, irons_count, mark_rounded, \
                illegal_maneuvers, mark_hits = \
                SailingAI._simulate_plan(plan, boat, eval_wind, course, is_prestart, live_marks)

            desired_dir = get_target_bearing(final_pos, target_pos, eval_wind)
            dir_diff = min((final_facing - desired_dir) % 6, (desired_dir - final_facing) % 6)
            end_dist = get_hex_distance(final_pos, target_pos)

            # Heuristic score for 4-card sequence
            # Momentum is worth exactly what it buys next round: action cards. A
            # skipper watching the vane values the cards she will actually HAVE once
            # the shift lands, which is what makes ending on the lifted tack — rather
            # than the one about to be headed into Irons — the better plan.
            momentum_value = projected_next_slots(final_facing, final_speed, forecast_wind, forecast_puff) \
                if reads_vane else final_speed
            score = end_dist * 100 + min_dist * 50 + dir_diff * 10 - momentum_value * 60

            if reads_vane:
                # Being shifted head-to-wind costs more than the one action the slot
                # projection shows: in Irons you cannot Trim at all, momentum keeps
                # bleeding, and it takes a Bear Off just to get sailing again.
                if forecast_pos_of_sail(final_facing, forecast_wind) == "Irons":
                    score += 600

                # Will this heading be worth anything once the shift lands? Momentum
                # alone does not answer that. A 60 degree shift re-labels which hex
                # headings are close-hauled, and beating to a mark dead upwind that is
                # the whole game: before the shift the best tack closes at 0.5 hexes of
                # ground per hex sailed, and after it the lifted tack lays the mark
                # directly at 1.0. Ending the round on the tack the shift is about to
                # lift is worth far more than the action card the projection counts.
                score -= forecast_vmg(final_pos, final_facing, target_pos,
                                      forecast_wind) * 250
            if illegal_maneuvers > 0:
                score += illegal_maneuvers * 10000  # Massive penalty to completely reject illegal maneuvers
            
            # Directional Progress Penalty: heavy penalty for a sequence that gives
            # away ground along the wind axis, in the direction away from the target.
            final_rank = get_upwind_rank(final_pos, eval_wind)
            if is_upwind_context and final_rank < boat_rank:
                score += 800  # Sagging to leeward when the target is upwind
            elif is_downwind_context and final_rank > boat_rank:
                score += 800  # Climbing to windward when the target is downwind

            # Upwind Context Bear Off Penalty: Do not bear off away from upwind target if already facing it (dir_diff <= 1)
            curr_diff_wind = (boat.facing - eval_wind) % 6
            if is_upwind_context and (curr_diff_wind != 0) and "Bear Off" in plan and dir_diff <= 1:
                score += 600  # Penalize bearing off away from upwind target mark

            curr_q_dist = abs(boat.pos[0] - target_pos[0])
            final_q_dist = abs(final_pos[0] - target_pos[0])

            if boat.skill_level == "expert":
                # Layline corridor. Going to windward a boat gains half a hex of ground
                # per hex sailed, so reaching a mark `d` to windward takes 2d hexes
                # whichever mix of tacks she uses — and over those 2d hexes she can
                # slide 2d columns sideways for free. Being off the rhumb line is
                # therefore NOT a mistake; overstanding the layline is. She is only
                # penalised once she is further off than she can still recover.
                corridor = 2 * abs(target_rank - boat_rank)
                if final_q_dist > corridor:
                    score += (final_q_dist - corridor) * 300
                # Inside the corridor, prefer the tack that is already converging, but
                # gently — not enough to make her tack back and forth every round.
                elif final_q_dist < curr_q_dist:
                    score -= 40
            else:
                # Lesser skippers just steer at the mark, tacking whenever they drift
                # off the rhumb line, and pay for it in extra tacks.
                if final_q_dist > curr_q_dist:
                    score += (final_q_dist - curr_q_dist) * 300
                elif final_q_dist < curr_q_dist:
                    score -= 100

            # Upwind Tack Alignment (Across Expert & Intermediate AI):
            # On upwind legs, strongly reward tacking onto the converging tack towards target column q:
            is_wrong_tack = False
            if is_upwind_context:
                tack_starboard = (eval_wind + 1) % 6
                tack_port = (eval_wind - 1) % 6
                is_wrong_tack = (boat.pos[0] > target_pos[0] + 1 and boat.facing == tack_starboard) or \
                                (boat.pos[0] < target_pos[0] - 1 and boat.facing == tack_port)
                if is_wrong_tack:
                    if "Tack" in plan:
                        score -= 300  # Strong reward for tacking onto the converging tack towards target q
                    elif plan == straight_line_plan:
                        score += 300  # Penalty for continuing on the wrong tack away from target column q

            # Expert AI Tactical Refinements:
            # Clear Air Priority & Wind Shadow Avoidance: penalise ending in an
            # opponent's dirty air, reward holding a clear lane.
            #
            # A low-speed/stall penalty used to sit here too. Like the tack and
            # steering penalties before it, it was a hand-tuned proxy for something the
            # base score now prices directly (momentum IS next round's action count),
            # so it double-counted. Ablated over 250 five-boat races, dropping it moved
            # expert mean finishing place from 2.69 to 2.53.
            #
            # Two further terms used to live here: a straight-line/steering reward and
            # an extra penalty for playing Tack. Both were hand-tuned proxies for
            # "turning costs you speed", written when momentum had no mechanical
            # effect at all. Now that momentum IS next round's action count, the base
            # score prices that directly through `- final_speed * 60`, so the proxies
            # double-counted: they made the expert under-tack upwind and overstand the
            # mark, leaving it losing to the intermediate AI. Ablated over 200 five-
            # boat races, dropping them moved expert win/entry from 0.175 to 0.287.
            if boat.skill_level == "expert":
                # Clear Air vs Dirty Air / Wind Shadow Evaluation
                dirty_air_count = 0
                for ob in other_boats:
                    if ob is not boat and not ob.finished:
                        if final_pos in wind_shadow_hexes(ob.pos, eval_wind):
                            dirty_air_count += 1
                if dirty_air_count > 0:
                    score += dirty_air_count * 300  # Heavy penalty for ending in opponent dirty air / wind shadow
                else:
                    score -= 150  # Bonus for securing 100% Clear Air lane


            # Finish Layline Corridor Protection (ALL skill levels):
            # A boat can only finish between the pin and the committee boat, so drifting
            # outside that span is a legality problem rather than a finesse one — a boat
            # that crosses r=0 outside the line simply never finishes the race.
            if boat.target_mark_idx >= len(course.marks):
                min_q = min(course.finish_pin[0], course.finish_committee[0])
                max_q = max(course.finish_pin[0], course.finish_committee[0])
                if final_pos[0] < min_q:
                    score += (min_q - final_pos[0]) * 500  # Penalty for drifting West of pin mark
                elif final_pos[0] > max_q:
                    score += (final_pos[0] - max_q) * 500  # Penalty for drifting East of committee boat

            if irons_count > 0:
                score += irons_count * 1500  # Heavy penalty to completely eliminate plans that enter Irons
            if mark_hits > 0:
                # Marks are the single largest source of Protests, and unlike a rival a
                # buoy cannot be ducked with a Bail Out — it never moves out of the way.
                # A skipper plans AROUND a mark; she does not discover it at reveal. The
                # cost of a Protest is 2 action slots next round, so this is priced above
                # anything a single round of progress can be worth.
                score += mark_hits * 2000
            if mark_rounded:
                score -= 1000

            # Open-Water Luff Penalty (Across ALL AI skill levels):
            # Luffing bleeds speed and should ONLY be used in Pre-Start or when rounding a mark within 3 hexes.
            # In open water, penalize Luff by +500 so AI skippers never crawl downwind at Speed 1.
            if not is_prestart and "Luff" in plan:
                dist_to_mark = get_hex_distance(boat.pos, target_pos)
                if dist_to_mark > 3:
                    score += 500  # Penalize bleeding speed in open water

            # Pre-Start Lateral Containment (ALL skill levels):
            # A boat has to be between the pin and the committee boat at the gun or she
            # cannot start at all. Nothing in the pre-start scoring used to reference q,
            # so the highest-scoring line was to reach sideways along the line at full
            # speed and end up off the end of it.
            if is_prestart:
                line_lo = min(course.pin_mark[0], course.committee_boat[0])
                line_hi = max(course.pin_mark[0], course.committee_boat[0])
                if final_pos[0] < line_lo:
                    score += (line_lo - final_pos[0]) * 700
                elif final_pos[0] > line_hi:
                    score += (final_pos[0] - line_hi) * 700
                # Hold your assigned lane on the line rather than sliding along it.
                score += abs(final_pos[0] - target_pos[0]) * 150

            # Pre-Start Timing (Expert & Intermediate AI).
            # Momentum is now how many hexes a boat is FORCED to travel, so building
            # speed early just carries her away from the line — which is exactly what
            # a real skipper manages by killing speed and then accelerating onto the
            # gun. The AI needs to know how long is left to do the same.
            if is_prestart and boat.skill_level in ("expert", "intermediate"):
                final_line_rank = line_rank(final_pos)
                if final_line_rank >= 0:
                    score += 1200 if boat.skill_level == "expert" else 600  # OCS: over early

                if prestart_turns_left <= 1:
                    # The gun fires at the end of this turn. Be right on the line with
                    # every point of momentum you can carry onto the first leg.
                    score -= final_speed * 220
                    score += abs(final_line_rank + 1) * 300
                else:
                    # Time in hand. Hold station right below the line and do not build
                    # speed you cannot hold, since each point of momentum is another
                    # hex you are obliged to sail. Weights grid-searched on race
                    # outcome: this keeps ~26% of boats on the line at the gun (vs 2%)
                    # and lifts fleet completion to 98.8%, for one extra round.
                    score += abs(final_line_rank + 1) * 700
                    score += final_speed * 200

                # Priority #2: Clear Air (Avoid opponent wind shadows and 2-hex traffic crowding)
                for ob in other_boats:
                    if ob.boat_id == boat.boat_id or ob.finished:
                        continue
                    if final_pos in wind_shadow_hexes(ob.pos, eval_wind) or get_hex_distance(final_pos, ob.pos) <= 2:
                        score += 350  # Clear air & traffic penalty

                # Priority #3: Being Right at the Start Line (Target r=1)
                line_dist = abs(line_rank(final_pos) + 1)
                score += line_dist * 120  # Penalize distance away from start line segment

                # AI Collision Avoidance: Stay away from other boats during pre-start
                if boat.skill_level in ("expert", "intermediate"):
                    for ob in other_boats:
                        if ob.boat_id == boat.boat_id or ob.finished:
                            continue
                        if get_hex_distance(final_pos, ob.pos) <= 1:
                            penalty = 300 if boat.skill_level == "expert" else 150
                            score += penalty  # Penalty for ending too close to another boat (pile-up avoidance)

            # Expert & Intermediate AI avoid finishing sequence in another boat's wind shadow during race
            elif boat.skill_level in ("expert", "intermediate"):
                for ob in other_boats:
                    if ob.boat_id == boat.boat_id or ob.finished:
                        continue
                    if final_pos in wind_shadow_hexes(ob.pos, eval_wind):
                        score += 200  # Penalty for ending the round in an opponent's wind shadow

            scored_plans.append((score, plan, illegal_maneuvers))

        # Keep only plans with no illegal maneuvers. This used to test `score < 5000`,
        # which a merely unattractive plan could trip once penalties stacked up —
        # dropping legal options and then falling back to genuinely illegal ones.
        legal_scored_plans = [sp for sp in scored_plans if sp[2] == 0]
        if not legal_scored_plans:
            legal_scored_plans = scored_plans  # every option is illegal; take the least bad

        legal_scored_plans.sort(key=lambda x: x[0])

        # Selection based on boat skill level (selecting only from legal candidate plans).
        # These rates are tuned so the rungs of the ladder are evenly spaced: each tier
        # beats the one below it in roughly 70% of head-to-head finishes. Note that
        # plan-selection quality is the ONLY lever that moves the result — weakening the
        # lesser skippers' wind-shadow avoidance or wind-vane reading measured as no
        # change at all, which says those terms carry little competitive weight.
        if boat.skill_level == "expert":
            return legal_scored_plans[0][1]
        elif boat.skill_level == "intermediate":
            # 78% top plan, otherwise the 2nd or 3rd best
            if random.random() < 0.78 or len(legal_scored_plans) < 2:
                return legal_scored_plans[0][1]
            else:
                idx = min(random.randint(1, 2), len(legal_scored_plans) - 1)
                return legal_scored_plans[idx][1]
        elif boat.skill_level == "beginner":
            # 72% top plan, otherwise anywhere in the next four.
            # Tuned so she is clearly the slowest without being lost: below about 70%
            # she stops merely losing and starts falling far enough behind to miss the
            # Finishing Window, which is a broken-feeling result rather than a weak one.
            if random.random() < 0.72 or len(legal_scored_plans) < 2:
                return legal_scored_plans[0][1]
            else:
                idx = min(random.randint(1, 4), len(legal_scored_plans) - 1)
                return legal_scored_plans[idx][1]
        elif boat.skill_level == "random":
            return random.choice(legal_scored_plans)[1]
        else:
            return scored_plans[0][1]

# -----------------------------------------------------------------------------
# Main Regatta Simulator Engine with Analytics Metrics
# -----------------------------------------------------------------------------
class RegattaSimulator:
    def __init__(self, course_path, num_boats, wind_shifts, total_laps, prestart_turns, ai_skill="expert", est_turn_time_sec=90, wind_forecast=False, log_file=None, verbose=True,
                 protest_cost=2, finish_window=20, bail_out="last", wind_hysteresis="spring"):
        self.num_boats = min(max(1, num_boats), 8)
        # The course lays itself out around a start line of boats + 2 hexes, square
        # to the base wind, so no post-hoc coordinate shifting is needed.
        self.course = CourseConfig(course_path, self.num_boats)
        self.line_length = self.course.line_length
        self.wind_shifts = wind_shifts
        self.total_laps = total_laps
        self.prestart_turns = prestart_turns
        self.ai_skill = ai_skill
        self.est_turn_time_sec = est_turn_time_sec
        self.wind_forecast = wind_forecast
        self.log_file_path = log_file
        self.verbose = verbose
        self.protest_cost = protest_cost
        # Rounds the fleet gets after the first boat finishes (0 = no limit).
        self.finish_window = finish_window
        self.first_finisher_name = None
        # Bail Out rule: False / "last" / "random" (which face-down card pays for it)
        self.bail_out = bail_out
        # Wind tends back to Base rather than random-walking into a corner.
        self.wind_hysteresis = wind_hysteresis

        self.log_handle = open(log_file, "w", encoding="utf-8") if log_file else None
        
        self.global_wind = 0  # 0: North
        self.forecast_roll = 7
        self.forecast_wind = 0
        self.forecast_puff = False
        
        self.boats = []
        self._setup_boats()
        self.finishers_count = 0
        self._initiative_index = {}
        
        # Performance & Game Metrics Tracking
        self.metrics = {
            "start_time": 0,
            "end_time": 0,
            "total_rounds_played": 0,
            "winning_round": None,
            "wind_shifts_count": 0,
            "puffs_count": 0,
            "tacks_count": 0,
            "gybes_count": 0,
            "irons_penalty_count": 0,
            "total_hexes_sailed": 0,
            "protests_count": 0,
            "boundary_hits": 0,
            "wind_shadow_rounds": 0,
            "penalties_served": 0,
            "window_expired": False,
            "bail_outs": 0
        }

    def log(self, msg):
        if self.verbose:
            print(msg)
        if self.log_handle:
            self.log_handle.write(msg + "\n")
            self.log_handle.flush()

    def _roll_next_forecast(self):
        if not self.wind_shifts:
            self.forecast_wind = self.global_wind
            self.forecast_puff = False
            return
            
        roll = roll_2d6()
        next_w, puff = next_wind(self.global_wind, roll, self.wind_hysteresis)

        self.forecast_roll = roll
        self.forecast_wind = next_w
        self.forecast_puff = puff

    def _apply_wind_shadow(self):
        """Blankets boats sitting in the 2 hexes directly downwind of another boat.

        rules.md: a boat that STARTS the round in a wind shadow has her maximum
        momentum reduced by 1 for that round (floor of 1). Shadow entered later, during
        the Movement Phase, is ignored — this is resolved once, here.

        The reduction does not stack: two boats blanketing you costs the same as one.
        Because momentum is the action count, losing a point of it costs a card, so
        being covered genuinely slows you down.
        """
        active = [b for b in self.boats if not b.finished]
        blanketed = set()
        for src in active:
            for hex_pos in wind_shadow_hexes(src.pos, self.global_wind):
                for tgt in active:
                    if tgt is not src and tgt.pos == hex_pos:
                        blanketed.add(tgt.boat_id)

        for b in active:
            b.momentum_penalty = 1 if b.boat_id in blanketed else 0
            if not b.momentum_penalty:
                continue
            self.metrics["wind_shadow_rounds"] += 1
            cap = b.get_max_momentum(self.global_wind)   # already includes the penalty
            if b.speed > cap:
                b.speed = cap
                self.log(f"🌬️ {b.name} is blanketed in dirty air! Momentum capped at {cap}.")
            else:
                self.log(f"🌬️ {b.name} is blanketed in dirty air! Max momentum {cap} this round.")

    def _setup_boats(self):
        """Places the fleet across the pre-start area, one hex to leeward of the line."""
        skill_rotation = ["expert", "intermediate", "beginner", "intermediate", "expert"]
        placed = []
        # Candidate berths: hexes along the line, one hex downwind of it.
        free_slots = list(range(-self.line_length + 1, 0))
        downwind = DIRECTIONS[(BASE_WIND + 3) % 6]

        def berth(slot):
            on_line = self.course.along_line(slot)
            return (on_line[0] + downwind[0], on_line[1] + downwind[1])

        for i in range(self.num_boats):
            name, color = BOAT_NAMES[i]
            boat_skill = skill_rotation[i % len(skill_rotation)] if self.ai_skill == "mixed" else self.ai_skill

            if boat_skill in ("expert", "intermediate") and placed and free_slots:
                # Expert/Intermediate pick the berth furthest from the boats already
                # placed, for clear air off the line.
                slot = max(free_slots, key=lambda s: min(get_hex_distance(berth(s), p) for p in placed))
            elif free_slots:
                spacing = max(1, self.line_length // (self.num_boats + 1))
                target = -self.line_length + ((i + 1) * spacing)
                slot = min(free_slots, key=lambda s: abs(s - target))
            else:
                slot = -1

            pos = berth(slot)
            placed.append(pos)
            if slot in free_slots:
                free_slots.remove(slot)

            start_facing = 1 if i % 2 == 0 else 5  # Alternate 60° NE and 300° NW
            # Every boat starts at Momentum 2 (rules.md, Race Setup). Starting at 0
            # would leave a 1-slot boat spending the entire pre-start just getting
            # under way.
            boat = Boat(i + 1, name, color, pos, start_facing, 2, skill_level=boat_skill)
            boat.start_slot = slot
            self.boats.append(boat)

    def run_simulation(self, max_rounds=None):
        if max_rounds is None:
            max_rounds = self.total_laps * 50 + 15   # same scaling the CLI uses
        self.metrics["start_time"] = time.perf_counter()
        if self.wind_forecast:
            self._roll_next_forecast()
        
        self.log(f"==================================================================")
        self.log(f"⛵ CARDBOARD REGATTA SIMULATOR Engine")
        self.log(f"==================================================================")
        self.log(f"Course: {self.course.name}")
        self.log(f"Fleet Size: {self.num_boats} Boats | Line Length: {self.line_length} Hexes ({self.num_boats} Boats + 2)")
        self.log(f"Start Line: Pin {self.course.pin_mark} <===> Committee Boat {self.course.committee_boat}")
        self.log(f"Laps: {self.total_laps} | Wind Shifts: {self.wind_shifts} | Forecast: {self.wind_forecast}")
        self.log(f"Pre-Start Countdown: {self.prestart_turns} Turns | Est. Turn Time: {self.est_turn_time_sec}s")
        self.log(f"Finishing Window: {self.finish_window or 'none'} rounds after first finisher "
                 f"| Protest Cost: {self.protest_cost} slots | Bail Out: {self.bail_out or 'off'}")
        self.log(f"------------------------------------------------------------------\n")
        
        # Pre-Start Phase
        if self.prestart_turns > 0:
            self.log(f"--- PRE-START SEQUENCE ({self.prestart_turns} Turns) ---")
            for ps_turn in range(self.prestart_turns, 0, -1):
                self.log(f"\n📢 Pre-Start Gun Countdown: {ps_turn} Turn(s) Remaining")
                self._execute_round(round_num=f"Pre-Start {ps_turn}", is_prestart=True, prestart_turns_left=ps_turn)
                
            self.log(f"\n🚀 START GUN FIRES! Checking for OCS (On Course Side) boats...")
            for b in self.boats:
                if line_rank(b.pos) > 0:
                    b.is_returning_ocs = True
                    self.log(f"⚠️ {b.name} is OCS at (q={b.pos[0]}, r={b.pos[1]})! Must return to pre-start side.")
                else:
                    self.log(f"✅ {b.name} starts legally at (q={b.pos[0]}, r={b.pos[1]}).")
            self.log(f"------------------------------------------------------------------\n")

        # Main Race Rounds
        round_num = 1
        while round_num <= max_rounds and self.finishers_count < self.num_boats:
            self.log(f"\n======================================")
            self.log(f"ROUND {round_num}")
            self.log(f"======================================")
            
            self._execute_round(round_num)
            self.metrics["total_rounds_played"] = round_num

            if all(b.finished for b in self.boats):
                break

            # Finishing Window (RRS Sailing Instructions): once the first boat is
            # home, the rest have a fixed number of rounds to get there. Anyone still
            # racing when it expires is scored DNF, which is what stops one straggler
            # holding the whole table hostage.
            first = self.metrics["winning_round"]
            if self.finish_window and isinstance(first, int) and round_num >= first + self.finish_window:
                still_out = [b.name for b in self.boats if not b.finished]
                self.metrics["window_expired"] = True
                self.log(f"\n⏱️ FINISHING WINDOW CLOSED — {self.finish_window} rounds after "
                         f"{self.first_finisher_name} finished in Round {first}.")
                self.log(f"   Scored DNF: {', '.join(still_out)}")
                break

            round_num += 1

        self.metrics["end_time"] = time.perf_counter()
        self._print_final_standings()

    def _execute_round(self, round_num, is_prestart=False, prestart_turns_left=0):
        # The line marks are live during the pre-start (rules.md, "The line marks count
        # too"), which _live_marks needs to know.
        self._is_prestart = is_prestart

        # Phase 1: Wind & Forecast Phase
        puff_active = False
        if not is_prestart:
            if self.wind_forecast:
                prev_wind = self.global_wind
                self.global_wind = self.forecast_wind
                puff_active = self.forecast_puff
                if puff_active: self.metrics["puffs_count"] += 1
                if prev_wind != self.global_wind: self.metrics["wind_shifts_count"] += 1
                self.log(f"💨 Phase 1 Wind Phase: forecast wind arrives -> {DIR_NAMES[self.global_wind]}")
            else:
                roll = roll_2d6()
                prev_wind = self.global_wind
                self.global_wind, puff_active = next_wind(prev_wind, roll, self.wind_hysteresis)
                if puff_active:
                    self.metrics["puffs_count"] += 1
                if self.global_wind != prev_wind:
                    self.metrics["wind_shifts_count"] += 1
                self.log(f"💨 Wind Roll: {roll} -> {describe_wind_change(prev_wind, self.global_wind, puff_active)} "
                         f"(Wind: {DIR_NAMES[self.global_wind]})")
        else:
            self.log(f"💨 Wind: Steady at {DIR_NAMES[self.global_wind]}")

        # Apply Speed Adjustments
        for b in self.boats:
            b.received_protest_this_round = False
            if b.finished:
                continue

            # A wind shift can put a boat on the other tack without her playing a card,
            # so tack has to be re-derived before any right-of-way is judged.
            b.update_tack(self.global_wind)

            if b.get_pos_of_sail(self.global_wind) == "Irons":
                b.speed = max(0, b.speed - 1)
                self.metrics["irons_penalty_count"] += 1
                self.log(f"⚠️ {b.name} is in Irons! Speed reduced to {b.speed}.")
                
            if puff_active:
                # A gust does nothing for a boat stalled head to wind — her sails are
                # flogging. rules.md caps Irons at 1 with or without a puff.
                if b.get_pos_of_sail(self.global_wind) == "Irons":
                    self.log(f"💨 Puff does nothing for {b.name} — she is in Irons.")
                else:
                    max_s = b.get_max_speed(self.global_wind)
                    b.speed = min(max_s + 1, b.speed + 1)
                    self.log(f"💨 Puff boosts {b.name} speed to {b.speed}!")

        # Wind Shadow is resolved once, on the positions boats hold at the start of
        # the round, and lasts the whole round. It is applied after the puff, so a
        # blanketed boat does not get to bank a gust she is not sitting in.
        self._apply_wind_shadow()

        # Phase 2: Planning Phase
        if self.wind_forecast and not is_prestart:
            self._roll_next_forecast()
            self.log(f"🔮 Wind Vane Forecast for Next Round: {DIR_NAMES[self.forecast_wind]} (2d6 Roll: {self.forecast_roll})")

        plans = {}
        for b in self.boats:
            if b.finished:
                continue

            # Momentum at the start of the round is how many action cards she plays.
            b.slots = slots_for_momentum(b.speed)

            # Serving a Protest costs action slots. The penalty is applied BEFORE
            # planning, not by truncating a finished plan — a skipper knows she is
            # serving a penalty and plans the shorter round accordingly.
            if getattr(b, "active_protest", False):
                b.slots = max(1, b.slots - self.protest_cost)
                b.active_protest = False
                self.metrics["penalties_served"] += 1
                self.log(f"📉 {b.name} serves her Protest: {self.protest_cost} fewer action "
                         f"slots this round ({b.slots} left).")

            forecast_to_pass = self.forecast_wind if self.wind_forecast else None
            puff_to_pass = self.forecast_puff if self.wind_forecast else False
            plan = SailingAI.plan_round_actions(b, self.boats, self.global_wind, self.course,
                                                slots=b.slots, forecast_wind=forecast_to_pass,
                                                is_prestart=is_prestart,
                                                prestart_turns_left=prestart_turns_left,
                                                forecast_puff=puff_to_pass,
                                                live_marks=frozenset(self._live_marks(b)))

            plans[b.boat_id] = plan
            self.log(f"📋 {b.name} (momentum {b.speed} -> {b.slots} slots) plans: {plan}")

        # Phase 3: Movement Phase (one Action Step per card played)
        # Initiative is re-read at the start of every Action Step: the furthest boat
        # to windward that has not yet moved goes next. Freezing the order for the
        # whole phase made the rule untrue almost immediately — measured over 7,741
        # steps, a frozen order differed from the live one 50.8% of the time, and put
        # the wrong boat first in 19%.
        #
        # Only boats that have NOT moved this step are ever compared, so they are all
        # still on their step-start hexes. That makes "furthest upwind not yet moved"
        # exactly equivalent to sorting once at the head of the step, with no way for
        # a mid-step move to reshuffle the running order.
        racing = [b for b in self.boats if not b.finished]
        # The d6 tie-break is rolled once and held for the round. The ORDER is still
        # re-read every step — what persists is each boat's roll, so whichever pair of
        # boats ends up level settles it the same way all round.
        for b in racing:
            b.initiative_roll = random.random()

        # Boats no longer all act the same number of times: a faster boat keeps
        # sailing in the later steps after slower boats have run out of cards.
        total_steps = max((len(plans[b.boat_id]) for b in racing), default=0)

        for step in range(total_steps):
            self.log(f"\n --- Action Step {step + 1} ---")

            # Re-read initiative from the board, on the positions boats hold now.
            # The upwind axis follows the current wind, so a shift between rounds
            # rotates it — and hands initiative to a different boat.
            active_boats = [b for b in racing
                            if not b.finished and step < len(plans[b.boat_id])]
            active_boats.sort(key=lambda x: (-get_upwind_rank(x.pos, self.global_wind),
                                             -x.speed, x.initiative_roll))
            self._initiative_index = {b.boat_id: i for i, b in enumerate(active_boats)}

            for b in active_boats:
                card = plans[b.boat_id][step]
                if card is None:
                    continue        # slot spent paying for a Bail Out
                card, bailed = self._maybe_bail_out(b, plans[b.boat_id], step, card)
                b.current_card = card
                b.step_start_pos = b.pos
                b.step_start_facing = b.facing
                prev_pos = b.pos

                if bailed:
                    # Spilled wind and held station: no movement, no rotation, and a
                    # point of momentum lost for the sudden loss of way.
                    b.speed = max(0, b.speed - 1)
                    self.log(f"   ↳ {b.name} holds at {b.pos}. Momentum {b.speed}.")
                    continue

                new_pos, new_facing, new_speed, new_tack, moved, legal, hit_edge = apply_card(
                    b.pos, b.facing, b.speed, b._held_tack, card, self.global_wind,
                    self.course.bounds, b.momentum_penalty,
                    edge_target=get_target_pos(b, self.course))

                b.pos, b.facing, b.speed, b._held_tack = new_pos, new_facing, new_speed, new_tack
                b.tack_side = new_tack
                if moved:
                    b.history.append(b.pos)
                    self.metrics["total_hexes_sailed"] += 1

                if not legal:
                    coast = f" Coasts forward to {b.pos}." if moved else ""
                    self.log(f"❌ {b.name}: {card} is illegal for her point of sail / momentum. Discarded.{coast}")
                elif card == "Tack":
                    self.metrics["tacks_count"] += 1
                    self.log(f"🔄 {b.name} TACKS at {b.pos} to {DIR_NAMES[b.facing]} ({b.tack_side} Tack). Speed: {b.speed}.")
                elif card == "Gybe":
                    self.metrics["gybes_count"] += 1
                    self.log(f"🔄 {b.name} GYBES at {b.pos} onto {b.tack_side} Tack (still {DIR_NAMES[b.facing]}).")
                elif card == "Luff":
                    where = f"Moves to {b.pos}." if moved else "Holds in place."
                    self.log(f"🛑 {b.name} plays Luff. {where} Speed reduced to {b.speed}.")
                elif card == "Trim":
                    self.log(f"⛵ {b.name} plays Trim. Moves to {b.pos}. Speed: {b.speed}.")
                else:
                    where = f"Moves to {b.pos}." if moved else "Pivots in place."
                    self.log(f"🔄 {b.name} plays {card}. {where} Heading: {DIR_NAMES[b.facing]}.")

                if hit_edge:
                    self.metrics["boundary_hits"] = self.metrics.get("boundary_hits", 0) + 1
                    self.log(f"💥 {b.name} hits the board boundary! Movement canceled, Momentum drops to 0.")

                if b.is_returning_ocs and line_rank(b.pos) <= 0:
                    b.is_returning_ocs = False
                    self.log(f"✅ {b.name} has cleared OCS penalty and is legally in the race!")

                if b.target_mark_idx < len(self.course.marks):
                    target_mark = self.course.marks[b.target_mark_idx]
                    mark_pos = target_mark["pos"]
                    dist = get_hex_distance(b.pos, mark_pos)
                    
                    # Mark Rounding: she must actually get to the mark and pass it on
                    # the required hand. This replaces a proximity-and-latitude
                    # shortcut that ignored `rounding_direction` entirely and let the
                    # Triangle's Reach Mark be credited from 6 hexes away.
                    # Judge the rounding by the angle she sweeps around the mark, not by
                    # which way she happened to be pointing at her closest point. On a
                    # beat she is tacking, so an instantaneous heading test is close to
                    # a coin flip — it failed ~9 approaches per boat, and every failure
                    # cost her a full loop back to try again.
                    #
                    # Sweeping anticlockwise leaves the mark to port; clockwise leaves it
                    # to starboard. Passing on the correct side is worth ~180 degrees, so
                    # the threshold below credits her once she is clearly round.
                    # Leaving a mark to port means passing to the RIGHT of the leg.
                    required = -1 if target_mark["rounding_direction"] == "Port" else 1
                    is_rounded = False

                    if dist <= MARK_ZONE:
                        b.entered_zone = True
                        # Any moment inside the zone on the required hand counts. Pinning
                        # this to the single closest hex meant one awkward step forced a
                        # whole loop back to try again.
                        if side_of_leg(b.pos, mark_pos, target_mark["leg_dir"]) == required:
                            b.passed_correct_side = True

                    if dist < b.closest_to_mark:
                        b.closest_to_mark = dist
                    elif dist > b.closest_to_mark:
                        if b.entered_zone and b.passed_correct_side:
                            is_rounded = True
                        elif dist > MARK_ZONE + 1:
                            b.closest_to_mark = float("inf")
                            b.passed_correct_side = False
                            b.entered_zone = False

                    if is_rounded:
                        b.closest_to_mark = float("inf")
                        b.passed_correct_side = False
                        b.entered_zone = False
                        self.log(f"🚩 {b.name} ROUNDS {target_mark['name'].upper()}! (Lap {b.current_lap})")
                        b.target_mark_idx += 1
                        if b.target_mark_idx >= len(self.course.marks) and b.current_lap < self.total_laps:
                            b.current_lap += 1
                            b.target_mark_idx = 0
                            self.log(f"🔄 {b.name} COMPLETES LAP {b.current_lap - 1}! Starting Lap {b.current_lap}.")

                if b.target_mark_idx >= len(self.course.marks) and b.current_lap == self.total_laps:
                    if self.course.within_line_span(b.pos):
                        # The final leg fixes which way the line must be crossed. A boat
                        # that wanders back over the line from the finish side has not
                        # finished (rules.md: "in the direction indicated by the final
                        # course leg"). A hex split by the line counts as the finish side.
                        was, now = line_rank(prev_pos), line_rank(b.pos)
                        last_upwind = self.course.marks[-1]["upwind"] if self.course.marks else 10
                        if last_upwind > 0:      # coming down from windward: cross to leeward
                            crossed = was > 0 >= now
                        else:                    # coming up from leeward: cross to windward
                            crossed = was < 0 <= now

                        if crossed:
                            b.finished = True
                            b.finish_round = round_num if isinstance(round_num, int) else 0
                            b.finish_step = step + 1
                            self.finishers_count += 1
                            if self.finishers_count == 1:
                                self.metrics["winning_round"] = round_num
                                self.first_finisher_name = b.name
                            split = " (split hex -> finish side)" if line_rank(b.pos) == 0 else ""
                            self.log(f"🏁 {b.name} CROSSES THE FINISH LINE at {b.pos}{split}! (Step {step + 1})")
            
            # Step-by-step hex collision & Right-of-Way protest resolution
            self._resolve_step_collisions(step)

    def _card_lands_on(self, boat, card):
        """Where a card would leave a boat, without committing to it."""
        pos, _f, _s, _t, _m, _l, _e = apply_card(
            boat.pos, boat.facing, boat.speed, boat._held_tack, card,
            self.global_wind, self.course.bounds, boat.momentum_penalty)
        return pos

    def _occupied_by_other(self, boat, hex_pos):
        return any(o is not boat and not o.finished and o.pos == hex_pos for o in self.boats)

    def _would_be_give_way(self, boat, other, hex_pos, card):
        """Would this boat be the one carrying the Protest if she takes the collision?"""
        saved_card, saved_start = getattr(boat, "current_card", ""), boat.step_start_pos
        boat.current_card, boat.step_start_pos = card, boat.pos
        foul, _row, _rule = self._adjudicate(boat, other, hex_pos)
        boat.current_card, boat.step_start_pos = saved_card, saved_start
        return foul is boat

    def _maybe_bail_out(self, boat, plan, step, card):
        """The Bail Out rule: a boat about to sail into an occupied hex may discard one
        of her remaining face-down cards to spill wind and stop short.

        She does not move this step, her momentum drops by 1, and the revealed card is
        set aside unplayed. Returns (card, bailed).

        Note this cannot be done by swapping cards. The Golden Movement Rule advances a
        boat 1 hex in her CURRENT facing before any rotation, so at momentum 1+ every
        card in the deck lands her on the same hex — a different card changes only
        which way she points on arrival, never whether she arrives. The only way to
        decline a collision is to stop.

        Because the payment is a REMAINING face-down card, a boat can never bail out on
        her last action of the round — late-round contact is still unavoidable.
        """
        if not self.bail_out or boat.speed < 1:
            return card, False

        landing = self._card_lands_on(boat, card)

        # A boat holding right of way has no reason to pay: the other boat carries the
        # Protest. She only ducks a rival when the foul would be hers.
        blocker = next((o for o in self.boats
                        if o is not boat and not o.finished and o.pos == landing), None)
        duck_boat = blocker is not None and self._would_be_give_way(boat, blocker, landing, card)

        # A mark cannot be ducked, and the reason is worth recording: bailing stops a
        # boat but does not turn her. Against a rival that works, because SHE moves and
        # the hex clears. A buoy never moves. A boat aimed at one just bails again next
        # step, burning her spare cards for nothing and hitting it anyway once she has
        # none left — measured, that cost 17.6 bail-outs a race on the Triangle to
        # avoid 0.1 mark hits per boat, and pushed DNF from 13% to 22%.
        if not duck_boat:
            return card, False
        hazard = blocker.name

        payable = [i for i in range(step + 1, len(plan)) if plan[i] is not None]
        if not payable:
            return card, False      # nothing left to pay with; she has to take her medicine

        # "last" discards the final face-down card: deterministic, no shuffling
        # mid-movement, and it costs her the end of her round.
        slot = random.choice(payable) if self.bail_out == "random" else payable[-1]
        plan[slot] = None
        self.metrics["bail_outs"] += 1
        self.log(f"😬 {boat.name} BAILS OUT — spills wind short of {hazard} at {landing}, "
                 f"setting aside {card} and discarding her Action {slot + 1} card.")
        return card, True

    def _live_marks(self, boat):
        """The marks that bound the leg this boat is sailing (RRS 31): the one she is
        rounding now and the one she has just left. Only these can be hit.

        The Committee Boat and Pin bound the starting leg and the finishing leg, so they
        are live during the **pre-start, Leg 1, and the final leg** and are scenery the
        rest of the time (rules.md, "The line marks count too"). That is what makes
        barging at the boat end a real risk rather than a free squeeze — a windward boat
        has the leeward boat's right of way on one side and a buoy that will not move on
        the other.

        On a multi-lap race only the FIRST lap's Leg 1 and the LAST lap's final leg touch
        the line; the line is not a boundary of lap 2's first leg.
        """
        n = len(self.course.marks)
        live = set()
        if boat.target_mark_idx < n:
            live.add(self.course.marks[boat.target_mark_idx]["pos"])
        if 0 < boat.target_mark_idx <= n:
            live.add(self.course.marks[boat.target_mark_idx - 1]["pos"])

        on_starting_leg = boat.current_lap == 1 and boat.target_mark_idx == 0
        on_finishing_leg = boat.target_mark_idx >= n and boat.current_lap == self.total_laps
        if getattr(self, "_is_prestart", False) or on_starting_leg or on_finishing_leg:
            live.add(self.course.committee_boat)
            live.add(self.course.pin_mark)
        return live

    def _clear_astern(self, ahead, astern, p_ahead, p_astern):
        """Was `astern` sitting in the hex directly behind `ahead`, along her heading?

        That is the whole overlap test on a hex grid. Boats move one hex per step, so
        a collision always involves boats that were neighbours — and only one of the
        six neighbouring hexes is dead astern. Anything else adjacent is an overlap,
        which is what Rule 11 governs.
        """
        v = DIRECTIONS[(getattr(ahead, "step_start_facing", ahead.facing) + 3) % 6]
        return p_astern == (p_ahead[0] + v[0], p_ahead[1] + v[1])

    def _adjudicate(self, b1, b2, hex_pos):
        """Decides which of two boats sharing a hex must keep clear.

        Returns (foul_boat, row_boat, rule_text).
        """
        c1 = getattr(b1, "current_card", "")
        c2 = getattr(b2, "current_card", "")

        # Rule 13: a tacking boat has no right-of-way over anyone who is not tacking.
        if c1 == "Tack" and c2 != "Tack":
            return b1, b2, "Rule 13 (Tacking)"
        if c2 == "Tack" and c1 != "Tack":
            return b2, b1, "Rule 13 (Tacking)"

        # A boat returning to the pre-start side after starting early has no rights at
        # all and must keep clear of everyone who started properly (rules.md, OCS
        # Right-of-Way). Checked before the tack rules, since even a starboard-tack
        # boat gets no protection while she is sailing back.
        if b1.is_returning_ocs != b2.is_returning_ocs:
            return (b1, b2, "OCS (returning boat has no rights)") if b1.is_returning_ocs \
                else (b2, b1, "OCS (returning boat has no rights)")

        # Rule 10: on opposite tacks, Port keeps clear of Starboard.
        t1 = b1.get_tack(self.global_wind)
        t2 = b2.get_tack(self.global_wind)
        if t1 != t2:
            return (b1, b2, "Rule 10 (Starboard vs Port)") if t1 == "Port" \
                else (b2, b1, "Rule 10 (Starboard vs Port)")

        # Same tack. Both boats are now in the SAME hex, so their current positions
        # carry no information about who was windward or astern — the collision has
        # to be judged from where each boat began the action step.
        p1 = getattr(b1, "step_start_pos", b1.pos)
        p2 = getattr(b2, "step_start_pos", b2.pos)

        # Rule 12: was one boat sitting DEAD ASTERN of the other at the start of the
        # step? A boat can only move one hex, so any collision involves boats that
        # were already neighbours — and of the six neighbouring hexes exactly one is
        # dead astern. That single check is the whole overlap test: astern means clear
        # astern, anywhere else adjacent means overlapped.
        if self._clear_astern(b1, b2, p1, p2):
            return b2, b1, "Rule 12 (Clear Astern)"
        if self._clear_astern(b2, b1, p2, p1):
            return b1, b2, "Rule 12 (Clear Astern)"

        # Rule 11: converging from different hexes — the windward boat keeps clear.
        u1 = get_upwind_rank(p1, self.global_wind)
        u2 = get_upwind_rank(p2, self.global_wind)
        if u1 > u2:
            return b1, b2, "Rule 11 (Windward vs Leeward)"
        if u2 > u1:
            return b2, b1, "Rule 11 (Windward vs Leeward)"

        # Dead abreast on the wind axis: neither boat is windward and neither is
        # astern. The boat that resolved later in initiative order sailed into a hex
        # the other had already taken, so she is the one who failed to keep clear.
        i1 = self._initiative_index.get(b1.boat_id, 0)
        i2 = self._initiative_index.get(b2.boat_id, 0)
        return (b1, b2, "Rule 12 (Clear Astern)") if i1 > i2 \
            else (b2, b1, "Rule 12 (Clear Astern)")

    def _issue_protest(self, boat, reason):
        """Awards a Protest card, respecting the max-1-per-round limit."""
        if getattr(boat, "received_protest_this_round", False):
            return
        boat.received_protest_this_round = True
        boat.protests += 1
        # rules.md: the card must be cleared at the next Planning Phase, costing
        # action slots. `protest_cost` makes the size of that penalty configurable.
        boat.active_protest = True
        self.metrics["protests_count"] = self.metrics.get("protests_count", 0) + 1
        self.log(f"🚩 PROTEST! {boat.name} {reason} Incurs a Protest Card (Max 1 per Round).")

    def _resolve_step_collisions(self, step):
        """Checks for hex collisions during an Action Step and issues Protest Cards based on RRS Rules 10-14."""
        occupied = {}
        for b in self.boats:
            if b.finished:
                continue
            occupied.setdefault(b.pos, []).append(b)

        for hex_pos, boats_in_hex in occupied.items():
            if len(boats_in_hex) < 2:
                continue

            # Every pair in the pile-up is adjudicated, so a third boat is no longer
            # ignored. The max-1-per-round limit caps what any one boat can collect.
            for i in range(len(boats_in_hex)):
                for j in range(i + 1, len(boats_in_hex)):
                    foul_boat, row_boat, rule_violated = self._adjudicate(
                        boats_in_hex[i], boats_in_hex[j], hex_pos)
                    self._issue_protest(
                        foul_boat,
                        f"violated {rule_violated} against {row_boat.name} at {hex_pos}!")

        # Mark collisions. Only the marks that bound the leg she is on can be hit —
        # the one she is rounding now and the one she just left (RRS 31, and rules.md
        # "a mark on the current leg"). Blundering into a buoy from a leg she is not
        # sailing is not a foul, and penalising every mark on the board made a Triangle
        # boat liable for a mark she had finished with two legs ago.
        for b in self.boats:
            if b.finished:
                continue
            if b.pos in self._live_marks(b):
                self._issue_protest(b, f"ended the step on a mark at {b.pos}!")

    def _print_final_standings(self):
        self.log(f"\n==================================================================")
        self.log(f"🏆 FINAL REGATTA RACE RESULTS (RRS Appendix A Scoring)")
        self.log(f"==================================================================")
        
        finishers = [b for b in self.boats if b.finished]
        # Sort finishers by round, then step, then boat_id
        finishers.sort(key=lambda x: (x.finish_round, x.finish_step, x.boat_id))
        
        # There is no DSQ in Cardboard Regatta: a boat either finishes or is DNF.
        dnfs = [b for b in self.boats if not b.finished]

        # Calculate RRS A7 Split Points for Dead Heat Ties
        boat_scores = {}
        curr_rank = 1
        i = 0
        while i < len(finishers):
            j = i
            while j < len(finishers) and (finishers[j].finish_round, finishers[j].finish_step) == (finishers[i].finish_round, finishers[i].finish_step):
                j += 1
            tie_count = j - i
            if tie_count == 1:
                b = finishers[i]
                b.finish_rank = curr_rank
                boat_scores[b.boat_id] = float(curr_rank)
                curr_rank += 1
            else:
                # Sum positions from curr_rank to curr_rank + tie_count - 1
                total_pts = sum(range(curr_rank, curr_rank + tie_count))
                split_pts = total_pts / float(tie_count)
                for k in range(i, j):
                    b = finishers[k]
                    b.finish_rank = curr_rank
                    boat_scores[b.boat_id] = split_pts
                curr_rank += tie_count
            i = j

        self.log(f"\n{'Rank':<8} | {'Boat Name':<16} | {'Color':<8} | {'Skill':<12} | {'Status':<10} | {'Points':<8}")
        self.log("-" * 75)
        
        for b in finishers:
            pts = boat_scores[b.boat_id]
            is_tied = list(boat_scores.values()).count(pts) > 1
            rank_str = f"T-#{b.finish_rank}" if is_tied else f"#{b.finish_rank}"
            self.log(f"{rank_str:<8} | {b.name:<16} | {b.color:<8} | {b.skill_level:<12} | FINISHED   | {pts:.1f} pts")
            
        for b in dnfs:
            pts = float(self.num_boats + 1)
            self.log(f"{'DNF':<8} | {b.name:<16} | {b.color:<8} | {b.skill_level:<12} | DNF        | {pts:.1f} pts")
            
            
        self.log("=" * 75)
        
        # ---------------------------------------------------------------------
        # GAME & METRICS ANALYTICS DASHBOARD
        # ---------------------------------------------------------------------
        tot_rounds = self.metrics["total_rounds_played"]
        win_round = self.metrics["winning_round"] if self.metrics["winning_round"] else "N/A"
        est_time_min = (tot_rounds * self.est_turn_time_sec) / 60.0
        cpu_time_ms = (self.metrics["end_time"] - self.metrics["start_time"]) * 1000.0
        completion_pct = (len(finishers) / self.num_boats) * 100.0
        
        self.log(f"\n📊 SIMULATION METRICS & ANALYTICS DASHBOARD")
        self.log("=" * 70)
        self.log(f" • AI Skill Setting Mode    : {self.ai_skill.upper()}")
        self.log(f" • Total Rounds Played      : {tot_rounds} Rounds")
        self.log(f" • Winning Round (1st Place): Round {win_round}")
        self.log(f" • Fleet Completion Rate   : {completion_pct:.1f}% ({len(finishers)}/{self.num_boats} Finished)")
        self.log(f" • Average Round Time (Est) : {self.est_turn_time_sec} seconds / round")
        self.log(f" • Est. Tabletop Playtime   : {est_time_min:.1f} minutes")
        self.log(f" • Wind Shifts Triggered    : {self.metrics['wind_shifts_count']}")
        self.log(f" • Global Puffs Triggered   : {self.metrics['puffs_count']}")
        self.log(f" • Total Tacks Executed     : {self.metrics['tacks_count']}")
        self.log(f" • Total Gybes Executed     : {self.metrics['gybes_count']}")
        self.log(f" • Irons Penalties Incurred : {self.metrics['irons_penalty_count']}")
        self.log(f" • Protest Cards Issued     : {self.metrics['protests_count']} "
                 f"({self.metrics['protests_count'] / max(1, self.num_boats):.2f} per boat)")
        self.log(f" • Protest Penalties Served : {self.metrics['penalties_served']} "
                 f"(-{self.protest_cost} action slots each)")
        self.log(f" • Bail Outs (ducked)       : {self.metrics['bail_outs']} collisions declined")
        self.log(f" • Wind Shadow Blankets     : {self.metrics['wind_shadow_rounds']} boat-rounds in dirty air")
        self.log(f" • Board Boundary Hits      : {self.metrics['boundary_hits']}")
        self.log(f" • Total Distance Sailed    : {self.metrics['total_hexes_sailed']} hex moves")
        self.log(f" • CPU Execution Time       : {cpu_time_ms:.2f} ms")
        if self.log_file_path:
            self.log(f" • Log File Written To      : {self.log_file_path}")
        self.log("=" * 70 + "\n")

# -----------------------------------------------------------------------------
# CLI Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Cardboard Regatta - Python Playtest Simulator Engine"
    )
    parser.add_argument(
        "--boats", type=int, default=4,
        help="Number of boats in the regatta (1 to 8, default: 4)"
    )
    parser.add_argument(
        "--wind-shifts", action=argparse.BooleanOptionalAction, default=True,
        help="Enable 2d6 global wind shifts (use --no-wind-shifts for a steady-wind test)"
    )
    parser.add_argument(
        "--course", type=str, default="courses/course2_windward_leeward.json",
        help="Path to course JSON configuration file (default: courses/course2_windward_leeward.json)"
    )
    parser.add_argument(
        "--laps", type=int, default=1,
        help="Number of laps for the race (default: 1)"
    )
    parser.add_argument(
        "--prestart-turns", type=int, default=3,
        help="Number of pre-start countdown turns (0 for Instant Start, default: 3)"
    )
    parser.add_argument(
        "--ai-skill", type=str, choices=["expert", "intermediate", "beginner", "mixed", "random"], default="mixed",
        help="AI skill profile: expert, intermediate, beginner, mixed, or random (default: mixed)"
    )
    parser.add_argument(
        "--est-turn-time", type=int, default=90,
        help="Estimated tabletop average seconds per round (default: 90s / 1.5 mins)"
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for reproducible playtest runs"
    )
    parser.add_argument(
        "--wind-forecast", action=argparse.BooleanOptionalAction, default=True,
        help="Show next round's wind while planning (use --no-wind-forecast to sail blind)"
    )
    parser.add_argument(
        "--log-file", type=str, default="sim_output.log",
        help="Path to output file for complete playtest simulation log (default: sim_output.log)"
    )
    parser.add_argument(
        "--wind-hysteresis", choices=["off", "spring", "full"], default="spring",
        help="How strongly the wind returns to Base. 'spring': a shift past the limit "
             "springs it home. 'full': also returns on a 7 (default: spring)"
    )
    parser.add_argument(
        "--bail-out", choices=["last", "random", "off"], default="last",
        help="Bail Out rule: discard a remaining face-down card to stop short of a "
             "collision. 'last' discards the final card, 'random' picks one (default: last)"
    )
    parser.add_argument(
        "--finish-window", type=int, default=20,
        help="Rounds the fleet gets after the first boat finishes before the race closes "
             "and the rest are scored DNF (0 = no limit, default: 20)"
    )
    parser.add_argument(
        "--protest-cost", type=int, default=2,
        help="Action slots lost when serving a Protest card (default: 2, per the rulebook)"
    )
    parser.add_argument(
        "--max-rounds", type=int, default=None,
        help="Maximum round limit before calling DNF (default: scaled by laps -> laps * 50 + 15)"
    )

    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    # Dynamic round cap scaled by number of laps (e.g. 1 Lap = 65 rounds, 2 Laps = 115 rounds, 3 Laps = 165 rounds)
    max_rounds = args.max_rounds if args.max_rounds is not None else (args.laps * 50 + 15)

    sim = RegattaSimulator(
        course_path=args.course,
        num_boats=args.boats,
        wind_shifts=args.wind_shifts,
        total_laps=args.laps,
        prestart_turns=args.prestart_turns,
        ai_skill=args.ai_skill,
        est_turn_time_sec=args.est_turn_time,
        wind_forecast=args.wind_forecast,
        log_file=args.log_file,
        verbose=True,
        protest_cost=args.protest_cost,
        finish_window=args.finish_window,
        bail_out=(False if args.bail_out == "off" else args.bail_out),
        wind_hysteresis=(False if args.wind_hysteresis == "off" else args.wind_hysteresis)
    )
    
    sim.run_simulation(max_rounds=max_rounds)

if __name__ == "__main__":
    main()

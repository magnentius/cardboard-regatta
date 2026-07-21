#!/usr/bin/env python3
"""
Cardboard Regatta - Python Playtest Simulator Engine
=====================================================
A complete, modular simulation engine for testing Cardboard Regatta rules, 
courses, wind shift dynamics, multi-boat right-of-way, multi-lap sailing, 
and game metrics (rounds played, estimated tabletop play time, maneuver stats).

Usage Example:
  python3 simulator.py --boats 4 --wind-shifts --course courses/course2_beginner_sprint.json --laps 1 --est-turn-time 90
"""

import argparse
import json
import math
import os
import random
import sys
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
    def __init__(self, filepath):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Course configuration file not found: {filepath}")
        
        with open(filepath, "r") as f:
            data = json.load(f)
            
        self.name = data.get("name", "Custom Course")
        self.bounds = data.get("board_bounds", {"q_min": -15, "q_max": 15, "r_min": -20, "r_max": 15})
        self.pin_mark = tuple(data["start_line"]["pin_mark"])
        self.committee_boat = tuple(data["start_line"]["committee_boat"])
        
        self.marks = []
        for m in data.get("marks", []):
            self.marks.append({
                "id": m["id"],
                "name": m["name"],
                "pos": tuple(m["pos"]),
                "rounding_direction": m.get("rounding_direction", "Port")
            })
            
        finish = data.get("finish_line", data["start_line"])
        self.finish_pin = tuple(finish["pin_mark"])
        self.finish_committee = tuple(finish["committee_boat"])

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
        self.tack_side = "Starboard" if start_facing in [1, 2, 3] else "Port"
        self.skill_level = skill_level  # "expert", "intermediate", "beginner", "random"
        
        self.current_lap = 1
        self.target_mark_idx = 0        # Index into course marks list
        self.is_returning_ocs = False
        self.finished = False
        self.disqualified = False
        self.red_flags = 0
        self.finish_rank = 0
        self.history = [start_pos]

    def get_pos_of_sail(self, wind):
        """Returns Point of Sail string based on facing relative to wind."""
        diff = (self.facing - wind) % 6
        if diff == 0:
            return "Irons"
        elif diff in (1, 5):
            return "Close-Hauled"
        elif diff in (2, 4):
            return "Broad Reach"
        else:
            return "Run"

    def get_max_speed(self, wind):
        """Returns max speed polar limit for current Point of Sail."""
        pos = self.get_pos_of_sail(wind)
        if pos == "Irons":
            return 1
        elif pos == "Close-Hauled":
            return 3
        elif pos == "Broad Reach":
            return 4
        else: # Run
            return 3

# -----------------------------------------------------------------------------
# Improved Heuristic AI Planner
# -----------------------------------------------------------------------------
class SailingAI:
    @staticmethod
    def _simulate_4card_plan(plan, boat, wind, course):
        """Simulates a 4-card action plan for 1 round and returns (final_pos, final_facing, final_speed, min_dist_to_target, in_irons_count, mark_rounded)."""
        if boat.is_returning_ocs:
            target_pos = (course.pin_mark[0] + 1, course.pin_mark[1] + 2)
        elif boat.target_mark_idx < len(course.marks):
            target_pos = course.marks[boat.target_mark_idx]["pos"]
        else:
            finish_mid_q = (course.finish_pin[0] + course.finish_committee[0]) // 2
            finish_mid_r = (course.finish_pin[1] + course.finish_committee[1]) // 2
            target_r = finish_mid_r - 2 if boat.pos[1] > finish_mid_r else finish_mid_r + 2
            target_pos = (finish_mid_q, target_r)

        curr_pos = boat.pos
        curr_facing = boat.facing
        curr_speed = boat.speed
        
        min_dist = get_hex_distance(curr_pos, target_pos)
        irons_count = 0
        mark_rounded = False
        target_idx = boat.target_mark_idx
        
        for card in plan:
            diff_wind = (curr_facing - wind) % 6
            in_irons = (diff_wind == 0)
            
            if in_irons:
                irons_count += 1

            if card == "Sail":
                if not in_irons:
                    vec = DIRECTIONS[curr_facing]
                    curr_pos = (curr_pos[0] + vec[0], curr_pos[1] + vec[1])
                    max_s = Boat(0, "", "", curr_pos, curr_facing, curr_speed).get_max_speed(wind)
                    curr_speed = min(max_s, curr_speed + 1)
            elif card == "Head Up":
                if not in_irons and curr_speed > 0:
                    if diff_wind in (1, 2): curr_facing = (curr_facing - 1) % 6
                    elif diff_wind in (4, 5): curr_facing = (curr_facing + 1) % 6
            elif card == "Bear Off":
                if diff_wind in (1, 2): curr_facing = (curr_facing + 1) % 6
                elif diff_wind in (4, 5): curr_facing = (curr_facing - 1) % 6
                elif diff_wind == 0: curr_facing = (curr_facing + 1) % 6
            elif card == "Tack":
                if not in_irons and diff_wind in (1, 5) and curr_speed > 1:
                    curr_facing = (curr_facing + 2) % 6 if diff_wind == 5 else (curr_facing - 2) % 6
                    curr_speed = max(0, curr_speed - 1)
            elif card == "Gybe":
                if diff_wind == 3:
                    curr_facing = (curr_facing + 2) % 6
            elif card == "Luff":
                curr_speed = max(0, curr_speed - 1)

            dist = get_hex_distance(curr_pos, target_pos)
            if dist < min_dist:
                min_dist = dist

            if target_idx < len(course.marks):
                if get_hex_distance(curr_pos, course.marks[target_idx]["pos"]) <= 1:
                    mark_rounded = True

        return curr_pos, curr_facing, curr_speed, min_dist, irons_count, mark_rounded

    @staticmethod
    def plan_round_actions(boat, other_boats, wind, course, total_laps=1, forecast_wind=None):
        """
        Evaluates candidate 4-card sequence action plans and selects the best sequence.
        If forecast_wind is provided (Wind Forecast enabled), plans using forecasted wind heading.
        """
        eval_wind = forecast_wind if forecast_wind is not None else wind

        if boat.is_returning_ocs:
            target_pos = (course.pin_mark[0] + 1, course.pin_mark[1] + 2)
        elif boat.target_mark_idx < len(course.marks):
            target_pos = course.marks[boat.target_mark_idx]["pos"]
        else:
            finish_mid_q = (course.finish_pin[0] + course.finish_committee[0]) // 2
            finish_mid_r = (course.finish_pin[1] + course.finish_committee[1]) // 2
            target_r = finish_mid_r - 2 if boat.pos[1] > finish_mid_r else finish_mid_r + 2
            target_pos = (finish_mid_q, target_r)

        # Candidate 4-card plans to test
        candidate_plans = [
            ["Sail", "Sail", "Sail", "Sail"],
            ["Tack", "Sail", "Sail", "Sail"],
            ["Sail", "Tack", "Sail", "Sail"],
            ["Sail", "Sail", "Tack", "Sail"],
            ["Bear Off", "Sail", "Sail", "Sail"],
            ["Sail", "Bear Off", "Sail", "Sail"],
            ["Head Up", "Sail", "Sail", "Sail"],
            ["Sail", "Head Up", "Sail", "Sail"],
            ["Gybe", "Sail", "Sail", "Sail"],
            ["Sail", "Gybe", "Sail", "Sail"],
            ["Bear Off", "Bear Off", "Sail", "Sail"],
            ["Bear Off", "Tack", "Sail", "Sail"],
            ["Tack", "Head Up", "Sail", "Sail"],
            ["Sail", "Sail", "Sail", "Luff"]
        ]

        scored_plans = []

        for plan in candidate_plans:
            final_pos, final_facing, final_speed, min_dist, irons_count, mark_rounded = \
                SailingAI._simulate_4card_plan(plan, boat, eval_wind, course)

            desired_dir = get_target_bearing(final_pos, target_pos, eval_wind)
            dir_diff = min((final_facing - desired_dir) % 6, (desired_dir - final_facing) % 6)
            end_dist = get_hex_distance(final_pos, target_pos)

            # Heuristic score for 4-card sequence
            score = end_dist * 100 + min_dist * 50 + dir_diff * 10 - final_speed * 5 - final_speed * 5
            
            if irons_count > 0:
                score += irons_count * 300
            if mark_rounded:
                score -= 1000

            scored_plans.append((score, plan))

        scored_plans.sort(key=lambda x: x[0])

        # Selection based on boat skill level
        if boat.skill_level == "expert":
            return scored_plans[0][1]
        elif boat.skill_level == "intermediate":
            # 85% top plan, 15% 2nd or 3rd best plan
            if random.random() < 0.85 or len(scored_plans) < 2:
                return scored_plans[0][1]
            else:
                idx = min(random.randint(1, 2), len(scored_plans) - 1)
                return scored_plans[idx][1]
        elif boat.skill_level == "beginner":
            # 60% top plan, 40% 2nd to 4th best plan
            if random.random() < 0.60 or len(scored_plans) < 2:
                return scored_plans[0][1]
            else:
                idx = min(random.randint(1, 3), len(scored_plans) - 1)
                return scored_plans[idx][1]
        elif boat.skill_level == "random":
            return random.choice(candidate_plans)
        else:
            return scored_plans[0][1]

# -----------------------------------------------------------------------------
# Main Regatta Simulator Engine with Analytics Metrics
# -----------------------------------------------------------------------------
class RegattaSimulator:
    def __init__(self, course_path, num_boats, wind_shifts, total_laps, prestart_turns, ai_skill="expert", est_turn_time_sec=90, wind_forecast=False, log_file=None, verbose=True):
        self.course = CourseConfig(course_path)
        self.num_boats = min(max(1, num_boats), 8)
        self.wind_shifts = wind_shifts
        self.total_laps = total_laps
        self.prestart_turns = prestart_turns
        self.ai_skill = ai_skill
        self.est_turn_time_sec = est_turn_time_sec
        self.wind_forecast = wind_forecast
        self.log_file_path = log_file
        self.verbose = verbose
        
        # Dynamic Start Line Length: num_boats + 1d6 roll
        self.d6_line_roll = random.randint(1, 6)
        self.line_length = self.num_boats + self.d6_line_roll
        self.course.pin_mark = (-self.line_length, 0)
        self.course.committee_boat = (0, 0)
        self.course.finish_pin = (-self.line_length, 0)
        self.course.finish_committee = (0, 0)
        
        # Re-align buoy marks with center of dynamic start line
        mid_q = -self.line_length // 2
        for m in self.course.marks:
            m["pos"] = (mid_q, m["pos"][1])
        
        self.log_handle = open(log_file, "w", encoding="utf-8") if log_file else None
        
        self.global_wind = 0  # 0: North
        self.forecast_roll = 7
        self.forecast_wind = 0
        self.forecast_puff = False
        
        self.boats = []
        self._setup_boats()
        self.finishers_count = 0
        
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
            "total_hexes_sailed": 0
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
        next_w = self.global_wind
        puff = False
        
        if roll == 2:
            puff = True
            next_w = 5 if self.global_wind == 0 else (0 if self.global_wind == 1 else self.global_wind)
        elif 3 <= roll <= 4:
            next_w = 5 if self.global_wind == 0 else (0 if self.global_wind == 1 else self.global_wind)
        elif 5 <= roll <= 9:
            next_w = self.global_wind
        elif 10 <= roll <= 11:
            next_w = 1 if self.global_wind == 0 else (0 if self.global_wind == 5 else self.global_wind)
        elif roll == 12:
            puff = True
            next_w = 1 if self.global_wind == 0 else (0 if self.global_wind == 5 else self.global_wind)
            
        self.forecast_roll = roll
        self.forecast_wind = next_w
        self.forecast_puff = puff

    def _setup_boats(self):
        """Initializes boat tokens evenly across pre-start area with assigned skill levels."""
        skill_rotation = ["expert", "intermediate", "beginner", "intermediate", "expert"]
        spacing = max(1, self.line_length // (self.num_boats + 1))
        for i in range(self.num_boats):
            name, color = BOAT_NAMES[i]
            start_q = -self.line_length + ((i + 1) * spacing)
            start_r = 1
            start_facing = 1 if i % 2 == 0 else 5  # Alternate 60° NE and 300° NW
            start_speed = 2 if self.prestart_turns == 0 else 0
            
            if self.ai_skill == "mixed":
                boat_skill = skill_rotation[i % len(skill_rotation)]
            else:
                boat_skill = self.ai_skill
                
            self.boats.append(Boat(i + 1, name, color, (start_q, start_r), start_facing, start_speed, skill_level=boat_skill))

    def run_simulation(self, max_rounds=25):
        self.metrics["start_time"] = time.perf_counter()
        if self.wind_forecast:
            self._roll_next_forecast()
        
        self.log(f"==================================================================")
        self.log(f"⛵ CARDBOARD REGATTA SIMULATOR Engine")
        self.log(f"==================================================================")
        self.log(f"Course: {self.course.name}")
        self.log(f"Fleet Size: {self.num_boats} Boats | Line Length: {self.line_length} Hexes ({self.num_boats} Boats + 1d6 Roll: {self.d6_line_roll})")
        self.log(f"Start Line: Pin {self.course.pin_mark} <===> Committee Boat {self.course.committee_boat}")
        self.log(f"Laps: {self.total_laps} | Wind Shifts: {self.wind_shifts} | Forecast: {self.wind_forecast}")
        self.log(f"Pre-Start Countdown: {self.prestart_turns} Turns | Est. Turn Time: {self.est_turn_time_sec}s")
        self.log(f"------------------------------------------------------------------\n")
        
        # Pre-Start Phase
        if self.prestart_turns > 0:
            self.log(f"--- PRE-START SEQUENCE ({self.prestart_turns} Turns) ---")
            for ps_turn in range(self.prestart_turns, 0, -1):
                self.log(f"\n📢 Pre-Start Gun Countdown: {ps_turn} Turn(s) Remaining")
                self._execute_round(round_num=f"Pre-Start {ps_turn}")
                
            self.log(f"\n🚀 START GUN FIRES! Checking for OCS (On Course Side) boats...")
            for b in self.boats:
                if b.pos[1] <= 0:
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
            
            if all(b.finished or b.disqualified for b in self.boats):
                break
                
            round_num += 1

        self.metrics["end_time"] = time.perf_counter()
        self._print_final_standings()

    def _execute_round(self, round_num):
        # Phase 2: Wind Phase
        puff_active = False
        if self.wind_shifts:
            if self.wind_forecast:
                prev_wind = self.global_wind
                self.global_wind = self.forecast_wind
                puff_active = self.forecast_puff
                if puff_active: self.metrics["puffs_count"] += 1
                if prev_wind != self.global_wind: self.metrics["wind_shifts_count"] += 1
                self.log(f"💨 Phase 2 Wind Phase: Forecasted Wind applied -> {DIR_NAMES[self.global_wind]}")
            else:
                roll = roll_2d6()
                if roll == 2:
                    puff_active = True
                    self.metrics["puffs_count"] += 1
                    self.metrics["wind_shifts_count"] += 1
                    if self.global_wind == 0: self.global_wind = 5
                    elif self.global_wind == 1: self.global_wind = 0
                    self.log(f"💨 Wind Roll: 2 -> PUFF & SHIFT LEFT! (Wind: {DIR_NAMES[self.global_wind]})")
                elif 3 <= roll <= 4:
                    self.metrics["wind_shifts_count"] += 1
                    if self.global_wind == 0: self.global_wind = 5
                    elif self.global_wind == 1: self.global_wind = 0
                    self.log(f"💨 Wind Roll: {roll} -> SHIFT LEFT! (Wind: {DIR_NAMES[self.global_wind]})")
                elif 5 <= roll <= 9:
                    self.log(f"💨 Wind Roll: {roll} -> STEADY (Wind remains {DIR_NAMES[self.global_wind]})")
                elif 10 <= roll <= 11:
                    self.metrics["wind_shifts_count"] += 1
                    if self.global_wind == 0: self.global_wind = 1
                    elif self.global_wind == 5: self.global_wind = 0
                    self.log(f"💨 Wind Roll: {roll} -> SHIFT RIGHT! (Wind: {DIR_NAMES[self.global_wind]})")
                elif roll == 12:
                    puff_active = True
                    self.metrics["puffs_count"] += 1
                    self.metrics["wind_shifts_count"] += 1
                    if self.global_wind == 0: self.global_wind = 1
                    elif self.global_wind == 5: self.global_wind = 0
                    self.log(f"💨 Wind Roll: 12 -> PUFF & SHIFT RIGHT! (Wind: {DIR_NAMES[self.global_wind]})")
        else:
            self.log(f"💨 Wind: Steady at {DIR_NAMES[self.global_wind]}")

        # Apply Speed Adjustments
        for b in self.boats:
            if b.finished or b.disqualified:
                continue
                
            if b.get_pos_of_sail(self.global_wind) == "Irons":
                b.speed = max(0, b.speed - 1)
                self.metrics["irons_penalty_count"] += 1
                self.log(f"⚠️ {b.name} is in Irons! Speed reduced to {b.speed}.")
                
            if puff_active:
                max_s = b.get_max_speed(self.global_wind)
                b.speed = min(max_s + 1, b.speed + 1)
                self.log(f"💨 Puff boosts {b.name} speed to {b.speed}!")

        # Phase 3: Planning Phase
        if self.wind_forecast:
            self._roll_next_forecast()
            self.log(f"🔮 Barometer Forecast for Next Round: {DIR_NAMES[self.forecast_wind]} (2d6 Roll: {self.forecast_roll})")

        plans = {}
        for b in self.boats:
            if b.finished or b.disqualified:
                continue
            forecast_to_pass = self.forecast_wind if self.wind_forecast else None
            plan = SailingAI.plan_round_actions(b, self.boats, self.global_wind, self.course, self.total_laps, forecast_wind=forecast_to_pass)
            plans[b.boat_id] = plan
            self.log(f"📋 {b.name} plans: {plan}")

        # Phase 4: Movement Phase (4 Action Steps)
        for step in range(4):
            self.log(f"\n --- Action Step {step + 1} ---")
            
            active_boats = [b for b in self.boats if not b.finished and not b.disqualified]
            active_boats.sort(key=lambda x: (x.pos[1], -x.speed, x.boat_id))
            
            for b in active_boats:
                card = plans[b.boat_id][step]
                prev_pos = b.pos
                prev_facing = b.facing
                
                if card == "Sail":
                    if b.get_pos_of_sail(self.global_wind) == "Irons":
                        self.log(f"❌ {b.name} cannot Sail in Irons! Action discarded.")
                    else:
                        vec = DIRECTIONS[b.facing]
                        b.pos = (b.pos[0] + vec[0], b.pos[1] + vec[1])
                        b.speed = min(b.get_max_speed(self.global_wind), b.speed + 1)
                        b.history.append(b.pos)
                        self.metrics["total_hexes_sailed"] += 1
                        self.log(f"⛵ {b.name} plays Sail. Moves to {b.pos}. Speed: {b.speed}.")
                elif card == "Head Up":
                    if b.speed == 0 or b.get_pos_of_sail(self.global_wind) == "Irons":
                        self.log(f"❌ {b.name} cannot Head Up (Speed 0 or Irons)! Action discarded.")
                    else:
                        diff = (b.facing - self.global_wind) % 6
                        if diff in (1, 2): b.facing = (b.facing - 1) % 6
                        elif diff in (4, 5): b.facing = (b.facing + 1) % 6
                        self.log(f"🔄 {b.name} plays Head Up. Heading: {DIR_NAMES[b.facing]}.")
                elif card == "Bear Off":
                    diff = (b.facing - self.global_wind) % 6
                    if diff in (1, 2): b.facing = (b.facing + 1) % 6
                    elif diff in (4, 5): b.facing = (b.facing - 1) % 6
                    elif diff == 0: b.facing = (b.facing + 1) % 6
                    self.log(f"🔄 {b.name} plays Bear Off. Heading: {DIR_NAMES[b.facing]}.")
                elif card == "Tack":
                    if b.speed <= 1 or b.get_pos_of_sail(self.global_wind) != "Close-Hauled":
                        self.log(f"❌ {b.name} illegal Tack! Action discarded.")
                    else:
                        diff = (b.facing - self.global_wind) % 6
                        b.facing = (b.facing + 2) % 6 if diff == 5 else (b.facing - 2) % 6
                        b.speed = max(0, b.speed - 1)
                        b.tack_side = "Port" if b.tack_side == "Starboard" else "Starboard"
                        self.metrics["tacks_count"] += 1
                        self.log(f"🔄 {b.name} TACKS to {DIR_NAMES[b.facing]} ({b.tack_side} Tack). Speed: {b.speed}.")
                elif card == "Gybe":
                    if b.get_pos_of_sail(self.global_wind) != "Run":
                        self.log(f"❌ {b.name} illegal Gybe! Action discarded.")
                    else:
                        diff = (b.facing - self.global_wind) % 6
                        b.facing = (b.facing + 2) % 6 if diff == 3 else (b.facing - 2) % 6
                        b.tack_side = "Port" if b.tack_side == "Starboard" else "Starboard"
                        self.metrics["gybes_count"] += 1
                        self.log(f"🔄 {b.name} GYBES to {DIR_NAMES[b.facing]} ({b.tack_side} Tack).")
                elif card == "Luff":
                    b.speed = max(0, b.speed - 1)
                    self.log(f"🛑 {b.name} plays Luff. Speed reduced to {b.speed}.")

                if b.is_returning_ocs and b.pos[1] > 0:
                    b.is_returning_ocs = False
                    self.log(f"✅ {b.name} has cleared OCS penalty and is legally in the race!")

                if b.target_mark_idx < len(self.course.marks):
                    target_mark = self.course.marks[b.target_mark_idx]
                    if get_hex_distance(b.pos, target_mark["pos"]) <= 1:
                        self.log(f"🚩 {b.name} ROUNDS {target_mark['name'].upper()}! (Lap {b.current_lap})")
                        b.target_mark_idx += 1
                        if b.target_mark_idx >= len(self.course.marks) and b.current_lap < self.total_laps:
                            b.current_lap += 1
                            b.target_mark_idx = 0
                            self.log(f"🔄 {b.name} COMPLETES LAP {b.current_lap - 1}! Starting Lap {b.current_lap}.")

                if b.target_mark_idx >= len(self.course.marks) and b.current_lap == self.total_laps:
                    min_q = min(self.course.finish_pin[0], self.course.finish_committee[0]) - 1
                    max_q = max(self.course.finish_pin[0], self.course.finish_committee[0]) + 1
                    is_between_marks = (min_q <= b.pos[0] <= max_q)
                    
                    if is_between_marks:
                        crossed_clean = (prev_pos[1] < 0 and b.pos[1] > 0) or (prev_pos[1] > 0 and b.pos[1] < 0)
                        landed_split = (prev_pos[1] != 0 and b.pos[1] == 0)
                        
                        if crossed_clean:
                            # Clean crossing past the line to finish side
                            b.finished = True
                            b.finish_round = round_num if isinstance(round_num, int) else 0
                            b.finish_step = step + 1
                            self.finishers_count += 1
                            if self.finishers_count == 1:
                                self.metrics["winning_round"] = round_num
                            self.log(f"🏁 {b.name} CLEANLY CROSSES THE FINISH LINE! (Step {step + 1})")
                        elif landed_split:
                            # Landed on bisected / split finish line hex r = 0 -> Roll 1d6
                            finish_roll = random.randint(1, 6)
                            if finish_roll >= 4:
                                b.finished = True
                                b.finish_round = round_num if isinstance(round_num, int) else 0
                                b.finish_step = step + 1
                                self.finishers_count += 1
                                if self.finishers_count == 1:
                                    self.metrics["winning_round"] = round_num
                                self.log(f"🎲 1d6 Split Finish Hex Roll: {finish_roll} -> FINISH SIDE (4-6)! 🏁 {b.name} CROSSES THE FINISH LINE! (Step {step + 1})")
                            else:
                                self.log(f"🎲 1d6 Split Finish Hex Roll: {finish_roll} -> COURSE SIDE (1-3). {b.name} remains on course side at (q={b.pos[0]}, r=0).")

    def _print_final_standings(self):
        self.log(f"\n==================================================================")
        self.log(f"🏆 FINAL REGATTA RACE RESULTS (RRS Appendix A Scoring)")
        self.log(f"==================================================================")
        
        finishers = [b for b in self.boats if b.finished]
        # Sort finishers by round, then step, then boat_id
        finishers.sort(key=lambda x: (x.finish_round, x.finish_step, x.boat_id))
        
        dnfs = [b for b in self.boats if not b.finished and not b.disqualified]
        dsqs = [b for b in self.boats if b.disqualified]
        
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
            
        for b in dsqs:
            pts = float(self.num_boats + 1)
            self.log(f"{'DSQ':<8} | {b.name:<16} | {b.color:<8} | {b.skill_level:<12} | DSQ        | {pts:.1f} pts")
            
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
        "--boats", type=int, default=3,
        help="Number of boats in the regatta (1 to 8, default: 3)"
    )
    parser.add_argument(
        "--wind-shifts", action="store_true", default=True,
        help="Enable 2d6 global wind shifts (default: True)"
    )
    parser.add_argument(
        "--no-wind-shifts", action="store_false", dest="wind_shifts",
        help="Disable wind shifts for steady wind test"
    )
    parser.add_argument(
        "--course", type=str, default="courses/course2_beginner_sprint.json",
        help="Path to course JSON configuration file (default: courses/course2_beginner_sprint.json)"
    )
    parser.add_argument(
        "--laps", type=int, default=1,
        help="Number of laps for the race (default: 1)"
    )
    parser.add_argument(
        "--prestart-turns", type=int, default=0,
        help="Number of pre-start countdown turns (0 for Instant Start, default: 0)"
    )
    parser.add_argument(
        "--ai-skill", type=str, choices=["expert", "intermediate", "beginner", "mixed", "random"], default="expert",
        help="AI skill profile: expert, intermediate, beginner, mixed, or random (default: expert)"
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
        "--wind-forecast", action="store_true", default=False,
        help="Enable Wind Forecast (Barometer mechanic: pre-rolls 2d6 wind state at end of turn for next round planning)"
    )
    parser.add_argument(
        "--log-file", type=str, default="sim_output.log",
        help="Path to output file for complete playtest simulation log (default: sim_output.log)"
    )
    parser.add_argument(
        "--max-rounds", type=int, default=25,
        help="Maximum round limit before calling DNF (default: 25)"
    )

    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

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
        verbose=True
    )
    
    sim.run_simulation(max_rounds=args.max_rounds)

if __name__ == "__main__":
    main()

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
        self.protests = 0
        self.red_flags = 0  # Backward compatibility alias
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
        diff = (self.facing - wind) % 6
        if diff == 0:
            return "Irons"
        elif diff in (1, 5):
            return "Close-Hauled"
        elif diff in (2, 4):
            return "Broad Reach"
        else:
            return "Run"

    def get_max_momentum(self, wind):
        """Returns max momentum limit for current Point of Sail."""
        pos = self.get_pos_of_sail(wind)
        if pos == "Irons":
            return 1
        elif pos == "Close-Hauled":
            return 4
        elif pos == "Broad Reach":
            return 5
        else:
            return 4

    def get_max_speed(self, wind):
        return self.get_max_momentum(wind)

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
        illegal_maneuver_count = 0
        mark_rounded = False
        target_idx = boat.target_mark_idx
        
        for card in plan:
            diff_wind = (curr_facing - wind) % 6
            in_irons = (diff_wind == 0)
            
            if in_irons:
                irons_count += 1

            if card == "Trim":
                if not in_irons:
                    vec = DIRECTIONS[curr_facing]
                    next_pos = (curr_pos[0] + vec[0], curr_pos[1] + vec[1])
                    if course.bounds["q_min"] <= next_pos[0] <= course.bounds["q_max"] and course.bounds["r_min"] <= next_pos[1] <= course.bounds["r_max"]:
                        curr_pos = next_pos
                        max_s = Boat(0, "", "", curr_pos, curr_facing, curr_speed).get_max_speed(wind)
                        curr_speed = min(max_s, curr_speed + 1)
                    else:
                        illegal_maneuver_count += 1
                        curr_speed = 0
                else:
                    illegal_maneuver_count += 1
            elif card == "Head Up":
                if not in_irons and curr_speed > 0:
                    vec = DIRECTIONS[curr_facing]
                    next_pos = (curr_pos[0] + vec[0], curr_pos[1] + vec[1])
                    if course.bounds["q_min"] <= next_pos[0] <= course.bounds["q_max"] and course.bounds["r_min"] <= next_pos[1] <= course.bounds["r_max"]:
                        curr_pos = next_pos
                        if diff_wind in (1, 2): curr_facing = (curr_facing - 1) % 6
                        elif diff_wind in (4, 5): curr_facing = (curr_facing + 1) % 6
                        else: illegal_maneuver_count += 1
                    else:
                        illegal_maneuver_count += 1
                        curr_speed = 0
                else:
                    illegal_maneuver_count += 1
            elif card == "Bear Off":
                if curr_speed >= 1:
                    vec = DIRECTIONS[curr_facing]
                    next_pos = (curr_pos[0] + vec[0], curr_pos[1] + vec[1])
                    if course.bounds["q_min"] <= next_pos[0] <= course.bounds["q_max"] and course.bounds["r_min"] <= next_pos[1] <= course.bounds["r_max"]:
                        curr_pos = next_pos
                    else:
                        illegal_maneuver_count += 1
                        curr_speed = 0
                if diff_wind in (1, 2): curr_facing = (curr_facing + 1) % 6
                elif diff_wind in (4, 5): curr_facing = (curr_facing - 1) % 6
                elif diff_wind == 0: curr_facing = (curr_facing + 1) % 6
            elif card == "Tack":
                if not in_irons and diff_wind in (1, 5) and curr_speed > 1:
                    curr_facing = (curr_facing + 2) % 6 if diff_wind == 5 else (curr_facing - 2) % 6
                    curr_speed = max(0, curr_speed - 1)
                else:
                    illegal_maneuver_count += 1
            elif card == "Gybe":
                if diff_wind == 3:
                    curr_facing = (curr_facing + 2) % 6
                else:
                    illegal_maneuver_count += 1
            elif card == "Luff":
                curr_speed = max(0, curr_speed - 1)

            dist = get_hex_distance(curr_pos, target_pos)
            if dist < min_dist:
                min_dist = dist
            if target_idx < len(course.marks):
                if get_hex_distance(curr_pos, course.marks[target_idx]["pos"]) <= 1:
                    mark_rounded = True

        return curr_pos, curr_facing, curr_speed, min_dist, irons_count, mark_rounded, illegal_maneuver_count

    @staticmethod
    def plan_round_actions(boat, other_boats, wind, course, total_laps=1, forecast_wind=None, is_prestart=False):
        """
        Evaluates candidate 4-card sequence action plans and selects the best sequence.
        If is_prestart is True, Expert and Intermediate AI execute a Dip-Start strategy (holding at r=1/r=2 to build speed without crossing OCS).
        """
        # Skill-based Wind Forecast & Planning:
        # Beginner AI checks Wind Forecast 50% of the time.
        # Intermediate AI checks Wind Forecast 75% of the time.
        # Expert AI checks Wind Forecast 100% of the time.
        # Maneuver legality and movement physics must ALWAYS be evaluated against Current Wind (wind)
        eval_wind = wind

        if is_prestart:
            if boat.skill_level in ("expert", "intermediate"):
                target_pos = (boat.pos[0], 1)
            else:
                target_pos = course.marks[0]["pos"] if len(course.marks) > 0 else (0, -10)
        elif boat.is_returning_ocs:
            target_pos = (course.pin_mark[0] + 1, course.pin_mark[1] + 2)
        elif boat.target_mark_idx < len(course.marks):
            target_pos = course.marks[boat.target_mark_idx]["pos"]
        else:
            finish_mid_q = (course.finish_pin[0] + course.finish_committee[0]) // 2
            finish_mid_r = (course.finish_pin[1] + course.finish_committee[1]) // 2
            # Final leg direction determined by position of last mark relative to finish line:
            last_mark_r = course.marks[-1]["pos"][1] if len(course.marks) > 0 else -10
            if last_mark_r > finish_mid_r:
                target_r = finish_mid_r - 2  # Upwind finish leg heading North
            else:
                target_r = finish_mid_r + 2  # Downwind finish leg heading South
            target_pos = (finish_mid_q, target_r)

        dist_to_mark = get_hex_distance(boat.pos, target_pos)

        # Calculate current direction difference to target mark
        desired_dir = get_target_bearing(boat.pos, target_pos, eval_wind)
        curr_dir_diff = min((boat.facing - desired_dir) % 6, (desired_dir - boat.facing) % 6)

        candidate_plans = [
            ["Trim", "Trim", "Trim", "Trim"],
            ["Tack", "Trim", "Trim", "Trim"],
            ["Trim", "Tack", "Trim", "Trim"],
            ["Bear Off", "Trim", "Trim", "Trim"],
            ["Trim", "Bear Off", "Trim", "Trim"],
            ["Head Up", "Trim", "Trim", "Trim"],
            ["Trim", "Head Up", "Trim", "Trim"],
            ["Gybe", "Trim", "Trim", "Trim"],
            ["Trim", "Gybe", "Trim", "Trim"],
            ["Trim", "Trim", "Trim", "Luff"],
            ["Luff", "Trim", "Trim", "Trim"]
        ]

        if is_prestart or dist_to_mark <= 3 or curr_dir_diff >= 2:
            candidate_plans.extend([
                ["Bear Off", "Bear Off", "Trim", "Trim"],
                ["Bear Off", "Tack", "Trim", "Trim"],
                ["Tack", "Head Up", "Trim", "Trim"]
            ])

        if is_prestart:
            candidate_plans.extend([
                ["Trim", "Luff", "Trim", "Trim"],
                ["Bear Off", "Luff", "Trim", "Trim"],
                ["Luff", "Luff", "Trim", "Trim"]
            ])

        # Determine Leg Orientation & Point of Sail Context (Upwind vs Downwind)
        pos_of_sail = boat.get_pos_of_sail(eval_wind)
        is_upwind_context = (target_pos[1] <= boat.pos[1]) or (pos_of_sail in ("Close-Hauled", "Close Reach", "Irons"))
        is_downwind_context = (target_pos[1] > boat.pos[1]) or (pos_of_sail in ("Broad Reach", "Running"))

        # Filter candidate plans to prevent invalid maneuver selection across ALL AI skill levels:
        # - AI should NEVER plan a Tack on a Downwind Leg (or downwind point of sail)
        # - AI should NEVER plan a Gybe on an Upwind Leg (or upwind point of sail)
        filtered_plans = []
        for plan in candidate_plans:
            if is_upwind_context and "Gybe" in plan:
                continue
            if is_downwind_context and "Tack" in plan:
                continue
            filtered_plans.append(plan)

        scored_plans = []

        for plan in filtered_plans:
            final_pos, final_facing, final_speed, min_dist, irons_count, mark_rounded, illegal_maneuvers = \
                SailingAI._simulate_4card_plan(plan, boat, eval_wind, course)

            desired_dir = get_target_bearing(final_pos, target_pos, eval_wind)
            dir_diff = min((final_facing - desired_dir) % 6, (desired_dir - final_facing) % 6)
            end_dist = get_hex_distance(final_pos, target_pos)

            # Heuristic score for 4-card sequence
            score = end_dist * 100 + min_dist * 50 + dir_diff * 10 - final_speed * 10
            if illegal_maneuvers > 0:
                score += illegal_maneuvers * 10000  # Massive penalty to completely reject illegal maneuvers
            
            # Directional Progress Penalty: Heavy penalty for sequence that moves backwards away from target
            if target_pos[1] < boat.pos[1] and final_pos[1] > boat.pos[1]:
                score += 800  # Moving South when target is North
            elif target_pos[1] > boat.pos[1] and final_pos[1] < boat.pos[1]:
                score += 800  # Moving North when target is South

            # Upwind Context Bear Off Penalty: Do not bear off away from upwind target if already facing it (dir_diff <= 1)
            curr_diff_wind = (boat.facing - eval_wind) % 6
            if is_upwind_context and (curr_diff_wind != 0) and "Bear Off" in plan and dir_diff <= 1:
                score += 600  # Penalize bearing off away from upwind target mark

            # Lateral q-alignment Scoring (Strict convergence towards target column q):
            curr_q_dist = abs(boat.pos[0] - target_pos[0])
            final_q_dist = abs(final_pos[0] - target_pos[0])
            if final_q_dist > curr_q_dist:
                score += (final_q_dist - curr_q_dist) * 300  # Penalty for moving further away from target column q
            elif final_q_dist < curr_q_dist:
                score -= 100  # Reward for converging onto target column q

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
                    elif plan == ["Trim", "Trim", "Trim", "Trim"]:
                        score += 300  # Penalty for continuing on the wrong tack away from target column q

            # Expert AI Tactical & Regatta Series Strategy Refinements:
            # 1. Pure Straight-Line VMG Priority: Reward pure 4-Trim plans ONLY when aligned towards target (dir_diff <= 1)
            # 2. Steering & Tack Overhead Penalty: Penalize unnecessary Bear Off, Head Up, or Tack when already aligned
            # 3. Clear Air Priority & Wind Shadow Avoidance: Penalize positions in opponent wind shadows; reward clear air
            # 4. Low-Speed & Stall Risk Avoidance: Avoid ending turns at Speed 1 or in Irons near upwind tacks
            if boat.skill_level == "expert":
                has_steering = any(c in plan for c in ("Bear Off", "Head Up", "Tack"))
                if plan == ["Trim", "Trim", "Trim", "Trim"] and dir_diff <= 1 and not is_wrong_tack:
                    score -= 200  # Reward pure straight-line velocity ONLY when facing target mark on correct tack
                elif has_steering and dir_diff <= 1:
                    score += 250  # Penalize unnecessary turning/steering when already pointing towards mark
                
                if "Tack" in plan and not is_wrong_tack:
                    score += 400 if dir_diff <= 1 else 200  # Momentum loss penalty for tacking

                # Clear Air vs Dirty Air / Wind Shadow Evaluation
                dirty_air_count = 0
                for ob in other_boats:
                    if ob != boat and not ob.finished:
                        upwind_vec = DIRECTIONS[eval_wind]
                        shadow_hex1 = (final_pos[0] + upwind_vec[0], final_pos[1] + upwind_vec[1])
                        shadow_hex2 = (final_pos[0] + 2 * upwind_vec[0], final_pos[1] + 2 * upwind_vec[1])
                        if ob.pos in (shadow_hex1, shadow_hex2):
                            dirty_air_count += 1
                if dirty_air_count > 0:
                    score += dirty_air_count * 300  # Heavy penalty for ending in opponent dirty air / wind shadow
                else:
                    score -= 150  # Bonus for securing 100% Clear Air lane

                # Low-Speed & Stall Risk Avoidance
                final_diff_wind = (final_facing - eval_wind) % 6
                if is_upwind_context and (final_speed <= 1 or final_diff_wind == 0):
                    score += 500  # Penalty for ending turn at low speed / near Irons on upwind leg

            # Finish Layline Corridor Protection (Expert & Intermediate AI):
            # Heavy penalty for sequences that drift outside the finish line span q in [min_q, max_q]
            if boat.target_mark_idx >= len(course.marks) and boat.skill_level in ("expert", "intermediate"):
                min_q = min(course.finish_pin[0], course.finish_committee[0])
                max_q = max(course.finish_pin[0], course.finish_committee[0])
                if final_pos[0] < min_q:
                    score += (min_q - final_pos[0]) * 500  # Penalty for drifting West of pin mark
                elif final_pos[0] > max_q:
                    score += (final_pos[0] - max_q) * 500  # Penalty for drifting East of committee boat

            if irons_count > 0:
                score += irons_count * 1500  # Heavy penalty to completely eliminate plans that enter Irons
            if mark_rounded:
                score -= 1000

            # Open-Water Luff Penalty (Across ALL AI skill levels):
            # Luffing bleeds speed and should ONLY be used in Pre-Start or when rounding a mark within 3 hexes.
            # In open water, penalize Luff by +500 so AI skippers never crawl downwind at Speed 1.
            if not is_prestart and "Luff" in plan:
                dist_to_mark = get_hex_distance(boat.pos, target_pos)
                if dist_to_mark > 3:
                    score += 500  # Penalize bleeding speed in open water

            # Pre-Start Priority Hierarchy (Expert & Intermediate AI):
            # Priority #1: Max Speed Towards Windward Mark (Build velocity while closing distance to Mark 1)
            # Priority #2: Clear Air (Avoid opponent wind shadows and traffic crowding)
            # Priority #3: Being Right at the Start Line (Hold position at r=1 or r=2 right at the line; avoid OCS r<=0 and avoid drifting back r>2)
            if is_prestart and boat.skill_level in ("expert", "intermediate"):
                if final_pos[1] <= 0:
                    score += 1000 if boat.skill_level == "expert" else 500  # Penalty for jumping gun OCS
                
                # Preferred pre-start holding position is r=1 or r=2 right behind the start line
                if final_pos[1] in (1, 2):
                    score -= 500
                elif final_pos[1] > 2:
                    score += (final_pos[1] - 2) * 500  # Heavy penalty for drifting back away from start line
                
                # Priority #1: Speed Towards Windward Mark (advancing North towards Mark 1)
                upwind_progress = boat.pos[1] - final_pos[1]  # Positive when making upwind progress North
                if upwind_progress > 0:
                    score -= upwind_progress * final_speed * 40  # Speed bonus towards Windward Mark!
                elif upwind_progress < 0:
                    score += 500  # Penalty for moving away from Windward Mark (South)

                if final_speed <= 1:
                    score += 400  # Penalty for crawling or stopping at Speed 0/1 at the gun

                # Priority #2: Clear Air (Avoid opponent wind shadows and 2-hex traffic crowding)
                downwind_vec = DIRECTIONS[(eval_wind + 3) % 6]
                for ob in other_boats:
                    if ob.boat_id == boat.boat_id or ob.finished or ob.disqualified:
                        continue
                    shadow1 = (ob.pos[0] + downwind_vec[0], ob.pos[1] + downwind_vec[1])
                    shadow2 = (ob.pos[0] + 2 * downwind_vec[0], ob.pos[1] + 2 * downwind_vec[1])
                    if final_pos in (shadow1, shadow2) or get_hex_distance(final_pos, ob.pos) <= 2:
                        score += 350  # Clear air & traffic penalty

                # Priority #3: Being Right at the Start Line (Target r=1)
                line_dist = abs(final_pos[1] - 1)
                score += line_dist * 120  # Penalize distance away from start line segment

                # AI Collision Avoidance: Stay away from other boats during pre-start
                if boat.skill_level in ("expert", "intermediate"):
                    for ob in other_boats:
                        if ob.boat_id == boat.boat_id or ob.finished or ob.disqualified:
                            continue
                        if get_hex_distance(final_pos, ob.pos) <= 1:
                            penalty = 300 if boat.skill_level == "expert" else 150
                            score += penalty  # Penalty for ending too close to another boat (pile-up avoidance)

            # Expert & Intermediate AI avoid finishing sequence in another boat's wind shadow during race
            elif boat.skill_level in ("expert", "intermediate"):
                downwind_vec = DIRECTIONS[(eval_wind + 3) % 6]
                for ob in other_boats:
                    if ob.boat_id == boat.boat_id or ob.finished or ob.disqualified:
                        continue
                    shadow1 = (ob.pos[0] + downwind_vec[0], ob.pos[1] + downwind_vec[1])
                    shadow2 = (ob.pos[0] + 2 * downwind_vec[0], ob.pos[1] + 2 * downwind_vec[1])
                    if final_pos in (shadow1, shadow2):
                        score += 200  # Penalty for planning path into opponent's wind shadow

            scored_plans.append((score, plan))

        # Filter scored_plans to strictly 100% legal plans (score < 5000) across ALL AI skill levels:
        legal_scored_plans = [sp for sp in scored_plans if sp[0] < 5000]
        if not legal_scored_plans:
            legal_scored_plans = scored_plans  # Safety fallback

        legal_scored_plans.sort(key=lambda x: x[0])

        # Selection based on boat skill level (selecting only from legal candidate plans):
        if boat.skill_level == "expert":
            return legal_scored_plans[0][1]
        elif boat.skill_level == "intermediate":
            # 90% top plan, 10% 2nd or 3rd best legal plan
            if random.random() < 0.90 or len(legal_scored_plans) < 2:
                return legal_scored_plans[0][1]
            else:
                idx = min(random.randint(1, 2), len(legal_scored_plans) - 1)
                return legal_scored_plans[idx][1]
        elif boat.skill_level == "beginner":
            # 75% top plan, 25% 2nd to 4th best legal plan
            if random.random() < 0.75 or len(legal_scored_plans) < 2:
                return legal_scored_plans[0][1]
            else:
                idx = min(random.randint(1, 3), len(legal_scored_plans) - 1)
                return legal_scored_plans[idx][1]
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
        
        # Static Start Line Length: num_boats + 2
        self.d6_line_roll = 2
        self.line_length = self.num_boats + 2
        
        # Calculate q shift to maintain course shape relative to center
        original_mid_q = (self.course.pin_mark[0] + self.course.committee_boat[0]) // 2
        new_mid_q = -self.line_length // 2
        q_shift = new_mid_q - original_mid_q
        
        self.course.pin_mark = (-self.line_length, 0)
        self.course.committee_boat = (0, 0)
        self.course.finish_pin = (-self.line_length, 0)
        self.course.finish_committee = (0, 0)
        
        # Re-align buoy marks with center of dynamic start line
        for m in self.course.marks:
            m["pos"] = (m["pos"][0] + q_shift, m["pos"][1])
        
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
        """Initializes boat tokens across pre-start area with clear-air position selection for Expert & Intermediate AI."""
        skill_rotation = ["expert", "intermediate", "beginner", "intermediate", "expert"]
        placed_positions = []
        valid_q_coords = list(range(-self.line_length + 1, 0))
        
        for i in range(self.num_boats):
            name, color = BOAT_NAMES[i]
            boat_skill = skill_rotation[i % len(skill_rotation)] if self.ai_skill == "mixed" else self.ai_skill
            
            if boat_skill in ("expert", "intermediate") and placed_positions and valid_q_coords:
                # Expert/Intermediate AI selects starting hex q that maximizes distance to already-placed boats (Clear Air!)
                best_q = valid_q_coords[0]
                best_clear_air = -1
                for cand_q in valid_q_coords:
                    min_dist = min(get_hex_distance((cand_q, 1), pos) for pos in placed_positions)
                    if min_dist > best_clear_air:
                        best_clear_air = min_dist
                        best_q = cand_q
                start_q = best_q
            else:
                spacing = max(1, self.line_length // (self.num_boats + 1))
                start_q = -self.line_length + ((i + 1) * spacing)
                
            start_r = 1
            start_facing = 1 if i % 2 == 0 else 5  # Alternate 60° NE and 300° NW
            start_speed = 2 if self.prestart_turns == 0 else 0
            
            placed_positions.append((start_q, start_r))
            if start_q in valid_q_coords:
                valid_q_coords.remove(start_q)
                
            self.boats.append(Boat(i + 1, name, color, (start_q, start_r), start_facing, start_speed, skill_level=boat_skill))

    def run_simulation(self, max_rounds=25):
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
        self.log(f"------------------------------------------------------------------\n")
        
        # Pre-Start Phase
        if self.prestart_turns > 0:
            self.log(f"--- PRE-START SEQUENCE ({self.prestart_turns} Turns) ---")
            for ps_turn in range(self.prestart_turns, 0, -1):
                self.log(f"\n📢 Pre-Start Gun Countdown: {ps_turn} Turn(s) Remaining")
                self._execute_round(round_num=f"Pre-Start {ps_turn}", is_prestart=True)
                
            self.log(f"\n🚀 START GUN FIRES! Checking for OCS (On Course Side) boats...")
            for b in self.boats:
                if b.pos[1] < 0:
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

    def _execute_round(self, round_num, is_prestart=False):
        # Phase 1: Action Roll & Event Resolution
        puff_active = False
        if not is_prestart:
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
            b.received_protest_this_round = False
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
        if self.wind_forecast and not is_prestart:
            self._roll_next_forecast()
            self.log(f"🔮 Wind Vane Forecast for Next Round: {DIR_NAMES[self.forecast_wind]} (2d6 Roll: {self.forecast_roll})")

        plans = {}
        for b in self.boats:
            if b.finished or b.disqualified:
                continue
            forecast_to_pass = self.forecast_wind if self.wind_forecast else None
            plan = SailingAI.plan_round_actions(b, self.boats, self.global_wind, self.course, self.total_laps, forecast_wind=forecast_to_pass, is_prestart=is_prestart)
            
            if getattr(b, "active_protest", False):
                plan = plan[:2] + ["Pass", "Pass"]
                b.active_protest = False
                self.log(f"📉 {b.name} serves Protest penalty (discards 2 cards).")
                
            plans[b.boat_id] = plan
            self.log(f"📋 {b.name} plans: {plan}")

        # Phase 4: Movement Phase (4 Action Steps)
        # Static Initiative: Turn order determined once at the start of Phase 4
        initiative_order = [b for b in self.boats if not b.finished and not b.disqualified]
        initiative_order.sort(key=lambda x: (x.pos[1], -x.speed, random.random()))
        
        for step in range(4):
            self.log(f"\n --- Action Step {step + 1} ---")
            
            active_boats = [b for b in initiative_order if not b.finished and not b.disqualified]
            
            for b in active_boats:
                card = plans[b.boat_id][step]
                b.current_card = card
                prev_pos = b.pos
                prev_facing = b.facing
                
                if card == "Trim":
                    if b.get_pos_of_sail(self.global_wind) == "Irons":
                        self.log(f"❌ {b.name} cannot Trim in Irons! Action discarded.")
                    else:
                        vec = DIRECTIONS[b.facing]
                        next_pos = (b.pos[0] + vec[0], b.pos[1] + vec[1])
                        if self.course.bounds["q_min"] <= next_pos[0] <= self.course.bounds["q_max"] and self.course.bounds["r_min"] <= next_pos[1] <= self.course.bounds["r_max"]:
                            b.pos = next_pos
                            b.speed = min(b.get_max_speed(self.global_wind), b.speed + 1)
                            b.history.append(b.pos)
                            self.metrics["total_hexes_sailed"] += 1
                            self.log(f"⛵ {b.name} plays Trim. Moves to {b.pos}. Speed: {b.speed}.")
                        else:
                            b.speed = 0
                            self.log(f"💥 {b.name} hits board boundary playing Trim! Speed drops to 0.")
                elif card == "Head Up":
                    if b.speed == 0 or b.get_pos_of_sail(self.global_wind) == "Irons":
                        self.log(f"❌ {b.name} cannot Head Up (Speed 0 or Irons)! Action discarded.")
                    else:
                        vec = DIRECTIONS[b.facing]
                        next_pos = (b.pos[0] + vec[0], b.pos[1] + vec[1])
                        if self.course.bounds["q_min"] <= next_pos[0] <= self.course.bounds["q_max"] and self.course.bounds["r_min"] <= next_pos[1] <= self.course.bounds["r_max"]:
                            b.pos = next_pos
                            b.history.append(b.pos)
                            self.metrics["total_hexes_sailed"] += 1
                            diff = (b.facing - self.global_wind) % 6
                            if diff in (1, 2): b.facing = (b.facing - 1) % 6
                            elif diff in (4, 5): b.facing = (b.facing + 1) % 6
                            self.log(f"🔄 {b.name} plays Head Up. Moves to {b.pos}. Heading: {DIR_NAMES[b.facing]}.")
                        else:
                            b.speed = 0
                            self.log(f"💥 {b.name} hits board boundary playing Head Up! Speed drops to 0.")
                elif card == "Bear Off":
                    hit_boundary = False
                    if b.speed >= 1:
                        vec = DIRECTIONS[b.facing]
                        next_pos = (b.pos[0] + vec[0], b.pos[1] + vec[1])
                        if self.course.bounds["q_min"] <= next_pos[0] <= self.course.bounds["q_max"] and self.course.bounds["r_min"] <= next_pos[1] <= self.course.bounds["r_max"]:
                            b.pos = next_pos
                            b.history.append(b.pos)
                            self.metrics["total_hexes_sailed"] += 1
                        else:
                            b.speed = 0
                            hit_boundary = True
                            self.log(f"💥 {b.name} hits board boundary playing Bear Off! Speed drops to 0.")
                    diff = (b.facing - self.global_wind) % 6
                    if diff in (1, 2): b.facing = (b.facing + 1) % 6
                    elif diff in (4, 5): b.facing = (b.facing - 1) % 6
                    elif diff == 0: b.facing = (b.facing + 1) % 6
                    move_str = f"Moves to {b.pos}. " if b.speed >= 1 else "Pivots in place. "
                    self.log(f"🔄 {b.name} plays Bear Off. {move_str}Heading: {DIR_NAMES[b.facing]}.")
                elif card == "Tack":
                    if b.speed <= 0 or b.get_pos_of_sail(self.global_wind) != "Close-Hauled":
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
                    if b.speed >= 1:
                        vec = DIRECTIONS[b.facing]
                        b.pos = (b.pos[0] + vec[0], b.pos[1] + vec[1])
                        b.history.append(b.pos)
                        self.metrics["total_hexes_sailed"] += 1
                        b.speed = max(0, b.speed - 1)
                        self.log(f"🛑 {b.name} plays Luff. Moves to {b.pos}. Speed reduced to {b.speed}.")
                    else:
                        self.log(f"🛑 {b.name} plays Luff at Speed 0 in place. Speed remains 0.")

                if b.is_returning_ocs and b.pos[1] >= 0:
                    b.is_returning_ocs = False
                    self.log(f"✅ {b.name} has cleared OCS penalty and is legally in the race!")

                if b.target_mark_idx < len(self.course.marks):
                    target_mark = self.course.marks[b.target_mark_idx]
                    mark_pos = target_mark["pos"]
                    dist = get_hex_distance(b.pos, mark_pos)
                    
                    # Mark Rounding Check:
                    # 1. Direct proximity check (<= 2 hexes)
                    # 2. Latitudinal passing check (passing mark latitude within 4 hexes laterally)
                    is_rounded = (dist <= 2)
                    if not is_rounded:
                        if b.target_mark_idx == 0:  # Windward Mark (Upwind leg: boat reaches or passes North of mark)
                            if b.pos[1] <= mark_pos[1] and abs(b.pos[0] - mark_pos[0]) <= 4:
                                is_rounded = True
                        elif b.target_mark_idx == 1:  # Leeward Mark (Downwind leg: boat reaches or passes South of mark)
                            if b.pos[1] >= mark_pos[1] and abs(b.pos[0] - mark_pos[0]) <= 4:
                                is_rounded = True

                    if is_rounded:
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
                        
                        # Handle leaving split hex r=0 to finish side
                        last_mark_r = self.course.marks[-1]["pos"][1] if len(self.course.marks) > 0 else -10
                        if last_mark_r > 0:  # Upwind finish leg
                            left_split_to_finish = (prev_pos[1] == 0 and b.pos[1] < 0)
                        else:  # Downwind finish leg
                            left_split_to_finish = (prev_pos[1] == 0 and b.pos[1] > 0)
                            
                        if crossed_clean or left_split_to_finish:
                            # Clean crossing past the line to finish side
                            b.finished = True
                            b.finish_round = round_num if isinstance(round_num, int) else 0
                            b.finish_step = step + 1
                            self.finishers_count += 1
                            if self.finishers_count == 1:
                                self.metrics["winning_round"] = round_num
                            self.log(f"🏁 {b.name} CLEANLY CROSSES THE FINISH LINE! (Step {step + 1})")
                        elif prev_pos[1] != 0 and b.pos[1] == 0:
                            # Landed on bisected / split finish line hex r = 0 -> Always Finish Side
                            b.finished = True
                            b.finish_round = round_num if isinstance(round_num, int) else 0
                            b.finish_step = step + 1
                            self.finishers_count += 1
                            if self.finishers_count == 1:
                                self.metrics["winning_round"] = round_num
                            self.log(f"🏁 Split Finish Hex -> FINISH SIDE! {b.name} CROSSES THE FINISH LINE! (Step {step + 1})")
            
            # Step-by-step hex collision & Right-of-Way protest resolution
            self._resolve_step_collisions(step)

    def _resolve_step_collisions(self, step):
        """Checks for hex collisions during an Action Step and issues Protest Cards based on RRS Rules 10-14."""
        occupied = {}
        for b in self.boats:
            if b.finished or b.disqualified:
                continue
            occupied.setdefault(b.pos, []).append(b)

        for hex_pos, boats_in_hex in occupied.items():
            if len(boats_in_hex) < 2:
                continue
            
            b1, b2 = boats_in_hex[0], boats_in_hex[1]
            c1 = getattr(b1, "current_card", "")
            c2 = getattr(b2, "current_card", "")

            foul_boat = None
            row_boat = None
            rule_violated = "RRS Right-of-Way"

            if c1 == "Tack" and c2 != "Tack":
                foul_boat, row_boat, rule_violated = b1, b2, "Rule 13 (Tacking)"
            elif c2 == "Tack" and c1 != "Tack":
                foul_boat, row_boat, rule_violated = b2, b1, "Rule 13 (Tacking)"
            elif b1.tack_side == "Starboard" and b2.tack_side == "Port":
                foul_boat, row_boat, rule_violated = b2, b1, "Rule 10 (Starboard vs Port)"
            elif b2.tack_side == "Starboard" and b1.tack_side == "Port":
                foul_boat, row_boat, rule_violated = b1, b2, "Rule 10 (Starboard vs Port)"
            else:
                if b1.pos[1] < b2.pos[1]:  # b1 is further North (Windward)
                    foul_boat, row_boat, rule_violated = b1, b2, "Rule 11 (Windward vs Leeward)"
                elif b2.pos[1] < b1.pos[1]:
                    foul_boat, row_boat, rule_violated = b2, b1, "Rule 11 (Windward vs Leeward)"
                else:
                    foul_boat, row_boat, rule_violated = b2, b1, "Rule 12 (Clear Astern)"

            if foul_boat:
                if not getattr(foul_boat, "received_protest_this_round", False):
                    foul_boat.received_protest_this_round = True
                    foul_boat.protests += 1
                    foul_boat.red_flags = foul_boat.protests
                    self.metrics["protests_count"] = self.metrics.get("protests_count", 0) + 1
                    self.log(f"🚩 PROTEST! {foul_boat.name} violated {rule_violated} against {row_boat.name} at {hex_pos}! Incurs a Protest Card (Max 1 per Round).")

        # Mark Collisions
        mark_hexes = [m["pos"] for m in self.course.marks]
        for b in self.boats:
            if b.finished or b.disqualified:
                continue
            if b.pos in mark_hexes:
                if not getattr(b, "received_protest_this_round", False):
                    b.received_protest_this_round = True
                    b.protests += 1
                    b.red_flags = b.protests
                    self.metrics["protests_count"] = self.metrics.get("protests_count", 0) + 1
                    self.log(f"🚩 PROTEST! {b.name} hit a mark at {b.pos}! Incurs a Protest Card (Max 1 per Round).")

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
        "--boats", type=int, default=4,
        help="Number of boats in the regatta (1 to 8, default: 4)"
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
        "--wind-forecast", action="store_true", default=True,
        help="Enable Wind Forecast (pre-rolls 2d6 wind state at end of turn for next round planning)"
    )
    parser.add_argument(
        "--no-wind-forecast", action="store_false", dest="wind_forecast",
        help="Disable Wind Forecast"
    )
    parser.add_argument(
        "--log-file", type=str, default="sim_output.log",
        help="Path to output file for complete playtest simulation log (default: sim_output.log)"
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
        verbose=True
    )
    
    sim.run_simulation(max_rounds=max_rounds)

if __name__ == "__main__":
    main()

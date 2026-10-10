import json
import random
import boto3

dynamodb = boto3.resource("dynamodb")
poses_table = dynamodb.Table("flowforge-poses")

# A higher level includes every level below it
LEVELS = {"beginner": 1, "intermediate": 2, "advanced": 3}

# The order a flow moves through: warm up, build, peak, then cool down
TYPE_ORDER = [
    "dynamic_movement",
    "static_hold",
    "balance",
    "arm_balance",
    "inversion",
    "restorative",
]

# Every flow ends with this pose
REST_POSE = "Corpse Pose"


def seconds_for(pose):
    # A per-side pose is done on both sides, so it takes twice as long
    if pose["side_mode"] == "per_side":
        return pose["duration_seconds"] * 2
    return pose["duration_seconds"]


def works_body_area(pose, body_areas):
    if "full body" in body_areas:
        return True
    if "whole_body" in pose["body_areas"]:
        return True
    for area in pose["body_areas"]:
        if area in body_areas:
            return True
    return False


def level_rank(pose):
    return LEVELS[pose["difficulty"]]


def type_rank(pose):
    return TYPE_ORDER.index(pose["pose_type"])


def lambda_handler(event, context):
    body_areas = event["body_areas"]
    difficulty = event["difficulty"]
    target_seconds = event.get("minutes", 10) * 60
    max_level = LEVELS[difficulty]

    all_poses = poses_table.scan()["Items"]

    # Step 1: find the final rest pose, and the poses allowed in a flow
    rest_pose = None
    matches = []
    for pose in all_poses:
        if pose["name"] == REST_POSE:
            rest_pose = pose
        elif pose["v1_status"] == "candidate_for_v1":
            if LEVELS[pose["difficulty"]] <= max_level and works_body_area(pose, body_areas):
                matches.append(pose)

    # Step 2: save time at the end for the final rest
    rest_seconds = min(300, target_seconds // 6)
    time_for_poses = target_seconds - rest_seconds

    # Step 3: shuffle, put the hardest poses first, then add each pose that still fits
    random.shuffle(matches)
    matches.sort(key=level_rank, reverse=True)
    chosen = []
    used_seconds = 0
    for pose in matches:
        seconds = seconds_for(pose)
        if used_seconds + seconds <= time_for_poses:
            pose["flow_seconds"] = seconds
            chosen.append(pose)
            used_seconds = used_seconds + seconds

    if len(chosen) == 0:
        return {"statusCode": 404, "body": json.dumps({"error": "No poses found for that request."})}

    # Step 4: put the poses in flow order, then end with the rest pose
    chosen.sort(key=type_rank)
    if rest_pose is not None:
        rest_pose["flow_seconds"] = rest_seconds
        chosen.append(rest_pose)

    flow = {
        "body_areas": body_areas,
        "difficulty": difficulty,
        "requested_minutes": target_seconds / 60,
        "poses": chosen,
        "total_seconds": used_seconds + rest_seconds,
    }
    return {"statusCode": 200, "body": json.dumps(flow, default=int)}

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

# The longest flow a request can ask for
MAX_MINUTES = 60


def respond(status, payload):
    # One place that builds every response, so they all look the same
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload, default=int),
    }


def read_request(event):
    # API Gateway sends the JSON as a string in event["body"].
    # A direct test passes the fields at the top level of the event.
    if "body" in event:
        try:
            return json.loads(event["body"] or "{}")
        except json.JSONDecodeError:
            return None
    return event


def check_request(request):
    # Returns an error message, or None if the request is fine
    if not isinstance(request, dict):
        return "Request body must be valid JSON."

    body_areas = request.get("body_areas")
    if not isinstance(body_areas, list) or len(body_areas) == 0:
        return "body_areas must be a list with at least one body area."
    if not all(isinstance(area, str) for area in body_areas):
        return "body_areas must only contain text."

    difficulty = request.get("difficulty")
    if not isinstance(difficulty, str) or difficulty not in LEVELS:
        return "difficulty must be beginner, intermediate, or advanced."

    minutes = request.get("minutes", 10)
    if isinstance(minutes, bool) or not isinstance(minutes, int):
        return "minutes must be a whole number."
    if minutes < 1 or minutes > MAX_MINUTES:
        return "minutes must be between 1 and " + str(MAX_MINUTES) + "."

    return None


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
    request = read_request(event)
    error = check_request(request)
    if error:
        return respond(400, {"error": error})

    body_areas = request["body_areas"]
    difficulty = request["difficulty"]
    target_seconds = request.get("minutes", 10) * 60
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
        return respond(404, {"error": "No poses found for that request."})

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
    return respond(200, flow)
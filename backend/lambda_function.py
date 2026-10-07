import json
import random
import boto3

dynamodb = boto3.resource("dynamodb")
poses_table = dynamodb.Table("flowforge-poses")


def lambda_handler(event, context):
    target_area = event["target_area"]
    difficulty = event["difficulty"]
    count = event.get("count", 3)

    # Read every pose from DynamoDB (a "scan"), fine for ~8 items
    all_poses = poses_table.scan()["Items"]

    matches = []
    for pose in all_poses:
        if pose["target_area"] == target_area and pose["difficulty"] == difficulty:
            matches.append(pose)

    if len(matches) == 0:
        return {"statusCode": 404, "body": json.dumps({"error": "No poses found for that request."})}

    chosen = random.sample(matches, min(count, len(matches)))

    total_seconds = 0
    for pose in chosen:
        total_seconds = total_seconds + pose["hold_seconds"]

    flow = {
        "target_area": target_area,
        "difficulty": difficulty,
        "poses": chosen,
        "total_seconds": total_seconds,
    }
    return {"statusCode": 200, "body": json.dumps(flow, default=int)}

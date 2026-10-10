import csv
import boto3

dynamodb = boto3.resource("dynamodb")
poses_table = dynamodb.Table("flowforge-poses")


def make_pose_id(name):
    # "Child's Pose" becomes "childs-pose"
    cleaned = name.lower().replace("'", "").replace("(", "").replace(")", "")
    return cleaned.replace(" ", "-")


# Step 1: clear out whatever is in the table now
old_items = poses_table.scan()["Items"]
with poses_table.batch_writer() as batch:
    for item in old_items:
        batch.delete_item(Key={"pose_id": item["pose_id"]})
print(f"Cleared {len(old_items)} old poses")

# Step 2: load every row of poses.csv
count = 0
with open("backend/poses.csv", newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    with poses_table.batch_writer() as batch:
        for row in reader:
            item = {
                "pose_id": make_pose_id(row["name"]),
                "name": row["name"],
                "difficulty": row["difficulty"],
                "body_areas": row["body_areas"].split(";"),
                "duration_seconds": int(row["duration_seconds"]),
                "pose_type": row["pose_type"],
                "timing_mode": row["timing_mode"],
                "side_mode": row["side_mode"],
                "v1_status": row["v1_status"],
                "review_note": row["review_note"],
            }
            batch.put_item(Item=item)
            count = count + 1

print(f"Loaded {count} poses")

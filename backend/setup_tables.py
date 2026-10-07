import boto3

client = boto3.client("dynamodb")
resource = boto3.resource("dynamodb")

POSES = [
    {"pose_id": "child", "name": "Child's Pose", "target_area": "hips", "difficulty": "beginner", "hold_seconds": 45},
    {"pose_id": "low-lunge", "name": "Low Lunge", "target_area": "hips", "difficulty": "beginner", "hold_seconds": 40},
    {"pose_id": "pigeon", "name": "Pigeon Pose", "target_area": "hips", "difficulty": "intermediate", "hold_seconds": 60},
    {"pose_id": "frog", "name": "Frog Pose", "target_area": "hips", "difficulty": "intermediate", "hold_seconds": 60},
    {"pose_id": "thread-needle", "name": "Thread the Needle", "target_area": "shoulders", "difficulty": "beginner", "hold_seconds": 30},
    {"pose_id": "cow-face", "name": "Cow Face Pose", "target_area": "shoulders", "difficulty": "intermediate", "hold_seconds": 45},
    {"pose_id": "cat-cow", "name": "Cat-Cow", "target_area": "lower back", "difficulty": "beginner", "hold_seconds": 30},
    {"pose_id": "supine-twist", "name": "Supine Twist", "target_area": "lower back", "difficulty": "beginner", "hold_seconds": 45},
]


def create_table(table_name, key_name):
    client.create_table(
        TableName=table_name,
        KeySchema=[{"AttributeName": key_name, "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": key_name, "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    # Tables take a few seconds to build. The waiter pauses until it's ready.
    client.get_waiter("table_exists").wait(TableName=table_name)
    print(f"Created {table_name}")


create_table("flowforge-poses", "pose_id")
create_table("flowforge-flows", "flow_id")

poses_table = resource.Table("flowforge-poses")
for pose in POSES:
    poses_table.put_item(Item=pose)
    print(f"Loaded {pose['name']}")

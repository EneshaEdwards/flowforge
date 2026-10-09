import boto3

dynamodb = boto3.resource("dynamodb")
poses_table = dynamodb.Table("flowforge-poses")

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

for pose in POSES:
    poses_table.put_item(Item=pose)
    print(f"Loaded {pose['name']}")

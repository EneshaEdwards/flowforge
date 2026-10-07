import random

# Our pose library. Each pose is a dictionary, the same shape as a DynamoDB item.
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


def generate_flow(target_area, difficulty, count=3):
    # Step 1: keep only the poses that match what the user asked for
    matches = []
    for pose in POSES:
        if pose["target_area"] == target_area and pose["difficulty"] == difficulty:
            matches.append(pose)

    # Step 2: if nothing matches, say so
    if len(matches) == 0:
        return {"error": "No poses found for that request."}

    # Step 3: pick poses at random, but never more than we have
    how_many = min(count, len(matches))
    chosen = random.sample(matches, how_many)

    # Step 4: add up the total time and return the flow
    total_seconds = 0
    for pose in chosen:
        total_seconds = total_seconds + pose["hold_seconds"]

    return {
        "target_area": target_area,
        "difficulty": difficulty,
        "poses": chosen,
        "total_seconds": total_seconds,
    }


flow = generate_flow("hips", "beginner")
print(flow)

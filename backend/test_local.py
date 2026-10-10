import json
from lambda_function import lambda_handler


def show(result):
    body = json.loads(result["body"])
    if result["statusCode"] != 200:
        print(body)
        return
    for pose in body["poses"]:
        line = pose["name"] + " - " + str(pose["flow_seconds"]) + " sec"
        if pose["side_mode"] == "per_side":
            line = line + " (both sides)"
        print(line)
    print("Total seconds:", body["total_seconds"])


print("User 1: neck and back, advanced, 15 minutes")
show(lambda_handler({"body_areas": ["neck", "back"], "difficulty": "advanced", "minutes": 15}, None))

print()
print("User 2: full body, beginner, 10 minutes")
show(lambda_handler({"body_areas": ["full body"], "difficulty": "beginner", "minutes": 10}, None))

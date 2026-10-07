from lambda_function import lambda_handler

result = lambda_handler({"target_area": "hips", "difficulty": "beginner"}, None)
print(result)

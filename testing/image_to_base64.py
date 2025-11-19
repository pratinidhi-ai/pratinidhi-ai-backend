import base64
import json

image_path = "H:\\Educado\\random\\math_question_1.jpg"
output_file = "H:\\Educado\\random\\image_question.json"
with open(image_path, "rb") as image_file:
    b64 = base64.b64encode(image_file.read()).decode()
    

outp = {"image": b64}

with open(output_file, "w") as f:
    json.dump(outp, f)

print(f"Base64 image data saved to {output_file}")
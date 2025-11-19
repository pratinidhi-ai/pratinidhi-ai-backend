import base64
import json

problem_image_path = "H:\\Educado\\random\\math_question_1.jpg"
solution_image_path = "H:\\Educado\\random\\math_solution.jpg"
output_file = "H:\\Educado\\random\\problem_solution_question.json"

def convert_problem_to_json():
    with open(problem_image_path, "rb") as image_file:
        b64 = base64.b64encode(image_file.read()).decode()
        

    outp = {"image": b64}

    with open(output_file, "w") as f:
        json.dump(outp, f)

    print(f"Base64 image data saved to {output_file}")

def convert_problem_solution_to_json():
    with open(problem_image_path, "rb") as image_file:
        b64_problem = base64.b64encode(image_file.read()).decode()
    
    with open(solution_image_path, "rb") as image_file:
        b64_solution = base64.b64encode(image_file.read()).decode()

    outp = {
        "problem_image": b64_problem,
        "solution_image": b64_solution
    }

    with open(output_file, "w") as f:
        json.dump(outp, f)

    print(f"Base64 problem and solution images saved to {output_file}")


if __name__ == "__main__":
    convert_problem_solution_to_json()
    # convert_problem_to_json()
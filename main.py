from dotenv import load_dotenv
import os
from google import genai
from google.genai import types
import sys
import time

from functions.get_files_info import schema_get_files_info, get_files_info
from functions.get_file_content import schema_get_file_content, get_file_content
from functions.run_python_file import schema_run_python_file, run_python_file
from functions.write_file import schema_write_file, write_file


def main():
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not set in environment")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    system_prompt = """Your name is Veena. You are a helpful coding AI agent. 
You can create a function call plan and perform the following operations:

- List files and directories.
- Read the content of a file.
- Write to a file (create or update).
- Run a python file with optional arguments.

⚠️ Note: All paths you provide should be relative to the working directory. 
You do not need to specify the working directory in your function calls, 
as it is automatically injected for security reasons.
"""

    if len(sys.argv) < 2:
        print("Usage: python main.py '<prompt>' [--verbose]")
        sys.exit(1)

    verbose_flag = False
    if len(sys.argv) == 3 and sys.argv[2] == "--verbose":
        verbose_flag = True

    prompt = sys.argv[1]
    model = "gemini-2.5-flash"

    # Initial conversation
    messages = [
        types.Content(role="user", parts=[types.Part(text=prompt)]),
    ]

    available_functions = types.Tool(
        function_declarations=[
            schema_get_files_info,
            schema_get_file_content,
            schema_write_file,
            schema_run_python_file
        ]
    )

    config = types.GenerateContentConfig(
        tools=[available_functions],
        system_instruction=system_prompt,
    )

    max_iterations = 20
    response = None

    function_map = {
        "get_files_info": get_files_info,
        "get_file_content": get_file_content,
        "write_file": write_file,
        "run_python_file": run_python_file
    }

    for i in range(max_iterations):
        try:
            response = client.models.generate_content(
                model=model,
                contents=messages,
                config=config,
            )

            if not response or not hasattr(response, "candidates"):
                print("Error: Malformed response")
                return

            # Case 1: Model wants to call a function
            if getattr(response, "function_calls", None):
                for fc in response.function_calls:
                    func = function_map.get(fc.name)
                    if func:
                        result = func(
                            working_directory=".",
                            **fc.args
                        )
                        print(f"Function result ({fc.name}):\n{result}\n")

                        # Feed result back into the conversation
                        messages.append(
                            types.Content(role="function", parts=[
                                types.Part(
                                    function_response=types.FunctionResponse(
                                        name=fc.name,
                                        response={"result": str(result)}
                                    )
                                )
                            ])
                        )

                        # Continue loop → Gemini will now respond again
                        continue
                    else:
                        print(f"Unknown function: {fc.name}")
                        return

            # Case 2: Model produces a final text answer
            elif getattr(response, "text", None):
                print(response.text)
                break

        except Exception as e:
            print(f"Iteration {i+1} failed with error: {e}")
        time.sleep(0.1)

    if verbose_flag and getattr(response, "usage_metadata", None):
        print(
            f"Prompt tokens: {response.usage_metadata.prompt_token_count}\n"
            f"Response tokens: {
                response.usage_metadata.candidates_token_count}"
        )


if __name__ == "__main__":
    main()

import json
from pathlib import Path

from app.agent import run_agent


BASE_DIR = Path(__file__).parent


VISIBLE_CASES = BASE_DIR / "visible-cases.json"
CUSTOM_CASES = BASE_DIR / "custom-cases.json"

RESULT_FILE = BASE_DIR / "results.json"



# -----------------------------
# Load cases
# -----------------------------

def load_cases():

    cases = []


    # visible cases
    if VISIBLE_CASES.exists():

        with open(
            VISIBLE_CASES,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

            cases.extend(
                data.get(
                    "cases",
                    []
                )
            )



    # custom cases
    if CUSTOM_CASES.exists():

        with open(
            CUSTOM_CASES,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

            cases.extend(data)



    return cases





# -----------------------------
# Extract messages
# -----------------------------

def get_messages(case):


    # visible format

    if "messages" in case:

        return [

            message["content"]

            for message in case["messages"]

        ]



    # custom format

    if "input" in case:

        return [

            case["input"]

        ]



    return []





# -----------------------------
# Assertions
# -----------------------------

def check_response(
    response,
    case
):


    response_lower = response.lower()



    # custom + visible
    must_include = case.get(
        "must_include",
        []
    )


    for item in must_include:

        if item.lower() not in response_lower:

            return False, f"Missing: {item}"




    must_not_include = case.get(
        "must_not_include",
        []
    )


    for item in must_not_include:


        if item.lower() in response_lower:

            return False, f"Forbidden text: {item}"




    # visible expect block

    expect = case.get(
        "expect",
        {}
    )



    for item in expect.get(
        "must_include",
        []
    ):

        if item.lower() not in response_lower:

            return False, f"Missing: {item}"




    for item in expect.get(
        "must_not_include",
        []
    ):

        if item.lower() in response_lower:

            return False, f"Forbidden: {item}"




    # concept checks
    concepts = expect.get(
        "must_include_concepts",
        []
    )


    for concept in concepts:

        words = concept.lower().split()

        matched = any(
            word in response_lower
            for word in words
        )


        if not matched:

            return False, (
                f"Concept missing: {concept}"
            )



    return True, "Passed"





# -----------------------------
# Run evaluation
# -----------------------------

def run():


    cases = load_cases()


    results = []


    passed = 0
    failed = 0
    errors = 0




    for case in cases:


        name = (

            case.get(
                "id"
            )

            or

            case.get(
                "name",
                "unknown"
            )

        )



        print(
            f"\nRunning: {name}"
        )



        try:


            messages = get_messages(
                case
            )


            response = ""



            # multi-turn support

            for message in messages:


                response = run_agent(
                    message
                )




            success, message = check_response(
                response,
                case
            )



            if success:

                status = "PASS"

                passed += 1


            else:

                status = "FAIL"

                failed += 1




            results.append(

                {

                    "name": name,

                    "status": status,

                    "message": message,

                    "response": response

                }

            )



        except Exception as e:


            errors += 1


            results.append(

                {

                    "name": name,

                    "status": "ERROR",

                    "message": str(e)

                }

            )





    output = {


        "summary": {


            "total": len(cases),

            "passed": passed,

            "failed": failed,

            "errors": errors

        },


        "results": results

    }




    with open(

        RESULT_FILE,

        "w",

        encoding="utf-8"

    ) as f:


        json.dump(

            output,

            f,

            indent=4

        )





    print(
        "\n==================="
    )

    print(
        "Evaluation Complete"
    )

    print(
        "==================="
    )


    print(
        f"PASS : {passed}"
    )

    print(
        f"FAIL : {failed}"
    )

    print(
        f"ERROR: {errors}"
    )





if __name__ == "__main__":

    run()
# main.py

from graph import graph
from nodes import classify_request


def run_agent():
    print("Company Agent")
    print("Type 'exit' to stop.\n")

    while True:
        question = input("You: ")

        if question.lower() == "exit":
            print("Goodbye.")
            break

        # First check whether the request is sensitive
        classification = classify_request({
            "question": question
        })

        sensitive = classification["sensitive"]

        state = {
            "question": question
        }

        # Only ask for credentials when necessary
        if sensitive:
            print("\nThis request requires authentication.")

            username = input("Username: ")
            password = input("Password: ")

            state["username"] = username
            state["password"] = password

        # Run the actual LangGraph
        result = graph.invoke(state)

        print("\nAgent:")
        print(result["answer"])
        print()


if __name__ == "__main__":
    run_agent()
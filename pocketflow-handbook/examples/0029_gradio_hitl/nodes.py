from datetime import datetime
from queue import Queue

import yaml
from pocketflow import Node

from utils.call_llm import call_llm
from utils.call_mock_api import call_book_hotel_api, call_check_weather_api
from utils.conversation import load_conversation, save_conversation
from utils.format_chat_history import format_chat_history


class DecideAction(Node):
    def prep(self, shared):
        conversation_id = shared["conversation_id"]
        session = load_conversation(conversation_id)
        return session, shared["history"], shared["query"]

    def exec(self, prep_res):
        session, history, query = prep_res
        prompt = f"""
### INSTRUCTIONS
You are a lifestyle assistant capable of helping users book hotels and check weather conditions.
You need to decide the next action based on your last action, action execution result, chat history, and current user question.

### CHAT HISTORY
{format_chat_history(history)}

### CURRENT USER QUESTION
user: {query}

### CONTEXT
Last Action: {session.get("last_action", None)}
Last Action Result: {session.get("action_result", None)}
Current Date: {datetime.now().date()} 

### ACTION SPACE
[1] check-weather
Description: When the user asks about the weather, use this tool.
Parameters:
    - name: city
        description: The city to check the weather
        required: true
        example: Beijing
    - name: date
        description: The date to check the weather, if not provided, use the current date
        required: false
        example: 2025-05-28

[2] book-hotel
Description: When the user wants to book a hotel, use this tool.
Parameters:
    - name: hotel
        description: The name of the hotel to be booked
        required: true
        example: ShanghaiHilton Hotel
    - name: checkin_date
        description: The check-in date
        required: true
        example: 2025-05-28
    - name: checkout_date
        description: The check-out date
        required: true
        example: 2025-05-29

[3] follow-up
Description: 1. When the user's question is out of the scope of booking hotels and checking weather, use this tool to guide the user; 2. When the current information cannot meet the parameter requirements of the corresponding tool, use this tool to ask the user.
Parameters:
    - name: question
        description: Your guidance or follow-up to the user, maintain an enthusiastic and lively language style, and use the same language as the user's question.
        required: true
        example: Which hotel would you like to book?😊

[4] result-notification
Description: When the booking of a hotel or checking the weather is completed, use this tool to notify the user of the result and ask if they need any other help. If you find that the user's question is not completed in the history conversation, you can guide the user to complete the intention in the last step.
Parameters:
    - name: result
        description: Notify the user of the result based on the Last Action Result. Maintain an enthusiastic and lively language style, and use the same language as the user's question.
        required: true
        example: The hotel has been successfully booked for you. 😉\n\nThe check-in date is XX, and the check-out date is XX. Thank you for using it. Would you like any other help?😀

## NEXT ACTION
Decide the next action based on the context and available actions.
Return your response in this format:

```yaml
thinking: |
    <your step-by-step reasoning process>
action: check-weather OR book-hotel OR follow-up OR result-notification
reason: <why you chose this action>
question: <if action is follow-up>
city: <if action is check-weather> 
hotel: <if action is book-hotel>
checkin_date: <if action is book-hotel>
checkout_date: <if action is book-hotel>
result: <if action is result-notification>
```

IMPORTANT: Make sure to:
1. Use proper indentation (4 spaces) for all multi-line fields
2. Use the | character for multi-line text fields
3. Keep single-line fields without the | character
"""

        response = call_llm(prompt.strip())
        yaml_str = response.split("```yaml")[1].split("```")[0].strip()
        print(f"🤖 Agent response: \n{yaml_str}")
        decision = yaml.safe_load(yaml_str)
        return decision

    def post(self, shared, prep_res, exec_res):
        conversation_id = shared["conversation_id"]
        session: dict = load_conversation(conversation_id)
        """Save the decision and determine the next step in the flow."""
        # If LLM decided to search, save the search query
        session["last_action"] = exec_res["action"]
        flow_log: Queue = shared["flow_queue"]

        for line in exec_res["thinking"].split("\n"):
            line = line.replace("-", "").strip()
            if line:
                flow_log.put(f"🤔 {line}")

        if exec_res["action"] == "check-weather":
            session["check_weather_params"] = {
                "city": exec_res["city"],
                "date": exec_res.get("date", None),
            }
            flow_log.put(f"➡️ Agent decided to check weather for: {exec_res['city']}")
        elif exec_res["action"] == "book-hotel":
            session["book_hotel_params"] = {
                "hotel": exec_res["hotel"],
                "checkin_date": exec_res["checkin_date"],
                "checkout_date": exec_res["checkout_date"],
            }
            flow_log.put(f"➡️ Agent decided to book hotel: {exec_res['hotel']}")
        elif exec_res["action"] == "follow-up":
            session["follow_up_params"] = {"question": exec_res["question"]}
            flow_log.put(f"➡️ Agent decided to follow up: {exec_res['question']}")
        elif exec_res["action"] == "result-notification":
            session["result_notification_params"] = {"result": exec_res["result"]}
            flow_log.put(f"➡️ Agent decided to notify the result: {exec_res['result']}")
        save_conversation(conversation_id, session)
        # Return the action to determine the next node in the flow
        return exec_res["action"]


class CheckWeather(Node):
    def prep(self, shared):
        conversation_id = shared["conversation_id"]
        session: dict = load_conversation(conversation_id)
        city = session["check_weather_params"]["city"]
        date = session["check_weather_params"].get("date", None)
        return city, date

    def exec(self, prep_res):
        city, date = prep_res
        return call_check_weather_api(city, date)

    def post(self, shared, prep_res, exec_res):
        flow_log: Queue = shared["flow_queue"]
        flow_log.put(f"⬅️ Check weather result: {exec_res}")

        conversation_id = shared["conversation_id"]
        session: dict = load_conversation(conversation_id)
        session["action_result"] = exec_res
        save_conversation(conversation_id, session)
        return "default"


class BookHotel(Node):
    def prep(self, shared):
        conversation_id = shared["conversation_id"]
        session: dict = load_conversation(conversation_id)

        hotel = session["book_hotel_params"]["hotel"]
        checkin_date = session["book_hotel_params"]["checkin_date"]
        checkout_date = session["book_hotel_params"]["checkout_date"]
        return hotel, checkin_date, checkout_date

    def exec(self, prep_res):
        hotel, checkin_date, checkout_date = prep_res
        return call_book_hotel_api(hotel, checkin_date, checkout_date)

    def post(self, shared, prep_res, exec_res):
        flow_log: Queue = shared["flow_queue"]
        flow_log.put(f"⬅️ Book hotel result: {exec_res}")

        conversation_id = shared["conversation_id"]
        session: dict = load_conversation(conversation_id)
        session["action_result"] = exec_res
        save_conversation(conversation_id, session)
        return "default"


class FollowUp(Node):
    def prep(self, shared):
        flow_log: Queue = shared["flow_queue"]
        flow_log.put(None)

        conversation_id = shared["conversation_id"]
        session: dict = load_conversation(conversation_id)
        question = session["follow_up_params"]["question"]
        return question, shared["queue"]

    def exec(self, prep_res):
        question, queue = prep_res
        queue.put(question)
        queue.put(None)
        return question

    def post(self, shared, prep_res, exec_res):
        conversation_id = shared["conversation_id"]
        session: dict = load_conversation(conversation_id)
        session["action_result"] = exec_res
        return "done"


class ResultNotification(Node):
    def prep(self, shared):
        flow_log: Queue = shared["flow_queue"]
        flow_log.put(None)

        conversation_id = shared["conversation_id"]
        session: dict = load_conversation(conversation_id)
        result = session["result_notification_params"]["result"]
        return result, shared["queue"]

    def exec(self, prep_res):
        result, queue = prep_res
        queue.put(result)
        queue.put(None)
        return result

    def post(self, shared, prep_res, exec_res):
        conversation_id = shared["conversation_id"]
        session: dict = load_conversation(conversation_id)
        session["action_result"] = None
        session["last_action"] = None
        save_conversation(conversation_id, session)
        return "done"

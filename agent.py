from typing import TypedDict, List
from langgraph.graph import StateGraph, END
import json
import re

from llm import llm
from db import *
from validators import *
from prompts import *

def get_llm_text(response):
    content = response.content
    if isinstance(content, list):
        final_text = ""
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    final_text += item.get("text", "")
            else:
                final_text += str(item)
        return final_text.strip()
    return str(content).strip()

class BotState(TypedDict):
    user_input: str
    messages: List[dict]
    active_intent: str | None
    data: dict
    missing_fields: list
    validation_errors: dict
    response: str
    awaiting_confirmation: bool
    operation_complete: bool
    last_action: str | None
    interruption_detected: bool

def get_reset_state_dict(messages_to_keep):
    return {
        "user_input": "",
        "messages": messages_to_keep,
        "active_intent": None,
        "data": {},
        "missing_fields": [],
        "validation_errors": {},
        "response": "",
        "awaiting_confirmation": False,
        "operation_complete": False,
        "last_action": None,
        "interruption_detected": False
    }

def context_node(state: BotState):
    active_intent = state.get("active_intent")
    user_input = state.get("user_input", "")

    # 1. Handle Confirmations First
    if state.get("awaiting_confirmation"):
        if user_input.lower() in ["yes", "y", "no", "n", "cancel"]:
            return {"last_action": "CONFIRMATION_RESPONSE"}

    # 2. Python Regex Safety Net (MUST be before the Chat escape)
    fields = ["name", "email", "phone", "dob", "address", "date of birth", "full name"]
    is_field = any(user_input.strip().lower() == f for f in fields)
    if re.search(r'[\w\.-]+@[\w\.-]+\.\w+', user_input) or re.search(r'\b\d{10}\b', user_input) or re.search(r'\b\d{4}-\d{2}-\d{2}\b', user_input) or is_field:
        return {"last_action": "CONTINUE"}

    # 3. Handle Empty or Chat States safely
    if active_intent is None or active_intent == "CHAT":
        return {"last_action": "EVALUATE_INTENT"}

    # 4. Evaluate Interruptions
    prompt = INTERRUPTION_PROMPT.format(
        active_intent=active_intent,
        user_input=user_input
    )
    try:
        response = llm.invoke(prompt)
        result = get_llm_text(response).upper()
    except:
        result = "CONTINUE"

    if result.startswith("SWITCH"):
        new_intent = result.replace("SWITCH_", "")
        if new_intent == active_intent:
            return {"last_action": "CONTINUE"}
            
        new_state = get_reset_state_dict(state.get("messages", []))
        new_state["active_intent"] = new_intent
        new_state["interruption_detected"] = True
        new_state["response"] = f"Switched to {new_intent} operation."
        return new_state
        
    elif result == "GENERAL_CHAT":
        return {"last_action": "CHAT"}
    elif result == "CORRECTION":
        return {"last_action": "CORRECTION"}
    
    return {"last_action": "CONTINUE"}

def intent_node(state: BotState):
    # Only skip if we are locked into a valid CRUD workflow
    if state.get("active_intent") in ["CREATE", "READ", "UPDATE", "DELETE"]:
        return {}
        
    prompt = INTENT_PROMPT.format(user_input=state.get("user_input", ""))
    try:
        response = llm.invoke(prompt)
        intent = get_llm_text(response).upper()
        if intent not in ["CREATE", "READ", "UPDATE", "DELETE", "CHAT"]:
            intent = "CHAT"
    except:
        intent = "CHAT"
    return {"active_intent": intent}

def conversational_node(state: BotState):
    prompt = CHAT_PROMPT.format(
        active_intent=state.get("active_intent"),
        data=state.get("data", {}),
        user_input=state.get("user_input", "")
    )
    response = llm.invoke(prompt)
    message = get_llm_text(response)
    return {"response": message}

def extraction_node(state: BotState):
    user_input = state.get("user_input", "").strip()
    updated_data = dict(state.get("data", {}))
    intent = state.get("active_intent")

    # Python Regex Fallbacks
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', user_input)
    if email_match:
        if not updated_data.get("email"):
            updated_data["email"] = email_match.group(0)

    phone_match = re.search(r'\b\d{10}\b', user_input)
    if phone_match:
        if not updated_data.get("phone") and intent == "CREATE":
            updated_data["phone"] = phone_match.group(0)
        elif intent == "UPDATE" and "phone" in str(updated_data.get("field_to_update", "")).lower():
            updated_data["new_value"] = phone_match.group(0)

    prompt = EXTRACTION_PROMPT.format(
        intent=intent,
        current_data=state.get("data", {}),
        user_input=user_input
    )
    
    try:
        response = llm.invoke(prompt)
        content = get_llm_text(response).strip()
        if "{" in content and "}" in content:
            content = content[content.find("{"):content.rfind("}")+1]
            
        extracted = json.loads(content)
        for key, value in extracted.items():
            if value is not None and str(value).strip() != "" and str(value).lower() != "null":
                # Overwrite is allowed to fix errors
                updated_data[key] = value
    except Exception:
        pass

    return {"data": updated_data}

def validation_node(state: BotState):
    errors = {}
    data = dict(state.get("data", {}))
    intent = state.get("active_intent")

    # Instant Database Existence Checks
    if "email" in data and data["email"]:
        if not validate_email(data["email"]):
            errors["email"] = "Invalid email format."
            del data["email"]
        else:
            user_check = get_user(data["email"])
            
            if intent == "CREATE":
                if user_check and not isinstance(user_check, str):
                    errors["email"] = "This email is already registered in our database. Please provide a different email address."
                    del data["email"]
                    
            elif intent in ["READ", "UPDATE", "DELETE"]:
                if not user_check or isinstance(user_check, str):
                    errors["email"] = "We couldn't find an account associated with this email. Please check for typos and provide your registered email address."
                    del data["email"]
                
    if "phone" in data and data["phone"]:
        if not validate_phone(str(data["phone"])):
            errors["phone"] = "Phone number must contain exactly 10 digits."
            del data["phone"]
            
    if "dob" in data and data["dob"]:
        if not validate_dob(data["dob"]):
            errors["dob"] = "Invalid DOB format. Please use YYYY-MM-DD."
            del data["dob"]

    if intent == "UPDATE":
        if "field_to_update" in data and data["field_to_update"]:
            if "email" in str(data["field_to_update"]).lower():
                errors["field_to_update"] = "The email address is your primary identifier and cannot be changed. Which other field would you like to update?"
                del data["field_to_update"]

        if "new_value" in data and data["new_value"]:
            field = str(data.get("field_to_update", "")).lower()
            val = str(data["new_value"])
            
            if "phone" in field and not validate_phone(val):
                errors["new_value"] = "The new phone number must contain exactly 10 digits."
                del data["new_value"]
            elif "dob" in field and not validate_dob(val):
                errors["new_value"] = "The new DOB format is invalid. Please use YYYY-MM-DD."
                del data["new_value"]

    return {"validation_errors": errors, "data": data}

def missing_fields_node(state: BotState):
    intent = state.get("active_intent")
    data = state.get("data", {})
    missing = []

    if intent == "CREATE":
        required = ["full_name", "email", "phone", "dob", "address"]
    elif intent == "READ":
        required = ["email"]
    elif intent == "UPDATE":
        required = ["email", "field_to_update", "new_value"]
    elif intent == "DELETE":
        required = ["email"]
    else:
        required = []

    for field in required:
        if field not in data or not str(data[field]).strip():
            missing.append(field)
    return {"missing_fields": missing}

def reasoning_node(state: BotState):
    if state.get("validation_errors"):
        prompt = VALIDATION_PROMPT.format(errors=state["validation_errors"])
        response = llm.invoke(prompt)
        return {"response": get_llm_text(response)}

    if state.get("missing_fields"):
        prompt = MISSING_FIELD_PROMPT.format(
            intent=state.get("active_intent"),
            data=state.get("data"),
            missing_fields=state.get("missing_fields")
        )
        response = llm.invoke(prompt)
        return {"response": get_llm_text(response)}

    intent = state.get("active_intent")
    data = state.get("data", {})

    if intent == "CREATE":
        prompt = CREATE_CONFIRMATION_PROMPT.format(data=data)
        response = llm.invoke(prompt)
        return {"awaiting_confirmation": True, "response": get_llm_text(response)}
    elif intent == "UPDATE":
        prompt = UPDATE_CONFIRMATION_PROMPT.format(
            field=data.get("field_to_update", ""),
            new_value=data.get("new_value", "")
        )
        response = llm.invoke(prompt)
        return {"awaiting_confirmation": True, "response": get_llm_text(response)}
    elif intent == "DELETE":
        prompt = DELETE_CONFIRMATION_PROMPT.format(email=data.get("email", ""))
        response = llm.invoke(prompt)
        return {"awaiting_confirmation": True, "response": get_llm_text(response)}
        
    return {}

def crud_node(state: BotState):
    intent = state.get("active_intent")
    data = state.get("data", {})
    user_input = state.get("user_input", "").lower()

    if intent in ["CREATE", "UPDATE", "DELETE"] and state.get("awaiting_confirmation"):
        if user_input not in ["yes", "y"]:
            reset = get_reset_state_dict(state.get("messages", []))
            reset["response"] = "Operation cancelled."
            return reset

    if intent == "CREATE":
        result = create_user(data.get("full_name"), data.get("email"), data.get("phone"), data.get("dob"), data.get("address"))
        reset = get_reset_state_dict(state.get("messages", []))
        reset["response"] = result
        return reset

    elif intent == "READ":
        user = get_user(data.get("email"))
        profile_card = f"📋 **Registration Record Found:**\n\n- **Name:** {user[0]}\n- **Email:** {user[1]}\n- **Phone:** {user[2]}\n- **DOB:** {user[3]}\n- **Address:** {user[4]}"
        reset = get_reset_state_dict(state.get("messages", []))
        reset["response"] = profile_card
        return reset

    elif intent == "UPDATE":
        result = update_user(data.get("email"), data.get("field_to_update"), data.get("new_value"))
        reset = get_reset_state_dict(state.get("messages", []))
        reset["response"] = result
        return reset

    elif intent == "DELETE":
        result = delete_user(data.get("email"))
        reset = get_reset_state_dict(state.get("messages", []))
        reset["response"] = result
        return reset

    return {}

def context_router(state: BotState):
    if state.get("last_action") == "CONFIRMATION_RESPONSE":
        return "crud"
    # Route straight to intent if the last action was EVALUATE_INTENT
    if state.get("last_action") == "EVALUATE_INTENT":
        return "intent"
    if state.get("last_action") == "CHAT":
        return "chat"
    return "intent"

def intent_router(state: BotState):
    if state.get("active_intent") == "CHAT":
        return "chat"
    return "extract"

def reasoning_router(state: BotState):
    if state.get("validation_errors") or state.get("missing_fields"):
        return END
    if state.get("active_intent") == "READ":
        return "crud"
    if state.get("awaiting_confirmation"):
        return END
    return END

builder = StateGraph(BotState)
builder.add_node("context", context_node)
builder.add_node("intent", intent_node)
builder.add_node("chat", conversational_node)
builder.add_node("extract", extraction_node)
builder.add_node("validate", validation_node)
builder.add_node("missing", missing_fields_node)
builder.add_node("reason", reasoning_node)
builder.add_node("crud", crud_node)

builder.set_entry_point("context")

builder.add_conditional_edges("context", context_router, {"intent": "intent", "chat": "chat", "crud": "crud"})
builder.add_conditional_edges("intent", intent_router, {"extract": "extract", "chat": "chat"})
builder.add_edge("extract", "validate")
builder.add_edge("validate", "missing")
builder.add_edge("missing", "reason")
builder.add_conditional_edges("reason", reasoning_router, {"crud": "crud", END: END})
builder.add_edge("crud", END)
builder.add_edge("chat", END)

chatbot = builder.compile()
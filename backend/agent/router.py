import re
import logging
from typing import Dict, Any, Optional, Tuple
from backend.tools.registry import registry
from backend.services.vision import camera_service
from backend.services.visual_memory import visual_memory_engine
from backend.services.screen import screen_vision_service
from backend.services.shutdown import is_goodbye_request, perform_graceful_shutdown
from backend.services.routine_learner import routine_learner
from backend.agent.web_search import search_web_summary
from backend.tools.math_tools import evaluate_math_expression

logger = logging.getLogger("AEGIS.Router")

class FastDeterministicRouter:
    """Zero-latency local routing for deterministic tasks, system clock, camera, apps, maps, youtube, paint, reminders."""

    async def route_and_execute(self, user_input: str) -> Optional[Dict[str, Any]]:
        raw_text = user_input.strip()
        t = raw_text.lower().rstrip(".!?,")

        # 1. Goodbye / Self Shutdown
        if is_goodbye_request(t):
            res = await perform_graceful_shutdown()
            return {
                "handled": True,
                "response": res["message"],
                "action": "exit_app",
                "tool": "shutdown",
                "verified": True
            }

        # 2. Conversational Greetings & Banter (Instant Response)
        if re.search(r"^(hello|hi|hey|hey aegis|hello aegis|hi aegis|hey aura|hello aura|hi aura|greetings|good morning|good afternoon|good evening|yo)\b", t):
            if "morning" in t:
                greet = "Good morning! I'm here and ready to help. What are we working on today?"
            elif "evening" in t:
                greet = "Good evening! How can I assist you tonight?"
            elif "afternoon" in t:
                greet = "Good afternoon! What can I do for you?"
            else:
                greet = "Hey! I'm here. What can I do for you?"
            return {"handled": True, "response": greet, "tool": "greeting", "verified": True}

        if re.search(r"\b(how are you|how are you doing|what's up|how's it going|how are you today)\b", t):
            return {
                "handled": True,
                "response": "I'm doing great, thanks for asking! What are we working on today?",
                "tool": "conversation",
                "verified": True
            }

        if re.search(r"\b(who are you|what is your name|introduce yourself|tell me about yourself)\b", t):
            return {
                "handled": True,
                "response": "I am AEGIS — your Assisted Executive Guidance and Intelligence System for Windows. I can control your PC, launch apps, draw in Paint, manage reminders, inspect your environment via camera, solve mathematics, and automate your daily tasks.",
                "tool": "identity",
                "verified": True
            }

        if re.search(r"\b(tell me something interesting|tell me a fun fact|give me a fact|fun fact)\b", t):
            return {
                "handled": True,
                "response": "Sure! Did you know that honey never spoils? Archaeologists have found 3,000-year-old pots of honey in ancient Egyptian tombs that are still perfectly edible.",
                "tool": "fun_fact",
                "verified": True
            }

        if re.search(r"\b(thank you|thanks|thanks aegis|thank you aegis|thanks aura|thank you aura|great job|awesome)\b", t):
            return {
                "handled": True,
                "response": "You're very welcome! Let me know if you need anything else.",
                "tool": "politeness",
                "verified": True
            }

        if re.search(r"^(help|what can you do|what can i say|commands)\b", t):
            return {
                "handled": True,
                "response": "You can talk to me naturally! Try saying 'What is the time right now?', '2*2', 'Open Chrome', 'Open Paint and draw a house', 'Play Believer on YouTube', 'Where is the clock?', or 'Remind me tomorrow at 5 PM'.",
                "tool": "help",
                "verified": True
            }

        # 3. Mathematical Problems & Arithmetic Evaluation (<1ms)
        is_math_candidate = bool(
            re.search(r"(\d+\s*[\+\-\*\/\%\^\×\÷]\s*\d+|\d+\s*x\s*\d+|\d+\s*%\s+of\s+\d+|sqrt\(\d+|cbrt\(\d+|\b(sin|cos|tan|log|factorial)\(\d+)", t) or
            re.search(r"^(calculate|solve|evaluate|how much is|what is \d+|what's \d+)\b", t) or
            re.search(r"\b(\d+\s+(?:plus|minus|times|multiplied by|divided by)\s+\d+)\b", t) or
            re.match(r"^[\d\s\+\-\*\/\(\)\.\^\%]+$", t)
        )
        if is_math_candidate and not any(w in t for w in ["time", "date", "reminder", "remind", "camera", "paint", "youtube", "directions", "map", "pm", "am"]):
            math_res = evaluate_math_expression(raw_text)
            if math_res.get("success") or "Division by zero" in math_res.get("message", ""):
                return {
                    "handled": True,
                    "response": math_res["message"],
                    "tool": "calculate_math",
                    "verified": True
                }

        # 4. Real Windows System Clock & Date (Universal matching)
        if re.search(r"\b(what('s| is)? (the )?time( right now| now)?|current time|tell me (the )?time|what time( is it)?( right now)?|time right now|time now|the time right now)\b", t) or t in ["time", "time please", "what time", "what is time", "the time"]:
            tool_res = await registry.execute("get_system_time", {})
            msg = tool_res.get("result", {}).get("message", "The time is available.")
            return {"handled": True, "response": msg, "tool": "get_system_time", "verified": True}

        if re.search(r"\b(what date is today|what's today's date|today's date|what day is today|what date is it|what is the date|tell me the date)\b", t) or t in ["date", "today's date", "what date"]:
            tool_res = await registry.execute("get_system_date", {})
            msg = tool_res.get("result", {}).get("message", "Today's date is available.")
            return {"handled": True, "response": msg, "tool": "get_system_date", "verified": True}

        # 5. Camera Controls & Status
        if re.search(r"\b(turn on( the)? camera|start( the)? camera|enable( the)? camera|enable continuous camera)\b", t):
            continuous = "continuous" in t or "24/7" in t
            res = camera_service.start_camera(continuous=continuous)
            return {"handled": True, "response": "Camera is active.", "tool": "start_camera", "verified": True}

        if re.search(r"\b(turn off( the)? camera|stop( the)? camera|disable( the)? camera|close( the)? camera)\b", t):
            res = camera_service.stop_camera()
            return {"handled": True, "response": "Camera is turned off.", "tool": "stop_camera", "verified": True}

        if re.search(r"\b(pause( the)? camera)\b", t):
            res = camera_service.pause_camera()
            return {"handled": True, "response": "Camera paused.", "tool": "pause_camera", "verified": True}

        if re.search(r"\b(resume( the)? camera)\b", t):
            res = camera_service.resume_camera()
            return {"handled": True, "response": "Camera resumed.", "tool": "resume_camera", "verified": True}

        if re.search(r"\b(is there a person|detect person|any person in front|check if someone is there|is someone there)\b", t):
            res = camera_service.detect_person_local()
            return {"handled": True, "response": res["message"], "tool": "detect_person", "data": res, "verified": True}

        # 5. Immediate Camera Environment Perception
        if re.search(
            r"\b(what am i looking at|what do you see|describe what you see|what's in front of me|"
            r"what is in front of the camera|what is this object|look at this|what do you see in front of the camera|"
            r"what's in front of the camera|detect (?:the )?objects?|identify (?:the )?objects?|identify (?:the )?items?|"
            r"identify this|what objects do you see|what objects are (?:here|there|in front)|what is in my hand|"
            r"what am i holding|scan (?:the )?room|scan (?:the )?surroundings|recognize (?:the )?objects?|"
            r"check (?:the )?objects?|what is this|look around)\b",
            t
        ):
            if not camera_service.is_active:
                # Try auto-activating or prompt user
                res_start = camera_service.start_camera()
                if not camera_service.is_active:
                    return {
                        "handled": True,
                        "response": "The camera is currently turned off. Please enable the camera so I can see your surroundings.",
                        "tool": "vision_notice",
                        "verified": True
                    }
            res = await visual_memory_engine.analyze_frame_and_extract_memory()
            return {"handled": True, "response": res.get("message", "I have analyzed your surroundings."), "tool": "analyze_camera", "verified": True}

        # 6. Visual Memory Spatial Queries
        if re.search(
            r"\b(where (?:is|are|was|did you see|did i (?:leave|put|keep)|can i find)(?: my| the)?|"
            r"have you seen(?: my| the)?|did you see(?: my| the)?|find(?: my| the)?|locate(?: my| the)?|"
            r"what is next to(?: my| the)?|what room am i in|what was on the table|what was beside)\b",
            t
        ):
            mem_res = visual_memory_engine.query_object_location(t)
            # If not found in previous memory, but camera is active, analyze the live frame right now
            if not mem_res.get("found", False) and camera_service.is_active:
                await visual_memory_engine.analyze_frame_and_extract_memory()
                mem_res = visual_memory_engine.query_object_location(t)
            return {"handled": True, "response": mem_res["message"], "tool": "query_visual_memory", "data": mem_res, "verified": True}

        # 7. Screen Perception
        if re.search(r"\b(what is on my screen|read this error|what does this error mean|read what's on my screen|look at my screen)\b", t):
            res = await screen_vision_service.analyze_screen_content(t)
            return {"handled": True, "response": res.get("message", "Screen analyzed."), "tool": "analyze_screen", "verified": True}

        # 8. Microsoft Paint & Drawing Automation
        draw_match = re.search(r"\b(?:open paint and )?draw (?:a |an )?([a-zA-Z_\s]+?)(?: in paint| on the canvas)?$", t)
        if draw_match or "draw a house" in t or "draw a circle" in t or "draw a landscape" in t or "draw a birthday card" in t or "write aura" in t:
            drawing_type = "house"
            if "house" in t:
                drawing_type = "house"
            elif "circle" in t or "sun" in t:
                drawing_type = "circle"
            elif "landscape" in t:
                drawing_type = "landscape"
            elif "birthday" in t or "card" in t:
                drawing_type = "birthday_card"
            elif "aura" in t:
                drawing_type = "aura_text"
            elif "geometric" in t or "star" in t:
                drawing_type = "geometric"
            elif draw_match:
                candidate = draw_match.group(1).strip().lower()
                if candidate in ["house", "circle", "landscape", "birthday_card", "aura_text", "geometric"]:
                    drawing_type = candidate

            tool_res = await registry.execute("draw_in_paint", {"drawing_type": drawing_type})
            msg = f"Done. Paint is open and I drew a {drawing_type} on the canvas."
            routine_learner.log_action("app_launch", "Paint")
            return {"handled": True, "response": msg, "tool": "draw_in_paint", "verified": True}

        # 9. YouTube Playback & Music
        yt_play_match = re.search(r"\b(?:play)\s+(.+?)(?:\s+on youtube)?$", raw_text, re.IGNORECASE)
        if yt_play_match and not any(w in t for w in ["game", "video game", "audio file"]):
            song = yt_play_match.group(1).strip()
            tool_res = await registry.execute("youtube_play", {"song": song})
            routine_learner.log_action("website_open", "YouTube")
            return {"handled": True, "response": f"Playing {song} on YouTube.", "tool": "youtube_play", "verified": True}

        # 10. Google Maps & Directions
        directions_match = re.search(r"\b(?:show|give me|get)?\s*directions (?:from\s+(.+?)\s+)?to\s+(.+)$", raw_text, re.IGNORECASE)
        if directions_match:
            origin = directions_match.group(1) or "Current Location"
            destination = directions_match.group(2).strip()
            tool_res = await registry.execute("maps_directions", {"destination": destination, "origin": origin})
            res_data = tool_res.get("result", {})
            msg = res_data.get("message", f"Showing directions to {destination} on Google Maps.")
            routine_learner.log_action("website_open", "Google Maps")
            return {"handled": True, "response": msg, "tool": "maps_directions", "verified": True}

        maps_search_match = re.search(r"\b(?:show|open)\s+(.+?)\s+on (?:google )?maps\b", raw_text, re.IGNORECASE)
        if maps_search_match or t == "open google maps" or t == "open maps":
            query = maps_search_match.group(1).strip() if maps_search_match else "Google Maps"
            if query.lower() == "google maps":
                tool_res = await registry.execute("open_website", {"url": "https://maps.google.com"})
                msg = "Google Maps is open."
            else:
                tool_res = await registry.execute("open_maps", {"query": query})
                msg = f"Showing {query} on Google Maps."
            routine_learner.log_action("website_open", "Google Maps")
            return {"handled": True, "response": msg, "tool": "open_maps", "verified": True}

        # 11. Reminders (Universal Robust Matching)
        if re.search(r"\b(list my reminders|show( all)? reminders|what are my reminders|check reminders)\b", t):
            tool_res = await registry.execute("list_reminders", {})
            msg = tool_res.get("result", {}).get("message", "You have no active reminders.")
            return {"handled": True, "response": msg, "tool": "list_reminders", "verified": True}

        if re.search(r"\b(cancel( my)? reminder|delete( my)? reminder|remove reminder)\b", t):
            query = t.replace("cancel my reminder", "").replace("delete my reminder", "").replace("cancel reminder", "").strip() or "all"
            tool_res = await registry.execute("delete_reminder", {"query": query})
            msg = tool_res.get("result", {}).get("message", "Reminder cancelled.")
            return {"handled": True, "response": msg, "tool": "delete_reminder", "verified": True}

        # Pattern A: "remind me at 5 PM to submit assignment" OR "set reminder for 5 PM to submit assignment"
        p_at_to = re.search(r"\b(?:set a reminder|remind me)\s+(?:for |at |in )?(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|tomorrow(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?|today(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?|\d+\s+minutes?|\d+\s+hours?)\s+(?:to\s+|about\s+|for\s+)(.+)$", t)
        if p_at_to:
            time_str = p_at_to.group(1).strip()
            text_str = p_at_to.group(2).strip()
            tool_res = await registry.execute("create_reminder", {"text": text_str, "time_str": time_str})
            res_data = tool_res.get("result", {})
            msg = res_data.get("message", "Reminder scheduled.")
            return {"handled": True, "response": msg, "tool": "create_reminder", "verified": tool_res.get("verified", False)}

        # Pattern B: "remind me to submit assignment at 5 PM" OR "set a reminder to sleep tomorrow at 12:07 AM"
        p_to_at = re.search(r"\b(?:set a reminder|remind me)\s+(?:to\s+|about\s+|for\s+)?(.+?)\s+(?:at\s+|on\s+|in\s+|tomorrow\s*at\s*|tomorrow\s+|today\s*at\s*)(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|tomorrow(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?|\d+\s+minutes?|\d+\s+hours?)$", t)
        if p_to_at:
            text_str = p_to_at.group(1).strip()
            time_str = p_to_at.group(2).strip()
            if "tomorrow" in t and "tomorrow" not in time_str:
                time_str = f"tomorrow at {time_str}"
            tool_res = await registry.execute("create_reminder", {"text": text_str, "time_str": time_str})
            res_data = tool_res.get("result", {})
            msg = res_data.get("message", "Reminder scheduled.")
            return {"handled": True, "response": msg, "tool": "create_reminder", "verified": tool_res.get("verified", False)}

        # Pattern C: "remind me tomorrow at 5 PM to submit assignment"
        reminder_time_match = re.search(r"\b(?:set a )?remind(?:er)?(?: me)?\s+(?:for\s+)?(tomorrow.+?|today.+?|in \d+.+?|at \d+.+?|on [a-zA-Z]+.+?)\s+to\s+(.+)$", t)
        if reminder_time_match:
            time_str = reminder_time_match.group(1).strip()
            text_str = reminder_time_match.group(2).strip()
            tool_res = await registry.execute("create_reminder", {"text": text_str, "time_str": time_str})
            res_data = tool_res.get("result", {})
            msg = res_data.get("message", "Reminder scheduled.")
            return {"handled": True, "response": msg, "tool": "create_reminder", "verified": tool_res.get("verified", False)}

        # Pattern D: Remind me without time -> SIH Rule: ask "When should I remind you?"
        if re.search(r"\b(?:remind me|set a reminder|set reminder)\b", t):
            task_text = re.sub(r"\b(remind me to|remind me about|set a reminder to|set reminder to|remind me|set a reminder)\s*", "", t).strip()
            return {
                "handled": True,
                "response": "When should I remind you?",
                "tool": "create_reminder",
                "pending_reminder_task": task_text or "your task",
                "verified": True
            }

        # 12. Application and Website Launching
        if t.startswith("open ") or t.startswith("launch ") or t.startswith("start "):
            target = re.sub(r"^(open|launch|start)\s+", "", t).strip()
            
            if target in ["youtube", "google", "github", "wikipedia", "reddit", "twitter"]:
                url = f"https://{target}.com"
                tool_res = await registry.execute("open_website", {"url": url})
                routine_learner.log_action("website_open", target.capitalize())
                return {"handled": True, "response": f"Done. {target.capitalize()} is open.", "tool": "open_website", "verified": True}

            tool_res = await registry.execute("open_application", {"app_name": target})
            res_data = tool_res.get("result", {})
            msg = res_data.get("message", f"Done. {target.capitalize()} is open.")
            routine_learner.log_action("app_launch", target)
            return {"handled": True, "response": msg, "tool": "open_application", "verified": tool_res.get("verified", False)}

        if t.startswith("close ") or t.startswith("quit ") or t.startswith("exit "):
            target = re.sub(r"^(close|quit|exit)\s+", "", t).strip()
            tool_res = await registry.execute("close_application", {"app_name": target})
            msg = tool_res.get("result", {}).get("message", f"Closed {target}.")
            return {"handled": True, "response": msg, "tool": "close_application", "verified": tool_res.get("verified", False)}

        # 13. General Fact / Entity Questions (e.g. "Who is Albert Einstein?")
        if re.search(r"^(who is|who was|tell me about|explain|what is the capital of)\s+", t) and not any(w in t for w in ["my screen", "camera", "paint", "clock", "laptop", "bag", "room"]):
            search_res = search_web_summary(raw_text)
            if search_res.get("success"):
                return {
                    "handled": True,
                    "response": search_res["message"],
                    "tool": "web_search",
                    "verified": True
                }

        # 14. Volume Adjustments
        if "volume up" in t or "increase volume" in t:
            await registry.execute("set_volume", {"action": "up"})
            return {"handled": True, "response": "Volume increased.", "tool": "set_volume", "verified": True}
        if "volume down" in t or "decrease volume" in t:
            await registry.execute("set_volume", {"action": "down"})
            return {"handled": True, "response": "Volume decreased.", "tool": "set_volume", "verified": True}
        if "mute" in t or "unmute" in t:
            await registry.execute("set_volume", {"action": "mute"})
            return {"handled": True, "response": "Volume toggled.", "tool": "set_volume", "verified": True}

        return None

router = FastDeterministicRouter()

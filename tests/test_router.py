import pytest
from backend.agent.router import router
from backend.database import init_db

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

@pytest.mark.asyncio
async def test_fast_router_system_time_and_date():
    res_time = await router.route_and_execute("what time is it")
    assert res_time is not None
    assert res_time["handled"] is True
    assert "The current time is" in res_time["response"]

    res_date = await router.route_and_execute("what date is today")
    assert res_date is not None
    assert res_date["handled"] is True
    assert "Today is" in res_date["response"]

@pytest.mark.asyncio
async def test_fast_router_reminders():
    # When user says "Remind me to submit my assignment" without time, it MUST ask "When should I remind you?"
    res_ask = await router.route_and_execute("remind me to submit my assignment")
    assert res_ask is not None
    assert res_ask["handled"] is True
    assert res_ask["response"] == "When should I remind you?"

    # When time is given
    res_set = await router.route_and_execute("remind me tomorrow at 5 PM to submit my assignment")
    assert res_set is not None
    assert res_set["handled"] is True
    assert "Reminder set" in res_set["response"]

@pytest.mark.asyncio
async def test_fast_router_maps_and_youtube():
    res_yt = await router.route_and_execute("play Believer by Imagine Dragons")
    assert res_yt is not None
    assert res_yt["handled"] is True
    assert "Believer by Imagine Dragons" in res_yt["response"]
    assert res_yt.get("action") == "open_url"
    assert "youtube.com" in res_yt.get("url", "")

    res_maps = await router.route_and_execute("give me directions to Bangalore Airport")
    assert res_maps is not None
    assert res_maps["handled"] is True
    assert "Bangalore Airport" in res_maps["response"]

@pytest.mark.asyncio
async def test_fast_router_shutdown():
    res_bye = await router.route_and_execute("goodbye")
    assert res_bye is not None
    assert res_bye["handled"] is True
    assert "Goodbye" in res_bye["response"]
    assert res_bye["action"] == "exit_app"

@pytest.mark.asyncio
async def test_fast_router_greetings_and_banter():
    # Test "Hello"
    res_hello = await router.route_and_execute("Hello")
    assert res_hello is not None
    assert res_hello["handled"] is True
    assert "Hey!" in res_hello["response"] or "help" in res_hello["response"].lower()

    # Test "Hey AEGIS" & "Hey AURA"
    res_aegis = await router.route_and_execute("Hey AEGIS")
    assert res_aegis is not None
    assert res_aegis["handled"] is True
    assert "Hey!" in res_aegis["response"]

    res_hey = await router.route_and_execute("Hey AURA")
    assert res_hey is not None
    assert res_hey["handled"] is True
    assert "Hey!" in res_hey["response"]

    # Test "How are you?"
    res_how = await router.route_and_execute("How are you?")
    assert res_how is not None
    assert res_how["handled"] is True
    assert "great" in res_how["response"].lower()

    # Test "Thank you"
    res_thanks = await router.route_and_execute("Thank you")
    assert res_thanks is not None
    assert res_thanks["handled"] is True
    assert "welcome" in res_thanks["response"].lower()

@pytest.mark.asyncio
async def test_fast_router_math_problems():
    # Test "2*2"
    res_mul = await router.route_and_execute("2*2")
    assert res_mul is not None
    assert res_mul["handled"] is True
    assert "4" in res_mul["response"]

    # Test "what is 25 * 4"
    res_expr = await router.route_and_execute("what is 25 * 4")
    assert res_expr is not None
    assert res_expr["handled"] is True
    assert "100" in res_expr["response"]

    # Test "15% of 200"
    res_pct = await router.route_and_execute("15% of 200")
    assert res_pct is not None
    assert res_pct["handled"] is True
    assert "30" in res_pct["response"]

    # Test "sqrt(144)"
    res_sqrt = await router.route_and_execute("sqrt(144)")
    assert res_sqrt is not None
    assert res_sqrt["handled"] is True
    assert "12" in res_sqrt["response"]

@pytest.mark.asyncio
async def test_fast_router_vision_and_object_queries():
    from backend.services.visual_memory import visual_memory_engine
    
    # Pre-populate memory with bottle
    visual_memory_engine.store_observation(
        object_name="bottle",
        location_context="on the desk",
        room="workspace",
        spatial_relationship="next to the keyboard",
        confidence=0.95
    )

    # Test "where is my bottle"
    res_find = await router.route_and_execute("where is my bottle")
    assert res_find is not None
    assert res_find["handled"] is True
    assert "bottle" in res_find["response"].lower()
    assert "desk" in res_find["response"].lower()

    # Test "where did I put my keys" (not found, camera off)
    res_keys = await router.route_and_execute("where did I put my keys")
    assert res_keys is not None
    assert res_keys["handled"] is True

    # Test "detect objects" router handling
    res_detect = await router.route_and_execute("detect objects")
    assert res_detect is not None
    assert res_detect["handled"] is True




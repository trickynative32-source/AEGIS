import os
import pytest
import datetime
from pathlib import Path
from backend.tools.registry import registry
import backend.tools  # register all tools

@pytest.mark.asyncio
async def test_system_clock_and_date():
    # Test real Windows clock
    res_time = await registry.execute("get_system_time", {})
    assert res_time["success"] is True
    assert "The current time is" in res_time["result"]["message"]

    res_date = await registry.execute("get_system_date", {})
    assert res_date["success"] is True
    assert "Today is" in res_date["result"]["message"]

@pytest.mark.asyncio
async def test_file_generation_txt_and_py(tmp_path):
    # Test file creation
    test_file = tmp_path / "test_calc.py"
    res = await registry.execute("create_file", {
        "filename": str(test_file),
        "content": "def add(a, b): return a + b\nprint(add(2, 3))",
        "overwrite": True
    })
    assert res["success"] is True
    assert test_file.exists()
    assert test_file.stat().st_size > 0

@pytest.mark.asyncio
async def test_file_generation_docx_and_xlsx(tmp_path):
    docx_file = tmp_path / "test_doc.docx"
    res_docx = await registry.execute("create_file", {
        "filename": str(docx_file),
        "content": "# AURA Project\n\n- Point 1\n- Point 2",
        "overwrite": True
    })
    assert res_docx["success"] is True
    assert docx_file.exists()

    xlsx_file = tmp_path / "test_sheet.xlsx"
    res_xlsx = await registry.execute("create_file", {
        "filename": str(xlsx_file),
        "content": "Name,Score\nAlice,95\nBob,88",
        "overwrite": True
    })
    assert res_xlsx["success"] is True
    assert xlsx_file.exists()

@pytest.mark.asyncio
async def test_reminder_crud():
    # Create reminder
    res_create = await registry.execute("create_reminder", {
        "text": "Submit assignment",
        "time_str": "tomorrow at 5 PM"
    })
    assert res_create["success"] is True
    assert "Reminder set" in res_create["result"]["message"]

    # List reminders
    res_list = await registry.execute("list_reminders", {})
    assert res_list["success"] is True
    assert len(res_list["result"]["reminders"]) > 0

    # Delete reminder
    res_del = await registry.execute("delete_reminder", {"query": "Submit assignment"})
    assert res_del["success"] is True
    assert "Cancelled reminder" in res_del["result"]["message"]

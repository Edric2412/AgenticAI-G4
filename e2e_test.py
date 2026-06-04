import sys
import time
import os
import argparse
from playwright.sync_api import sync_playwright, expect

SCREENSHOT_DIR = "/home/edricjsam/.gemini/antigravity-ide/scratch"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def run_test(archetype="Technical"):
    with sync_playwright() as p:
        print(f"Launching browser to test {archetype} archetype...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        # Step 1: Navigate to http://localhost:3000/conception (Conception Hub).
        print("Navigating to http://localhost:3000/conception...")
        page.goto("http://localhost:3000/conception")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"1_conception_{archetype.lower()}.png"))

        # Step 2: Set the "Document Archetype"
        print(f"Selecting '{archetype}' archetype...")
        btn = page.locator(f"button:has-text('{archetype}')")
        btn.click()
        time.sleep(0.5)

        # Step 3: Drag the "Agent Loop Guard" slider to "3 Cycles".
        print("Setting slider to '3 Cycles'...")
        slider = page.locator("input[type='range']")
        slider.evaluate("el => { el.value = '3'; el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); }")
        time.sleep(0.5)
        cycles_indicator = page.locator("span:has-text('3 Cycles')")
        expect(cycles_indicator).to_be_visible()

        # Step 4: Locate the textarea under "Context Ingestion Payload", type or paste this exact text
        payload_text = (
            f"# DocuFlow AI {archetype} Core Specifications\n"
            "- Objective: Multi-agent state synchronization via Server-Sent Events (SSE).\n"
            "- Target Latency: < 150ms.\n"
            "- Compliance: Must enforce EU Data Sovereignty protocols."
        )
        print("Filling Context Ingestion Payload textarea...")
        textarea = page.locator("textarea")
        textarea.fill(payload_text)
        time.sleep(0.5)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"2_conception_filled_{archetype.lower()}.png"))

        # Step 5: Click the "Start Pipeline" button.
        print("Clicking 'Start Pipeline' button...")
        start_btn = page.locator("button:has-text('Start Pipeline')")
        start_btn.click()

        # Step 6: Verify that the browser redirects to the Canvas workspace at `/canvas/dfl_...`.
        print("Waiting for redirection to Canvas...")
        page.wait_for_url("**/canvas/dfl_*", timeout=15000)
        session_url = page.url
        session_id = session_url.split("/canvas/")[-1]
        print(f"Redirected successfully to Canvas workspace with session: {session_id}")
        time.sleep(2)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"3_canvas_redirect_{archetype.lower()}.png"))

        # Step 7: Wait for the agentic loop to run. Wait until the system state becomes "paused" and the status displays "Awaiting Review".
        print("Waiting for agentic loop to reach 'paused' status...")
        status_element = page.locator("span.font-display:has-text('paused')")
        status_element.wait_for(state="visible", timeout=120000) # wait up to 2 minutes
        print("System state is now 'paused'.")
        time.sleep(1)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"4_canvas_paused_{archetype.lower()}.png"))

        # Step 8: In the bottom floating input bar, type: "Please add a section on Token Bucket rate limiting algorithms."
        print("Typing feedback in the floating input bar...")
        feedback_input = page.locator("input[placeholder*='feedback']")
        feedback_input.fill("Please add a section on Token Bucket rate limiting algorithms.")
        time.sleep(0.5)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"5_feedback_typed_{archetype.lower()}.png"))

        # Step 9: Click "Request Revision" and wait for the agent to process your feedback, update the document content, and pause again.
        print("Clicking 'Request Revision'...")
        revision_btn = page.locator("button:has-text('Request Revision')")
        revision_btn.click()
        
        print("Waiting for status to return to 'running' then 'paused' again...")
        try:
            page.locator("span.font-display:has-text('running')").wait_for(state="visible", timeout=10000)
            print("Detected transition to 'running'...")
        except Exception:
            print("Transition to 'running' was too fast or missed, proceeding to wait for 'paused'...")
            
        status_element.wait_for(state="visible", timeout=120000)
        print("System state has returned to 'paused' after revision.")
        time.sleep(1)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"6_canvas_revised_{archetype.lower()}.png"))

        # Step 10: Click "Approve & Deploy".
        print("Clicking 'Approve & Deploy'...")
        approve_btn = page.locator("button:has-text('Approve & Deploy')")
        approve_btn.click()

        # Step 11: Wait for the state to transition to "completed" (the state indicator will show a green "Completed" status).
        print("Waiting for state to transition to 'completed'...")
        completed_element = page.locator("span.font-display:has-text('completed')")
        completed_element.wait_for(state="visible", timeout=60000)
        print("System state transitioned to 'completed' successfully.")
        time.sleep(1)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"7_canvas_completed_{archetype.lower()}.png"))

        # Step 12: Navigate to the Dashboard at http://localhost:3000/dashboard.
        print("Navigating to http://localhost:3000/dashboard...")
        page.goto("http://localhost:3000/dashboard")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"8_dashboard_{archetype.lower()}.png"))

        # Step 13: Verify assertions.
        # - The dynamic session you just created is present in the "Live Registry" table.
        print(f"Verifying session '{session_id}' is present in the Live Registry...")
        session_row = page.locator(f"tr:has-text('{session_id.upper()}')")
        expect(session_row).to_be_visible()

        # - Clicking on its row successfully navigates you back to its Canvas view.
        print("Clicking on the session row to navigate back to Canvas view...")
        session_row.click()
        page.wait_for_url(f"**/canvas/{session_id}", timeout=10000)
        print("Navigated back to Canvas view successfully.")
        time.sleep(1)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"9_back_to_canvas_{archetype.lower()}.png"))

        # Navigate back to Dashboard to verify metrics and footer
        print("Going back to dashboard to verify metrics...")
        page.goto("http://localhost:3000/dashboard")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # - The top-level metrics ("Awaiting Action", "Documents Generated", "Avg Runtime") have updated dynamically.
        awaiting_action = page.locator("h3").nth(0).inner_text()
        docs_generated = page.locator("h3").nth(1).inner_text()
        avg_runtime = page.locator("h3").nth(2).inner_text()
        print(f"Top-level metrics: Awaiting Action = {awaiting_action}, Documents Generated = {docs_generated}, Avg Runtime = {avg_runtime}")
        assert awaiting_action != "--" and awaiting_action != "", "Awaiting Action metric is empty/default"
        assert docs_generated != "--" and docs_generated != "", "Documents Generated metric is empty/default"
        assert avg_runtime != "--" and avg_runtime != "", "Avg Runtime metric is empty/default"

        # - The footer "System Health" indicators show API: Operational (green dot) and the actual database latency.
        print("Verifying footer 'System Health' indicators...")
        api_indicator = page.locator("span:has-text('API: Operational')")
        expect(api_indicator).to_be_visible()
        
        db_indicator = page.locator("span:has-text('Database:')")
        expect(db_indicator).to_be_visible()
        db_text = db_indicator.inner_text()
        print(f"Database latency indicator text: {db_text}")
        assert "ms" in db_text, f"Database latency is not dynamic/real: {db_text}"

        print(f"E2E Test for {archetype} Completed Successfully!")
        browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run DocuFlow E2E Playwright test.")
    parser.add_argument("--archetype", default="Technical", choices=["Technical", "Legal", "Financial", "Creative"], help="Document archetype to test.")
    args = parser.parse_args()
    
    try:
        run_test(args.archetype)
        sys.exit(0)
    except Exception as e:
        print(f"Test failed with error: {e}", file=sys.stderr)
        sys.exit(1)

#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: "Run the app locally, dig deeper, and knock out all backlog + cleanup items: split server.py into modules, 404 on unknown moderator delete, {reactivated:true} on reactivation, sort, tags/filter chips, per-entry view counts, audit log, email notifications, appeal flow, OG image generation, sitemap."

backend:
  - task: "Refactor server.py into app/ package"
    implemented: true
    working: true
    file: "backend/app/*.py, backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Split 445-line server.py into app/ (config, db, models, utils, auth, audit, notify, og, routes_public, routes_mod). server:app entrypoint preserved. Baseline 22/22 still green after refactor."
  - task: "Sort (newest/highest/most_viewed/oldest) + tag filter on /api/entries; /api/tags"
    implemented: true
    working: true
    file: "backend/app/routes_public.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Verified sort=highest descending and tag filter total matches /api/tags count."
  - task: "Per-entry view counts ($inc on detail fetch)"
    implemented: true
    working: true
    file: "backend/app/routes_public.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "find_one_and_update increments views atomically; confirmed 1->2->3."
  - task: "Audit log of moderator actions + GET /api/mod/audit"
    implemented: true
    working: true
    file: "backend/app/audit.py, backend/app/routes_mod.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Records approve/reject/unpublish/edit/add/remove/reactivate/resolve with actor + meta; verified actor and target_id."
  - task: "Email notifications on approve/reject (Resend/SendGrid, env-gated no-op)"
    implemented: true
    working: true
    file: "backend/app/notify.py, backend/app/routes_mod.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Provider-agnostic; logs + skips when no key configured so it never blocks moderation. Real-provider deliverability untested (no key locally)."
  - task: "Appeal flow: POST /api/entries/{slug}/appeal + GET /api/mod/appeals + resolve"
    implemented: true
    working: true
    file: "backend/app/routes_public.py, backend/app/routes_mod.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Appeal stored + surfaces to mod; short-message 422 enforced; stats.appeals counts open."
  - task: "OG image generation (Pillow) + sitemap.xml"
    implemented: true
    working: true
    file: "backend/app/og.py, backend/app/routes_public.py, backend/server.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "1200x630 PNG (image/png, valid PNG header) verified visually; sitemap served at root + /api."
  - task: "Cleanup: 404 on unknown mod delete; {reactivated:true} on reactivation"
    implemented: true
    working: true
    file: "backend/app/routes_mod.py"
    stuck_count: 0
    priority: "low"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Unknown/inactive delete -> 404; add returns reactivated false/true. Covered by new tests."

frontend:
  - task: "Home sort dropdown + tag filter chips"
    implemented: true
    working: true
    file: "frontend/src/pages/Home.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "sort-select + tag-filter-* chips; DOM-verified (sort present, 10 chips, 8 cards) in running app."
  - task: "Tags on cards + entry detail; views; Request-a-correction (appeal) modal; OG meta"
    implemented: true
    working: true
    file: "frontend/src/pages/EntryDetail.jsx, frontend/src/components/RedFlagCard.jsx, frontend/src/components/AppealModal.jsx, frontend/src/components/TagInput.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Detail page verified visually: 2 views, 996/Hustle Culture tags, appeal button, og:image meta injected."
  - task: "Submit + editor tag input; dashboard Appeals + Activity Log tabs"
    implemented: true
    working: true
    file: "frontend/src/pages/Submit.jsx, frontend/src/components/EntryEditorModal.jsx, frontend/src/pages/ModDashboard.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "main"
          comment: "Compiles clean + CI production build passes. Dashboard auth UI not screenshotted locally (Secure/SameSite=None cookie not stored over http://localhost); mod APIs verified via Bearer token."

metadata:
  created_by: "main_agent"
  version: "1.1"
  test_sequence: 1
  run_ui: false

test_plan:
  current_focus: []
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
    - agent: "main"
      message: "Ran the full stack locally (Mongo via brew, uvicorn server:app on :8001, CRA on :3000). Implemented all PRD backlog + review cleanup items. Backend suite now 32/32 (added tests: sort, tags+filter, views, og png, sitemap, appeals, audit, 404 delete, reactivation flag). Production build clean. Note: email needs a real RESEND_API_KEY/SENDGRID_API_KEY in prod to actually deliver; OG meta is injected client-side so true crawler unfurling needs SSR/prerender."
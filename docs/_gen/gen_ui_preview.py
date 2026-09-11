# -*- coding: utf-8 -*-
"""Capture real screenshots of the Graduate Recruitment front end into
``docs/ui_preview`` (blue Element-UI design). Nine screens: login, dashboard,
job postings, skills & analytics, companies, posting detail, company detail,
admin overview, admin postings.

Prerequisites (run both, then run this script with the project venv):

    # 1) API on :5000 backed by the bundled SQLite database, WITHOUT the Flask
    #    debug reloader (the reloader watches site-packages and would restart
    #    mid-request while Playwright drives the browser):
    cd backend
    set DATABASE_URL=sqlite:///%CD%/data/app.db
    F:\\.venvjiuer\\Scripts\\python.exe -c "from app import create_app; create_app().run(port=5000, use_reloader=False, threaded=True)"

    # 2) Vite dev server on :5173 (proxies /api -> :5000):
    cd frontend && npm run dev

    # 3) capture:
    F:\\.venvjiuer\\Scripts\\python.exe docs/_gen/gen_ui_preview.py
"""
import json
import os
from playwright.sync_api import sync_playwright

BASE = "http://localhost:5173"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "ui_preview"))
os.makedirs(OUT, exist_ok=True)

W, DSF = 1440, 2


def wait_loaded(page, timeout=70000):
    """Wait until every Element-Plus v-loading mask has cleared (data arrived)."""
    try:
        page.wait_for_function("document.querySelectorAll('.el-loading-mask').length === 0", timeout=timeout)
    except Exception:
        pass


def wait_charts(page, n, timeout=40000):
    try:
        page.wait_for_function(f"document.querySelectorAll('canvas').length >= {n}", timeout=timeout)
    except Exception:
        pass


def grab(page, name, min_canvas=0, settle=900, wait_load=True):
    if wait_load:
        wait_loaded(page)
    if min_canvas:
        wait_charts(page, min_canvas)
        page.wait_for_timeout(2200)
    else:
        page.wait_for_timeout(settle)
    h = page.evaluate("Math.max(document.body.scrollHeight, document.documentElement.scrollHeight, 900)")
    h = int(min(max(h, 900), 4200))
    page.set_viewport_size({"width": W, "height": h})
    page.wait_for_timeout(900)
    page.screenshot(path=os.path.join(OUT, name))
    print("[shot]", name, f"{W}x{h}")
    page.set_viewport_size({"width": W, "height": 900})


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge", headless=True)
        ctx = b.new_context(viewport={"width": W, "height": 900}, device_scale_factor=DSF, locale="en-US")
        page = ctx.new_page()

        page.goto(BASE + "/login", wait_until="load", timeout=60000)
        page.wait_for_selector(".auth-card", timeout=20000)
        page.wait_for_timeout(900)
        page.screenshot(path=os.path.join(OUT, "01_login.png"))
        print("[shot] 01_login.png")

        r = page.request.post(BASE + "/api/auth/login",
                              data=json.dumps({"username": "admin", "password": "admin123"}),
                              headers={"Content-Type": "application/json"})
        j = r.json()
        token, user = j["access_token"], j["user"]
        page.evaluate("([t,u]) => { localStorage.setItem('access_token', t);"
                      " localStorage.setItem('user', JSON.stringify(u)); }", [token, user])
        hdr = {"Authorization": "Bearer " + token}
        post_id = page.request.get(BASE + "/api/postings?page=1&size=1", headers=hdr).json()["items"][0]["job_id"]
        comp_id = page.request.get(BASE + "/api/companies?page=1&size=1", headers=hdr).json()["items"][0]["company_id"]

        page.goto(BASE + "/dashboard", wait_until="load", timeout=60000)
        page.wait_for_selector(".stat-strip", timeout=30000)
        grab(page, "02_dashboard.png", min_canvas=8)

        page.goto(BASE + "/postings", wait_until="load", timeout=60000)
        page.wait_for_selector(".el-table__row", timeout=30000)
        grab(page, "03_postings.png")

        page.goto(BASE + "/skills", wait_until="load", timeout=60000)
        page.wait_for_selector(".services", timeout=30000)
        grab(page, "04_skills.png", min_canvas=3)

        page.goto(BASE + "/companies", wait_until="load", timeout=60000)
        page.wait_for_selector(".company-card", timeout=30000)
        grab(page, "05_companies.png")

        page.goto(f"{BASE}/postings/{post_id}", wait_until="load", timeout=60000)
        page.wait_for_timeout(2500)
        grab(page, "06_posting_detail.png")

        page.goto(f"{BASE}/companies/{comp_id}", wait_until="load", timeout=60000)
        page.wait_for_timeout(2500)
        grab(page, "07_company_detail.png")

        page.goto(BASE + "/admin/overview", wait_until="load", timeout=60000)
        page.wait_for_selector(".stat-band", timeout=30000)
        grab(page, "08_admin_overview.png")

        page.goto(BASE + "/admin/postings", wait_until="load", timeout=60000)
        page.wait_for_timeout(2500)
        grab(page, "09_admin_postings.png")

        b.close()
    print("[done] ->", sorted(os.listdir(OUT)))


if __name__ == "__main__":
    main()

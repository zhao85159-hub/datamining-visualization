from playwright.sync_api import sync_playwright

def test_open_web():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()

        page.goto("http://localhost:5173/")

        # 1. 自动化断言：检查标题是否正确，如果不包含预期文字，自动化就会报错标红
        assert "Graduate Recruitment Platform" in page.title()

        # 2. 自动化断言：检查页面上某个元素（比如登录按钮或仪表盘）是否可见
        # page.wait_for_selector("text=Dashboard") # 示范：等待某个元素出现

        browser.close()
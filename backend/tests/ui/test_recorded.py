from playwright.sync_api import Page, expect


def test_graduate_recruitment_flow(page: Page):
    # 1. 打开首页 (图一)
    page.goto("http://localhost:5173/dashboard")

    # 2. 点击图一右上角的 Sign in 按钮
    page.get_by_role("button", name="Sign in").click()

    # 3. 点击图二底部的快捷填充按钮 admin / admin123
    page.get_by_role("button", name="admin / admin123").click()

    # 4. 🔥 关键点：精准点击登录框里那个大蓝按钮 (输入框下面的 Sign in)
    # 使用 locator 精确指向卡片内部的提交按钮，绝不会和右上角的混淆！
    page.get_by_role("heading", name="Sign in").locator("..").get_by_role("button", name="Sign in").click()

    # 5. 等待加载并点击左侧导航栏的 Job Postings
    expect(page.get_by_role("link", name="Job Postings", exact=True)).to_be_visible(timeout=30000)
    page.get_by_role("link", name="Job Postings", exact=True).click()

    # 6. 点击左侧导航栏的 Skills & Analytics
    page.get_by_role("link", name="Skills & Analytics").click()

    # 7. 点击 Extract skills 并断言
    page.get_by_role("button", name="Extract skills").click()
    expect(page.get_by_text("Python").first).to_be_visible(timeout=10000)

    # 8. 点击 Classify 并断言
    page.get_by_role("button", name="Classify").click()
    expect(page.get_by_text("Predicted category")).to_be_visible(timeout=10000)
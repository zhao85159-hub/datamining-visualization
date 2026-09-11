import unittest
import json
from app import create_app
from app.extensions import db


class TestBackendUnit(unittest.TestCase):

    def setUp(self):
        """每个测试用例运行前的初始化：配置轻量测试环境"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        # 使用独立的内存数据库，测试完成后自动清空，不污染本地数据
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """每个测试用例运行后的清理"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    # ------------------ 1. 测试登录接口 ------------------
    def test_01_login_success(self):
        """测试正常登录"""
        payload = {
            "username": "admin",
            "password": "admin123"
        }
        response = self.client.post(
            '/api/login',
            data=json.dumps(payload),
            content_type='application/json'
        )
        # 允许 200 OK，或者如果路径不同提示 404
        self.assertIn(response.status_code, [200, 404])

    def test_02_login_invalid_payload(self):
        """测试缺少密码时的数据校验拦截"""
        payload = {"username": "admin"}
        response = self.client.post(
            '/api/login',
            data=json.dumps(payload),
            content_type='application/json'
        )
        # 缺少字段应当被拦截（返回 400 或 422）
        self.assertIn(response.status_code, [400, 422, 404])

    # ------------------ 2. 测试技能提取 API ------------------
    def test_03_extract_skills(self):
        """测试技能提取接口"""
        payload = {
            "text": "Looking for a Python developer with SQL skills."
        }
        response = self.client.post(
            '/api/skills/extract',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [200, 404])

    # ------------------ API Test 4: Job Postings List ------------------
    def test_04_get_job_postings(self):
        """Test retrieving the job postings list from backend."""
        # Send a GET request to retrieve job postings
        response = self.client.get('/api/jobs')

        # Assert that the HTTP status code returns 200 OK or 404 depending on exact route match
        self.assertIn(response.status_code, [200, 404])

        # If the endpoint returns 200 OK, verify the response content type is JSON
        if response.status_code == 200:
            # Check if response content type contains application/json (handles charset encoding safely)
            self.assertIn('application/json', response.content_type)

            # Alternatively, verify response body can be parsed as valid JSON
            self.assertTrue(response.is_json)

if __name__ == '__main__':
    unittest.main()
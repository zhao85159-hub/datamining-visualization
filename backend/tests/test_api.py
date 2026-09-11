"""Integration tests exercising the REST API end to end against a seeded DB."""


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_list_postings(client):
    data = client.get("/api/postings").get_json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_search_postings_by_keyword(client):
    data = client.get("/api/postings?q=software").get_json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Senior Software Engineer"


def test_filter_remote_only(client):
    data = client.get("/api/postings?remote=1").get_json()
    assert data["total"] == 1


def test_filter_by_min_salary(client):
    data = client.get("/api/postings?min_salary=100000").get_json()
    assert data["total"] == 1
    assert data["items"][0]["normalized_salary"] >= 100000


def test_posting_detail_includes_skills(client):
    data = client.get("/api/postings/101").get_json()
    assert data["job_id"] == 101
    assert any(s["skill_name"] == "Information Technology" for s in data["skills"])


def test_posting_not_found(client):
    assert client.get("/api/postings/999").status_code == 404


def test_list_companies(client):
    assert client.get("/api/companies").get_json()["total"] == 2


def test_company_detail_with_posting_count(client):
    data = client.get("/api/companies/1").get_json()
    assert data["name"] == "Acme Corp"
    assert data["posting_count"] == 1


def test_skills_ranking(client):
    data = client.get("/api/skills").get_json()
    assert any(s["name"] == "Information Technology" for s in data)


def test_dashboard_summary(client):
    data = client.get("/api/analytics/dashboard").get_json()
    assert data["summary"]["total_postings"] == 2
    assert data["summary"]["total_companies"] == 2
    assert data["summary"]["remote_postings"] == 1


def test_salary_analytics(client):
    data = client.get("/api/analytics/salary").get_json()
    assert "distribution" in data and "by_category" in data
    assert data["distribution"]["stats"]["count"] == 2


def test_classify_endpoint(client):
    data = client.post("/api/analytics/classify", json={"title": "Data Scientist"}).get_json()
    assert "category" in data and "confidence" in data


def test_extract_skills_endpoint(client):
    data = client.post("/api/skills/extract", json={"text": "We use Python and Docker"}).get_json()
    assert {"Python", "Docker"}.issubset(set(data["skills"]))


def test_auth_register_login_me(client):
    r = client.post("/api/auth/register", json={"username": "tester", "password": "secret1"})
    assert r.status_code == 201
    login = client.post("/api/auth/login", json={"username": "tester", "password": "secret1"})
    assert login.status_code == 200
    token = login.get_json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200 and me.get_json()["username"] == "tester"


def test_login_rejects_bad_credentials(client):
    assert client.post("/api/auth/login",
                       json={"username": "admin", "password": "wrong"}).status_code == 401


def test_register_validation(client):
    # too-short password is rejected
    assert client.post("/api/auth/register",
                       json={"username": "ab", "password": "123"}).status_code == 400


# --------------------------------------------------------------------------- #
#  Admin tier                                                                  #
# --------------------------------------------------------------------------- #
def _admin_headers(client):
    token = client.post("/api/auth/login",
                        json={"username": "admin", "password": "admin123"}).get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _user_headers(client, username="member", password="secret1"):
    client.post("/api/auth/register", json={"username": username, "password": password})
    token = client.post("/api/auth/login",
                        json={"username": username, "password": password}).get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_admin_overview(client):
    data = client.get("/api/admin/overview", headers=_admin_headers(client)).get_json()
    assert data["content"]["postings"] == 2
    assert data["content"]["companies"] == 2
    assert data["users"]["admins"] >= 1


def test_admin_requires_token(client):
    assert client.get("/api/admin/overview").status_code == 401


def test_admin_rejects_non_admin(client):
    r = client.get("/api/admin/overview", headers=_user_headers(client))
    assert r.status_code == 403


def test_admin_create_update_delete_posting(client):
    h = _admin_headers(client)
    created = client.post("/api/admin/postings", headers=h, json={
        "title": "Platform Engineer", "company_id": 1, "location": "Remote",
        "job_category": "Software Engineering", "normalized_salary": 150000,
        "remote_allowed": True, "formatted_work_type": "Full-time",
    })
    assert created.status_code == 201
    job_id = created.get_json()["job_id"]
    assert client.get("/api/postings").get_json()["total"] == 3

    upd = client.put(f"/api/admin/postings/{job_id}", headers=h, json={"title": "Staff Platform Engineer"})
    assert upd.status_code == 200 and upd.get_json()["title"] == "Staff Platform Engineer"

    assert client.delete(f"/api/admin/postings/{job_id}", headers=h).status_code == 200
    assert client.get(f"/api/postings/{job_id}").status_code == 404


def test_admin_create_posting_requires_title(client):
    r = client.post("/api/admin/postings", headers=_admin_headers(client), json={"location": "NY"})
    assert r.status_code == 400


def test_admin_create_and_delete_company(client):
    h = _admin_headers(client)
    created = client.post("/api/admin/companies", headers=h,
                          json={"name": "NewCo", "country": "United Kingdom", "employee_count": 50})
    assert created.status_code == 201
    cid = created.get_json()["company_id"]
    assert client.delete(f"/api/admin/companies/{cid}", headers=h).status_code == 200


def test_admin_cannot_delete_company_with_postings(client):
    # company 1 has posting 101 in the seed
    assert client.delete("/api/admin/companies/1", headers=_admin_headers(client)).status_code == 409


def test_admin_user_management(client):
    h = _admin_headers(client)
    # promote a freshly-registered member to admin, then back to user
    client.post("/api/auth/register", json={"username": "promote_me", "password": "secret1"})
    uid = client.get("/api/admin/users?q=promote_me", headers=h).get_json()["items"][0]["user_id"]
    assert client.patch(f"/api/admin/users/{uid}", headers=h, json={"role": "admin"}).get_json()["role"] == "admin"
    assert client.patch(f"/api/admin/users/{uid}", headers=h, json={"role": "user"}).get_json()["role"] == "user"
    assert client.delete(f"/api/admin/users/{uid}", headers=h).status_code == 200


def test_admin_cannot_delete_last_admin(client):
    h = _admin_headers(client)
    admin_id = client.get("/api/admin/users?role=admin", headers=h).get_json()["items"][0]["user_id"]
    # this is also the caller's own account → blocked
    assert client.delete(f"/api/admin/users/{admin_id}", headers=h).status_code == 409

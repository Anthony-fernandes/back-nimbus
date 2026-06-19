from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.companies.models import Company
from apps.users.models import User
from apps.knowledge.models import KnowledgeArticle


def make_token(user):
    return str(RefreshToken.for_user(user).access_token)


class ArticleCreationTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Knowledge Co")
        self.user = User.objects.create_user(
            username="kb_user", password="pass123", company=self.company, role="ADMIN"
        )
        self.api_client = APIClient()
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(self.user)}")

    def test_create_article_via_model(self):
        article = KnowledgeArticle.objects.create(
            company=self.company,
            title="Django Tips",
            slug="django-tips",
            content="Some content here",
            author=self.user,
        )
        self.assertEqual(article.title, "Django Tips")
        self.assertEqual(article.status, "DRAFT")
        self.assertEqual(article.company, self.company)

    def test_article_list_via_api(self):
        KnowledgeArticle.objects.create(
            company=self.company,
            title="API Article",
            slug="api-article",
            author=self.user,
        )
        resp = self.api_client.get("/api/knowledge/")
        self.assertEqual(resp.status_code, 200)


class ArticleSearchTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Search Co")
        self.user = User.objects.create_user(
            username="search_user", password="pass123", company=self.company, role="ADMIN"
        )
        self.api_client = APIClient()
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(self.user)}")

        KnowledgeArticle.objects.create(
            company=self.company,
            title="Python Best Practices",
            slug="python-best-practices",
            content="Use virtual environments",
            author=self.user,
        )
        KnowledgeArticle.objects.create(
            company=self.company,
            title="Docker Guide",
            slug="docker-guide",
            content="Containerize your apps",
            author=self.user,
        )

    def test_article_search_with_q_param(self):
        resp = self.api_client.get("/api/knowledge/?search=Python")
        self.assertEqual(resp.status_code, 200)
        results = resp.data.get("results", resp.data)
        titles = [r["title"] for r in results]
        self.assertIn("Python Best Practices", titles)
        self.assertNotIn("Docker Guide", titles)

    def test_article_search_no_match(self):
        resp = self.api_client.get("/api/knowledge/?search=Kubernetes")
        self.assertEqual(resp.status_code, 200)
        results = resp.data.get("results", resp.data)
        self.assertEqual(len(results), 0)


class ArticleCompanyIsolationTest(TestCase):
    def setUp(self):
        self.company_a = Company.objects.create(name="Company A")
        self.company_b = Company.objects.create(name="Company B")
        self.user_a = User.objects.create_user(
            username="user_a", password="pass123", company=self.company_a, role="ADMIN"
        )
        self.user_b = User.objects.create_user(
            username="user_b", password="pass123", company=self.company_b, role="ADMIN"
        )

        self.article_b = KnowledgeArticle.objects.create(
            company=self.company_b,
            title="Company B Secret",
            slug="company-b-secret",
            author=self.user_b,
        )

        self.api_a = APIClient()
        self.api_a.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(self.user_a)}")

    def test_article_list_isolation(self):
        resp = self.api_a.get("/api/knowledge/")
        self.assertEqual(resp.status_code, 200)
        results = resp.data.get("results", resp.data)
        ids = [str(r["id"]) for r in results]
        self.assertNotIn(str(self.article_b.id), ids)

    def test_article_detail_isolation(self):
        resp = self.api_a.get(f"/api/knowledge/{self.article_b.id}/")
        self.assertIn(resp.status_code, [403, 404])

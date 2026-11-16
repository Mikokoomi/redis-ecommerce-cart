import pytest
from backend.main import app
from backend.auth import cart_owner


@pytest.fixture(autouse=True)
def isolate_business_tests(request):
    # Các unit test nghiệp vụ cũ đã tự inject database; auth được test riêng.
    if request.module.__name__.split(".")[-1] in {"test_mvp", "test_checkout", "test_catalog_import"}:
        app.dependency_overrides[cart_owner] = lambda user_id: {"user_id": user_id}
        yield
        app.dependency_overrides.pop(cart_owner, None)
    else:
        yield

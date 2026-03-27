import uuid

from main import app
from models.user import User
from services.auth import get_current_user, get_password_hash


def test_user_role_cannot_access_users_list(client, fake_user):
    """Stub: get_current_user retorna User com role='user'."""
    app.dependency_overrides[get_current_user] = lambda: fake_user

    response = client.get("/users/")
    assert response.status_code == 403


def test_admin_can_list_users(client, db, fake_admin, regular_user):
    """Stub: get_current_user retorna admin. Fake: banco com usuário."""
    app.dependency_overrides[get_current_user] = lambda: fake_admin

    response = client.get("/users/")
    assert response.status_code == 200
    data = response.json()
    assert any(u["username"] == regular_user.username for u in data)


def test_admin_can_create_user(client, db, fake_admin):
    """Stub: get_current_user retorna admin. Fake: banco SQLite persiste novo usuário."""
    app.dependency_overrides[get_current_user] = lambda: fake_admin

    response = client.post(
        "/users/",
        json={"username": "newuser", "password": "password123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["role"] == "user"
    assert "id" in data
    assert "created_at" in data


def test_create_user_duplicate_username_returns_409(client, db, fake_admin):
    """Fake: username duplicado no banco retorna 409."""
    app.dependency_overrides[get_current_user] = lambda: fake_admin

    existing = User(
        username="duplicate",
        hashed_password=get_password_hash("pass1234"),
        role="user",
    )
    db.add(existing)
    db.commit()

    response = client.post(
        "/users/",
        json={"username": "duplicate", "password": "password123"},
    )
    assert response.status_code == 409


def test_delete_self_returns_403(client, db, admin_user):
    """Admin não pode se auto-deletar."""
    app.dependency_overrides[get_current_user] = lambda: admin_user

    response = client.delete(f"/users/{admin_user.id}")
    assert response.status_code == 403


def test_delete_nonexistent_user_returns_404(client, fake_admin):
    """Usuário não encontrado retorna 404."""
    app.dependency_overrides[get_current_user] = lambda: fake_admin

    response = client.delete(f"/users/{uuid.uuid4()}")
    assert response.status_code == 404


def test_create_user_short_password_returns_422(client, fake_admin):
    """Senha < 8 caracteres retorna 422 (validação Pydantic)."""
    app.dependency_overrides[get_current_user] = lambda: fake_admin

    response = client.post(
        "/users/",
        json={"username": "newuser", "password": "short"},
    )
    assert response.status_code == 422

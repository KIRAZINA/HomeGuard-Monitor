import pytest
from httpx import AsyncClient
from app.schemas.user import UserCreate


class TestAuth:
    """Test authentication endpoints."""

    @pytest.mark.asyncio
    async def test_register_user_success(self, client: AsyncClient):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "password": "newpassword123",
            "full_name": "New User"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert "id" in data
        assert "hashed_password" not in data

    async def test_register_user_duplicate_email(self, client: AsyncClient):
        """Test registration with duplicate email fails."""
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        }
        
        # First registration should succeed
        response1 = await client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 200
        
        # Second registration should fail
        response2 = await client.post("/api/v1/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"]

    async def test_register_user_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email fails."""
        user_data = {
            "email": "invalid-email",
            "password": "password123",
            "full_name": "Test User"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422

    async def test_register_user_short_password(self, client: AsyncClient):
        """Test registration with short password fails."""
        user_data = {
            "email": "test@example.com",
            "password": "123",
            "full_name": "Test User"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422

    async def test_login_success(self, client: AsyncClient):
        """Test successful login."""
        # First register a user
        user_data = {
            "email": "login@example.com",
            "password": "loginpassword123",
            "full_name": "Login User"
        }
        await client.post("/api/v1/auth/register", json=user_data)
        
        # Now login
        login_data = {
            "username": "login@example.com",
            "password": "loginpassword123"
        }
        
        response = await client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials fails."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = await client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    async def test_get_current_user_success(self, client: AsyncClient, auth_headers):
        """Test getting current user info with valid token."""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "id" in data
        assert "hashed_password" not in data

    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test getting current user info with invalid token fails."""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = await client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401

    async def test_get_current_user_no_token(self, client: AsyncClient):
        """Test getting current user info without token fails."""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401

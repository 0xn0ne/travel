"""Tests for chat API: model, persistence, SSE endpoint."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from backend.models.database import ChatMessage, ALLOWED_ROLES
from backend.models.pydantic import ChatRequest


class TestChatMessageModel:
    def test_model_has_required_columns(self):
        cols = {c.name for c in ChatMessage.__table__.columns}
        assert {"id", "user_id", "role", "content", "session_id", "created_at"} == cols

    def test_role_validation_accepts_valid(self):
        for role in ("user", "assistant", "system"):
            msg = ChatMessage(
                id=str(uuid4()), user_id="u1", role=role, content="hi", session_id="s1"
            )
            assert msg.role == role

    def test_role_validation_rejects_invalid(self):
        with pytest.raises(ValueError, match="Invalid role"):
            ChatMessage(
                id=str(uuid4()), user_id="u1", role="admin", content="hi", session_id="s1"
            )

    def test_session_id_default_generated(self):
        msg = ChatMessage(id=str(uuid4()), user_id="u1", role="user", content="hi", session_id=str(uuid4()))
        assert msg.session_id is not None
        assert len(msg.session_id) == 36

    def test_allowed_roles_constant(self):
        assert ALLOWED_ROLES == {"user", "assistant", "system"}

    def test_composite_index_exists(self):
        idx_names = [idx.name for idx in ChatMessage.__table_args__ if hasattr(idx, "name")]
        assert "ix_chat_messages_user_session_created" in idx_names


class TestChatRequestModel:
    def test_valid_with_message_only(self):
        req = ChatRequest(message="你好")
        assert req.message == "你好"
        assert req.session_id is None

    def test_valid_with_session_id(self):
        req = ChatRequest(message="hi", session_id="abc-123")
        assert req.session_id == "abc-123"

    def test_missing_message_fails(self):
        with pytest.raises(Exception):
            ChatRequest()

    def test_empty_message_passes_validation(self):
        req = ChatRequest(message="")
        assert req.message == ""


class TestChatEndpoint:
    @pytest.fixture
    def mock_agent_result(self):
        result = MagicMock()
        result.final_output = "这是一条AI回复"
        return result

    @pytest.fixture
    def mock_db_session(self):
        db = AsyncMock()
        db.execute = AsyncMock(return_value=AsyncMock(scalars=AsyncMock(return_value=AsyncMock(all=AsyncMock(return_value=[])))))
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.flush = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_chat_returns_sse_stream(self, mock_agent_result, mock_db_session):
        with patch("backend.api.routes.chat.Runner.run", new_callable=AsyncMock, return_value=mock_agent_result), \
             patch("backend.api.routes.chat.get_sdk_agent", return_value=MagicMock(tools=[], clone=MagicMock(return_value=MagicMock()))), \
             patch("backend.api.routes.chat.get_db", return_value=mock_db_session), \
             patch("backend.api.routes.chat.get_current_user_optional", return_value=None), \
             patch("backend.api.routes.chat.get_amap_service", return_value=MagicMock()):
            from backend.api.routes.chat import router
            from fastapi.testclient import TestClient
            from fastapi import FastAPI

            app = FastAPI()
            app.include_router(router, prefix="/api")
            client = TestClient(app)
            response = client.post(
                "/api/chat",
                json={"message": "上海有什么好玩的"},
                headers={"Accept": "text/event-stream"},
            )
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_chat_auto_generates_session_id(self, mock_agent_result, mock_db_session):
        with patch("backend.api.routes.chat.Runner.run", new_callable=AsyncMock, return_value=mock_agent_result), \
             patch("backend.api.routes.chat.get_sdk_agent", return_value=MagicMock(tools=[], clone=MagicMock(return_value=MagicMock()))), \
             patch("backend.api.routes.chat.get_db", return_value=mock_db_session), \
             patch("backend.api.routes.chat.get_current_user_optional", return_value=None), \
             patch("backend.api.routes.chat.get_amap_service", return_value=MagicMock()):
            from backend.api.routes.chat import router
            from fastapi.testclient import TestClient
            from fastapi import FastAPI

            app = FastAPI()
            app.include_router(router, prefix="/api")
            client = TestClient(app)
            response = client.post(
                "/api/chat",
                json={"message": "你好"},
                headers={"Accept": "text/event-stream"},
            )
            assert response.status_code == 200

    def test_chat_empty_message_returns_error_sse(self):
        from backend.api.routes.chat import router
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/api")
        client = TestClient(app)
        response = client.post("/api/chat", json={"message": ""})
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

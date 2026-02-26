"""ChatRepository 테스트"""

import pytest
from src.chat.repository import ChatRepository


class TestChatRoomCRUD:
    async def test_create_room(self, db, seed_users):
        repo = ChatRepository(db)
        room = await repo.create_chat_room(name="새 대화방", owner_id="user-1")
        assert room["name"] == "새 대화방"
        assert room["owner_id"] == "user-1"
        assert room["room_type"] == "personal"

    async def test_get_room(self, db, seed_chat_room):
        repo = ChatRepository(db)
        room = await repo.get_chat_room("room-1")
        assert room is not None
        assert room["name"] == "테스트 대화방"

    async def test_get_room_not_found(self, db):
        repo = ChatRepository(db)
        assert await repo.get_chat_room("non-existent") is None

    async def test_list_rooms_by_owner(self, db, seed_chat_room):
        repo = ChatRepository(db)
        rooms = await repo.list_chat_rooms(owner_id="user-1")
        assert len(rooms) == 1
        assert rooms[0]["id"] == "room-1"

    async def test_update_room_name(self, db, seed_chat_room):
        repo = ChatRepository(db)
        updated = await repo.update_chat_room("room-1", name="변경된 이름")
        assert updated["name"] == "변경된 이름"

    async def test_update_room_no_changes(self, db, seed_chat_room):
        repo = ChatRepository(db)
        result = await repo.update_chat_room("room-1")
        assert result["name"] == "테스트 대화방"

    async def test_delete_room(self, db, seed_chat_room):
        repo = ChatRepository(db)
        assert await repo.delete_chat_room("room-1") is True
        assert await repo.get_chat_room("room-1") is None


class TestChatMessages:
    async def test_create_message(self, db, seed_chat_room):
        repo = ChatRepository(db)
        msg = await repo.create_message(
            chat_room_id="room-1",
            user_id="user-1",
            content="안녕하세요",
        )
        assert msg["content"] == "안녕하세요"
        assert msg["role"] == "user"
        assert msg["chat_room_id"] == "room-1"

    async def test_list_messages_ordered(self, db, seed_chat_room):
        repo = ChatRepository(db)
        await repo.create_message("room-1", "user-1", "첫번째")
        await repo.create_message("room-1", "user-2", "두번째")
        messages = await repo.list_messages("room-1")
        assert len(messages) == 2
        # ASC 정렬
        assert messages[0]["content"] == "첫번째"
        assert messages[1]["content"] == "두번째"

    async def test_get_recent_messages(self, db, seed_chat_room):
        repo = ChatRepository(db)
        for i in range(5):
            await repo.create_message("room-1", "user-1", f"메시지 {i}")
        recent = await repo.get_recent_messages("room-1", limit=3)
        assert len(recent) == 3
        # 시간순 정렬 (오래된 것부터)
        assert recent[0]["content"] == "메시지 2"
        assert recent[2]["content"] == "메시지 4"


class TestChatRoomMembers:
    async def test_add_member(self, db, seed_chat_room):
        repo = ChatRepository(db)
        member = await repo.add_member("room-1", "user-3")
        assert member is not None
        assert member["user_id"] == "user-3"

    async def test_add_duplicate_member(self, db, seed_chat_room):
        repo = ChatRepository(db)
        with pytest.raises(Exception):  # IntegrityError (UNIQUE 제약)
            await repo.add_member("room-1", "user-1")

    async def test_is_member_true(self, db, seed_chat_room):
        repo = ChatRepository(db)
        assert await repo.is_member("room-1", "user-1") is True

    async def test_is_member_false(self, db, seed_chat_room):
        repo = ChatRepository(db)
        assert await repo.is_member("room-1", "user-3") is False

    async def test_remove_member(self, db, seed_chat_room):
        repo = ChatRepository(db)
        assert await repo.remove_member("room-1", "user-2") is True
        assert await repo.is_member("room-1", "user-2") is False

    async def test_list_members(self, db, seed_chat_room):
        repo = ChatRepository(db)
        members = await repo.list_members("room-1")
        assert len(members) == 2

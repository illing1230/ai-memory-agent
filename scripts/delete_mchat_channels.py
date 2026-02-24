"""Mchat(Mattermost) 채널 삭제 CLI"""

import asyncio
import logging
import sys

from src.mchat.client import MchatClient
from src.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger(__name__)


async def list_all_channels(client: MchatClient) -> list:
    """모든 채널 목록 조회"""
    channels = []
    
    try:
        # 사용자가 속한 모든 팀 조회
        teams = await client.get_teams()
        
        for team in teams:
            team_id = team["id"]
            team_name = team["name"]
            logger.info(f"Team: {team_name}")
            
            # 팀의 채널 목록 조회
            team_channels = await client.get_channels_for_team(team_id)
            for channel in team_channels:
                channels.append({
                    "id": channel["id"],
                    "name": channel["name"],
                    "display_name": channel.get("display_name", channel["name"]),
                    "type": channel.get("type", "O"),
                    "team_id": team_id,
                    "team_name": team_name,
                })
                logger.info(f"  - [{channel.get('type', 'O')}] {channel.get('display_name', channel['name'])} ({channel['id']})")
    
    except Exception as e:
        logger.error(f"Failed to list channels: {e}")
    
    return channels


async def delete_channel(client: MchatClient, channel_id: str, channel_name: str):
    """채널 삭제"""
    try:
        logger.info(f"Deleting channel: {channel_name} ({channel_id})")
        await client.delete_channel(channel_id)
        logger.info(f"✅ Channel deleted successfully: {channel_name}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to delete channel {channel_name}: {e}")
        return False


async def main():
    """메인 함수"""
    settings = get_settings()
    
    if not settings.mchat_enabled:
        logger.error("Mchat is disabled. Set MCHAT_ENABLED=true in .env")
        sys.exit(1)
    
    if not settings.mchat_token:
        logger.error("MCHAT_TOKEN is not set in .env")
        sys.exit(1)
    
    client = MchatClient()
    
    # 연결 테스트
    if not await client.ping():
        logger.error(f"Failed to connect to Mattermost: {settings.mchat_url}")
        sys.exit(1)
    
    logger.info(f"Connected to Mattermost: {settings.mchat_url}")
    
    # Bot 정보 조회
    try:
        me = await client.get_me()
        logger.info(f"Logged in as: {me.get('username')} ({me.get('id')})")
    except Exception as e:
        logger.error(f"Failed to get bot info: {e}")
        sys.exit(1)
    
    # 모든 채널 목록 조회
    print("\n" + "=" * 50)
    print("채널 목록:")
    print("=" * 50)
    channels = await list_all_channels(client)
    
    if not channels:
        logger.info("No channels found")
        sys.exit(0)
    
    print(f"\n총 {len(channels)}개의 채널을 찾았습니다.")
    
    # 사용자 입력
    print("\n채널 삭제:")
    print("1. 특정 채널 삭제")
    print("2. 여러 채널 삭제")
    print("3. 모든 채널 삭제")
    print("0. 종료")
    
    try:
        choice = input("\n선택 (0-3): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n종료합니다.")
        sys.exit(0)
    
    if choice == "0":
        logger.info("종료합니다.")
        sys.exit(0)
    
    elif choice == "1":
        # 특정 채널 삭제
        channel_id = input("삭제할 채널 ID를 입력하세요: ").strip()
        channel = next((c for c in channels if c["id"] == channel_id), None)
        
        if not channel:
            logger.error(f"채널을 찾을 수 없습니다: {channel_id}")
            sys.exit(1)
        
        confirm = input(f"'{channel['display_name']}' 채널을 정말 삭제하시겠습니까? (yes/no): ").strip().lower()
        if confirm != "yes":
            logger.info("삭제가 취소되었습니다.")
            sys.exit(0)
        
        await delete_channel(client, channel_id, channel["display_name"])
    
    elif choice == "2":
        # 여러 채널 삭제
        ids_input = input("삭제할 채널 ID들을 쉼표로 구분하여 입력하세요: ").strip()
        channel_ids = [id.strip() for id in ids_input.split(",") if id.strip()]
        
        target_channels = []
        for channel_id in channel_ids:
            channel = next((c for c in channels if c["id"] == channel_id), None)
            if channel:
                target_channels.append(channel)
            else:
                logger.warning(f"채널을 찾을 수 없습니다: {channel_id}")
        
        if not target_channels:
            logger.error("삭제할 채널이 없습니다.")
            sys.exit(1)
        
        print(f"\n삭제할 채널: {len(target_channels)}개")
        for ch in target_channels:
            print(f"  - {ch['display_name']} ({ch['id']})")
        
        confirm = input("\n이 채널들을 모두 삭제하시겠습니까? (yes/no): ").strip().lower()
        if confirm != "yes":
            logger.info("삭제가 취소되었습니다.")
            sys.exit(0)
        
        for ch in target_channels:
            await delete_channel(client, ch["id"], ch["display_name"])
    
    elif choice == "3":
        # 모든 채널 삭제
        print(f"\n총 {len(channels)}개의 채널을 삭제합니다.")
        confirm = input("정말로 모든 채널을 삭제하시겠습니까? (yes/no): ").strip().lower()
        if confirm != "yes":
            logger.info("삭제가 취소되었습니다.")
            sys.exit(0)
        
        deleted_count = 0
        for ch in channels:
            if await delete_channel(client, ch["id"], ch["display_name"]):
                deleted_count += 1
        
        logger.info(f"\n총 {deleted_count}/{len(channels)}개의 채널이 삭제되었습니다.")
    
    else:
        logger.error("잘못된 선택입니다.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

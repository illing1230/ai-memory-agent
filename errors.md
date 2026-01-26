(base) hy.joo@nautilus:~/2026/gitprojects/ai-memory-agent$ python -m src.mchat.example
MCHAT_URL: https://mchat.mosaic.sec.samsung.net
MCHAT_TOKEN: s....
MCHAT_ENABLED: True

=== 1. Bot 정보 조회 ===
Bot ID: wazzwxjmwidfurkjsdwyrycyyr
Username: hy.joo
Nickname: 

=== 2. 팀 목록 ===
  - 모자이크 빅 팀​ (37937-38734)
  - 자동화혁신그룹​ (mchat-0000001949)
  - M Chat 챗봇 개발자 Workspace​ (2891998-2892004)
  - AIG Insight​ (mchat-0000003287)

=== 3. '모자이크 빅 팀​' 팀 채널 ===
  - [DM] 3zcrmx5ueb8w3d67qdchip7mqy__wazzwxjmwidfurkjsdwyrycyyr
  - [DM] ednfrtpgx7b15px4rf769ig7ue__wazzwxjmwidfurkjsdwyrycyyr
  - [DM] 9xxrtg7odinkzpb7ogdmj6g31r__wazzwxjmwidfurkjsdwyrycyyr
  - [DM] wazzwxjmwidfurkjsdwyrycyyr__yjx8ekwtrtyo3eejweyuhyixje
  - [DM] t6igk9z4q7b7i8rdxq8x4cxc5h__wazzwxjmwidfurkjsdwyrycyyr
  - [DM] 6mf6yjor6ins3pjtqfjgpfdr5a__wazzwxjmwidfurkjsdwyrycyyr
  - [DM] wazzwxjmwidfurkjsdwyrycyyr__z5j9scgw17dwpef6k9k3pixk1c
  - [DM] wazzwxjmwidfurkjsdwyrycyyr__yp9dbiowgbbafeu3yibb36rt8c
  - [DM] 7hrnapjtgtfczdyjepfggsi8ta__wazzwxjmwidfurkjsdwyrycyyr
  - [DM] 6m5szzkdpiro9pdpngknwp3yuh__wazzwxjmwidfurkjsdwyrycyyr
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/mchat/example.py", line 107, in <module>
    asyncio.run(main())
    ~~~~~~~~~~~^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/asyncio/runners.py", line 195, in run
    return runner.run(main)
           ~~~~~~~~~~^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/asyncio/base_events.py", line 725, in run_until_complete
    return future.result()
           ~~~~~~~~~~~~~^^
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/mchat/example.py", line 58, in main
    @client.on("posted")
     ~~~~~~~~~^^^^^^^^^^
TypeError: MchatClient.on() missing 1 required positional argument: 'handler'
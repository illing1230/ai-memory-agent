INFO:     127.0.0.1:53986 - "POST /api/v1/memories/search HTTP/1.1" 500 Internal Server Error
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/uvicorn/protocols/http/httptools_impl.py", line 409, in run_asgi
    result = await app(  # type: ignore[func-returns-value]
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        self.scope, self.receive, self.send
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/uvicorn/middleware/proxy_headers.py", line 60, in __call__
    return await self.app(scope, receive, send)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/fastapi/applications.py", line 1135, in __call__
    await super().__call__(scope, receive, send)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/applications.py", line 107, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/middleware/errors.py", line 186, in __call__
    raise exc
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/middleware/errors.py", line 164, in __call__
    await self.app(scope, receive, _send)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/middleware/cors.py", line 93, in __call__
    await self.simple_response(scope, receive, send, request_headers=headers)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/middleware/cors.py", line 144, in simple_response
    await self.app(scope, receive, send)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/fastapi/middleware/asyncexitstack.py", line 18, in __call__
    await self.app(scope, receive, send)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/routing.py", line 716, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/routing.py", line 736, in app
    await route.handle(scope, receive, send)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/routing.py", line 290, in handle
    await self.app(scope, receive, send)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/fastapi/routing.py", line 115, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/fastapi/routing.py", line 101, in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/fastapi/routing.py", line 355, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<3 lines>...
    )
    ^
  File "/home/hy.joo/miniconda3/lib/python3.13/site-packages/fastapi/routing.py", line 243, in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/memory/router.py", line 137, in search_memories
    results = await service.search_memories(
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<7 lines>...
    )
    ^
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/memory/service.py", line 176, in search_memories
    results = await search_vectors(
              ^^^^^^^^^^^^^^^^^^^^^
    ...<4 lines>...
    )
    ^
  File "/home/hy.joo/2026/gitprojects/ai-memory-agent/src/shared/vector_store.py", line 141, in search_vectors
    results = await client.search(
                    ^^^^^^^^^^^^^
AttributeError: 'AsyncQdrantClient' object has no attribute 'search'
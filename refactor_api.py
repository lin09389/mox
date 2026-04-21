import sys

with open('mox/api.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('@app.get(f"{API_V1_PREFIX}/', '@api_router.get("/')
content = content.replace('@app.get(f"{COMPAT_PREFIX}/', '# @app.get(f"{COMPAT_PREFIX}/')
content = content.replace('@app.post(f"{API_V1_PREFIX}/', '@api_router.post("/')
content = content.replace('@app.post(f"{COMPAT_PREFIX}/', '# @app.post(f"{COMPAT_PREFIX}/')

new_content = []
for line in content.split('\n'):
    if line.strip().startswith('# @app.get') or line.strip().startswith('# @app.post'):
        continue
    new_content.append(line)

content = '\n'.join(new_content)

# Add api_router = APIRouter() after app = create_app()
content = content.replace('app = create_app()', 'app = create_app()\n\nfrom fastapi import APIRouter\napi_router = APIRouter()')

# Add app.include_router(api_router, prefix=API_V1_PREFIX) and app.include_router(api_router, prefix=COMPAT_PREFIX) before if __name__ == "__main__":
if 'def run_server():' in content:
    content = content.replace('def run_server():', 'app.include_router(api_router, prefix=API_V1_PREFIX)\napp.include_router(api_router, prefix=COMPAT_PREFIX)\n\ndef run_server():')

with open('mox/api.py', 'w', encoding='utf-8') as f:
    f.write(content)

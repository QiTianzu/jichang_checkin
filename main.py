import requests, json, os
from playwright.sync_api import sync_playwright
from urllib.parse import quote

# 机场的地址
url = os.environ.get('URL')
# 配置用户名（一般是邮箱）和密码
config = os.environ.get('CONFIG')
# server酱
SCKEY = os.environ.get('SCKEY')

login_url = '{}/auth/login'.format(url)
check_url = '{}/user/checkin'.format(url)

def push_message(content):
  if SCKEY:
    encoded_content = quote(content)
    push_url = f"https://sctapi.ftqq.com/{SCKEY}.send?title=机场签到&desp={encoded_content}"
    print(f"[调试] 推送内容（原文）: {content}")
    print(f"[调试] 推送内容（URL 编码后）: {encoded_content}")
    print(f"[调试] 推送 URL: {push_url}")
    requests.get(push_url)
    print('推送成功')

def sign(order,user,pwd):
  print(f"===账号{order}进行登录...===")
  print(f"账号：{user}")
  try:
    with sync_playwright() as p:
      browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
      page = browser.new_page()

      # 打开登录页（最多等待 60 秒加载页面）
      page.goto(login_url, timeout=60000)
      # 等待页面 DOM 加载完成
      page.wait_for_load_state("domcontentloaded")
      # 给 Cloudflare 验证时间
      page.wait_for_timeout(5000)
      # 判断是否进入 Cloudflare 验证页
      if "Just a moment..." in page.content():
        print("⚠️ Cloudflare 验证页仍在加载，可能未通过挑战")
      # 截图以查看页面加载情况
      page.screenshot(path=f"cf_debug_{order}.png")

      # 填写账号密码
      # 等待邮箱输入框出现并填入
      page.wait_for_selector('#email', timeout=60000)
      page.fill('#email', user)
      # 等待密码输入框出现并填入
      page.wait_for_selector('#passwd, #password', timeout=60000)
      page.fill('#passwd, #password', pwd)

      # 点击登录按钮
      page.click('button[type="submit"]')

      # 等待跳转或网络空闲
      page.wait_for_load_state("networkidle")
      # 等待 3 秒，确保 Cloudflare 验证和跳转完成
      page.wait_for_timeout(3000)

      # 判断是否登录成功（页面跳转到 /user 或 /dashboard）
      if "/user" in page.url or "/dashboard" in page.url:
        print("登录成功，准备签到")
      else:
        print("登录失败，跳过签到")
        return
      
      # 登录后直接直接发 POST 请求        
      response = page.request.post(check_url)
      try:
        result = response.json()
        print(f"[调试] 签到响应内容: {result}")
        content = result.get("msg", str(result))
      except Exception:
        content = response.text()
      finally:
        print(f"[调试] 签到响应内容: {content}")
        browser.close()
        # 进行推送
        push_message(content)

  except Exception as ex:
    content = '签到失败'
    print(content)
    print(f"出现如下异常: {ex}")
    push_message(content)

  finally:
    print(f"===账号{order}签到结束===\n")

if __name__ == '__main__':
  if not config:
    print('CONFIG 未设置')
    exit()
  configs = config.splitlines()
  if len(configs) %2 != 0:
    print('CONFIG 格式错误')
    exit()
  user_quantity = len(configs)
  user_quantity = user_quantity // 2
  for i in range(user_quantity):
    user = configs[i*2]
    pwd = configs[i*2+1]
    sign(i,user,pwd)

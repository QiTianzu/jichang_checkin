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

      # 打开登录页（会自动等待 Cloudflare 验证通过）
      page.goto(login_url, wait_until="networkidle")

      # 填写账号密码
      # 等待邮箱输入框出现并填入
      page.wait_for_selector('#email', timeout=60000)
      page.fill('#email', user)
      # 等待密码输入框出现并填入
      page.wait_for_selector('#passwd', timeout=60000)
      page.fill('#passwd', pwd)

      # 点击登录按钮
      page.click('button[type="submit"]')

      # 等待跳转或网络空闲
      page.wait_for_load_state("networkidle")

      # 登录后直接访问签到接口
      page.goto(check_url, wait_until="networkidle")
      res_text = page.text_content("body")
      print(res_text)

      try:
        result = json.loads(res_text)
        content = result.get("msg", res_text)
      except json.JSONDecodeError:
        content = res_text
      finally:
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

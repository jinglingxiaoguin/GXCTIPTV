import re
import subprocess
import datetime

# 获取当前时间的格式化字符串
def timestamp():
    return datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

# 服务器地址，机顶盒抓包后在Wireshark中http流找到 /EPG/jsp/ValidAuthenticationHWCTC.jsp 这个请求，找到Destination IP和端口
BASE_URL = "http://xxx.xxx.xxx.xxx:xxxxx/EPG/jsp"

# 认证请求参数：在 “HTML Form URL Encoded” 上单击右键选择 复制 - As Printable Text，会获得‘UserID=02012345678&Lang=&SupportHD=1&NetUserID=02012345678%40iptv.gd&DHCPUserID=02012345678%40iptv.gd&Authenticator=[HEX DUMP]&STBType=...&STBVersion=...&conntype=2&STBID=...&templateName=iptvsnmv3&areaId=&userToken=...&userGroupId=...&productPackageId=&mac=...&UserField=&SoftwareVersion=&IsSmartStb=0&desktopId=1&stbmaker=&VIP=’
# 将上面的信息填入AUTH_DATA
AUTH_URL = f"{BASE_URL}/ValidAuthenticationHWCTC.jsp"
AUTH_DATA = (
    "UserID=02012345678&Lang=&SupportHD=1&NetUserID=02012345678%40iptv.gd&DHCPUserID=02012345678%40iptv.gd&Authenticator=[HEX DUMP]&STBType=...&STBVersion=...&conntype=2&STBID=...&templateName=iptvsnmv3&areaId=&userToken=...&userGroupId=...&productPackageId=&mac=...&UserField=&SoftwareVersion=&IsSmartStb=0&desktopId=1&stbmaker=&VIP="
)

# 频道列表请求
CHANNEL_URL = f"{BASE_URL}/getchannellistHWCTC.jsp"

print(f"{timestamp()} 开始认证...")

# 执行认证请求，并获取 Set-Cookie 头部信息
auth_result = subprocess.run(
    ["curl", "-s", AUTH_URL, "-H", "Content-Type: application/x-www-form-urlencoded", "--data", AUTH_DATA, "-i"],
    check=True, capture_output=True, text=True
)

# 提取 Cookie
cookie_lines = [line for line in auth_result.stdout.split("\n") if "Set-Cookie:" in line]
cookies = "; ".join([line.split(": ", 1)[1].split(";", 1)[0] for line in cookie_lines])

print(f"{timestamp()} 认证成功，获取频道列表...")

# 执行获取频道列表请求，并将 HTML 存储到变量
channel_result = subprocess.run(
    ["curl", "-s", CHANNEL_URL, "-H", f"Cookie: {cookies}"],
    check=True, capture_output=True, text=True
)

html_content = channel_result.stdout  # 直接存储 HTML 内容

# 解析HTML并生成播放列表
M3U_FILE = "ct_new.m3u"
TXT_FILE = "rtsp_new.txt"

m3u_content = "#EXTM3U\n"
txt_content = "电信单播,#genre#\n"

# 正则匹配频道信息
channel_pattern = re.compile(
    r'ChannelID="(\d+)",ChannelName="(.*?)",.*?ChannelURL="(igmp://[^"|]+).*?(rtsp://[^"|]+?.smil)',
    re.DOTALL
)

print(f"{timestamp()} 解析频道数据...")
for match in channel_pattern.finditer(html_content):
    channel_id, channel_name, igmp_url, rtsp_url = match.groups()
    
    # 生成 m3u 格式，igmp替换自己的UDPXY服务地址
    m3u_url = igmp_url.replace("igmp://", "http://xxx.xxx.xxx.xxx:xxxxx/rtp/")
    m3u_content += f'#EXTINF:-1 tvg-id="{channel_name}" tvg-name="{channel_name}" group-title="电信组播",{channel_name}\n{m3u_url}\n'

    
    # 生成 txt 格式
    txt_content += f"{channel_name},{rtsp_url}\n"

# 写入 m3u 文件
with open(M3U_FILE, "w", encoding="utf-8") as file:
    file.write(m3u_content)

# 写入 txt 文件
with open(TXT_FILE, "w", encoding="utf-8") as file:
    file.write(txt_content)

print(f"{timestamp()} 播放列表已生成：\n- {M3U_FILE}\n- {TXT_FILE}")

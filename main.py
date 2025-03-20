# script/QFNUNoticeMonitor/main.py

import logging
import os
import sys
import json
import aiohttp
from datetime import datetime
from bs4 import BeautifulSoup
import hashlib

# 添加项目根目录到sys.path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.config import *
from app.api import *
from app.switch import load_switch, save_switch


# 数据存储路径，实际开发时，请将QFNUNoticeMonitor替换为具体的数据存放路径
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "QFNUNoticeMonitor",
)

# 历史记录文件路径
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

# 监控URL
MONITOR_URLS = {
    "通知": "https://jwc.qfnu.edu.cn/tz_j_.htm#/",
    "公告": "https://jwc.qfnu.edu.cn/gg_j_.htm#/",
}

# 上次执行时间
last_execution_time = None

# 在文件开头的常量定义部分添加
ENABLED_GROUPS_FILE = os.path.join(DATA_DIR, "enabled_groups.json")


# 查看功能开关状态
def load_function_status(group_id):
    """加载群组功能状态"""
    # 检查总开关状态
    if not load_switch(group_id, "QFNUNoticeMonitor"):
        return False

    # 检查本地存储的状态
    if os.path.exists(ENABLED_GROUPS_FILE):
        with open(ENABLED_GROUPS_FILE, "r", encoding="utf-8") as f:
            enabled_groups = json.load(f)
            return str(group_id) in enabled_groups
    return False


# 保存功能开关状态
def save_function_status(group_id, status):
    """保存群组功能状态"""
    # 保存总开关状态
    save_switch(group_id, "QFNUNoticeMonitor", status)

    # 保存本地状态
    os.makedirs(DATA_DIR, exist_ok=True)
    enabled_groups = []

    if os.path.exists(ENABLED_GROUPS_FILE):
        with open(ENABLED_GROUPS_FILE, "r", encoding="utf-8") as f:
            enabled_groups = json.load(f)

    group_id = str(group_id)
    if status and group_id not in enabled_groups:
        enabled_groups.append(group_id)
    elif not status and group_id in enabled_groups:
        enabled_groups.remove(group_id)

    with open(ENABLED_GROUPS_FILE, "w", encoding="utf-8") as f:
        json.dump(enabled_groups, f, ensure_ascii=False, indent=2)


# 处理开关状态
async def toggle_function_status(websocket, group_id, message_id, authorized):
    if not authorized:
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]❌❌❌你没有权限对QFNUNoticeMonitor功能进行操作,请联系管理员。",
        )
        return

    if load_function_status(group_id):
        save_function_status(group_id, False)
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]🚫🚫🚫QFNUNoticeMonitor功能已关闭",
        )
    else:
        save_function_status(group_id, True)
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]✅✅✅QFNUNoticeMonitor功能已开启",
        )


# 群消息处理函数
async def handle_group_message(websocket, msg):
    """处理群消息"""
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        user_id = str(msg.get("user_id"))
        group_id = str(msg.get("group_id"))
        raw_message = str(msg.get("raw_message"))
        message_id = str(msg.get("message_id"))
        authorized = user_id in owner_id

        # 处理开关命令
        if raw_message == "qfnunm":
            await toggle_function_status(websocket, group_id, message_id, authorized)
            return
        # 检查功能是否开启
        if load_function_status(group_id):
            # 其他群消息处理逻辑
            pass
    except Exception as e:
        logging.error(f"处理QFNUNoticeMonitor群消息失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            "处理QFNUNoticeMonitor群消息失败，错误信息：" + str(e),
        )
        return


# 私聊消息处理函数
async def handle_private_message(websocket, msg):
    """处理私聊消息"""
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        user_id = str(msg.get("user_id"))
        raw_message = str(msg.get("raw_message"))
        # 私聊消息处理逻辑
        pass
    except Exception as e:
        logging.error(f"处理QFNUNoticeMonitor私聊消息失败: {e}")
        await send_private_msg(
            websocket,
            msg.get("user_id"),
            "处理QFNUNoticeMonitor私聊消息失败，错误信息：" + str(e),
        )
        return


# 群通知处理函数
async def handle_group_notice(websocket, msg):
    """处理群通知"""
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        user_id = str(msg.get("user_id"))
        group_id = str(msg.get("group_id"))
        notice_type = str(msg.get("notice_type"))
        operator_id = str(msg.get("operator_id", ""))

    except Exception as e:
        logging.error(f"处理QFNUNoticeMonitor群通知失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            "处理QFNUNoticeMonitor群通知失败，错误信息：" + str(e),
        )
        return


# 回应事件处理函数
async def handle_response(websocket, msg):
    """处理回调事件"""
    try:
        echo = msg.get("echo")
        if echo and echo.startswith("xxx"):
            # 回调处理逻辑
            pass
    except Exception as e:
        logging.error(f"处理QFNUNoticeMonitor回调事件失败: {e}")
        await send_group_msg(
            websocket,
            msg.get("group_id"),
            f"处理QFNUNoticeMonitor回调事件失败，错误信息：{str(e)}",
        )
        return


# 请求事件处理函数
async def handle_request_event(websocket, msg):
    """处理请求事件"""
    try:
        request_type = msg.get("request_type")
        pass
    except Exception as e:
        logging.error(f"处理QFNUNoticeMonitor请求事件失败: {e}")
        return


def is_five_minutes():
    """检查当前分钟是否是5的倍数"""
    current_minute = datetime.now().minute
    return current_minute % 5 == 0


def load_history():
    """加载历史记录"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"通知": [], "公告": []}


def save_history(history):
    """保存历史记录"""
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


async def fetch_page(url):
    """获取网页内容"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()


def get_all_groups():
    """获取所有已启用功能的群组ID列表"""
    if os.path.exists(ENABLED_GROUPS_FILE):
        with open(ENABLED_GROUPS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def parse_notices(html, notice_type):
    """解析网页内容，提取通知/公告信息"""
    soup = BeautifulSoup(html, "html.parser")
    notices = []

    # 根据网页结构解析内容
    for item in soup.select("ul.n_listxx1 li"):
        # 获取标题和链接
        title_elem = item.select_one("h2 a")
        if not title_elem:
            continue

        title = title_elem.get_text(strip=True)
        link = title_elem.get("href", "")

        # 获取摘要
        summary_elem = item.select_one("p")
        summary = summary_elem.get_text(strip=True) if summary_elem else ""

        # 处理链接
        if link and isinstance(link, str):
            if not link.startswith("http"):
                link = f"https://jwc.qfnu.edu.cn/{link}"

        # 生成唯一标识
        notice_id = hashlib.md5(f"{title}{link}".encode()).hexdigest()

        notices.append(
            {
                "id": notice_id,
                "title": title,
                "link": link,
                "summary": summary,
                "type": notice_type,
            }
        )

    return notices


async def check_and_send_notices(websocket):
    """检查并发送新通知"""
    global last_execution_time

    # 检查是否是5的倍数分钟
    if not is_five_minutes():
        logging.info("当前时间不是5的倍数，跳过监控教务处公告")
        return

    # 检查是否已经在本分钟内执行过
    current_time = datetime.now()
    if last_execution_time and last_execution_time.minute == current_time.minute:
        logging.info("当前分钟已执行过，跳过监控教务处公告")
        return

    last_execution_time = current_time

    try:
        history = load_history()

        for notice_type, url in MONITOR_URLS.items():
            html = await fetch_page(url)
            current_notices = parse_notices(html, notice_type)

            # 获取历史记录中的通知ID列表
            history_ids = [notice["id"] for notice in history[notice_type]]

            # 检查新通知
            new_notices = [
                notice for notice in current_notices if notice["id"] not in history_ids
            ]

            if new_notices:
                # 更新历史记录
                history[notice_type] = current_notices[:10]  # 只保留最新的10条
                save_history(history)

                # 发送新通知到所有开启功能的群
                for notice in new_notices:
                    message = (
                        f"🔔 新{notice_type}：\n"
                        f"📌 标题：{notice['title']}\n"
                        f"🔗 链接：{notice['link']}\n"
                        f"📝 摘要：{notice['summary']}"
                    )

                    # 获取所有群组并发送消息
                    for group_id in get_all_groups():
                        if load_function_status(group_id):
                            await send_group_msg(websocket, group_id, message)

    except Exception as e:
        logging.error(f"检查新通知失败: {e}")


# 统一事件处理入口
async def handle_events(websocket, msg):
    """统一事件处理入口"""
    post_type = msg.get("post_type", "response")  # 添加默认值
    try:
        # 处理回调事件
        if msg.get("status") == "ok":
            await handle_response(websocket, msg)
            return

        post_type = msg.get("post_type")

        # 处理元事件
        if post_type == "meta_event":
            # 检查新通知
            await check_and_send_notices(websocket)

        # 处理消息事件
        elif post_type == "message":
            message_type = msg.get("message_type")
            if message_type == "group":
                await handle_group_message(websocket, msg)
            elif message_type == "private":
                await handle_private_message(websocket, msg)

        # 处理通知事件
        elif post_type == "notice":
            await handle_group_notice(websocket, msg)

        # 处理请求事件
        elif post_type == "request":
            await handle_request_event(websocket, msg)

    except Exception as e:
        error_type = {
            "message": "消息",
            "notice": "通知",
            "request": "请求",
            "meta_event": "元事件",
        }.get(post_type, "未知")

        logging.error(f"处理QFNUNoticeMonitor{error_type}事件失败: {e}")

        # 发送错误提示
        if post_type == "message":
            message_type = msg.get("message_type")
            if message_type == "group":
                await send_group_msg(
                    websocket,
                    msg.get("group_id"),
                    f"处理QFNUNoticeMonitor{error_type}事件失败，错误信息：{str(e)}",
                )
            elif message_type == "private":
                await send_private_msg(
                    websocket,
                    msg.get("user_id"),
                    f"处理QFNUNoticeMonitor{error_type}事件失败，错误信息：{str(e)}",
                )

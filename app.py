import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta
import json
import os

# 设置页面配置
st.set_page_config(
    page_title="活动室预约系统",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 数据文件路径
DATA_FILE = "bookings.json"

# 管理员密码（在实际部署时应该使用环境变量或加密存储）
ADMIN_PASSWORD = "admin123"

# 时段定义
TIME_SLOTS = {
    "上午第一节": "08:00-10:00",
    "上午第二节": "10:00-12:00",
    "下午第一节": "14:00-16:00",
    "下午第二节": "16:00-18:00"
}

def load_bookings():
    """加载预约数据"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_bookings(bookings):
    """保存预约数据"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(bookings, f, ensure_ascii=False, indent=2)

def get_next_week_dates():
    """获取从今天开始的7天日期列表"""
    today = datetime.date.today()
    
    # 生成从今天开始的7天
    week_dates = []
    for i in range(7):
        week_dates.append(today + timedelta(days=i))
    
    return week_dates

def get_weekday_name(date):
    """获取中文星期名称"""
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return weekdays[date.weekday()]

def main():
    st.title("🏢 活动室预约系统")
    st.markdown("---")
    
    # 初始化 session state
    if 'selected_date_index' not in st.session_state:
        st.session_state.selected_date_index = 0
    if 'selected_slot_index' not in st.session_state:
        st.session_state.selected_slot_index = 0
    
    # 加载预约数据
    bookings = load_bookings()
    
    # 获取下一周日期
    week_dates = get_next_week_dates()
    
    # 侧边栏 - 预约表单
    with st.sidebar:
        st.header("📝 预约信息")
        
        # 日期选择 - 使用 session state 控制
        selected_date = st.selectbox(
            "选择日期",
            options=week_dates,
            index=st.session_state.selected_date_index,
            format_func=lambda x: f"{x.strftime('%Y-%m-%d')} ({get_weekday_name(x)})",
            key="date_selector"
        )
        
        # 时段选择 - 使用 session state 控制
        slot_options = list(TIME_SLOTS.keys())
        selected_slot = st.selectbox(
            "选择时段",
            options=slot_options,
            index=st.session_state.selected_slot_index,
            format_func=lambda x: f"{x} ({TIME_SLOTS[x]})",
            key="slot_selector"
        )
        
        # 检查该时段是否已被预约
        date_str = selected_date.strftime('%Y-%m-%d')
        slot_key = f"{date_str}_{selected_slot}"
        is_booked = slot_key in bookings
        
        if is_booked:
            st.error(f"❌ 该时段已被预约")
            booking_info = bookings[slot_key]
            st.info(f"预约人：{booking_info['name']}")
        else:
            st.success(f"✅ 该时段可预约")
            
            # 预约表单
            with st.form("booking_form"):
                st.subheader("填写预约信息")
                
                name = st.text_input("姓名 *", placeholder="请输入您的姓名")
                student_id = st.text_input("学号 *", placeholder="请输入您的学号")
                class_name = st.text_input("班级 *", placeholder="请输入您的班级")
                phone = st.text_input("电话 *", placeholder="请输入您的联系电话")
                reason = st.text_area("预约原因 *", placeholder="请简述活动室使用目的")
                
                submitted = st.form_submit_button("确认预约", type="primary")
                
                if submitted:
                    # 验证表单
                    if not all([name, student_id, class_name, phone, reason]):
                        st.error("请填写所有必填项！")
                    else:
                        # 保存预约
                        booking_data = {
                            "name": name,
                            "student_id": student_id,
                            "class": class_name,
                            "phone": phone,
                            "reason": reason,
                            "booking_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        bookings[slot_key] = booking_data
                        save_bookings(bookings)
                        st.success("✅ 预约成功！")
                        st.rerun()
    
    # 主内容区域 - 日程表
    st.header("📅 未来7天活动室日程表")
    st.info(f"当前时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 预约范围：{week_dates[0].strftime('%Y-%m-%d')} 至 {week_dates[-1].strftime('%Y-%m-%d')}")
    st.markdown("💡 **提示：点击日程表中的时段可快速跳转到预约**")
    
    # 自定义CSS样式
    st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        height: 80px;
        white-space: pre-line;
        font-size: 12px;
        border-radius: 8px;
        margin: 2px 0;
    }
    .stButton > button[kind="secondary"] {
        background-color: #e8f5e8;
        border-color: #28a745;
        color: #155724;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: #d4edda;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 创建可点击的日程表
    # 显示表头
    cols = st.columns([1.5] + [1] * len(week_dates))
    cols[0].markdown("**时段**")
    for i, date in enumerate(week_dates):
        cols[i + 1].markdown(f"**{date.strftime('%m-%d')}<br>{get_weekday_name(date)}**", unsafe_allow_html=True)
    
    # 显示每个时段
    for slot_idx, (time_slot, time_range) in enumerate(TIME_SLOTS.items()):
        cols = st.columns([1.5] + [1] * len(week_dates))
        
        # 时段名称列
        cols[0].markdown(f"**{time_slot}**<br>({time_range})", unsafe_allow_html=True)
        
        # 每天的时段按钮
        for date_idx, date in enumerate(week_dates):
            date_str = date.strftime('%Y-%m-%d')
            slot_key = f"{date_str}_{time_slot}"
            
            with cols[date_idx + 1]:
                if slot_key in bookings:
                    booking = bookings[slot_key]
                    # 已预约的时段 - 显示信息，但也可以点击查看
                    display_text = f"❌ 已预约\n{booking['name']}"
                    if 'student_id' in booking:
                        display_text += f"\n{booking['student_id']}"
                    display_text += f"\n{booking['class']}"
                    
                    if st.button(
                        display_text, 
                        key=f"btn_{date_idx}_{slot_idx}",
                        help="点击查看预约详情",
                        use_container_width=True
                    ):
                        st.session_state.selected_date_index = date_idx
                        st.session_state.selected_slot_index = slot_idx
                        st.rerun()
                else:
                    # 可预约的时段 - 点击后跳转到预约
                    if st.button(
                        "✅ 可预约", 
                        key=f"btn_{date_idx}_{slot_idx}",
                        help="点击快速预约",
                        use_container_width=True,
                        type="secondary"
                    ):
                        st.session_state.selected_date_index = date_idx
                        st.session_state.selected_slot_index = slot_idx
                        st.rerun()
    
    # 统计信息
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    total_slots = len(week_dates) * len(TIME_SLOTS)
    booked_slots = len(bookings)
    available_slots = total_slots - booked_slots
    
    with col1:
        st.metric("总时段数", total_slots)
    
    with col2:
        st.metric("已预约", booked_slots)
    
    with col3:
        st.metric("可预约", available_slots)
    
    # 预约记录查看
    if bookings:
        st.markdown("---")
        st.header("📋 所有预约记录")
        
        records = []
        for slot_key, booking in bookings.items():
            date_str, time_slot = slot_key.split('_', 1)
            record = {
                "日期": date_str,
                "时段": time_slot,
                "姓名": booking['name'],
                "学号": booking.get('student_id', '未填写'),
                "班级": booking['class'],
                "电话": booking['phone'],
                "预约原因": booking['reason'],
                "预约时间": booking['booking_time']
            }
            records.append(record)
        
        records_df = pd.DataFrame(records)
        st.dataframe(records_df, use_container_width=True, hide_index=True)
        
        # 管理员功能 - 删除预约
        st.markdown("---")
        st.header("🔧 管理员功能")
        
        # 密码验证
        admin_password = st.text_input("管理员密码", type="password", key="admin_pwd")
        
        if admin_password == ADMIN_PASSWORD:
            st.success("✅ 密码验证成功")
            
            # 删除指定预约
            st.subheader("🗑️ 删除指定预约")
            if bookings:
                # 创建预约选项列表
                booking_options = []
                for slot_key, booking in bookings.items():
                    date_str, time_slot = slot_key.split('_', 1)
                    option_text = f"{date_str} {time_slot} - {booking['name']}"
                    if 'student_id' in booking:
                        option_text += f" ({booking['student_id']})"
                    option_text += f" - {booking['class']}"
                    booking_options.append((option_text, slot_key))
                
                if booking_options:
                    selected_booking = st.selectbox(
                        "选择要删除的预约",
                        options=[option[0] for option in booking_options],
                        key="delete_select"
                    )
                    
                    if st.button("🗑️ 删除选中预约", type="secondary", key="delete_single"):
                        # 找到对应的slot_key
                        slot_key_to_delete = None
                        for option_text, slot_key in booking_options:
                            if option_text == selected_booking:
                                slot_key_to_delete = slot_key
                                break
                        
                        if slot_key_to_delete and slot_key_to_delete in bookings:
                            deleted_booking = bookings.pop(slot_key_to_delete)
                            save_bookings(bookings)
                            st.success(f"✅ 已删除预约：{deleted_booking['name']} 的 {selected_booking}")
                            st.rerun()
                else:
                    st.info("暂无预约记录可删除")
            else:
                st.info("暂无预约记录")
            
            # 清空所有预约
            st.subheader("🗑️ 清空所有预约")
            if bookings:
                if st.button("🗑️ 清空所有预约", type="secondary", key="clear_all"):
                    if st.session_state.get('confirm_delete_all', False):
                        bookings.clear()
                        save_bookings(bookings)
                        st.success("✅ 所有预约已清空！")
                        st.session_state.confirm_delete_all = False
                        st.rerun()
                    else:
                        st.session_state.confirm_delete_all = True
                        st.warning("⚠️ 请再次点击确认清空所有预约")
                
                # 取消确认
                if st.session_state.get('confirm_delete_all', False):
                    if st.button("❌ 取消", key="cancel_delete_all"):
                        st.session_state.confirm_delete_all = False
                        st.info("已取消操作")
            else:
                st.info("暂无预约记录可清空")
                
        elif admin_password:
            st.error("❌ 密码错误，请输入正确的管理员密码")
        else:
            st.info("请输入管理员密码以访问管理功能")

if __name__ == "__main__":
    main() 
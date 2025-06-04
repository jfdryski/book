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

# 教室配置
CLASSROOMS = ["217", "211"]

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
    
    # 生成从今天开始的7天FF
    week_dates = []
    for i in range(7):
        week_dates.append(today + timedelta(days=i))
    
    return week_dates

def get_weekday_name(date):
    """获取中文星期名称"""
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return weekdays[date.weekday()]

def get_available_classrooms(bookings, date_str, time_slot):
    """获取指定日期时段的可用教室"""
    available = []
    for classroom in CLASSROOMS:
        slot_key = f"{date_str}_{time_slot}_{classroom}"
        if slot_key not in bookings:
            available.append(classroom)
    return available

def is_slot_fully_booked(bookings, date_str, time_slot):
    """检查指定时段是否完全被预约（所有教室都被预约）"""
    return len(get_available_classrooms(bookings, date_str, time_slot)) == 0

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
        available_classrooms = get_available_classrooms(bookings, date_str, selected_slot)
        is_fully_booked = is_slot_fully_booked(bookings, date_str, selected_slot)
        
        if is_fully_booked:
            st.error(f"❌ 该时段所有教室已被预约")
            # 显示已预约的教室信息
            for classroom in CLASSROOMS:
                slot_key = f"{date_str}_{selected_slot}_{classroom}"
                if slot_key in bookings:
                    booking_info = bookings[slot_key]
                    st.info(f"教室{classroom}：{booking_info['name']} ({booking_info.get('student_id', '未知')})")
        else:
            st.success(f"✅ 该时段有 {len(available_classrooms)} 个教室可预约")
            
            # 教室选择
            selected_classroom = st.selectbox(
                "选择教室",
                options=available_classrooms,
                format_func=lambda x: f"教十A {x}"
            )
            
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
                        # 再次检查教室是否可用（防止并发预约）
                        slot_key = f"{date_str}_{selected_slot}_{selected_classroom}"
                        if slot_key in bookings:
                            st.error("抱歉，该教室刚刚被其他人预约了，请选择其他教室。")
                        else:
                            # 保存预约
                            booking_data = {
                                "name": name,
                                "student_id": student_id,
                                "class": class_name,
                                "phone": phone,
                                "reason": reason,
                                "classroom": selected_classroom,
                                "booking_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                            bookings[slot_key] = booking_data
                            save_bookings(bookings)
                            st.success(f"✅ 预约成功！教室{selected_classroom}")
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
            
            with cols[date_idx + 1]:
                # 检查该时段的教室预约情况
                available_classrooms = get_available_classrooms(bookings, date_str, time_slot)
                is_fully_booked = is_slot_fully_booked(bookings, date_str, time_slot)
                
                if is_fully_booked:
                    # 所有教室都被预约
                    booked_info = []
                    for classroom in CLASSROOMS:
                        slot_key = f"{date_str}_{time_slot}_{classroom}"
                        if slot_key in bookings:
                            booking = bookings[slot_key]
                            info = f"{classroom}: {booking['name']}"
                            if 'student_id' in booking:
                                info += f"({booking['student_id']})"
                            booked_info.append(info)
                    
                    display_text = "❌ 已满\n" + "\n".join(booked_info)
                    
                    if st.button(
                        display_text, 
                        key=f"btn_{date_idx}_{slot_idx}",
                        help="点击查看预约详情",
                        use_container_width=True
                    ):
                        st.session_state.selected_date_index = date_idx
                        st.session_state.selected_slot_index = slot_idx
                        st.rerun()
                        
                elif len(available_classrooms) == len(CLASSROOMS):
                    # 所有教室都可预约
                    if st.button(
                        f"✅ 可预约\n({len(CLASSROOMS)}个教室)", 
                        key=f"btn_{date_idx}_{slot_idx}",
                        help="点击快速预约",
                        use_container_width=True,
                        type="secondary"
                    ):
                        st.session_state.selected_date_index = date_idx
                        st.session_state.selected_slot_index = slot_idx
                        st.rerun()
                        
                else:
                    # 部分教室被预约
                    booked_info = []
                    for classroom in CLASSROOMS:
                        slot_key = f"{date_str}_{time_slot}_{classroom}"
                        if slot_key in bookings:
                            booking = bookings[slot_key]
                            info = f"{classroom}: {booking['name']}"
                            if 'student_id' in booking:
                                info += f"({booking['student_id']})"
                            booked_info.append(info)
                    
                    display_text = f"⚠️ 部分可约\n剩余{len(available_classrooms)}个\n" + "\n".join(booked_info)
                    
                    if st.button(
                        display_text, 
                        key=f"btn_{date_idx}_{slot_idx}",
                        help="点击预约剩余教室",
                        use_container_width=True,
                        type="secondary"
                    ):
                        st.session_state.selected_date_index = date_idx
                        st.session_state.selected_slot_index = slot_idx
                        st.rerun()
    
    # 统计信息
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    total_slots = len(week_dates) * len(TIME_SLOTS) * len(CLASSROOMS)
    booked_slots = len(bookings)
    available_slots = total_slots - booked_slots
    
    # 计算完全可预约的时段数
    fully_available_slots = 0
    for date in week_dates:
        for time_slot in TIME_SLOTS.keys():
            date_str = date.strftime('%Y-%m-%d')
            if len(get_available_classrooms(bookings, date_str, time_slot)) == len(CLASSROOMS):
                fully_available_slots += 1
    
    with col1:
        st.metric("总教室时段数", total_slots)
    
    with col2:
        st.metric("已预约", booked_slots)
    
    with col3:
        st.metric("剩余可预约", available_slots)
        
    with col4:
        st.metric("完全空闲时段", fully_available_slots)
    
    # 预约记录查看
    if bookings:
        st.markdown("---")
        st.header("📋 所有预约记录")
        
        records = []
        for slot_key, booking in bookings.items():
            # 解析slot_key，支持新旧格式
            parts = slot_key.split('_')
            if len(parts) >= 3:  # 新格式：date_slot_classroom
                date_str = parts[0]
                time_slot = '_'.join(parts[1:-1])
                classroom = parts[-1]
            else:  # 旧格式：date_slot（兼容性）
                date_str = parts[0]
                time_slot = '_'.join(parts[1:])
                classroom = booking.get('classroom', '未知')
                
            record = {
                "日期": date_str,
                "时段": time_slot,
                "教室": classroom,
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
                    # 解析slot_key，支持新旧格式
                    parts = slot_key.split('_')
                    if len(parts) >= 3:  # 新格式：date_slot_classroom
                        date_str = parts[0]
                        time_slot = '_'.join(parts[1:-1])
                        classroom = parts[-1]
                    else:  # 旧格式：date_slot（兼容性）
                        date_str = parts[0]
                        time_slot = '_'.join(parts[1:])
                        classroom = booking.get('classroom', '未知')
                        
                    option_text = f"{date_str} {time_slot} 教室{classroom} - {booking['name']}"
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
import streamlit as st
from ui_modules.input_ui.input_panel import render_input_panel
from ui_modules.output_ui.output_panel import render_output_panel

# 页面配置
st.set_page_config(page_title="农村光伏经济评估系统", layout="wide")

# 页面标题
st.title("🏡 农村光伏项目经济性评估工具")

# ⬅️ 渲染左侧参数输入（侧边栏），不添加多余标题
with st.sidebar:
    user_inputs = render_input_panel()

# ➡️ 渲染右侧分析结果（主页面）
render_output_panel()

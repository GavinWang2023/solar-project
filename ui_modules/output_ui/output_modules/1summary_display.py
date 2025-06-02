# output_modules/project_overview.py

import streamlit as st
import yaml
import os

MODULE_META = {
    "title": "项目基本情况",
    "category": "总览信息",
    "order": 1
}

# 默认输入路径（可根据需要修改）
USER_INPUT_PATH = "user_inputs.yaml"

def load_user_inputs(path):
    if not os.path.exists(path):
        st.error(f"未找到参数文件：{path}")
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        st.error(f"读取参数文件失败：{e}")
        return {}

def render():
    st.markdown("")

    user_inputs = load_user_inputs(USER_INPUT_PATH)
    if not user_inputs:
        st.warning("⚠️ 未能加载项目参数。")
        return

    # 制度配置展示
    config = user_inputs.get("1制度配置", {})
    st.markdown("### 🧩 制度配置")
    if config:
        st.table([{k: str(v) for k, v in config.items()}])  # 强制转为字符串
    else:
        st.info("暂无制度配置信息。")
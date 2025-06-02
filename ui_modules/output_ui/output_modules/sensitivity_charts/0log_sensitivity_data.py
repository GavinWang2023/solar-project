import streamlit as st
import yaml
import os
from datetime import datetime

INPUT_PATH = "user_inputs.yaml"
OUTPUT_PATH = "user_outputs.yaml"
LOG_PATH = "sensitivity_log.yaml"

def read_yaml_file(path):
    if not os.path.exists(path):
        st.error(f"找不到文件：{path}")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def append_to_log(log_path, new_entry):
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            log_data = yaml.safe_load(f) or []
    else:
        log_data = []
    log_data.append(new_entry)
    with open(log_path, "w", encoding="utf-8") as f:
        yaml.dump(log_data, f, allow_unicode=True)

def extract_relevant_data(inputs, outputs):
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "input_parameters": {
            "光伏发电参数": inputs.get("2光伏发电参数", {}),
            "项目建设参数配置": inputs.get("3项目建设参数配置", {}),
            "经济分析方法参数配置": inputs.get("4经济分析方法参数配置", {})
        },
        "output_results": outputs.get("现金流分析", {}).get("净现值与内部收益率", {})
    }

def render_chart():
    # st.markdown("#### 📌 敏感性分析日志记录")
    # st.info("每次加载此模块时，将自动记录指定输入与输出参数到 `sensitivity_log.yaml` 文件中。")

    inputs = read_yaml_file(INPUT_PATH)
    outputs = read_yaml_file(OUTPUT_PATH)

    new_log_entry = extract_relevant_data(inputs, outputs)
    append_to_log(LOG_PATH, new_log_entry)
    #
    # st.success("✅ 参数日志已追加")
    # with st.expander("📄 本次记录内容"):
    #     st.code(yaml.dump(new_log_entry, allow_unicode=True), language="yaml")

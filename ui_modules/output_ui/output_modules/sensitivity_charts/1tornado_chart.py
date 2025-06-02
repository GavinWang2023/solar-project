import streamlit as st
import yaml
import os
import pandas as pd
import numpy as np
import plotly.express as px

LOG_PATH = "sensitivity_log.yaml"

def load_sensitivity_log():
    if not os.path.exists(LOG_PATH):
        st.warning("⚠️ 未找到 `sensitivity_log.yaml`，请先运行记录模块。")
        return []
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or []

def flatten_log_entry(entry):
    flat = {}
    inputs = entry.get("input_parameters", {})
    for section, params in inputs.items():
        for k, v in params.items():
            flat[f"[输入]{section}/{k}"] = v

    outputs = entry.get("output_results", {})
    for k, v in outputs.items():
        flat[f"[输出]{k}"] = v

    return flat

def normalize_and_filter(df):
    numeric_df = df.select_dtypes(include=[np.number])
    norm_df = (numeric_df - numeric_df.min()) / (numeric_df.max() - numeric_df.min() + 1e-8)
    return norm_df, numeric_df.columns.tolist()

def render_chart():
    st.markdown("### 🌪️ 敏感性分析 Tornado 图表")

    logs = load_sensitivity_log()
    if len(logs) < 5:
        st.info("📉 日志数据不足，至少需要 5 条记录才能分析。")
        return

    df_all = pd.DataFrame([flatten_log_entry(entry) for entry in logs])

    input_cols = [col for col in df_all.columns if col.startswith("[输入]")]
    output_cols = [col for col in df_all.columns if col.startswith("[输出]")]

    norm_df, numeric_cols = normalize_and_filter(df_all[input_cols + output_cols])
    input_numeric = [col for col in input_cols if col in numeric_cols]
    output_numeric = [col for col in output_cols if col in numeric_cols]

    if not input_numeric or not output_numeric:
        st.error("❌ 无法找到足够的数值型输入/输出字段，请检查日志。")
        return

    selected_output = st.selectbox("🎯 选择输出指标进行敏感性分析", output_numeric)

    corr_series = norm_df[input_numeric].corrwith(norm_df[selected_output]).sort_values(key=abs, ascending=False)
    df_corr = corr_series.reset_index()
    df_corr.columns = ["参数", "相关系数"]
    df_corr["影响方向"] = df_corr["相关系数"].apply(lambda x: "正向" if x > 0 else "负向")

    st.markdown("---")

    # 显示图表
    st.subheader("📊 Tornado 图")
    fig = px.bar(
        df_corr,
        x="相关系数",
        y="参数",
        orientation="h",
        color="影响方向",
        color_discrete_map={"正向": "#4CAF50", "负向": "#F44336"},
        title=f"{selected_output} 的敏感性分析",
        height=40 + 30 * len(df_corr)
    )
    fig.update_layout(yaxis=dict(tickfont=dict(size=11)), xaxis_title="归一化后 Pearson 相关系数")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # 显示表格
    st.subheader("📋 敏感性分析数据表")
    st.dataframe(df_corr.set_index("参数"), use_container_width=True)

    st.markdown("---")
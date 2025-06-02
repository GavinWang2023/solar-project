import streamlit as st
import yaml
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import numpy_financial as npf


MODULE_META = {
    "order": 3,
    "title": "净现金流分析"
}

OUTPUT_YAML_PATH = os.path.abspath("user_outputs.yaml")

def load_output_data():
    try:
        with open(OUTPUT_YAML_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        st.error(f"❌ 读取输出文件出错：{e}")
        return None

def calculate_net_cashflow(income_list, expense_list, initial_investment):
    try:
        df_income = pd.DataFrame(income_list)
        df_expense = pd.DataFrame(expense_list)

        result = []

        for i in range(len(df_income)):
            year = df_income.loc[i, "使用年份"]
            income = df_income.loc[i, "总收入（元）"]
            expense = df_expense.loc[i, "总支出（元）"]

            if year == 1:
                net = income - expense - initial_investment
            else:
                net = income - expense

            result.append({
                "使用年份": year,
                "年总收入（元）": round(income, 2),
                "年总支出（元）": round(expense, 2),
                "当年净现金流（元）": round(net, 2)
            })

        return pd.DataFrame(result)
    except Exception as e:
        st.error(f"❌ 计算现金流出错：{e}")
        return None


def append_cashflow_to_yaml(cashflow_df):
    try:
        with open(OUTPUT_YAML_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        data.setdefault("现金流分析", {})
        data["现金流分析"]["年度净现金流明细"] = cashflow_df.to_dict(orient="records")

        with open(OUTPUT_YAML_PATH, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True)

        # st.success("✅ 现金流结果已保存到 user_outputs.yaml")
    except Exception as e:
        st.error(f"❌ 保存现金流数据失败：{e}")


def append_dynamic_cashflow_to_yaml(cashflow_df):
    try:
        with open(OUTPUT_YAML_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        data.setdefault("现金流分析", {})
        data["现金流分析"]["动态净现金流明细"] = cashflow_df[[
            "使用年份",
            "当年净现金流（元）",
            "现值现金流（元）",
            "累计现值现金流（元）"
        ]].to_dict(orient="records")

        with open(OUTPUT_YAML_PATH, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True)
    except Exception as e:
        st.error(f"❌ 保存动态现金流数据失败：{e}")


def calculate_cumulative_cashflow(cashflow_df):
    try:
        cashflow_df["累计现金流（元）"] = cashflow_df["当年净现金流（元）"].cumsum()
        return cashflow_df
    except Exception as e:
        st.error(f"❌ 累计现金流计算失败：{e}")
        return None


def calculate_dynamic_cashflow(cashflow_df, discount_rate, inflation_rate):
    try:
        real_rate = (1 + discount_rate) / (1 + inflation_rate) - 1
        cashflow_df["动态净现金流（元）"] = cashflow_df.apply(
            lambda row: round(row["当年净现金流（元）"] / ((1 + real_rate) ** row["使用年份"]), 2),
            axis=1
        )
        return cashflow_df, real_rate
    except Exception as e:
        st.error(f"❌ 动态现金流计算失败：{e}")
        return cashflow_df, None


def calculate_and_save_npv_irr_from_yaml(discount_rate):
    try:
        with open(OUTPUT_YAML_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        # 获取静态现金流：使用“年度净现金流明细”中的“当年净现金流（元）”
        static_cashflow = [
            item["当年净现金流（元）"]
            for item in data["现金流分析"].get("年度净现金流明细", [])
        ]

        # 获取动态现金流：使用“动态净现金流明细”中的“现值现金流（元）”
        dynamic_cashflow = [
            item["现值现金流（元）"]
            for item in data["现金流分析"].get("动态净现金流明细", [])
        ]

        # === 正确计算 ===
        static_npv = npf.npv(discount_rate, static_cashflow)
        static_irr = npf.irr(static_cashflow)

        dynamic_npv = sum(dynamic_cashflow)  # ⚠️ 动态现金流已经折现，不能再用 npv()
        dynamic_irr = npf.irr(static_cashflow)  # IRR 仍基于原始现金流，动态无意义

        # 写入到 YAML
        data["现金流分析"]["净现值与内部收益率"] = {
            "静态净现值（NPV）": float(round(static_npv, 2)),
            "静态内部收益率（IRR）": float(round(static_irr, 6)),
            "动态净现值（NPV）": float(round(dynamic_npv, 2)),
            "动态内部收益率（IRR）": float(round(dynamic_irr, 6)),  # 此处仍基于静态 IRR
        }

        with open(OUTPUT_YAML_PATH, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True)

        return static_npv, static_irr, dynamic_npv, dynamic_irr

    except Exception as e:
        st.error(f"❌ 从 YAML 计算/写入 NPV/IRR 失败：{e}")
        return None, None, None, None




def render():
    st.subheader("💰 净现金流分析")

    st.markdown("""
    <div style="font-size: 14px">
    <b>计算说明：</b><br>
    净现金流 = 年度收入 - 年度支出<br>
    第一年的净现金流需额外减去初始投入金额。<br>
    </div>
    """, unsafe_allow_html=True)

    data = load_output_data()
    if not data:
        return

    try:
        income_list = data["现金流分析"]["年度收入明细"]
        expense_list = data["现金流分析"]["年度支出明细"]
        initial_investment = data["初始投入计算"]["初始投入总计"]

        cashflow_df = calculate_net_cashflow(income_list, expense_list, initial_investment)

        if cashflow_df is not None:
            st.markdown("#### 📋 年度现金流明细")
            st.dataframe(cashflow_df, use_container_width=True)

            # 显示经济学风格的现金流量图（柱状图）
            st.markdown("#### 📊 年度净现金流量图")
            st.bar_chart(cashflow_df.set_index("使用年份")[["当年净现金流（元）"]])

            append_cashflow_to_yaml(cashflow_df)

            # 计算累计现金流
            cashflow_df = calculate_cumulative_cashflow(cashflow_df)

            # ==== 替换累计现金流图显示 ====
            st.markdown("#### 📈 累计现金流趋势图（含盈亏平衡点）")

            fig = px.line(cashflow_df, x="使用年份", y="累计现金流（元）", markers=True)
            fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="盈亏平衡",
                          annotation_position="bottom right")

            # ===== 线性插值法求投资回收期 =====
            payback_year = None
            years = cashflow_df["使用年份"]
            cumulative = cashflow_df["累计现金流（元）"]

            for i in range(1, len(cumulative)):
                if cumulative[i - 1] < 0 and cumulative[i] >= 0:
                    x1, y1 = years[i - 1], cumulative[i - 1]
                    x2, y2 = years[i], cumulative[i]
                    payback_year = round(x1 + (-y1) * (x2 - x1) / (y2 - y1), 2)
                    break

            if payback_year:
                fig.add_vline(
                    x=payback_year,
                    line_dash="dot",
                    line_color="red",
                    annotation_text=f"投资回收期 ≈ 第 {payback_year} 年",
                    annotation_position="top left"
                )
                st.plotly_chart(fig, use_container_width=True)
                st.markdown(f"📌 **预计投资回收期：第 {payback_year} 年**")
            else:
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("📌 **未达到投资回收期（累计现金流未转正）**")

            # === 动态现金流分析 ===
            st.markdown("#### 🧮 动态现金流（现值现金流）分析")

            # 从 user_inputs.yaml 中读取折现率和通货膨胀率
            input_path = os.path.abspath("user_inputs.yaml")
            try:
                with open(input_path, "r", encoding="utf-8") as f:
                    input_data = yaml.safe_load(f)
                discount_rate = input_data["4经济分析方法参数配置"]["折现率"] / 100
                inflation_rate = input_data["4经济分析方法参数配置"]["通货膨胀率"] / 100
            except Exception as e:
                st.error(f"❌ 无法读取 user_inputs.yaml 中的经济参数：{e}")
                return

            # 计算实际折现率（费雪方程简化近似）：real_rate ≈ (1 + r) / (1 + i) - 1
            try:
                real_rate = (1 + discount_rate) / (1 + inflation_rate) - 1
            except ZeroDivisionError:
                real_rate = discount_rate  # 若无通胀率则退化为名义折现率

            # 增加现值现金流列（动态现金流）
            try:
                cashflow_df["现值现金流（元）"] = cashflow_df.apply(
                    lambda row: round(row["当年净现金流（元）"] / ((1 + real_rate) ** (row["使用年份"] - 1)), 2),
                    axis=1
                )
                cashflow_df["累计现值现金流（元）"] = cashflow_df["现值现金流（元）"].cumsum()

                append_dynamic_cashflow_to_yaml(cashflow_df)

            except Exception as e:
                st.error(f"❌ 动态现金流计算失败：{e}")
                return

            # 显示动态现金流图
            st.markdown("#### 📉 动态现金流图（考虑折现与通胀）")
            fig_dynamic = px.line(
                cashflow_df,
                x="使用年份",
                y="累计现值现金流（元）",
                markers=True,
                title="累计现值现金流趋势"
            )
            fig_dynamic.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="盈亏平衡")

            # 线性插值求动态投资回收期
            dyn_cum = cashflow_df["累计现值现金流（元）"]
            dyn_payback = None
            for i in range(1, len(dyn_cum)):
                if dyn_cum[i - 1] < 0 and dyn_cum[i] >= 0:
                    x1, y1 = years[i - 1], dyn_cum[i - 1]
                    x2, y2 = years[i], dyn_cum[i]
                    dyn_payback = round(x1 + (-y1) * (x2 - x1) / (y2 - y1), 2)
                    break

            if dyn_payback:
                fig_dynamic.add_vline(
                    x=dyn_payback,
                    line_dash="dot",
                    line_color="red",
                    annotation_text=f"动态回收期 ≈ 第 {dyn_payback} 年",
                    annotation_position="top left"
                )
                st.plotly_chart(fig_dynamic, use_container_width=True)
                st.markdown(f"📌 **预计动态投资回收期：第 {dyn_payback} 年**")
            else:
                st.plotly_chart(fig_dynamic, use_container_width=True)
                st.markdown("📌 **未达到动态投资回收期（现值现金流未转正）**")

            # === NPV / IRR 最终分析输出 ===
            st.markdown("#### 📐 净现值（NPV）与内部收益率（IRR）")

            st.markdown("""
            <div style="font-size: 14px">
            <b>说明：</b><br>
            净现值（NPV）和内部收益率（IRR）有静态分析与动态分析两种方式：<br><br>
            📊 <b>静态分析</b>：基于名义现金流和名义折现率计算，<b>不考虑通货膨胀</b>，适合预算报表、合同金额等场景。<br>
            📉 <b>动态分析</b>：基于已折现的现金流（现值现金流）和实际折现率（考虑通胀后得出），<b>更真实地反映货币的时间价值</b>，适合投资决策与长期评估。<br><br>
            <b>
            </div>
            """, unsafe_allow_html=True)

            static_npv, static_irr, dynamic_npv, dynamic_irr = calculate_and_save_npv_irr_from_yaml(discount_rate)

            if None not in (static_npv, static_irr, dynamic_npv, dynamic_irr):
                st.markdown("""
                <style>
                    .npv-table {
                        font-size: 15px;
                        border-collapse: collapse;
                        width: 100%;
                    }
                    .npv-table th, .npv-table td {
                        border: 1px solid #ddd;
                        padding: 8px;
                        text-align: center;
                    }
                    .npv-table th {
                        background-color: #f2f2f2;
                    }
                </style>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <table class="npv-table">
                    <thead>
                        <tr>
                            <th>分析类型</th>
                            <th>净现值（NPV）</th>
                            <th>内部收益率（IRR）</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>📊 静态分析</td>
                            <td>￥{static_npv:,.2f}</td>
                            <td>{static_irr * 100:.2f}%</td>
                        </tr>
                        <tr>
                            <td>📉 动态分析（考虑通胀与实际折现）</td>
                            <td>￥{dynamic_npv:,.2f}</td>
                            <td>{dynamic_irr * 100:.2f}%</td>
                        </tr>
                    </tbody>
                </table>
                """, unsafe_allow_html=True)


    except KeyError as e:
        st.error(f"❌ 缺失字段：{e}")


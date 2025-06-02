import streamlit as st
import yaml
import os
import pandas as pd

# 模块元信息
MODULE_META = {
    "order": 2,
    "title": "每年现金流计算"
}

YAML_PATH = os.path.abspath("user_inputs.yaml")
OUTPUT_YAML_PATH = os.path.abspath("user_outputs.yaml")


def load_output_data():
    try:
        with open(OUTPUT_YAML_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        st.error(f"❌ 无法读取 user_outputs.yaml：{e}")
        return {}


def load_yaml_data(yaml_path):
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        st.error(f"❌ 无法加载 YAML 文件：{e}")
        return None


def calculate_annual_cash_flows(data):
    try:
        # 基本参数
        lifetime = data["4经济分析方法参数配置"]["产品使用寿命"]
        radiation = data["2光伏发电参数"]["年辐射量"]
        area = data["2光伏发电参数"]["太阳能板面积（㎡）"]
        efficiency = data["2光伏发电参数"]["太阳能板转换效率（η）"]
        pr = data["2光伏发电参数"]["系统效率因子（PR）"]
        decay = data["2光伏发电参数"]["光伏发电衰减率（%/年）"]

        sell_ratio = data["4经济分析方法参数配置"]["发电售卖比例"] / 100
        subsidy = data["4经济分析方法参数配置"]["年补贴金额"]
        sell_price = data["4经济分析方法参数配置"]["售电电价"]
        use_price = data["4经济分析方法参数配置"]["用电电价"]

        result = []

        for year in range(1, lifetime + 1):
            decay_factor = (1 - decay) ** year
            annual_generation = radiation * area * efficiency * pr * decay_factor

            # 收益计算
            sell_income = annual_generation * sell_ratio * (sell_price + subsidy)
            self_use_income = annual_generation * (1 - sell_ratio) * (use_price - sell_price)
            total_income = sell_income + self_use_income

            result.append({
                "使用年份": year,
                "年发电量（kWh）": round(annual_generation, 2),
                "售电收益（元）": round(sell_income, 2),
                "自用收益（元）": round(self_use_income, 2),
                "总收入（元）": round(total_income, 2)
            })

        return pd.DataFrame(result)

    except KeyError as e:
        st.error(f"❌ YAML 数据中缺失字段：{e}")
        return None
    except Exception as e:
        st.error(f"❌ 计算过程中出错：{e}")
        return None


def calculate_annual_expenses(data, income_df):
    try:
        # 强制从 user_outputs.yaml 读取初始投入总计
        output_data = load_output_data()
        initial_investment = output_data.get("初始投入计算", {}).get("初始投入总计", None)

        if initial_investment is None:
            st.error("❌ 无法获取初始投入数据，请先运行“初始投入计算”模块。")
            return None

        area = data["2光伏发电参数"]["太阳能板面积（㎡）"]
        om_cost_per_m2 = data["4经济分析方法参数配置"]["年运维成本"]
        tax_rate = data["4经济分析方法参数配置"]["综合税率"] / 100
        depreciation_rate = data["4经济分析方法参数配置"]["年折旧率"] / 100

        expense_result = []

        for _, row in income_df.iterrows():
            year = row["使用年份"]
            income = row["总收入（元）"]

            om_cost = om_cost_per_m2 * area
            tax_cost = income * tax_rate
            depreciation = depreciation_rate * initial_investment

            total_expense = om_cost + tax_cost + depreciation

            expense_result.append({
                "使用年份": year,
                "运维费用（元）": round(om_cost, 2),
                "税费（元）": round(tax_cost, 2),
                "折旧费用（元）": round(depreciation, 2),
                "总支出（元）": round(total_expense, 2)
            })

        return pd.DataFrame(expense_result)

    except Exception as e:
        st.error(f"❌ 计算支出时出错：{e}")
        return None


def append_cashflow_to_output(income_df, expense_df):
    try:
        # 将 DataFrame 转换为列表形式，适合 YAML 存储
        income_records = income_df.to_dict(orient="records")
        expense_records = expense_df.to_dict(orient="records")

        # 加载原有内容
        if os.path.exists(OUTPUT_YAML_PATH):
            with open(OUTPUT_YAML_PATH, "r", encoding="utf-8") as f:
                existing_data = yaml.safe_load(f) or {}
        else:
            existing_data = {}

        # 写入/更新字段
        existing_data["现金流分析"] = {
            "年度收入明细": income_records,
            "年度支出明细": expense_records
        }

        # 写回文件
        with open(OUTPUT_YAML_PATH, "w", encoding="utf-8") as f:
            yaml.dump(existing_data, f, allow_unicode=True)

        # st.success("✅ 年度收入和支出数据已保存到 user_outputs.yaml")

    except Exception as e:
        st.error(f"❌ 保存到 YAML 文件出错：{e}")


def render():
    st.subheader("📆 每年现金收入计算")

    # 显示计算说明
    st.markdown("""
    <div style="font-size: 14px">
    <h4>🧮 计算方法说明：</h4>

    <b>1. 年发电量计算：</b>  
    年发电量 = 年辐射量 × 太阳能板面积 × 转换效率 × 系统效率因子 × (1 - 衰减率)<sup>使用年数</sup>  

    <b>2. 现金收入计算：</b>  
    发电收益 = (年发电量 × 售电比例) × (上网电价 + 补贴)  
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;+ (年发电量 × 自用比例) × (用电电价 − 上网电价)

    <hr style="margin-top:10px; margin-bottom:10px">
    </div>
    """, unsafe_allow_html=True)

    data = load_yaml_data(YAML_PATH)
    if not data:
        return

    df = calculate_annual_cash_flows(data)
    if df is None:
        return

    # 显示表格
    st.markdown("#### 📋 每年发电量与现金收入")
    st.dataframe(df, use_container_width=True)

    # 显示图表
    st.markdown("#### 📊 收入趋势图")
    st.line_chart(df.set_index("使用年份")[["总收入（元）", "售电收益（元）", "自用收益（元）"]])

    # ==== 现金支出计算 ====
    st.markdown("#### 💸 每年现金支出计算")

    st.markdown("""
    <div style="font-size: 14px">
    <b>计算公式：</b><br>
    当年支出 = （年运维成本 × 面积） + （综合税率 × 当年发电收益） + （年折旧率 × 初始投入）<br>
    </div>
    """, unsafe_allow_html=True)

    expense_df = calculate_annual_expenses(data, df)
    if expense_df is not None:
        st.dataframe(expense_df, use_container_width=True)

        st.markdown("#### 📉 支出趋势图")
        st.line_chart(expense_df.set_index("使用年份")[["总支出（元）", "运维费用（元）", "税费（元）", "折旧费用（元）"]])

        # === 保存收入和支出数据到 YAML ===
        append_cashflow_to_output(df, expense_df)
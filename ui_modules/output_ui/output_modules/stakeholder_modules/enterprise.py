import streamlit as st
import yaml
import os
import pandas as pd
import plotly.graph_objects as go

STAKEHOLDER_META = {
    "label": "企业",
    "order": 2
}


def calculate_detailed_farmer_investment(initial_investment_data: dict, ratio_map: dict) -> float:
    """
    根据每项费用的出资比例计算农户总出资。
    """
    total = 0.0
    for item, cost in initial_investment_data.items():
        if isinstance(cost, (int, float)) and item in ratio_map:
            ratio = max(0.0, min(1.0, ratio_map[item]))
            total += cost * ratio
    return total


def calculate_loan_schedule(loan_amount: float, annual_rate: float, years: int, method: str) -> list:
    """
    返回每年的还款金额列表
    """
    schedule = []

    if loan_amount <= 0 or years <= 0:
        return [0.0] * years

    r = annual_rate  # 已经是年利率
    n = years

    if method == "等额本息":
        annuity = loan_amount * r * (1 + r) ** n / ((1 + r) ** n - 1)
        schedule = [annuity] * n
    elif method == "等额本金":
        principal = loan_amount / n
        for i in range(n):
            interest = (loan_amount - i * principal) * r
            schedule.append(principal + interest)
    else:
        schedule = [0.0] * n

    return schedule


def update_farmer_cashflow(data_to_update: dict, filename: str = "enterprise_cashflow.yaml"):
    path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", filename)

    # 读取原有内容（如果文件存在）
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            existing_data = yaml.safe_load(f) or {}
    else:
        existing_data = {}

    # 更新内容
    existing_data.update(data_to_update)

    # 保存
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(existing_data, f, allow_unicode=True)


def calculate_farmer_income_expense_table(
    income_details: list,
    expense_details: list,
    income_ratio_map: dict,
    expense_ratio_map: dict
) -> list:
    """
    计算农户每年各项收入与支出分担结果，返回用于展示的表格数据。
    """
    table = []
    n_years = min(len(income_details), len(expense_details))

    income_keys = [k for k in income_details[0].keys()
                   if k not in ("使用年份", "总收入（元）") and "（元）" in k]

    expense_keys = [k for k in expense_details[0].keys()
                    if k not in ("使用年份", "总支出（元）")]

    for year in range(n_years):
        income_row = income_details[year]
        expense_row = expense_details[year]

        row = {}
        row["使用年份"] = int(income_row.get("使用年份", year + 1))

        # 先处理所有收入项
        for key in income_keys:
            value = income_row.get(key, 0.0)
            ratio = income_ratio_map.get(key, 0.0)
            row[key] = value * ratio

        # 再处理所有支出项
        for key in expense_keys:
            value = expense_row.get(key, 0.0)
            ratio = expense_ratio_map.get(key, 0.0)
            row[key] = value * ratio

        # ✅ 最后强制写入新总收入和总支出
        row["企业总收入（元）"] = sum(
            income_row.get(key, 0.0) * income_ratio_map.get(key, 0.0)
            for key in income_keys
        )

        row["企业总支出（元）"] = sum(
            expense_row.get(key, 0.0) * expense_ratio_map.get(key, 0.0)
            for key in expense_keys
        )

        table.append(row)

    return table


def calculate_roof_rent(unit_price: float, area: float, years: int) -> dict:
    """
    计算屋顶租金：返回每年租金金额和总租金
    """
    annual_rent = unit_price * area
    rent_schedule = [annual_rent] * years
    total_rent = sum(rent_schedule)
    return {
        "annual_rent": annual_rent,
        "rent_schedule": rent_schedule,
        "total_rent": total_rent
    }

def generate_farmer_cashflow_plot(data: dict) -> pd.DataFrame:
    initial_invest = data.get("企业总初期出资金额", 0.0)
    loan_amount = data.get("贷款额度（元）", 0.0)

    # 组织三类年度数据
    cashflow = {item["使用年份"]: item for item in data.get("年度现金流", [])}
    rent = {item["使用年份"]: item["屋顶租金（元）"] for item in data.get("屋顶租金明细", [])}
    loan = {item["使用年份"]: item["贷款偿还金额（元）"] for item in data.get("贷款偿还明细", [])}

    all_years = sorted(set([0] + list(cashflow.keys()) + list(rent.keys()) + list(loan.keys())))
    records = []

    for year in all_years:
        if year == 0:
            income = loan_amount
            expense = initial_invest
            rent_cost = 0.0
            loan_cost = 0.0
            net = income - expense  # 修复点
        else:
            income = cashflow.get(year, {}).get("企业总收入（元）", 0.0)
            rent_cost = rent.get(year, 0.0)
            loan_cost = loan.get(year, 0.0)
            base_expense = cashflow.get(year, {}).get("企业总支出（元）", 0.0)
            expense = base_expense + rent_cost
            net = income - expense - loan_cost

        records.append({
            "使用年份": year,
            "企业总收入": income,
            "企业总支出": base_expense if year != 0 else expense,
            "屋顶租金": rent_cost,
            "贷款偿还": loan_cost,
            "净现金流": net
        })

    df = pd.DataFrame(records)
    df["累计净现金流"] = df["净现金流"].cumsum()

    # ✅ 计算经济性指标
    recovery_year = None
    interpolated_year = None
    for i in range(1, len(df)):
        if df.loc[i - 1, "累计净现金流"] < 0 and df.loc[i, "累计净现金流"] >= 0:
            # 插值计算投资回收期
            y0 = df.loc[i - 1, "累计净现金流"]
            y1 = df.loc[i, "累计净现金流"]
            x0 = df.loc[i - 1, "使用年份"]
            x1 = df.loc[i, "使用年份"]
            interpolated_year = x0 + (-y0) / (y1 - y0) * (x1 - x0)
            recovery_year = x1
            break

    total_profit = df["累计净现金流"].iloc[-1]

    # ✅ 可视化图表
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["使用年份"], y=df["净现金流"], name="净现金流"))
    fig.add_trace(go.Scatter(x=df["使用年份"], y=df["累计净现金流"], mode='lines+markers', name="累计现金流"))
    fig.update_layout(
        title="📊 企业项目生命周期现金流图",
        xaxis_title="使用年份",
        yaxis_title="金额（元）",
        barmode='group',
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

    # ✅ 展示指标
    st.markdown("### 📌 项目关键经济性指标")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📈 投资回收期", f"{interpolated_year:.2f} 年" if interpolated_year else "未回收")
    with col2:
        st.metric("✅ 盈亏平衡年", f"{recovery_year} 年" if recovery_year else "未达成")
    with col3:
        st.metric("💰 总净收益", f"{total_profit:,.2f} 元")

    # ✅ 保存指标到 YAML 文件
    indicators = {
        "经济性指标": {
            "累计盈亏平衡年": int(recovery_year) if recovery_year is not None else None,
            "投资回收期": round(float(interpolated_year), 2) if interpolated_year is not None else None,
            "总净收益": round(float(total_profit), 2),
        }
    }

    # 保存回原 YAML 中
    fc_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "enterprise_cashflow.yaml")
    with open(fc_path, "r", encoding="utf-8") as f:
        all_data = yaml.safe_load(f) or {}

    all_data.update(indicators)

    with open(fc_path, "w", encoding="utf-8") as f:
        yaml.dump(all_data, f, allow_unicode=True)

    return df


def load_yaml_data(file_path: str) -> dict:
    if not os.path.exists(file_path):
        st.error(f"❌ 未找到文件：{file_path}")
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_farmer_cashflow(data: dict, filename: str = "enterprise_cashflow.yaml"):
    save_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", filename)
    with open(save_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)


def render():

    # st.markdown("## 👨‍🌾 农户视角经济分析 - 初期投资")
    st.markdown("---")
    # 加载项目输出数据
    outputs_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "user_outputs.yaml")
    data = load_yaml_data(outputs_path)
    initial_investment_data = data.get("初始投入计算", {})

    if not initial_investment_data:
        st.warning("⚠️ 未找到初始投入相关数据，请检查 user_outputs.yaml。")
        return

    st.markdown("### ✅ 企业各项初始投资出资比例设置")

    # 排除不需要设置比例的汇总字段
    excluded_items = {"初始投入总计", "设备费合计"}
    ratio_map = {}

    # 只保留需要设置比例的条目
    items = [
        (item, cost) for item, cost in initial_investment_data.items()
        if isinstance(cost, (int, float)) and item not in excluded_items
    ]

    with st.container():
        for i in range(0, len(items), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(items):
                    item, cost = items[i + j]
                    with cols[j]:
                        st.markdown(f"**{item}**")
                        st.markdown(f"{cost:,.2f} 元")
                        ratio = st.slider(
                            label="企业出资比例",
                            min_value=0,
                            max_value=100,
                            value=100,
                            step=5,
                            key=f"{item}_ratio_slider"
                        ) / 100.0
                        ratio_map[item] = ratio

    investment_amount = calculate_detailed_farmer_investment(initial_investment_data, ratio_map)

    # st.markdown("---")
    st.success(f"💰 企业总初期出资金额为：**{investment_amount:,.2f} 元**")

    # ✅ 保存到 enterprise_cashflow.yaml
    farmer_cashflow_data = {
        "企业总初期出资金额": float(round(investment_amount, 2))
    }
    save_farmer_cashflow(farmer_cashflow_data)
    # st.info("✅ 农户初期出资金额已保存到 enterprise_cashflow.yaml")



    # ======== 收入/支出比例设置和农户收益支出表格 ========
    st.markdown("---")

    # 加载年度收入支出明细
    cashflow_section = data.get("现金流分析", {})
    income_details = cashflow_section.get("年度收入明细", [])
    expense_details = cashflow_section.get("年度支出明细", [])

    if not income_details or not expense_details:
        st.warning("⚠️ 未找到收入或支出明细数据，请检查 user_outputs.yaml。")
        return

    st.markdown("### 📈 项目运行期产生的企业收益分成和支出分担比例设置")

    income_keys = [k for k in income_details[0].keys()
                   if k not in ("使用年份", "总收入（元）") and "（元）" in k]

    expense_keys = [k for k in expense_details[0].keys()
                    if k not in ("使用年份", "总支出（元）")]

    income_ratio_map = {}
    expense_ratio_map = {}

    with st.expander("🔧 设置企业收入分成比例"):
        for key in income_keys:
            income_ratio_map[key] = st.slider(
                f"企业参与收入比例 - {key}",
                min_value=0,
                max_value=100,
                value=100,
                step=5,
                key=f"income_ratio_{key}"
            ) / 100.0

    with st.expander("🔧 设置企业支出分担比例"):
        for key in expense_keys:
            expense_ratio_map[key] = st.slider(
                f"企业分担支出比例 - {key}",
                min_value=0,
                max_value=100,
                value=100,
                step=5,
                key=f"expense_ratio_{key}"
            ) / 100.0

    # ✅ 使用独立函数进行计算
    farmer_table = calculate_farmer_income_expense_table(
        income_details,
        expense_details,
        income_ratio_map,
        expense_ratio_map
    )

    # ✅ 渲染最终表格
    st.markdown("### 📋 项目运行期产生的企业收益分成和支出分担")
    st.dataframe(farmer_table, use_container_width=True)

    # ✅ 提取每年农户总收入与支出
    annual_cashflow = []
    for row in farmer_table:
        annual_cashflow.append({
            "使用年份": row.get("使用年份"),
            "企业总收入（元）": round(row.get("企业总收入（元）"), 2),
            "企业总支出（元）": round(row.get("企业总支出（元）"), 2),
        })

    # ✅ 保存到 enterprise_cashflow.yaml 中
    update_farmer_cashflow({
        "年度现金流": annual_cashflow
    })

    # st.info("✅ 每年农户总收入与支出已保存到 enterprise_cashflow.yaml")

    # ======== 屋顶租金模块 ========
    st.markdown("---")
    st.markdown("### 🏠 屋顶租金计算")

    with st.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            unit_price = st.number_input("屋顶租金单价（元/㎡·年）", min_value=0.0, value=10.0, step=1.0)
        with col2:
            area = st.number_input("屋顶租赁面积（㎡）", min_value=0.0, value=50.0, step=10.0)
        with col3:
            years = st.number_input("租赁年限", min_value=1, max_value=50, value=20, step=1)

    rent_result = calculate_roof_rent(unit_price, area, years)

    st.markdown(f"📅 每年租金：**{rent_result['annual_rent']:,.2f} 元**")
    st.markdown(f"💰 总租金（{years} 年）：**{rent_result['total_rent']:,.2f} 元**")

    with st.expander("📋 展开查看每年租金明细"):
        for i, rent in enumerate(rent_result["rent_schedule"], start=1):
            st.write(f"第 {i} 年：{rent:,.2f} 元")


    # ✅ 将屋顶租金明细写入 enterprise_cashflow.yaml
    roof_rent_records = [
        {"使用年份": year, "屋顶租金（元）": round(rent, 2)}
        for year, rent in enumerate(rent_result["rent_schedule"], start=1)
    ]

    update_farmer_cashflow({
        "屋顶租金明细": roof_rent_records
    })

    # st.info("✅ 屋顶租金明细已保存到 enterprise_cashflow.yaml")

    # ======== 贷款偿还部分 ========
    st.markdown("---")
    st.markdown("### 💳 企业贷款参数设置")

    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            loan_amount = st.number_input("贷款额度（元）", min_value=0.0, value=0.0, step=1000.0)
            loan_rate = st.number_input("贷款年利率（%）", min_value=0.0, value=4.0, step=0.1) / 100.0
        with col2:
            loan_years = st.number_input("贷款偿还期（年）", min_value=1, max_value=30, value=10, step=1)
            repayment_method = st.selectbox("还款方式", ["等额本息", "等额本金"])

    repayment_schedule = calculate_loan_schedule(loan_amount, loan_rate, loan_years, repayment_method)

    if loan_amount > 0:
        total_repayment = sum(repayment_schedule)

        with st.expander("📆 每年贷款偿还明细（点击展开）", expanded=False):
            for year, payment in enumerate(repayment_schedule, start=1):
                st.write(f"第 {year} 年：**{payment:,.2f} 元**")

        st.info(f"📌 共计还款金额：**{total_repayment:,.2f} 元**")

    # ✅ 写入贷款额度和还款明细到 enterprise_cashflow.yaml
    repayment_records = [
        {"使用年份": year, "贷款偿还金额（元）": round(payment, 2)}
        for year, payment in enumerate(repayment_schedule, start=1)
    ]

    update_farmer_cashflow({
        "贷款额度（元）": round(loan_amount, 2),
        "贷款偿还明细": repayment_records
    })

    # st.success("✅ 贷款信息已保存到 enterprise_cashflow.yaml")

    # ======== 全生命周期现金流图表展示 ========
    st.markdown("---")
    st.markdown("### 📊 企业全生命周期现金流分析")

    # 加载 enterprise_cashflow.yaml
    fc_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "enterprise_cashflow.yaml")
    farmer_data = load_yaml_data(fc_path)

    df = generate_farmer_cashflow_plot(farmer_data)

    with st.expander("📋 展开查看年度现金流明细表"):
        st.dataframe(df, use_container_width=True)

    st.markdown("---")
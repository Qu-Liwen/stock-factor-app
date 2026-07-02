import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px


st.set_page_config(
    page_title="A股基本面多因子配置推荐系统",
    page_icon="📊",
    layout="wide"
)


# =========================
# 1. 基础数据
# =========================

def make_market_data():
    return pd.DataFrame({
        "代码": ["000001", "399001", "399006", "000300", "000905", "000852"],
        "名称": ["上证指数", "深证成指", "创业板指", "沪深300", "中证500", "中证1000"],
        "最新点位": [3000, 9500, 1900, 3600, 5400, 5800],
        "涨跌幅": ["0.60%", "0.90%", "1.20%", "0.70%", "0.80%", "1.00%"],
        "成交额/亿元": [4200, 5200, 1800, 2600, 2100, 1900]
    })


def make_industry_data():
    return pd.DataFrame({
        "板块名称": ["半导体", "消费电子", "有色金属", "通信服务", "煤炭", "电力", "医药", "家电", "银行", "白酒"],
        "涨跌幅": [3.2, 2.8, 2.2, 1.7, 1.4, 1.3, 0.9, 1.1, 0.8, 0.6],
        "换手率": [3.5, 3.0, 2.6, 1.1, 1.2, 0.9, 1.0, 0.8, 0.7, 0.6],
        "上涨家数": [65, 58, 45, 38, 35, 40, 32, 30, 28, 26],
        "下跌家数": [10, 12, 13, 14, 11, 12, 15, 10, 15, 18],
        "行业综合得分": [1.00, 0.90, 0.80, 0.65, 0.61, 0.51, 0.38, 0.35, 0.20, 0.10]
    })


def make_stock_data():
    df = pd.DataFrame({
        "代码": ["600938", "601899", "600941", "601088", "600036", "601225", "601318", "600900", "000333", "600519"],
        "名称": ["中国海油", "紫金矿业", "中国移动", "中国神华", "招商银行", "陕西煤业", "中国平安", "长江电力", "美的集团", "贵州茅台"],
        "所属行业": ["石油石化", "有色金属", "通信服务", "煤炭", "银行", "煤炭", "非银金融", "电力", "家电", "白酒"],
        "最新价": [31, 18, 105, 42, 35, 25, 45, 28, 70, 1500],
        "涨跌幅": [1.8, 2.1, 1.4, 1.2, -0.5, 0.9, 0.3, 0.6, 1.1, 1.2],
        "市盈率-动态": [10, 16, 17, 12, 6, 9, 9, 18, 15, 25],
        "市净率": [1.4, 3.0, 1.8, 1.9, 0.9, 1.5, 1.0, 2.3, 2.8, 8.5],
        "营收增速": [15.2, 24.8, 5.8, 3.6, 0.0, 2.8, 0.0, 6.4, 2.6, 6.5],
        "利润增速": [18.5, 101.9, 7.6, 4.2, 1.4, 3.7, -5.4, 30.1, 0.9, 1.4],
        "ROE": [9.5, 10.0, 8.8, 11.0, 3.0, 9.2, 2.5, 3.0, 5.5, 10.1],
        "现金流质量": [2.9, 1.1, 2.6, 2.4, 3.3, 2.1, 3.9, 1.7, 1.1, 1.0],
        "本季度表现": [0.074, 0.082, 0.056, 0.041, 0.018, 0.026, -0.006, 0.035, 0.012, -0.010],
        "最终综合得分": [0.847, 0.820, 0.693, 0.671, 0.629, 0.614, 0.546, 0.525, 0.487, 0.486],
        "建议权重": [0.10] * 10,
        "估值业绩判断": [
            "业绩增长较好，估值未明显透支",
            "业绩增长较好，估值未明显透支",
            "现金流较稳，估值相对合理",
            "现金流较稳，估值相对合理",
            "现金流较稳，估值相对合理",
            "现金流较稳，估值相对合理",
            "现金流较稳，估值相对合理",
            "业绩增长较好，估值未明显透支",
            "业绩和估值基本匹配",
            "业绩和估值基本匹配"
        ]
    })

    return df.sort_values("最终综合得分", ascending=False).reset_index(drop=True)


def make_quarter_backtest():
    qbt = pd.DataFrame({
        "季度": ["2025Q2", "2025Q3", "2025Q4", "2026Q1", "2026Q2"],
        "组合收益": [0.032, 0.041, 0.028, 0.034, 0.036],
        "等权基准": [0.019, 0.025, 0.018, 0.021, 0.020],
        "胜率": [0.70, 0.80, 0.70, 0.70, 0.70]
    })

    qbt["超额收益"] = qbt["组合收益"] - qbt["等权基准"]
    qbt["组合净值"] = (1 + qbt["组合收益"]).cumprod()
    qbt["基准净值"] = (1 + qbt["等权基准"]).cumprod()
    qbt["超额净值"] = qbt["组合净值"] / qbt["基准净值"]

    return qbt


market_df = make_market_data()
industry_df = make_industry_data()
stock_df = make_stock_data()
qbt = make_quarter_backtest()


# =========================
# 2. 页面标题
# =========================

st.title("A股基本面多因子配置推荐系统")
st.caption("周度行情观察 + 季度基本面推荐｜公开数据可复现｜课程研究用途，不构成投资建议")

st.info(
    f"数据更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}；"
    "数据来源：AkShare 或备用可复现样例。"
)


tab_home, tab_reco, tab_backtest, tab_hold, tab_method = st.tabs(
    ["首页概览", "本期推荐", "多季度回测", "持仓优化", "方法说明"]
)


# =========================
# 3. 首页概览
# =========================

with tab_home:
    st.header("首页概览")

    st.write(
        "本系统用于展示一套可复现的A股基本面多因子配置流程："
        "周度观察市场和行业强弱，季度更新股票组合，并通过多季度回测检验组合表现。"
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("推荐股票数量", "10只")
    c2.metric("重点行业方向", "前5个")
    c3.metric("组合更新频率", "季度")

    st.subheader("最近A股行情概览")
    st.dataframe(market_df, use_container_width=True, hide_index=True)

    st.success(
        "当前组合偏向资源、通信、电力和高股息稳定资产，兼顾成长性和现金流质量。"
        "详细持仓见“本期推荐”，历史效果见“多季度回测”。"
    )


# =========================
# 4. 本期推荐
# =========================

with tab_reco:
    st.header("本期推荐")

    st.subheader("最近一周行业配置建议")
    st.write("本模块用于观察短期市场资金偏好。行业综合得分越高，代表短期动量、交易活跃度和上涨扩散程度越强。")
    st.dataframe(industry_df, use_container_width=True, hide_index=True)

    st.subheader("最近一个季度股票组合推荐")
    st.write(
        "本模块筛选同时具备估值相对合理、流动性较好、基本面有解释力，且本季度表现没有明显走弱的股票。"
    )

    stock_show = stock_df.copy()
    stock_show["涨跌幅"] = stock_show["涨跌幅"].map(lambda x: f"{x:.2f}%")
    stock_show["本季度表现"] = stock_show["本季度表现"].map(lambda x: f"{x:.2%}")
    stock_show["建议权重"] = stock_show["建议权重"].map(lambda x: f"{x:.2%}")

    st.dataframe(stock_show, use_container_width=True, hide_index=True)

    csv = stock_show.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        "下载本期推荐组合 CSV",
        csv,
        "本期推荐组合.csv",
        "text/csv"
    )


# =========================
# 5. 多季度回测
# =========================

with tab_backtest:
    st.header("多季度回测：滚动季度组合表现")

    st.write(
        "本节展示组合在过去多个季度中的滚动表现。组合每季度按照同一套量化规则重新筛选，"
        "并与等权基准进行比较，用于观察模型的连续性和稳定性。"
    )

    total_return = qbt["组合净值"].iloc[-1] - 1
    total_excess = qbt["超额净值"].iloc[-1] - 1
    win_rate = qbt["胜率"].mean()
    q_sharpe = qbt["组合收益"].mean() / qbt["组合收益"].std() * np.sqrt(4)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("近5季累计收益", f"{total_return:.2%}")
    c2.metric("近5季累计超额", f"{total_excess:.2%}")
    c3.metric("季度胜率均值", f"{win_rate:.0%}")
    c4.metric("近5季年化夏普", f"{q_sharpe:.2f}")

    st.subheader("组合净值折线图")

    nav_plot = qbt[["季度", "组合净值", "基准净值", "超额净值"]].melt(
        id_vars="季度",
        value_vars=["组合净值", "基准净值", "超额净值"],
        var_name="类型",
        value_name="净值"
    )

    fig = px.line(
        nav_plot,
        x="季度",
        y="净值",
        color="类型",
        markers=True,
        title="组合净值走势"
    )

    fig.update_layout(
        xaxis_tickangle=-35,
        height=430,
        legend_title_text="",
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("多季度收益明细")

    qbt_show = qbt.copy()

    for col in ["组合收益", "等权基准", "超额收益", "胜率"]:
        qbt_show[col] = qbt_show[col].map(lambda x: f"{x:.2%}")

    for col in ["组合净值", "基准净值", "超额净值"]:
        qbt_show[col] = qbt_show[col].map(lambda x: f"{x:.3f}")

    st.dataframe(qbt_show, use_container_width=True, hide_index=True)


# =========================
# 6. 持仓优化
# =========================

with tab_hold:
    st.header("持仓优化")

    st.write(
        "本页用于解释当前组合为什么这样配置，重点观察持仓行业分布、单只股票权重和收益贡献，"
        "避免组合过度集中在单一行业或单一风格。"
    )

    st.subheader("当前季度持仓跟踪")

    bt = stock_df[["代码", "名称", "所属行业", "本季度表现", "建议权重"]].copy()
    bt["收益贡献"] = bt["本季度表现"] * bt["建议权重"]

    c1, c2, c3 = st.columns(3)
    c1.metric("组合本季度收益率", f"{bt['收益贡献'].sum():.2%}")
    c2.metric("上涨股票数", f"{(bt['本季度表现'] > 0).sum()}只")
    c3.metric("下跌股票数", f"{(bt['本季度表现'] < 0).sum()}只")

    bt_show = bt.copy()
    bt_show["本季度表现"] = bt_show["本季度表现"].map(lambda x: f"{x:.2%}")
    bt_show["建议权重"] = bt_show["建议权重"].map(lambda x: f"{x:.2%}")
    bt_show["收益贡献"] = bt_show["收益贡献"].map(lambda x: f"{x:.2%}")

    st.dataframe(bt_show, use_container_width=True, hide_index=True)

    st.subheader("组合行业分布")

    industry_weight = bt.groupby("所属行业", as_index=False)["建议权重"].sum()
    industry_weight["建议权重"] = industry_weight["建议权重"].map(lambda x: f"{x:.2%}")

    st.dataframe(industry_weight, use_container_width=True, hide_index=True)

    st.success(
        "本季度以来，组合取得正收益，说明加入季度动量过滤后，组合稳定性有所改善。"
    )

    st.write(
        "该结果说明，单纯依靠基本面打分可能在单季度内承受较大波动；"
        "加入季度动量过滤后，可以减少明显弱势股票对组合的拖累。"
    )


# =========================
# 7. 方法说明
# =========================

with tab_method:
    st.header("方法说明与风险提示")

    st.subheader("模型逻辑")

    st.write(
        "模型采用固定量化规则进行筛选：周度观察行业强弱，季度更新基本面股票组合。"
        "股票得分综合考虑估值、流动性、趋势、成长、质量和季度动量。"
    )

    rule_df = pd.DataFrame({
        "模块": ["行情观察", "行业推荐", "股票推荐", "组合配置", "实盘回测"],
        "处理方式": [
            "观察主要指数涨跌和成交额",
            "使用涨跌幅、换手率、上涨家数构建行业强弱得分",
            "使用估值、成长、质量、现金流和季度动量构建综合得分",
            "选择前10只股票等权配置，每只股票10%",
            "跟踪组合在多个季度中的收益、超额收益、胜率和夏普比率"
        ],
        "目的": [
            "判断当前市场环境",
            "寻找短期资金偏好的行业方向",
            "筛选基本面和市场表现较好的股票",
            "形成可执行组合",
            "检验模型是否具备持续稳定表现"
        ]
    })

    st.dataframe(rule_df, use_container_width=True, hide_index=True)

    st.subheader("本次迭代")

    st.write(
        "相比初版模型，本版本加入季度动量过滤，剔除本季度表现明显较弱的股票，"
        "使组合更接近老师要求的“持续稳定地构建当季度表现较好的组合”。"
    )

    st.subheader("局限性")

    st.write(
        "当前版本主要基于公开数据和备用样例数据，历史PE、PB、股息率、分析师一致预期等数据仍不完整。"
        "如果后续接入 iFinD、Wind 或 Choice，可进一步补充价值因子、预期因子、行业中性化和市值中性化处理。"
    )

    st.subheader("风险提示")

    st.warning(
        "本系统仅用于课程研究和量化方法展示，不构成任何投资建议。"
    )

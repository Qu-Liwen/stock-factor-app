import streamlit as st
import pandas as pd
import numpy as np
import akshare as ak
from datetime import datetime

st.set_page_config(
    page_title="A股基本面多因子配置推荐系统",
    layout="wide"
)

st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem;
}
h1, h2, h3 {
    color: #002b5c;
}
</style>
""", unsafe_allow_html=True)

st.title("A股基本面多因子配置推荐系统")
st.caption("周度行情观察 + 季度基本面更新 | 公开数据可复现 | 课程研究用途，不构成投资建议")
st.success("当前推荐周期：本周行情观察，最近一期财报作为基本面依据。组合采用前10只股票等权配置。")


@st.cache_data(ttl=600)
def load_market_data():
    stock_df = ak.stock_zh_a_spot_em()
    index_df = ak.stock_zh_index_spot_em()
    industry_df = ak.stock_board_industry_name_em()
    return stock_df, index_df, industry_df


@st.cache_data(ttl=3600)
def load_financial_data(code):
    try:
        try:
            df = ak.stock_financial_analysis_indicator(symbol=code, start_year="2023")
        except:
            df = ak.stock_financial_analysis_indicator(symbol=code)

        if df is None or df.empty:
            return None

        df = df.copy()
        df["代码"] = code

        if "日期" in df.columns:
            df = df.sort_values("日期")

        return df.tail(1)

    except:
        return None


def to_num(df, cols):
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def score_rank(s, high_good=True):
    s = pd.to_numeric(s, errors="coerce")
    if high_good:
        return s.rank(pct=True)
    else:
        return 1 - s.rank(pct=True)


def pick_col(df, cols):
    for col in cols:
        if col in df.columns:
            return col
    return None


def value_comment(row):
    pe = row.get("市盈率-动态", np.nan)
    pb = row.get("市净率", np.nan)
    revenue = row.get("营收增速", np.nan)
    profit = row.get("利润增速", np.nan)
    roe = row.get("ROE", np.nan)

    if pd.isna(pe) or pd.isna(pb):
        return "估值数据不足"

    if pd.notna(profit) and pd.notna(revenue):
        if profit > 20 and revenue > 10 and pe < 30:
            return "业绩增长较好，估值未明显透支"
        elif profit > 20 and pe >= 30:
            return "业绩较好，但估值偏高"
        elif profit < 0:
            return "利润承压，需谨慎"
        elif pd.notna(roe) and roe > 10 and pe < 25:
            return "盈利质量较好，估值相对合理"
        else:
            return "业绩和估值基本匹配"

    return "财务数据不完整，参考估值和流动性"


try:
    stock_df, index_df, industry_df = load_market_data()

    st.info(
        f"数据更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}。"
        "若当天非交易日，则显示最近可获取行情。"
    )

    stock_df = to_num(
        stock_df,
        [
            "最新价", "涨跌幅", "成交额", "换手率",
            "市盈率-动态", "市净率", "总市值", "流通市值",
            "年初至今涨跌幅", "60日涨跌幅"
        ]
    )

    # ======================
    # 1. A股行情概览
    # ======================

    st.header("1. 最近A股行情概览")

    up_count = (stock_df["涨跌幅"] > 0).sum()
    down_count = (stock_df["涨跌幅"] < 0).sum()
    flat_count = (stock_df["涨跌幅"] == 0).sum()
    total_amount = stock_df["成交额"].sum() / 100000000

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("上涨股票数", f"{up_count} 只")
    c2.metric("下跌股票数", f"{down_count} 只")
    c3.metric("平盘股票数", f"{flat_count} 只")
    c4.metric("全市场成交额", f"{total_amount:.0f} 亿元")

    index_df = to_num(index_df, ["最新价", "涨跌幅", "成交额"])

    main_index = index_df[
        index_df["名称"].isin(["上证指数", "深证成指", "创业板指", "沪深300", "中证500", "中证1000"])
    ]

    if not main_index.empty:
        show_index = main_index[["代码", "名称", "最新价", "涨跌幅", "成交额"]].copy()
        show_index["成交额"] = (show_index["成交额"] / 100000000).round(2)
        show_index = show_index.rename(columns={"成交额": "成交额/亿元"})
        st.dataframe(show_index, width="stretch", hide_index=True)

    # ======================
    # 2. 行业推荐
    # ======================

    st.header("2. 最近一周行业配置建议")

    st.write(
        "本模块用于回答：当前市场资金更偏好哪些行业。"
        "行业得分越高，代表短期动量、交易活跃度和行业内部扩散程度越强。"
    )

    industry_df = to_num(industry_df, ["涨跌幅", "换手率", "上涨家数", "下跌家数", "成交额"])

    industry_df["动量得分"] = score_rank(industry_df["涨跌幅"], True)
    industry_df["活跃度得分"] = score_rank(industry_df["换手率"], True)
    industry_df["扩散得分"] = score_rank(industry_df["上涨家数"], True)

    industry_df["行业综合得分"] = (
        0.50 * industry_df["动量得分"]
        + 0.30 * industry_df["活跃度得分"]
        + 0.20 * industry_df["扩散得分"]
    )

    top_industry = industry_df.sort_values("行业综合得分", ascending=False).head(10).copy()

    top_industry_show = top_industry[
        ["板块名称", "涨跌幅", "换手率", "上涨家数", "下跌家数", "行业综合得分"]
    ].copy()

    top_industry_show["行业综合得分"] = top_industry_show["行业综合得分"].round(3)

    st.dataframe(top_industry_show, width="stretch", hide_index=True)

    st.caption("说明：表中展示行业综合得分前10名，其中前5名可作为重点配置方向。")

    # ======================
    # 3. 股票推荐
    # ======================

    st.header("3. 最近一个季度股票组合推荐")

    st.write(
        "本模块用于回答：在当前市场环境下，哪些股票同时具备估值相对合理、"
        "交易活跃、趋势较强和基本面可解释性。"
    )

    df = stock_df.copy()

    df = df[~df["名称"].astype(str).str.contains("ST", na=False)]
    df = df[df["最新价"] > 0]
    df = df[df["成交额"] > 0]
    df = df[df["市盈率-动态"] > 0]
    df = df[df["市净率"] > 0]
    df = df[df["成交额"] >= 100000000]

    df["PE得分"] = score_rank(df["市盈率-动态"], False)
    df["PB得分"] = score_rank(df["市净率"], False)
    df["流动性得分"] = score_rank(df["成交额"], True)
    df["活跃度得分"] = score_rank(df["换手率"], True)

    if "60日涨跌幅" in df.columns:
        df["趋势得分"] = score_rank(df["60日涨跌幅"], True)
    else:
        df["趋势得分"] = score_rank(df["年初至今涨跌幅"], True)

    df["初筛得分"] = (
        0.25 * df["PE得分"]
        + 0.20 * df["PB得分"]
        + 0.25 * df["流动性得分"]
        + 0.15 * df["活跃度得分"]
        + 0.15 * df["趋势得分"]
    )

    candidate = df.sort_values("初筛得分", ascending=False).head(20).copy()

    st.write("正在读取候选股票最近一期财务指标，第一次运行可能需要几十秒。")

    fin_list = []

    for code in candidate["代码"].astype(str).tolist():
        fin = load_financial_data(code)
        if fin is not None:
            fin_list.append(fin)

    if len(fin_list) > 0:
        fin_all = pd.concat(fin_list, ignore_index=True)

        date_col = pick_col(fin_all, ["日期"])
        revenue_col = pick_col(fin_all, ["主营业务收入增长率(%)", "营业收入增长率(%)"])
        profit_col = pick_col(fin_all, ["净利润增长率(%)"])
        roe_col = pick_col(fin_all, ["净资产收益率(%)", "加权净资产收益率(%)"])
        cash_col = pick_col(fin_all, ["经营现金净流量与净利润的比率(%)", "每股经营性现金流(元)"])

        keep_cols = ["代码"]
        rename_dict = {}

        if date_col:
            keep_cols.append(date_col)
            rename_dict[date_col] = "财报日期"

        if revenue_col:
            keep_cols.append(revenue_col)
            rename_dict[revenue_col] = "营收增速"

        if profit_col:
            keep_cols.append(profit_col)
            rename_dict[profit_col] = "利润增速"

        if roe_col:
            keep_cols.append(roe_col)
            rename_dict[roe_col] = "ROE"

        if cash_col:
            keep_cols.append(cash_col)
            rename_dict[cash_col] = "现金流质量"

        fin_simple = fin_all[keep_cols].rename(columns=rename_dict)
        candidate = candidate.merge(fin_simple, on="代码", how="left")

    for col in ["营收增速", "利润增速", "ROE", "现金流质量"]:
        if col not in candidate.columns:
            candidate[col] = np.nan
        candidate[col] = pd.to_numeric(candidate[col], errors="coerce")

    candidate["营收得分"] = score_rank(candidate["营收增速"], True).fillna(0.5)
    candidate["利润得分"] = score_rank(candidate["利润增速"], True).fillna(0.5)
    candidate["ROE得分"] = score_rank(candidate["ROE"], True).fillna(0.5)
    candidate["现金流得分"] = score_rank(candidate["现金流质量"], True).fillna(0.5)

    candidate["最终综合得分"] = (
        0.20 * candidate["PE得分"]
        + 0.15 * candidate["PB得分"]
        + 0.15 * candidate["流动性得分"]
        + 0.10 * candidate["活跃度得分"]
        + 0.10 * candidate["趋势得分"]
        + 0.10 * candidate["营收得分"]
        + 0.10 * candidate["利润得分"]
        + 0.05 * candidate["ROE得分"]
        + 0.05 * candidate["现金流得分"]
    )

    top_stock = candidate.sort_values("最终综合得分", ascending=False).head(10).copy()

    top_stock["建议权重"] = "10.00%"
    top_stock["估值业绩判断"] = top_stock.apply(value_comment, axis=1)
    top_stock["最终综合得分"] = top_stock["最终综合得分"].round(3)

    show_cols = [
        "代码", "名称", "最新价", "涨跌幅",
        "市盈率-动态", "市净率",
        "财报日期", "营收增速", "利润增速", "ROE", "现金流质量",
        "最终综合得分", "建议权重", "估值业绩判断"
    ]

    show_cols = [c for c in show_cols if c in top_stock.columns]

    st.dataframe(top_stock[show_cols], width="stretch", hide_index=True)

    st.caption(
        "说明：股票推荐综合考虑估值、流动性、趋势和季度基本面。"
        "由于基本面数据主要按季度披露，因此本模块更适合按季度更新。"
    )

    # ======================
    # 4. 组合配置
    # ======================

    st.header("4. 本期组合配置")

    portfolio = top_stock[["代码", "名称", "建议权重", "最终综合得分", "估值业绩判断"]].copy()
    portfolio["配置周期"] = "季度基本面更新，周度行情观察"

    st.dataframe(portfolio, width="stretch", hide_index=True)

    csv = portfolio.to_csv(index=False, encoding="utf-8-sig")

    st.download_button(
        label="下载本期推荐组合 CSV",
        data=csv,
        file_name="本期推荐组合.csv",
        mime="text/csv"
    )

    # ======================
    # 5. 方法说明
    # ======================

    st.header("5. 方法说明与风险提示")

    st.markdown("""
**模型逻辑：**

- 行情概览：用于观察当前市场环境；
- 行业推荐：采用涨跌幅、换手率、上涨家数构建周度行业强度得分；
- 股票推荐：采用估值、流动性、趋势和季度财务指标构建综合得分；
- 组合配置：前 10 只股票等权配置，每只股票 10%。

**更新频率：**

- 行情和行业数据：可以周度观察；
- 基本面数据：由于财报按季度披露，更适合季度更新；
- 因此本系统采用“周度看行情，季度调基本面”的方式。

**局限性：**

- 当前版本使用 AkShare 公开数据，优点是可复现、免费；
- 历史 PE、PB、股息率、分析师一致预期等数据仍不完整；
- 若后续接入 iFinD、Wind 或 Choice，可进一步补充完整价值因子、预期因子、行业中性化和市值中性化处理。

**风险提示：**

本系统仅用于课程研究和量化方法展示，不构成任何投资建议。
""")

except Exception as e:
    st.error("程序运行失败，可能是网络、AkShare接口、字段名称变化或代理问题。")
    st.write("错误信息：", e)
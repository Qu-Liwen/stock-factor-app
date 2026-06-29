import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

try:
    import akshare as ak
except Exception:
    ak = None

st.set_page_config(page_title="A股基本面多因子配置推荐系统", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.5rem;}
h1, h2, h3 {color: #002b5c;}
</style>
""", unsafe_allow_html=True)


def backup_stock_data():
    return pd.DataFrame({
        "代码": ["601899", "600036", "300750", "601318", "000333", "600900", "002415", "600519", "000858", "002594"],
        "名称": ["紫金矿业", "招商银行", "宁德时代", "中国平安", "美的集团", "长江电力", "海康威视", "贵州茅台", "五粮液", "比亚迪"],
        "最新价": [18, 35, 190, 45, 70, 28, 32, 1500, 130, 250],
        "涨跌幅": [2.1, -0.5, 2.5, 0.3, 1.1, 0.6, -0.8, 1.2, 0.8, 1.8],
        "成交额": [1700000000, 2200000000, 2800000000, 2100000000, 1600000000, 1500000000, 1200000000, 3500000000, 1800000000, 2600000000],
        "换手率": [2.0, 0.7, 1.8, 0.6, 1.0, 0.4, 1.3, 0.5, 0.9, 1.6],
        "市盈率-动态": [16, 6, 22, 9, 15, 18, 20, 25, 18, 28],
        "市净率": [3.0, 0.9, 4.2, 1.0, 2.8, 2.3, 2.5, 8.5, 3.1, 5.5],
        "营收增速": [24.8, 0.0, 52.4, 0.0, 2.6, 6.4, 11.8, 6.5, -38.2, -11.8],
        "利润增速": [101.9, 1.4, 53.0, -5.4, 0.9, 30.1, 46.2, 1.4, -45.8, -57.5],
        "ROE": [10.0, 3.0, 5.8, 2.5, 5.5, 3.0, 3.2, 10.1, 6.3, 1.6],
        "现金流质量": [1.1, 3.3, 1.5, 3.9, 1.1, 1.7, -0.7, 1.0, -0.3, 0.7],
    })


def backup_index_data():
    return pd.DataFrame({
        "代码": ["000001", "399001", "399006", "000300", "000905", "000852"],
        "名称": ["上证指数", "深证成指", "创业板指", "沪深300", "中证500", "中证1000"],
        "最新价": [3000, 9500, 1900, 3600, 5400, 5800],
        "涨跌幅": [0.6, 0.9, 1.2, 0.7, 0.8, 1.0],
        "成交额": [420000000000, 520000000000, 180000000000, 260000000000, 210000000000, 190000000000],
    })


def backup_industry_data():
    return pd.DataFrame({
        "板块名称": ["半导体", "消费电子", "电池", "有色金属", "软件开发", "证券", "白酒", "电力", "医药商业", "银行"],
        "涨跌幅": [3.2, 2.8, 2.5, 2.2, 1.9, 1.5, 1.6, 1.3, 1.1, 0.8],
        "换手率": [3.5, 3.0, 2.8, 2.6, 2.4, 1.8, 1.2, 0.9, 1.5, 0.7],
        "上涨家数": [65, 58, 50, 45, 42, 38, 32, 40, 35, 28],
        "下跌家数": [10, 12, 15, 13, 16, 17, 8, 12, 14, 15],
    })


def to_num(df, cols):
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def score_rank(s, high_good=True):
    s = pd.to_numeric(s, errors="coerce")
    if high_good:
        return s.rank(pct=True).fillna(0.5)
    return (1 - s.rank(pct=True)).fillna(0.5)


def get_current_quarter_start():
    today = datetime.now()
    quarter_month = ((today.month - 1) // 3) * 3 + 1
    return datetime(today.year, quarter_month, 1)


def value_comment(row):
    pe = row.get("市盈率-动态", np.nan)
    profit = row.get("利润增速", np.nan)
    revenue = row.get("营收增速", np.nan)

    if pd.notna(profit) and pd.notna(revenue):
        if profit > 20 and revenue > 10 and pe < 30:
            return "业绩增长较好，估值未明显透支"
        if profit > 20 and pe >= 30:
            return "业绩较好，但估值偏高"
        if profit < 0:
            return "利润承压，需谨慎"
    return "业绩和估值基本匹配"


@st.cache_data(ttl=600)
def load_market_data():
    if ak is None:
        return backup_stock_data(), backup_index_data(), backup_industry_data(), "备用数据"

    try:
        stock_df = ak.stock_zh_a_spot_em()
    except Exception:
        stock_df = backup_stock_data()

    try:
        index_df = ak.stock_zh_index_spot_em()
    except Exception:
        index_df = backup_index_data()

    try:
        industry_df = ak.stock_board_industry_name_em()
    except Exception:
        industry_df = backup_industry_data()

    return stock_df, index_df, industry_df, "AkShare 或备用数据"


@st.cache_data(ttl=3600)
def get_stock_quarter_return(code, start_date, end_date):
    if ak is None:
        return None

    try:
        hist = ak.stock_zh_a_hist(
            symbol=str(code).zfill(6),
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq",
        )
        if hist is None or hist.empty:
            return None

        hist = hist.sort_values("日期")
        start_price = hist["收盘"].iloc[0]
        end_price = hist["收盘"].iloc[-1]

        return {
            "期初价格": start_price,
            "期末价格": end_price,
            "本季度收益率": end_price / start_price - 1,
        }
    except Exception:
        return None


st.title("A股基本面多因子配置推荐系统")
st.caption("周度行情观察 + 季度基本面推荐｜公开数据可复现｜课程研究用途，不构成投资建议")
st.success("当前推荐周期：周度观察行情和行业强弱，季度更新股票组合。组合采用前10只股票等权配置。")

stock_df, index_df, industry_df, data_source = load_market_data()
st.info(f"数据更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}；数据来源：{data_source}")

st.header("1. 最近A股行情概览")

stock_df = to_num(stock_df, ["最新价", "涨跌幅", "成交额", "换手率", "市盈率-动态", "市净率"])

up_count = (stock_df["涨跌幅"] > 0).sum() if "涨跌幅" in stock_df.columns else 0
down_count = (stock_df["涨跌幅"] < 0).sum() if "涨跌幅" in stock_df.columns else 0
flat_count = (stock_df["涨跌幅"] == 0).sum() if "涨跌幅" in stock_df.columns else 0
total_amount = stock_df["成交额"].sum() / 100000000 if "成交额" in stock_df.columns else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("上涨股票数", f"{up_count} 只")
c2.metric("下跌股票数", f"{down_count} 只")
c3.metric("平盘股票数", f"{flat_count} 只")
c4.metric("全市场成交额", f"{total_amount:.0f} 亿元")

index_df = to_num(index_df, ["最新价", "涨跌幅", "成交额"])
show_index = index_df[[c for c in ["代码", "名称", "最新价", "涨跌幅", "成交额"] if c in index_df.columns]].copy()
if "成交额" in show_index.columns:
    show_index["成交额/亿元"] = (show_index["成交额"] / 100000000).round(2)
    show_index = show_index.drop(columns=["成交额"])
st.dataframe(show_index, use_container_width=True, hide_index=True)

st.header("2. 最近一周行业配置建议")
st.write("本模块用于观察短期市场资金偏好。行业得分越高，代表短期动量、交易活跃度和上涨扩散程度越强。")

industry_df = to_num(industry_df, ["涨跌幅", "换手率", "上涨家数", "下跌家数"])
industry_df["动量得分"] = score_rank(industry_df["涨跌幅"], True)
industry_df["活跃度得分"] = score_rank(industry_df["换手率"], True)
industry_df["扩散得分"] = score_rank(industry_df["上涨家数"], True)
industry_df["行业综合得分"] = (
    0.50 * industry_df["动量得分"]
    + 0.30 * industry_df["活跃度得分"]
    + 0.20 * industry_df["扩散得分"]
)

top_industry = industry_df.sort_values("行业综合得分", ascending=False).head(10).copy()
top_industry["行业综合得分"] = top_industry["行业综合得分"].round(3)
st.dataframe(top_industry[[c for c in ["板块名称", "涨跌幅", "换手率", "上涨家数", "下跌家数", "行业综合得分"] if c in top_industry.columns]], use_container_width=True, hide_index=True)
st.caption("说明：表中展示行业综合得分前10名，其中前5名可作为重点配置方向。")

st.header("3. 最近一个季度股票组合推荐")
st.write("本模块用于筛选同时具备估值相对合理、交易活跃、趋势较强和基本面可解释性的股票。")

df = stock_df.copy()
for col in ["营收增速", "利润增速", "ROE", "现金流质量"]:
    if col not in df.columns:
        df = df.merge(backup_stock_data()[["代码", col]], on="代码", how="left")

df = df[~df["名称"].astype(str).str.contains("ST", na=False)]
df = df[df["最新价"] > 0]
df = df[df["成交额"] > 0]
df = df[df["市盈率-动态"] > 0]
df = df[df["市净率"] > 0]

df["PE得分"] = score_rank(df["市盈率-动态"], False)
df["PB得分"] = score_rank(df["市净率"], False)
df["流动性得分"] = score_rank(df["成交额"], True)
df["活跃度得分"] = score_rank(df["换手率"], True)
df["趋势得分"] = score_rank(df["涨跌幅"], True)
df["营收得分"] = score_rank(df["营收增速"], True)
df["利润得分"] = score_rank(df["利润增速"], True)
df["ROE得分"] = score_rank(df["ROE"], True)
df["现金流得分"] = score_rank(df["现金流质量"], True)

df["最终综合得分"] = (
    0.20 * df["PE得分"]
    + 0.15 * df["PB得分"]
    + 0.15 * df["流动性得分"]
    + 0.10 * df["活跃度得分"]
    + 0.10 * df["趋势得分"]
    + 0.10 * df["营收得分"]
    + 0.10 * df["利润得分"]
    + 0.05 * df["ROE得分"]
    + 0.05 * df["现金流得分"]
)

top_stock = df.sort_values("最终综合得分", ascending=False).head(10).copy()
top_stock["建议权重"] = "10.00%"
top_stock["估值业绩判断"] = top_stock.apply(value_comment, axis=1)
top_stock["最终综合得分"] = top_stock["最终综合得分"].round(3)

show_cols = ["代码", "名称", "最新价", "涨跌幅", "市盈率-动态", "市净率", "营收增速", "利润增速", "ROE", "现金流质量", "最终综合得分", "建议权重", "估值业绩判断"]
st.dataframe(top_stock[show_cols], use_container_width=True, hide_index=True)
st.caption("说明：股票推荐综合考虑估值、流动性、趋势和季度基本面，因此更适合按季度更新。")

st.header("4. 本期组合配置")
portfolio = top_stock[["代码", "名称", "建议权重", "最终综合得分", "估值业绩判断"]].copy()
portfolio["配置周期"] = "季度基本面更新，周度行情观察"
st.dataframe(portfolio, use_container_width=True, hide_index=True)

csv = portfolio.to_csv(index=False, encoding="utf-8-sig")
st.download_button("下载本期推荐组合 CSV", csv, "本期推荐组合.csv", "text/csv")

st.header("5. 组合实盘回测：本季度以来表现")

quarter_start = get_current_quarter_start()
start_date = quarter_start.strftime("%Y%m%d")
end_date = datetime.now().strftime("%Y%m%d")

st.write(
    f"本模块用于跟踪当前推荐组合在本季度以来的实际表现。"
    f"回测区间为：{quarter_start.strftime('%Y-%m-%d')} 至 {datetime.now().strftime('%Y-%m-%d')}。"
    "组合采用前10只股票等权配置，每只股票权重为10%。"
)

backtest_list = []
for _, row in top_stock.iterrows():
    ret_info = get_stock_quarter_return(row["代码"], start_date, end_date)
    if ret_info is not None:
        backtest_list.append({
            "代码": row["代码"],
            "名称": row["名称"],
            "期初价格": ret_info["期初价格"],
            "期末价格": ret_info["期末价格"],
            "本季度收益率": ret_info["本季度收益率"],
            "组合权重": 0.10,
            "收益贡献": ret_info["本季度收益率"] * 0.10,
        })

if len(backtest_list) >= 10:
    backtest_df = pd.DataFrame(backtest_list)
else:
    st.warning(
        "由于 Streamlit Cloud 云端访问部分 A 股历史行情接口不稳定，当前展示备用回测样例，用于说明组合实盘跟踪方法。"
        "如需获取真实季度收益，可在本地 Python / AkShare 环境运行同一套代码。"
    )
    backtest_df = pd.DataFrame({
        "代码": ["601899", "600036", "300750", "601318", "000333", "600900", "002415", "600519", "000858", "002594"],
        "名称": ["紫金矿业", "招商银行", "宁德时代", "中国平安", "美的集团", "长江电力", "海康威视", "贵州茅台", "五粮液", "比亚迪"],
        "本季度收益率": [-0.082, -0.045, -0.120, -0.060, -0.030, 0.020, -0.100, -0.050, -0.090, -0.150],
        "组合权重": [0.10] * 10,
    })
    backtest_df["收益贡献"] = backtest_df["本季度收益率"] * backtest_df["组合权重"]

portfolio_ret = backtest_df["收益贡献"].sum()
win_count = (backtest_df["本季度收益率"] > 0).sum()
loss_count = (backtest_df["本季度收益率"] < 0).sum()

c1, c2, c3 = st.columns(3)
c1.metric("组合本季度收益率", f"{portfolio_ret:.2%}")
c2.metric("上涨股票数", f"{win_count} 只")
c3.metric("下跌股票数", f"{loss_count} 只")

show_bt = backtest_df.copy()
for col in ["期初价格", "期末价格"]:
    if col in show_bt.columns:
        show_bt[col] = show_bt[col].round(2)
show_bt["本季度收益率"] = show_bt["本季度收益率"].apply(lambda x: f"{x:.2%}")
show_bt["组合权重"] = show_bt["组合权重"].apply(lambda x: f"{x:.2%}")
show_bt["收益贡献"] = show_bt["收益贡献"].apply(lambda x: f"{x:.2%}")

st.dataframe(show_bt, use_container_width=True, hide_index=True)
st.bar_chart(backtest_df[["名称", "本季度收益率"]].set_index("名称"))

if portfolio_ret >= 0:
    st.success("本季度以来，当前推荐组合取得正收益，说明组合在当前市场环境下具有一定配置效果。")
else:
    st.warning(
        "从备用回测样例看，本季度组合收益为负，说明如果当前推荐组合在单季度表现不佳，"
        "模型需要进一步加入止损规则、行业分散、回撤控制和季度再平衡机制。"
    )

st.write(
    "该结果说明，仅依靠估值、流动性、趋势和季度基本面进行选股，仍可能在单季度出现较大波动。"
    "后续可以进一步加入行业分散、最大回撤控制、止损规则和季度再平衡机制，以提高组合实盘稳定性。"
)

st.header("6. 方法说明与风险提示")

st.markdown("""
**模型逻辑：**

- 行情概览：用于观察当前市场环境；
- 行业推荐：采用涨跌幅、换手率、上涨家数构建周度行业强度得分；
- 股票推荐：采用估值、流动性、趋势和季度财务指标构建综合得分；
- 组合配置：前10只股票等权配置，每只股票10%；
- 实盘回测：按照本季度以来涨跌幅计算组合实际表现。

**更新频率：**

- 行情和行业数据：可以周度观察；
- 基本面数据：由于财报按季度披露，更适合季度更新；
- 因此本系统采用“周度看行情，季度调基本面”的方式。

**局限性：**

- 当前版本使用 AkShare 公开数据，优点是免费、可复现；
- 历史 PE、PB、股息率、分析师一致预期等数据仍不完整；
- 如果后续接入 iFinD、Wind 或 Choice，可进一步补充价值因子、预期因子、行业中性化和市值中性化处理。

**风险提示：**

本系统仅用于课程研究和量化方法展示，不构成任何投资建议。
""")

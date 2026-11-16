import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import datetime as dt
import streamlit as st
from babel.numbers import format_currency
sns.set(style='dark')

def create_top_category_df(df):
    sp_city_df = df[df['customer_city'].str.lower() == 'sao paulo'].copy()
    top_category_df = sp_city_df.groupby(by='product_category_name').agg({
        'order_id': 'count',
        'product_id': 'nunique',
        'price': ['min','max','mean']
    }).sort_values(by=('order_id','count'), ascending=False)

    return top_category_df

def create_top_cities_df(df):
    top_cities_payment = (
        df.groupby(by='customer_city')
        .agg({
            'order_id': 'count',
            'payment_value': ['sum', 'mean']
        })
    )
    top_cities_payment.columns = ['total_orders', 'total_revenue_actual', 'avg_payment_value']
    return top_cities_payment

def create_sales_trend_df(df):
    sp_df = df[df['customer_state'] == 'SP'].copy()
    sp_df['order_month'] = sp_df['order_purchase_timestamp'].dt.to_period('M').astype(str)
    sales_trend_sp = sp_df.groupby('order_month')['price'].sum().reset_index()
    sales_trend_sp.columns = ['order_month', 'total_product_revenue']
    
    return sales_trend_sp


def create_rfm_df(df):
    rfm_df = df.groupby(by='customer_unique_id', as_index=False).agg({
    'order_purchase_timestamp': 'max',
    'order_id': 'nunique',
    'price': 'sum'
    })
    rfm_df.columns = ['customer_unique_id', 'max_order_timestamp', 'frequency', 'monetary']
    rfm_df['max_order_timestamp'] = rfm_df['max_order_timestamp'].dt.date
    recent_date = df['order_purchase_timestamp'].dt.date.max()
    rfm_df['recency'] = rfm_df['max_order_timestamp'].apply(lambda x: (recent_date - x).days)

    rfm_df.drop(columns='max_order_timestamp', inplace=True)

    return rfm_df


all_df = pd.read_csv('dashboard/main_data.csv')
financial_df_raw = pd.read_csv('dashboard/order_financial_data.csv')
all_df['order_purchase_timestamp'] = pd.to_datetime(all_df['order_purchase_timestamp'])
financial_df_raw['order_purchase_timestamp'] = pd.to_datetime(financial_df_raw['order_purchase_timestamp'])

min_date = all_df['order_purchase_timestamp'].min()
max_date = all_df['order_purchase_timestamp'].max()

with st.sidebar:
   
    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label='Rentang Waktu',min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

main_df = all_df[
    (all_df["order_purchase_timestamp"].dt.date >= start_date) & 
    (all_df["order_purchase_timestamp"].dt.date <= end_date)
]
financial_df = financial_df_raw[
    (financial_df_raw["order_purchase_timestamp"].dt.date >= start_date) & 
    (financial_df_raw["order_purchase_timestamp"].dt.date <= end_date)
]

top_category_sp = create_top_category_df(main_df)
top_cities_payment = create_top_cities_df(financial_df)
sales_trend_sp = create_sales_trend_df(main_df)
rfm_df = create_rfm_df(main_df)

start_year = pd.to_datetime(start_date).strftime("%Y")
end_year = pd.to_datetime(end_date).strftime("%Y")
year_label = start_year if start_year == end_year else f"{start_year} - {end_year}"

st.header('Dicoding E-Commerce Dashboard :shopping_cart:')

#p1
st.subheader(f"Kategori Produk Terpopuler di Kota Sao Paulo ({year_label})")
top_10_cat = top_category_sp.head(10).copy()
top_10_cat = top_10_cat.sort_values(by=('order_id','count'), ascending=True)

fig, ax = plt.subplots(figsize=(10, 6))

ax.barh(
    y=top_10_cat.index,
    width=top_10_cat[('order_id', 'count')],
    color='cornflowerblue',
    edgecolor='black',
    linewidth=0.5
)
ax.set_xlabel('Jumlah Order', fontstyle='italic', labelpad=12)
ax.set_ylabel('Kategori Produk', fontstyle='italic', labelpad=12)
ax.grid(axis='x', linestyle='--', alpha=0.7)
plt.tight_layout()
st.pyplot(fig)

#p2
st.subheader(f"Kota Yang Memberikan Pendapatan Tertinggi ({year_label})")
top_10_cities = top_cities_payment.sort_values(by='total_revenue_actual', ascending=False).head(10).copy()
top_10_cities = top_10_cities.sort_values(by='total_revenue_actual', ascending=True)

fig, ax = plt.subplots(figsize=(10, 6))

ax.barh(
    y=top_10_cities.index,
    width=top_10_cities['total_revenue_actual'],
    color='cornflowerblue',
    edgecolor='black',
    linewidth=0.5
)
ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('R${x:,.0f}'))
ax.set_xlabel('Total Pendapatan Aktual', fontstyle='italic', labelpad=12)
ax.set_ylabel('Kota Pelanggan', fontstyle='italic', labelpad=12)
ax.grid(axis='x', linestyle='--', alpha=0.7)
plt.tight_layout()
st.pyplot(fig)

#p3
st.subheader(f"Tren Penjualan Produk di Sao Paulo State ({year_label})")
fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(
    sales_trend_sp['order_month'],
    sales_trend_sp['total_product_revenue'],
    marker='o',
    linestyle='-',
    color='cornflowerblue',
    linewidth=2,
    markersize=6
)
ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('R${x:,.0f}'))
ax.set_xlabel('Bulan', fontstyle='italic', labelpad=12)
ax.set_ylabel('Total Product Revenue', fontstyle='italic', labelpad=12)
plt.xticks(rotation=45)
ax.grid(axis='both', linestyle='--', alpha=0.7)
plt.tight_layout()
st.pyplot(fig)

# RFM
st.subheader('Best Customers Based on RFM Parameters (customer_unique_id)')

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)
 
with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_monetary = format_currency(rfm_df.monetary.mean(), "BRL", locale='pt_BR') 
    st.metric("Average Monetary", value=avg_monetary)

fig, ax = plt.subplots(nrows=3, ncols=1, figsize=(12, 18))

# Recency
sns.barplot(
    x='recency',
    y='customer_unique_id',
    data=rfm_df.sort_values(by=['recency','monetary', 'frequency'], ascending=[True, False, False]).head(5),
    color='cornflowerblue',
    edgecolor='black',
    linewidth=.5,
    ax=ax[0]
)
ax[0].set_ylabel(None)
ax[0].set_xlabel('Recency (Days)', fontsize=18, fontstyle='italic')
ax[0].set_title('5 Customer dengan Recency Tertinggi', loc='center', fontsize=22, fontweight='regular')
ax[0].tick_params(axis='y', labelsize=14)
ax[0].tick_params(axis='x', labelsize=14)

# Frequency
sns.barplot(
    x='frequency',
    y='customer_unique_id',
    data=rfm_df.sort_values(by=['frequency', 'monetary', 'recency'], ascending=[False, False, True]).head(5),
    color='cornflowerblue',
    edgecolor='black',
    linewidth=.5,
    ax=ax[1]
)
ax[1].set_ylabel(None)
ax[1].set_xlabel('Frequency (Orders)', fontsize=18, fontstyle='italic')
ax[1].set_title('5 Customer dengan Frequency Tertinggi', loc='center', fontsize=22, fontweight='regular')
ax[1].tick_params(axis='y', labelsize=14)
ax[1].tick_params(axis='x', labelsize=14)

# Monetary
sns.barplot(
    x='monetary',
    y='customer_unique_id',
    data=rfm_df.sort_values(by=['monetary', 'frequency', 'recency'], ascending=[False, False, True]).head(5),
    color='cornflowerblue',
    edgecolor='black',
    linewidth=.5,
    ax=ax[2]
)
ax[2].set_ylabel(None)
ax[2].set_xlabel('Monetary (R$)', fontsize=18, fontstyle='italic')
ax[2].set_title('5 Customer dengan Monetary Tertinggi', loc='center', fontsize=22, fontweight='regular')
ax[2].tick_params(axis='y', labelsize=14)
ax[2].tick_params(axis='x', labelsize=14)

plt.tight_layout(h_pad=5.0)
st.pyplot(fig)
st.caption('Copyright (c) Muhammad Sidiq Fathurochman 2026')
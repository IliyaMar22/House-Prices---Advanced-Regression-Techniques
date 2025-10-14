"""Interactive Streamlit dashboard for financial review."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
import json

# Page config
st.set_page_config(
    page_title="Financial Review Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.big-metric {
    font-size: 2rem;
    font-weight: bold;
    color: #1f77b4;
}
.positive {
    color: #2ca02c;
}
.negative {
    color: #d62728;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data(data_dir: Path):
    """Load all data files from output directory."""
    data = {}
    
    # Load mapped data
    parquet_path = data_dir / "mapped_data.parquet"
    if parquet_path.exists():
        data['mapped_data'] = pd.read_parquet(parquet_path)
    
    # Load summary Excel
    excel_path = data_dir / "summary.xlsx"
    if excel_path.exists():
        data['summary'] = pd.read_excel(excel_path, sheet_name='Summary', header=None)
        data['monthly_trends'] = pd.read_excel(excel_path, sheet_name='Monthly Trends')
        
        try:
            data['ar_aging'] = pd.read_excel(excel_path, sheet_name='AR Aging')
        except:
            pass
        
        try:
            data['ap_aging'] = pd.read_excel(excel_path, sheet_name='AP Aging')
        except:
            pass
    
    # Load commentary
    commentary_path = data_dir / "commentary.txt"
    if commentary_path.exists():
        with open(commentary_path, 'r') as f:
            data['commentary'] = f.read()
    
    # Load data quality report
    quality_path = data_dir / "data_quality_report.json"
    if quality_path.exists():
        with open(quality_path, 'r') as f:
            data['quality'] = json.load(f)
    
    return data


def main():
    st.title("📊 Financial Review Dashboard")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.title("Configuration")
    
    # Get data directory from command line or file selector
    if len(sys.argv) > 1 and '--data-dir' in sys.argv:
        idx = sys.argv.index('--data-dir')
        data_dir = Path(sys.argv[idx + 1])
    else:
        data_dir_str = st.sidebar.text_input(
            "Data Directory",
            value="reports/latest",
            help="Path to the report output directory"
        )
        data_dir = Path(data_dir_str)
    
    if not data_dir.exists():
        st.error(f"❌ Data directory not found: {data_dir}")
        st.info("Please run the pipeline first to generate reports.")
        return
    
    # Load data
    try:
        data = load_data(data_dir)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return
    
    if 'mapped_data' not in data:
        st.error("No mapped data found. Please run the pipeline first.")
        return
    
    df = data['mapped_data']
    
    # Sidebar filters
    st.sidebar.markdown("### Filters")
    
    # Date range filter
    min_date = df['posting_date'].min()
    max_date = df['posting_date'].max()
    
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Type filter
    types = ['All'] + sorted(df['type'].unique().tolist())
    selected_type = st.sidebar.selectbox("Type", types)
    
    # Bucket filter
    buckets = ['All'] + sorted(df['bucket'].unique().tolist())
    selected_bucket = st.sidebar.selectbox("Bucket", buckets)
    
    # Apply filters
    filtered_df = df.copy()
    
    if len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['posting_date'] >= pd.to_datetime(date_range[0])) &
            (filtered_df['posting_date'] <= pd.to_datetime(date_range[1]))
        ]
    
    if selected_type != 'All':
        filtered_df = filtered_df[filtered_df['type'] == selected_type]
    
    if selected_bucket != 'All':
        filtered_df = filtered_df[filtered_df['bucket'] == selected_bucket]
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Overview",
        "💰 P&L Analysis",
        "📅 AR/AP Aging",
        "🔍 Drill Down",
        "📝 Commentary"
    ])
    
    # Tab 1: Overview
    with tab1:
        st.header("Financial Overview")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        revenue = filtered_df[filtered_df['type'] == 'Revenue']['amount'].sum()
        opex = filtered_df[filtered_df['type'] == 'OPEX']['amount'].sum()
        payroll = filtered_df[filtered_df['type'] == 'Payroll']['amount'].sum()
        net_profit = revenue - opex - payroll
        
        with col1:
            st.metric("Total Revenue", f"€{revenue/1000:.1f}K")
        
        with col2:
            st.metric("Total OPEX", f"€{opex/1000:.1f}K")
        
        with col3:
            st.metric("Total Payroll", f"€{payroll/1000:.1f}K")
        
        with col4:
            margin = (net_profit / revenue * 100) if revenue != 0 else 0
            st.metric("Net Profit", f"€{net_profit/1000:.1f}K", f"{margin:.1f}%")
        
        st.markdown("---")
        
        # Monthly trends
        if 'monthly_trends' in data:
            st.subheader("Monthly Trends")
            
            monthly = data['monthly_trends']
            
            fig = go.Figure()
            
            if 'revenue' in monthly.columns:
                fig.add_trace(go.Scatter(
                    x=monthly['year_month'],
                    y=monthly['revenue'],
                    mode='lines+markers',
                    name='Revenue',
                    line=dict(color='#2ca02c', width=2)
                ))
            
            if 'opex' in monthly.columns:
                fig.add_trace(go.Scatter(
                    x=monthly['year_month'],
                    y=monthly['opex'],
                    mode='lines+markers',
                    name='OPEX',
                    line=dict(color='#d62728', width=2)
                ))
            
            fig.update_layout(
                title="Revenue & OPEX Trends",
                xaxis_title="Month",
                yaxis_title="Amount (€)",
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Transaction volume
        st.subheader("Transaction Volume by Type")
        
        type_counts = filtered_df['type'].value_counts()
        
        fig = px.bar(
            x=type_counts.index,
            y=type_counts.values,
            labels={'x': 'Type', 'y': 'Transaction Count'},
            color=type_counts.values,
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Tab 2: P&L Analysis
    with tab2:
        st.header("P&L Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Amount by Type")
            
            type_amounts = filtered_df.groupby('type')['amount'].sum().abs().sort_values(ascending=False)
            
            fig = px.pie(
                values=type_amounts.values,
                names=type_amounts.index,
                title="Distribution by Type"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Top 10 Buckets")
            
            bucket_amounts = filtered_df.groupby('bucket')['amount'].sum().abs().nlargest(10)
            
            fig = px.bar(
                x=bucket_amounts.values,
                y=bucket_amounts.index,
                orientation='h',
                labels={'x': 'Amount (€)', 'y': 'Bucket'},
                color=bucket_amounts.values,
                color_continuous_scale='Reds'
            )
            
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        # Time series by bucket
        st.subheader("Bucket Trends Over Time")
        
        top_buckets = filtered_df.groupby('bucket')['amount'].sum().abs().nlargest(5).index.tolist()
        
        selected_buckets = st.multiselect(
            "Select buckets to display",
            options=top_buckets,
            default=top_buckets[:3]
        )
        
        if selected_buckets:
            bucket_monthly = filtered_df[filtered_df['bucket'].isin(selected_buckets)].groupby(
                ['year_month', 'bucket']
            )['amount'].sum().reset_index()
            
            fig = px.line(
                bucket_monthly,
                x='year_month',
                y='amount',
                color='bucket',
                title="Selected Buckets Over Time"
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Tab 3: AR/AP Aging
    with tab3:
        st.header("Receivables & Payables Aging")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Accounts Receivable Aging")
            
            if 'ar_aging' in data:
                ar_aging = data['ar_aging']
                
                fig = px.bar(
                    ar_aging,
                    x='aging_bucket',
                    y='outstanding_amount',
                    title="AR Aging Distribution",
                    labels={'outstanding_amount': 'Amount (€)', 'aging_bucket': 'Aging Bucket'},
                    color='outstanding_amount',
                    color_continuous_scale='Oranges'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(ar_aging, use_container_width=True)
            else:
                st.info("No AR aging data available")
        
        with col2:
            st.subheader("Accounts Payable Aging")
            
            if 'ap_aging' in data:
                ap_aging = data['ap_aging']
                
                fig = px.bar(
                    ap_aging,
                    x='aging_bucket',
                    y='outstanding_amount',
                    title="AP Aging Distribution",
                    labels={'outstanding_amount': 'Amount (€)', 'aging_bucket': 'Aging Bucket'},
                    color='outstanding_amount',
                    color_continuous_scale='Purples'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(ap_aging, use_container_width=True)
            else:
                st.info("No AP aging data available")
        
        # Overdue items
        st.subheader("Overdue Items")
        
        overdue = filtered_df[filtered_df['is_overdue'] == True]
        
        if len(overdue) > 0:
            st.write(f"Total overdue items: {len(overdue)}")
            st.write(f"Total overdue amount: €{overdue['open_amount'].sum()/1000:.1f}K")
            
            # Top overdue parties
            if 'customer_vendor' in overdue.columns:
                top_overdue = overdue.groupby('customer_vendor')['open_amount'].sum().abs().nlargest(10)
                
                fig = px.bar(
                    x=top_overdue.values,
                    y=top_overdue.index,
                    orientation='h',
                    title="Top 10 Overdue Parties",
                    labels={'x': 'Overdue Amount (€)', 'y': 'Party'}
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("✅ No overdue items")
    
    # Tab 4: Drill Down
    with tab4:
        st.header("Transaction Drill Down")
        
        st.write(f"Showing {len(filtered_df):,} transactions")
        
        # Display options
        show_columns = st.multiselect(
            "Select columns to display",
            options=filtered_df.columns.tolist(),
            default=['posting_date', 'doc_id', 'gl_account', 'bucket', 'type', 'amount', 'customer_vendor']
        )
        
        # Export button
        csv = filtered_df[show_columns].to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name="filtered_transactions.csv",
            mime="text/csv"
        )
        
        # Display dataframe
        st.dataframe(
            filtered_df[show_columns].sort_values('posting_date', ascending=False),
            use_container_width=True,
            height=500
        )
    
    # Tab 5: Commentary
    with tab5:
        st.header("Automated Commentary & Insights")
        
        if 'commentary' in data:
            st.text_area(
                "Executive Summary",
                value=data['commentary'],
                height=600,
                disabled=True
            )
        else:
            st.info("No commentary available")
        
        # Data quality
        if 'quality' in data:
            st.subheader("Data Quality Report")
            
            quality = data['quality']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Quality Score", f"{quality.get('quality_score', 0):.2f}")
            
            with col2:
                st.metric("Warnings", quality.get('warnings', []))
            
            with col3:
                st.metric("Unmapped GLs", quality.get('unmapped_gls_count', 0))
            
            if quality.get('warnings'):
                with st.expander("View Warnings"):
                    for warning in quality['warnings']:
                        st.warning(warning)


if __name__ == '__main__':
    main()


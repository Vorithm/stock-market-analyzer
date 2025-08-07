import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Expense Analyzer",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">💰 Expense Analyzer</h1>', unsafe_allow_html=True)

# Initialize session state
if 'data_updated' not in st.session_state:
    st.session_state.data_updated = False

# Predefined categories
PREDEFINED_CATEGORIES = [
    'Groceries', 'Utilities', 'Rent', 'Entertainment', 'Transportation',
    'Dining', 'Shopping', 'Healthcare', 'Education', 'Insurance',
    'Investment', 'Travel', 'Personal Care', 'Home & Garden', 'Other'
]

# File upload section
st.header("📁 Upload Bank Statement")
uploaded_file = st.file_uploader(
    "Choose a CSV file",
    type=['csv'],
    help="Upload your bank statement CSV file"
)

if uploaded_file is not None:
    # Display file details
    st.success(f"✅ File uploaded: {uploaded_file.name}")
    
    # Launch analysis button
    if st.button("🚀 Launch Smart Analysis", type="primary"):
        with st.spinner("Processing your data..."):
            # Upload file to backend
            files = {'file': uploaded_file}
            response = requests.post("http://localhost:5001/api/upload_csv", files=files)
            
            if response.status_code == 200:
                result = response.json()
                st.success(f"✅ {result['message']}")
                st.info(f"📊 Processed {result['total_transactions']} transactions")
                
                # Show category distribution
                if result['categories']:
                    st.subheader("📋 Initial Category Distribution")
                    category_df = pd.DataFrame([
                        {'Category': cat, 'Count': count}
                        for cat, count in result['categories'].items()
                    ])
                    
                    # Create a bar chart
                    fig = px.bar(
                        category_df,
                        x='Category',
                        y='Count',
                        title='Transaction Categories',
                        color='Count',
                        color_continuous_scale='viridis'
                    )
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                
                st.session_state.data_updated = True
                st.rerun()
            else:
                error_msg = response.json().get('error', 'Unknown error occurred')
                st.error(f"❌ Error processing file: {error_msg}")

# Main analysis section
if st.session_state.data_updated or st.button("🔄 Refresh Data"):
    st.header("📊 Financial Overview")
    
    # Get transactions data
    response = requests.get("http://localhost:5001/api/get_transactions")
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        
        if not df.empty:
            # Basic metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_transactions = len(df)
                st.metric("Total Transactions", total_transactions)
            
            with col2:
                total_amount = df['Amount'].sum()
                st.metric("Net Amount", f"₹{total_amount:,.2f}")
            
            with col3:
                expenses = df[df['Amount'] < 0]['Amount'].sum()
                st.metric("Total Expenses", f"₹{abs(expenses):,.2f}")
            
            with col4:
                income = df[df['Amount'] > 0]['Amount'].sum()
                st.metric("Total Income", f"₹{income:,.2f}")
            
            # Category analysis
            st.subheader("📈 Category Analysis")
            
            # Get expense summary
            summary_response = requests.get("http://localhost:5001/api/get_expense_summary")
            if summary_response.status_code == 200:
                summary_data = summary_response.json()
                
                if summary_data:
                    # Create category breakdown
                    category_df = pd.DataFrame(summary_data)
                    
                    # Calculate percentages
                    total_expense = category_df['Amount'].sum()
                    category_df['Percentage'] = (category_df['Amount'] / total_expense * 100).round(1)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Pie chart
                        fig_pie = px.pie(
                            category_df,
                            values='Amount',
                            names='Category',
                            title='Expense Distribution by Category'
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)
                    
                    with col2:
                        # Bar chart
                        fig_bar = px.bar(
                            category_df,
                            x='Category',
                            y='Amount',
                            title='Expense Amount by Category',
                            color='Amount',
                            color_continuous_scale='viridis'
                        )
                        fig_bar.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig_bar, use_container_width=True)
                    
                    # Category table
                    st.subheader("📋 Category Details")
                    category_df['Amount (₹)'] = category_df['Amount'].apply(lambda x: f"₹{x:,.2f}")
                    category_df['Percentage'] = category_df['Percentage'].apply(lambda x: f"{x:.1f}%")
                    
                    display_cols = ['Category', 'Amount (₹)', 'Percentage', 'Transaction_Count']
                    st.dataframe(
                        category_df[display_cols],
                        use_container_width=True,
                        hide_index=True
                    )
            
            # Transaction list
            st.subheader("📋 All Transactions")
            
            # Add amount formatting
            display_df = df.copy()
            if 'Amount' in display_df.columns:
                display_df['Amount (₹)'] = display_df['Amount'].apply(lambda x: f"₹{x:,.2f}")
            
            # Select columns to display
            display_cols = ['Date', 'Description', 'Amount (₹)', 'Category']
            available_cols = [col for col in display_cols if col in display_df.columns]
            
            st.dataframe(
                display_df[available_cols],
                use_container_width=True,
                hide_index=True
            )
            
            # Manual categorization section
            st.header("✏️ Manual Categorization")
            
            # Get "Other" transactions for manual categorization
            other_response = requests.get("http://localhost:5001/api/get_other_transactions")
            if other_response.status_code == 200:
                other_data = other_response.json()
                other_df = pd.DataFrame(other_data)
                
                if other_df.empty:
                    st.success("✅ All transactions have been categorized!")
                else:
                    st.write(f"📊 Found {len(other_df)} uncategorized transactions")
                    
                    # Display other transactions
                    other_display = other_df.copy()
                    if 'Amount' in other_display.columns:
                        other_display['Amount (₹)'] = other_display['Amount'].apply(lambda x: f"₹{x:,.2f}")
                    
                    display_cols = ['Date', 'Description', 'Amount (₹)', 'Category']
                    available_cols = [col for col in display_cols if col in other_display.columns]
                    
                    st.dataframe(
                        other_display[available_cols],
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Enhanced categorization form
                    st.subheader("📝 Update Transaction Category")
                    
                    # Tab-based interface for different categorization options
                    cat_tab1, cat_tab2 = st.tabs(["🔄 Quick Categorization", "➕ Add Custom Category"])
                    
                    with cat_tab1:
                        with st.form("categorize_form"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # Transaction selection
                                transaction_options = []
                                for idx, row in other_df.iterrows():
                                    desc = str(row['Description'])[:50] + "..." if len(str(row['Description'])) > 50 else str(row['Description'])
                                    amount = f"₹{abs(row['Amount']):,.2f}" if 'Amount' in row else "No amount"
                                    transaction_options.append(f"ID {row['id']}: {desc} - {amount}")
                                
                                selected_transaction = st.selectbox(
                                    "Select Transaction to Categorize",
                                    options=range(len(transaction_options)),
                                    format_func=lambda x: transaction_options[x]
                                )
                                
                                # Get the actual row index from the DataFrame
                                actual_row_idx = other_df.index[selected_transaction]
                                selected_id = other_df.loc[actual_row_idx, 'id']
                            
                            with col2:
                                # Category selection
                                new_category = st.selectbox(
                                    "Select Category",
                                    options=PREDEFINED_CATEGORIES,
                                    help="Choose from predefined categories"
                                )
                                
                                # Custom description for the category
                                custom_description = st.text_input(
                                    "Custom Description (optional)",
                                    help="Add a specific description for this transaction",
                                    placeholder="e.g., 'Medical checkup', 'Birthday gift', etc."
                                )
                            
                            # Submit button
                            submitted = st.form_submit_button("🔄 Update Category", type="primary")
                            
                            if submitted:
                                with st.spinner("Updating category..."):
                                    update_data = {
                                        'id': int(selected_id),
                                        'category': new_category,
                                        'custom_name': custom_description
                                    }
                                    
                                    update_response = requests.post("http://localhost:5001/api/update_category", json=update_data)
                                    
                                    if update_response.status_code == 200:
                                        success_msg = f"✅ Updated transaction ID {selected_id} to '{new_category}'"
                                        if custom_description:
                                            success_msg += f" with description '{custom_description}'"
                                        st.success(success_msg)
                                        st.session_state.data_updated = True
                                        st.rerun()
                                    else:
                                        error_msg = update_response.json().get('error', 'Unknown error')
                                        st.error(f"❌ Failed to update category: {error_msg}")
                    
                    with cat_tab2:
                        st.write("Create a new custom category and optionally apply it to similar transactions:")
                        
                        with st.form("custom_category_form"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # Transaction selection
                                transaction_options = []
                                for idx, row in other_df.iterrows():
                                    desc = str(row['Description'])[:50] + "..." if len(str(row['Description'])) > 50 else str(row['Description'])
                                    amount = f"₹{abs(row['Amount']):,.2f}" if 'Amount' in row else "No amount"
                                    transaction_options.append(f"ID {row['id']}: {desc} - {amount}")
                                
                                selected_transaction_custom = st.selectbox(
                                    "Select Transaction for Custom Category",
                                    options=range(len(transaction_options)),
                                    format_func=lambda x: transaction_options[x],
                                    key="custom_transaction_select"
                                )
                                
                                # Get the actual row index from the DataFrame
                                actual_row_idx_custom = other_df.index[selected_transaction_custom]
                                selected_id_custom = other_df.loc[actual_row_idx_custom, 'id']
                                
                                # Custom category name
                                custom_category_name = st.text_input(
                                    "Custom Category Name",
                                    help="Enter a name for your custom category",
                                    placeholder="e.g., 'Medical Expenses', 'Pet Care', 'Donations'"
                                )
                            
                            with col2:
                                # Keywords for similar transactions
                                st.write("**Auto-categorize similar transactions:**")
                                keywords_input = st.text_area(
                                    "Keywords (one per line)",
                                    help="Enter keywords to automatically categorize similar transactions",
                                    placeholder="APOLLO\nHOSPITAL\nMEDICAL\nDOCTOR",
                                    height=100
                                )
                                
                                # Preview of transactions that would be affected
                                if keywords_input:
                                    keywords = [k.strip() for k in keywords_input.split('\n') if k.strip()]
                                    if keywords:
                                        # Get all transactions data
                                        all_response = requests.get("http://localhost:5001/api/get_transactions")
                                        if all_response.status_code == 200:
                                            all_data = all_response.json()
                                            all_df = pd.DataFrame(all_data)
                                            
                                            # Find matching transactions
                                            matching_mask = pd.Series([False] * len(all_df))
                                            for keyword in keywords:
                                                matching_mask |= all_df['Description'].str.contains(keyword, case=False, na=False)
                                            
                                            matching_count = matching_mask.sum()
                                            st.info(f"📊 {matching_count} transactions would be categorized with these keywords")
                            
                            # Submit button
                            submitted_custom = st.form_submit_button("➕ Add Custom Category", type="primary")
                            
                            if submitted_custom:
                                if not custom_category_name:
                                    st.error("❌ Please enter a custom category name")
                                else:
                                    with st.spinner("Adding custom category..."):
                                        keywords = [k.strip() for k in keywords_input.split('\n') if k.strip()] if keywords_input else []
                                        
                                        custom_data = {
                                            'id': int(selected_id_custom),
                                            'custom_category': custom_category_name,
                                            'description_keywords': keywords
                                        }
                                        
                                        custom_response = requests.post("http://localhost:5001/api/add_custom_category", json=custom_data)
                                        
                                        if custom_response.status_code == 200:
                                            st.success(custom_response.json()['message'])
                                            st.session_state.data_updated = True
                                            st.rerun()
                                        else:
                                            error_msg = custom_response.json().get('error', 'Unknown error')
                                            st.error(f"❌ Failed to add custom category: {error_msg}")
            else:
                st.error("❌ Could not retrieve 'Other' transactions")
        else:
            error_msg = response.json().get('error', 'Unknown error occurred')
            st.error(f"❌ Failed to retrieve transactions: {error_msg}")

# Simplified Sidebar
st.sidebar.header("ℹ️ Information")
st.sidebar.info("""
**Simple Expense Analyzer Features:**
- 📁 Upload CSV bank statements
- 🏷️ Smart expense categorization
- 📊 Financial overview & analysis
- ✏️ Manual category correction
- ➕ Custom category creation
- 🔄 Real-time data processing

**Supported Categories:**
- 🥬 Groceries
- 🏠 Utilities  
- 🏘️ Rent
- 🎬 Entertainment
- 🚗 Transportation
- 🍽️ Dining
- 🛒 Shopping
- 🏥 Healthcare
- 🎓 Education
- 🛡️ Insurance
- 💰 Investment
- ✈️ Travel
- 💅 Personal Care
- 🏡 Home & Garden
- ❓ Other (with custom names)
""")

st.sidebar.header("📋 Instructions")
st.sidebar.markdown("""
1. **Upload** your bank statement CSV file
2. **Click** 'Launch Smart Analysis' to process
3. **Review** the financial overview
4. **Use Manual Categorization** for uncategorized transactions
5. **Explore** category breakdowns and insights
""")

st.sidebar.header("🔧 CSV Format Support")
st.sidebar.info("""
**Format 1:** Standard
- Date, Description, Amount

**Format 2:** Bank Statement
- Date, Narration, Withdrawal Amt., Deposit Amt.

**Note:** The app handles both formats automatically.
""") 
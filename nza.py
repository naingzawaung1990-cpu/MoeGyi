import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json
import html

# ============================================
# GOOGLE SHEETS SETUP
# ============================================
# 1. Google Cloud Console: https://console.cloud.google.com/
# 2. Project ဖန်တီး → APIs & Services → Enable APIs → "Google Sheets API" enable
# 3. Credentials → Create Credentials → Service Account → JSON key download
# 4. JSON file ကို "credentials.json" အမည်နဲ့ ဒီ folder ထဲထည့်
# 5. Google Sheet ဖန်တီးပြီး Service Account email ကို Editor အဖြစ် share ပေး
# ============================================

# Page config
st.set_page_config(
    page_title="NZA - Multi Store Menu",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Google Sheets connection
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Credentials file path
CREDENTIALS_FILE = "credentials.json"

# Your Google Sheet URL or ID
# Sheet ဖန်တီးပြီးရင် ဒီမှာ ထည့်ပါ
SPREADSHEET_ID = "1jENS6aSpQbriTPGA1ZSx9GVvaLOidlTxEWy59OCGgmU"

@st.cache_resource
def get_gsheet_connection():
    """Google Sheets connection - supports both local file and Streamlit Secrets"""
    import os
    
    # Try Streamlit Secrets first (for Streamlit Cloud deployment)
    try:
        if hasattr(st, 'secrets') and len(st.secrets) > 0 and 'gcp_service_account' in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            client = gspread.authorize(creds)
            return client
    except Exception:
        pass  # No secrets file, fall back to local credentials
    
    # Fall back to local credentials.json file (for local development)
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        creds_path = os.path.join(script_dir, CREDENTIALS_FILE)
        
        if not os.path.exists(creds_path):
            st.error(f"❌ credentials.json မတွေ့ပါ: {creds_path}")
            return None
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"❌ Connection error: {e}")
        return None
def get_or_create_worksheet(spreadsheet, name, headers):
    """Worksheet ရှိရင်ယူ၊ မရှိရင်ဖန်တီး"""
    try:
        worksheet = spreadsheet.worksheet(name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=name, rows=1000, cols=20)
        worksheet.append_row(headers)
    return worksheet

@st.cache_data(ttl=60)  # Cache for 60 seconds
def load_stores(_spreadsheet):
    """ဆိုင်စာရင်း load"""
    ws = get_or_create_worksheet(_spreadsheet, "Stores", 
        ["store_id", "store_name", "admin_key", "logo", "subtitle"])
    data = ws.get_all_records()
    return data

@st.cache_data(ttl=60)
def load_categories(_spreadsheet, store_id):
    """Categories load"""
    ws = get_or_create_worksheet(_spreadsheet, "Categories",
        ["store_id", "category_name"])
    data = ws.get_all_records()
    return [d for d in data if d.get('store_id') == store_id]

@st.cache_data(ttl=60)
def load_menu_items(_spreadsheet, store_id):
    """Menu items load"""
    ws = get_or_create_worksheet(_spreadsheet, "MenuItems",
        ["store_id", "item_id", "name", "price", "category"])
    data = ws.get_all_records()
    return [d for d in data if d.get('store_id') == store_id]

def clear_all_cache():
    """Clear all cached data"""
    load_stores.clear()
    load_categories.clear()
    load_menu_items.clear()

def save_store(spreadsheet, store_data):
    """ဆိုင်အသစ်သိမ်း"""
    ws = get_or_create_worksheet(spreadsheet, "Stores",
        ["store_id", "store_name", "admin_key", "logo", "subtitle"])
    ws.append_row([
        store_data['store_id'],
        store_data['store_name'],
        store_data['admin_key'],
        store_data.get('logo', '☕'),
        store_data.get('subtitle', 'Food & Drinks')
    ])
    clear_all_cache()

def save_category(spreadsheet, store_id, category_name):
    """Category သိမ်း"""
    ws = get_or_create_worksheet(spreadsheet, "Categories",
        ["store_id", "category_name"])
    ws.append_row([store_id, category_name])
    clear_all_cache()

def save_menu_item(spreadsheet, store_id, item_data):
    """Menu item သိမ်း"""
    ws = get_or_create_worksheet(spreadsheet, "MenuItems",
        ["store_id", "item_id", "name", "price", "category"])
    ws.append_row([
        store_id,
        item_data['item_id'],
        item_data['name'],
        item_data['price'],
        item_data['category']
    ])
    clear_all_cache()

def update_menu_item(spreadsheet, store_id, item_id, new_data):
    """Menu item update"""
    ws = spreadsheet.worksheet("MenuItems")
    data = ws.get_all_records()
    for idx, row in enumerate(data, start=2):  # row 1 is header
        if row.get('store_id') == store_id and row.get('item_id') == item_id:
            ws.update(f'C{idx}:E{idx}', [[new_data['name'], new_data['price'], new_data['category']]])
            break
    clear_all_cache()

def delete_menu_item(spreadsheet, store_id, item_id):
    """Menu item delete"""
    ws = spreadsheet.worksheet("MenuItems")
    data = ws.get_all_records()
    for idx, row in enumerate(data, start=2):
        if row.get('store_id') == store_id and row.get('item_id') == item_id:
            ws.delete_rows(idx)
            break
    clear_all_cache()

def delete_category(spreadsheet, store_id, category_name):
    """Category delete"""
    ws = spreadsheet.worksheet("Categories")
    data = ws.get_all_records()
    for idx, row in enumerate(data, start=2):
        if row.get('store_id') == store_id and row.get('category_name') == category_name:
            ws.delete_rows(idx)
            break
    clear_all_cache()

def update_store(spreadsheet, store_id, new_data):
    """Store update"""
    ws = spreadsheet.worksheet("Stores")
    data = ws.get_all_records()
    for idx, row in enumerate(data, start=2):
        if row.get('store_id') == store_id:
            ws.update(f'B{idx}:E{idx}', [[
                new_data['store_name'],
                new_data['admin_key'],
                new_data.get('logo', '☕'),
                new_data.get('subtitle', 'Food & Drinks')
            ]])
            break
    clear_all_cache()

def delete_store(spreadsheet, store_id):
    """Store delete - ဆိုင်နဲ့ သူ့ categories, items တွေအကုန်ဖျက်"""
    # Delete store
    ws = spreadsheet.worksheet("Stores")
    data = ws.get_all_records()
    for idx, row in enumerate(data, start=2):
        if row.get('store_id') == store_id:
            ws.delete_rows(idx)
            break
    
    # Delete categories
    try:
        ws_cat = spreadsheet.worksheet("Categories")
        data_cat = ws_cat.get_all_records()
        rows_to_delete = []
        for idx, row in enumerate(data_cat, start=2):
            if row.get('store_id') == store_id:
                rows_to_delete.append(idx)
        for idx in reversed(rows_to_delete):
            ws_cat.delete_rows(idx)
    except:
        pass
    
    # Delete menu items
    try:
        ws_items = spreadsheet.worksheet("MenuItems")
        data_items = ws_items.get_all_records()
        rows_to_delete = []
        for idx, row in enumerate(data_items, start=2):
            if row.get('store_id') == store_id:
                rows_to_delete.append(idx)
        for idx in reversed(rows_to_delete):
            ws_items.delete_rows(idx)
    except:
        pass
    
    clear_all_cache()

# ============================================
# SESSION STATE
# ============================================
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'current_store' not in st.session_state:
    st.session_state.current_store = None
if 'editing_id' not in st.session_state:
    st.session_state.editing_id = None
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'editing_store' not in st.session_state:
    st.session_state.editing_store = None
if 'confirm_delete_store' not in st.session_state:
    st.session_state.confirm_delete_store = None

# Super Admin key (ဆိုင်အကုန်ကြည့်ချင်တဲ့ boss အတွက်)
SUPER_ADMIN_KEY = "superadmin123"

# ============================================
# MAIN APP
# ============================================
def main():
    # Check Google Sheets connection
    client = get_gsheet_connection()
    
    if client is None:
        st.error("⚠️ Google Sheets ချိတ်ဆက်မှု မအောင်မြင်ပါ။")
        st.markdown("""
        ### Setup လုပ်နည်း:
        
        1. **Google Cloud Console** သွားပါ: https://console.cloud.google.com/
        2. **Project အသစ်** ဖန်တီးပါ
        3. **APIs & Services** → **Enable APIs** → **Google Sheets API** enable လုပ်ပါ
        4. **Credentials** → **Create Credentials** → **Service Account** ဖန်တီးပါ
        5. **Keys** tab → **Add Key** → **JSON** → Download
        6. Download ရတဲ့ JSON file ကို **`credentials.json`** အမည်ပေးပြီး ဒီ folder ထဲထည့်ပါ
        7. **Google Sheet** တစ်ခုဖန်တီးပြီး Service Account email ကို **Editor** share ပေးပါ
        8. Sheet URL ထဲက ID ကို code ထဲက `SPREADSHEET_ID` မှာ ထည့်ပါ
        
        **Sheet URL ဥပမာ:**
        ```
        https://docs.google.com/spreadsheets/d/ABC123XYZ/edit
        ```
        `ABC123XYZ` က Spreadsheet ID ပါ။
        """)
        return
    
    try:
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
    except Exception as e:
        if "YOUR_SPREADSHEET_ID_HERE" in SPREADSHEET_ID:
            st.warning("⚠️ SPREADSHEET_ID ထည့်ပေးပါ။ Code ထဲမှာ line 37 မှာ ထည့်ရမယ်။")
        else:
            st.error(f"Sheet ဖွင့်မရပါ: {e}")
        return
    
    # Load stores
    stores = load_stores(spreadsheet)
    
    # ============================================
    # SIDEBAR
    # ============================================
    st.sidebar.title("☕ NZA Menu System")
    
    # Check URL parameter for specific store
    query_params = st.query_params
    url_store_id = query_params.get("store", None)
    
    # Store selection
    current_store = None
    store_from_url = False
    
    if stores:
        store_options = {s['store_name']: s for s in stores}
        store_by_id = {s['store_id']: s for s in stores}
        
        # If URL has store parameter, use that store
        if url_store_id and url_store_id in store_by_id:
            current_store = store_by_id[url_store_id]
            store_from_url = True
            # Only show store selector for admins
            if st.session_state.is_admin:
                selected_store_name = st.sidebar.selectbox(
                    "🏪 ဆိုင်ရွေးပါ",
                    options=list(store_options.keys()),
                    index=list(store_options.keys()).index(current_store['store_name'])
                )
                current_store = store_options[selected_store_name]
            else:
                # Customer view - show store name but no selector
                st.sidebar.markdown(f"### 🏪 {current_store['store_name']}")
        else:
            # No URL parameter - show selector for everyone
            selected_store_name = st.sidebar.selectbox(
                "🏪 ဆိုင်ရွေးပါ",
                options=list(store_options.keys())
            )
            current_store = store_options[selected_store_name]
        
        st.session_state.current_store = current_store
    else:
        st.sidebar.info("ဆိုင်မရှိသေးပါ။ အောက်မှာ ထည့်ပါ။")
    
    st.sidebar.divider()
    
    # Admin Login - hide for customer view (URL with store parameter)
    if not st.session_state.is_admin:
        # Show admin login in expander (collapsed by default for customers)
        if store_from_url:
            with st.sidebar.expander("🔐 Admin Login", expanded=False):
                admin_key = st.text_input("Password", type="password", key="admin_pwd")
                if st.button("Login", use_container_width=True, key="admin_login"):
                    if admin_key == SUPER_ADMIN_KEY:
                        st.session_state.is_admin = True
                        st.session_state.is_super_admin = True
                        st.rerun()
                    elif current_store and admin_key == current_store.get('admin_key'):
                        st.session_state.is_admin = True
                        st.session_state.is_super_admin = False
                        st.rerun()
                    else:
                        st.error("❌ Password မှားနေပါတယ်။")
        else:
            st.sidebar.subheader("🔐 Admin Login")
            admin_key = st.sidebar.text_input("Password", type="password")
            if st.sidebar.button("Login", use_container_width=True):
                # Check super admin
                if admin_key == SUPER_ADMIN_KEY:
                    st.session_state.is_admin = True
                    st.session_state.is_super_admin = True
                    st.rerun()
                # Check store admin
                elif current_store and admin_key == current_store.get('admin_key'):
                    st.session_state.is_admin = True
                    st.session_state.is_super_admin = False
                    st.rerun()
                else:
                    st.sidebar.error("❌ Password မှားနေပါတယ်။")
    else:
        if st.session_state.get('is_super_admin'):
            st.sidebar.success("👑 Super Admin Mode")
        else:
            st.sidebar.success("👨‍💼 Admin Mode")
        
        if st.sidebar.button("Logout", use_container_width=True):
            st.session_state.is_admin = False
            st.session_state.is_super_admin = False
            st.session_state.editing_id = None
            st.rerun()
    
    # Customer search (when viewing via URL)
    if store_from_url and not st.session_state.is_admin and current_store:
        st.sidebar.subheader("🔍 Menu ရှာဖွေရန်")
        st.session_state.search_query = st.sidebar.text_input(
            "ပစ္စည်းအမည်", 
            value=st.session_state.search_query,
            key="customer_search"
        )
    
    # Admin Controls
    if st.session_state.is_admin:
        st.sidebar.divider()
        
        # Super Admin: Add new store
        if st.session_state.get('is_super_admin'):
            st.sidebar.subheader("🏪 ဆိုင်အသစ်ထည့်ရန်")
            with st.sidebar.form("add_store_form", clear_on_submit=True):
                new_store_id = st.text_input("Store ID *", placeholder="naypyidaw")
                new_store_name = st.text_input("ဆိုင်အမည် *", placeholder="နေပြည်တော်")
                new_admin_key = st.text_input("Admin Password *", placeholder="npt123")
                new_logo = st.text_input("Logo (emoji သို့ image URL)", value="☕", help="☕ သို့ https://example.com/logo.jpg")
                new_subtitle = st.text_input("Subtitle", value="Food & Drinks")
                
                if st.form_submit_button("➕ ဆိုင်ထည့်မည်", use_container_width=True):
                    if new_store_id and new_store_name and new_admin_key:
                        # Clean up logo value
                        clean_logo = new_logo.strip() if new_logo else '☕'
                        if not clean_logo:
                            clean_logo = '☕'
                        
                        save_store(spreadsheet, {
                            'store_id': new_store_id.strip().lower(),
                            'store_name': new_store_name.strip(),
                            'admin_key': new_admin_key.strip(),
                            'logo': clean_logo,
                            'subtitle': new_subtitle.strip() if new_subtitle else 'Food & Drinks'
                        })
                        st.sidebar.success(f"✅ '{new_store_name}' ထည့်ပြီးပါပြီ။")
                        st.rerun()
                    else:
                        st.sidebar.error("⚠️ လိုအပ်တဲ့အချက်များ ဖြည့်ပါ။")
            
            # Edit/Delete current store
            if current_store:
                st.sidebar.divider()
                st.sidebar.subheader("⚙️ ဆိုင်ပြင်ဆင်ရန်")
                
                # Show QR Code Link for this store
                st.sidebar.markdown("**📱 QR Code Link:**")
                store_url = f"?store={current_store['store_id']}"
                st.sidebar.code(store_url, language=None)
                st.sidebar.caption("ဒီ link ကို QR code generator မှာထည့်ပါ။ Customer က scan လုပ်ရင် ဒီဆိုင်ပဲမြင်ရမယ်။")
                
                # Show current logo value for debugging
                current_logo = current_store.get('logo', '☕')
                if current_logo.startswith(('http://', 'https://')):
                    st.sidebar.caption(f"📷 Logo URL: {current_logo[:50]}...")
                else:
                    st.sidebar.caption(f"🎨 Logo: {current_logo}")
                
                if st.session_state.editing_store == current_store['store_id']:
                    # Edit form
                    with st.sidebar.form("edit_store_form"):
                        edit_name = st.text_input("ဆိုင်အမည်", value=current_store['store_name'])
                        edit_key = st.text_input("Admin Password", value=current_store.get('admin_key', ''))
                        edit_logo = st.text_input("Logo (emoji သို့ image URL)", value=current_store.get('logo', '☕'), help="☕ သို့ https://example.com/logo.jpg")
                        edit_subtitle = st.text_input("Subtitle", value=current_store.get('subtitle', 'Food & Drinks'))
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            save_btn = st.form_submit_button("💾 သိမ်း", use_container_width=True)
                        with c2:
                            cancel_btn = st.form_submit_button("❌ ပယ်", use_container_width=True)
                        
                        if save_btn and edit_name.strip():
                            # Clean up logo value - preserve URL or emoji
                            clean_logo = edit_logo.strip() if edit_logo else '☕'
                            if not clean_logo:
                                clean_logo = '☕'
                            
                            update_store(spreadsheet, current_store['store_id'], {
                                'store_name': edit_name.strip(),
                                'admin_key': edit_key.strip(),
                                'logo': clean_logo,
                                'subtitle': edit_subtitle.strip() if edit_subtitle else 'Food & Drinks'
                            })
                            st.sidebar.success(f"✅ သိမ်းပြီးပါပြီ။")
                            st.session_state.editing_store = None
                            st.rerun()
                        if cancel_btn:
                            st.session_state.editing_store = None
                            st.rerun()
                else:
                    col1, col2 = st.sidebar.columns(2)
                    with col1:
                        if st.button("✏️ ပြင်မည်", use_container_width=True, key="edit_store"):
                            st.session_state.editing_store = current_store['store_id']
                            st.rerun()
                    with col2:
                        if st.button("🗑️ ဖျက်မည်", use_container_width=True, key="del_store"):
                            st.session_state.confirm_delete_store = current_store['store_id']
                    
                    # Delete confirmation
                    if st.session_state.get('confirm_delete_store') == current_store['store_id']:
                        st.sidebar.warning(f"⚠️ '{current_store['store_name']}' ကို ဖျက်မှာလား?")
                        st.sidebar.caption("ဆိုင်ရဲ့ categories နဲ့ items အကုန်ပါဖျက်ပါမယ်။")
                        c1, c2 = st.sidebar.columns(2)
                        with c1:
                            if st.button("✅ ဖျက်မယ်", use_container_width=True, key="confirm_del"):
                                delete_store(spreadsheet, current_store['store_id'])
                                st.session_state.confirm_delete_store = None
                                st.rerun()
                        with c2:
                            if st.button("❌ မဖျက်ဘူး", use_container_width=True, key="cancel_del"):
                                st.session_state.confirm_delete_store = None
                                st.rerun()
            
            st.sidebar.divider()
        
        if current_store:
            store_id = current_store['store_id']
            
            # Search
            st.sidebar.subheader("🔍 ရှာဖွေရန်")
            st.session_state.search_query = st.sidebar.text_input(
                "ပစ္စည်းအမည်", 
                value=st.session_state.search_query
            )
            
            # Category Management
            st.sidebar.divider()
            st.sidebar.subheader("📁 အမျိုးအစား")
            
            categories = load_categories(spreadsheet, store_id)
            cat_names = [c['category_name'] for c in categories]
            
            new_cat = st.sidebar.text_input("အမျိုးအစားအသစ်", placeholder="Desserts")
            if st.sidebar.button("➕ ထည့်မည်", use_container_width=True, key="add_cat"):
                if new_cat and new_cat.strip():
                    if new_cat.strip() not in cat_names:
                        save_category(spreadsheet, store_id, new_cat.strip())
                        st.sidebar.success(f"✅ '{new_cat}' ထည့်ပြီး။")
                        st.rerun()
                    else:
                        st.sidebar.warning("⚠️ ရှိပြီးသားပါ။")
            
            if cat_names:
                st.sidebar.caption("လက်ရှိ အမျိုးအစားများ:")
                for cat in cat_names:
                    col1, col2 = st.sidebar.columns([3, 1])
                    with col1:
                        st.write(f"• {cat}")
                    with col2:
                        if st.button("🗑️", key=f"delcat_{cat}"):
                            items = load_menu_items(spreadsheet, store_id)
                            items_in_cat = [i for i in items if i.get('category') == cat]
                            if items_in_cat:
                                st.sidebar.error(f"⚠️ ပစ္စည်း {len(items_in_cat)} ခုရှိနေပါသည်။")
                            else:
                                delete_category(spreadsheet, store_id, cat)
                                st.rerun()
            
            # Add Menu Item
            st.sidebar.divider()
            st.sidebar.subheader("➕ ပစ္စည်းအသစ်")
            
            if cat_names:
                with st.sidebar.form("add_item_form", clear_on_submit=True):
                    item_name = st.text_input("အမည် *", placeholder="Cappuccino")
                    item_price = st.text_input("ဈေးနှုန်း *", placeholder="2500")
                    item_cat = st.selectbox("အမျိုးအစား *", cat_names)
                    
                    if st.form_submit_button("✅ ထည့်မည်", use_container_width=True):
                        if item_name and item_price:
                            import uuid
                            save_menu_item(spreadsheet, store_id, {
                                'item_id': str(uuid.uuid4())[:8],
                                'name': item_name.strip(),
                                'price': item_price.strip(),
                                'category': item_cat
                            })
                            st.sidebar.success(f"✅ '{item_name}' ထည့်ပြီး။")
                            st.rerun()
                        else:
                            st.sidebar.error("⚠️ အချက်အလက် ဖြည့်ပါ။")
            else:
                st.sidebar.info("အမျိုးအစား အရင်ထည့်ပါ။")
            
            # Stats
            items = load_menu_items(spreadsheet, store_id)
            st.sidebar.divider()
            st.sidebar.metric("📊 ပစ္စည်းအရေအတွက်", len(items))
    
    # ============================================
    # MAIN CONTENT
    # ============================================
    if not current_store:
        st.title("☕ NZA Menu System")
        st.info("ဆိုင်မရှိသေးပါ။ Super Admin Login ဝင်ပြီး ဆိုင်အသစ်ထည့်ပါ။")
        st.markdown(f"**Super Admin Password:** `{SUPER_ADMIN_KEY}`")
        return
    
    store_id = current_store['store_id']
    
    # Logo and Header
    logo_value = current_store.get('logo', '☕')
    # Check if logo is image URL
    is_image = isinstance(logo_value, str) and (logo_value.startswith(('http://', 'https://')) or logo_value.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')))
    
    # Build logo HTML
    if is_image:
        logo_html = f'<img src="{html.escape(logo_value)}" style="width:150px; height:150px; object-fit:contain; border-radius:10px;" alt="Logo">'
    else:
        logo_html = f'<span style="font-size:8em;">{logo_value}</span>'
    
    # Full header with proper centering and font sizes
    st.markdown(f"""
    <style>
    .header-container {{
        text-align: center;
        padding: 20px 0 10px 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }}
    .header-logo {{
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 10px;
    }}
    .header-title {{
        font-size: 4em;
        font-weight: bold;
        color: #2E86AB;
        margin: 10px 0 5px 0;
        text-align: center;
    }}
    .header-subtitle {{
        font-size: 2em;
        color: #8B4513;
        margin: 5px 0;
        letter-spacing: 3px;
        text-align: center;
    }}
    .header-divider {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 15px;
        margin: 10px 0;
    }}
    .header-line {{
        width: 100px;
        height: 2px;
        background: linear-gradient(90deg, transparent, #8B4513, transparent);
    }}
    </style>
    <div class="header-container">
        <div class="header-logo">
            {logo_html}
        </div>
        <div class="header-title">{html.escape(current_store['store_name'])}</div>
        <div class="header-divider">
            <span class="header-line"></span>
            <span style="color:#8B4513;">◆</span>
            <span class="header-line"></span>
        </div>
        <div class="header-subtitle">{html.escape(current_store.get('subtitle', 'Food & Drinks'))}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    categories = load_categories(spreadsheet, store_id)
    items = load_menu_items(spreadsheet, store_id)
    
    # Filter by search
    if st.session_state.search_query:
        items = [i for i in items if st.session_state.search_query.lower() in i['name'].lower()]
    
    # Group by category
    cat_names = [c['category_name'] for c in categories]
    category_items = {cat: [] for cat in cat_names}
    for item in items:
        cat = item.get('category', '')
        if cat in category_items:
            category_items[cat].append(item)
    
    if not items and not categories:
        st.info("ℹ️ ပစ္စည်းမရှိသေးပါ။ Admin Login ဝင်ပြီး ထည့်ပါ။")
    else:
        # Menu Style CSS
        st.markdown("""
        <style>
        .stApp { background-color: #f8f5f0; }
        .cat-header {
            background: linear-gradient(135deg, #8B4513 0%, #A0522D 100%);
            color: #fff;
            text-align: center;
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 1.1em;
            font-weight: 600;
            margin: 25px 0 15px 0;
            box-shadow: 0 3px 10px rgba(139,69,19,0.2);
        }
        .menu-row {
            display: flex;
            align-items: center;
            padding: 8px 0;
            color: #5D4037;
            font-size: 1em;
        }
        .menu-name { flex: 0 0 auto; font-weight: 500; }
        .menu-dots { flex: 1; border-bottom: 1px dotted #8B4513; margin: 0 10px; min-width: 20px; }
        .menu-price { flex: 0 0 auto; font-weight: 600; color: #8B4513; }
        </style>
        """, unsafe_allow_html=True)
        
        # Two column layout
        col_left, col_right = st.columns(2)
        
        cats_with_items = [c for c in cat_names if category_items.get(c)]
        mid = (len(cats_with_items) + 1) // 2
        left_cats = cats_with_items[:mid]
        right_cats = cats_with_items[mid:]
        
        def render_category(cat, cat_items):
            st.markdown(f'<div class="cat-header">{html.escape(cat)}</div>', unsafe_allow_html=True)
            for item in cat_items:
                item_id = item['item_id']
                
                if st.session_state.editing_id == item_id and st.session_state.is_admin:
                    with st.container(border=True):
                        with st.form(f"edit_{item_id}", clear_on_submit=False):
                            new_name = st.text_input("အမည်", value=item['name'])
                            new_price = st.text_input("ဈေးနှုန်း", value=str(item['price']))
                            cat_idx = cat_names.index(item.get('category', cat_names[0])) if item.get('category') in cat_names else 0
                            new_cat = st.selectbox("အမျိုးအစား", cat_names, index=cat_idx)
                            c1, c2 = st.columns(2)
                            with c1:
                                save = st.form_submit_button("💾 သိမ်း", use_container_width=True)
                            with c2:
                                cancel = st.form_submit_button("❌ ပယ်", use_container_width=True)
                            if save and new_name.strip() and new_price.strip():
                                update_menu_item(spreadsheet, store_id, item_id, {
                                    'name': new_name.strip(),
                                    'price': new_price.strip(),
                                    'category': new_cat
                                })
                                st.session_state.editing_id = None
                                st.rerun()
                            if cancel:
                                st.session_state.editing_id = None
                                st.rerun()
                else:
                    st.markdown(
                        f'<div class="menu-row">'
                        f'<span class="menu-name">{html.escape(item["name"])}</span>'
                        f'<span class="menu-dots"></span>'
                        f'<span class="menu-price">{html.escape(str(item["price"]))}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    if st.session_state.is_admin:
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("✏️ Edit", key=f"e_{item_id}", use_container_width=True):
                                st.session_state.editing_id = item_id
                                st.rerun()
                        with c2:
                            if st.button("🗑️ Remove", key=f"d_{item_id}", use_container_width=True):
                                delete_menu_item(spreadsheet, store_id, item_id)
                                st.rerun()
        
        with col_left:
            for cat in left_cats:
                render_category(cat, category_items[cat])
        
        with col_right:
            for cat in right_cats:
                render_category(cat, category_items[cat])
    
    st.divider()
    st.caption("💻 Developed with Streamlit & Google Sheets")

if __name__ == "__main__":
    main()



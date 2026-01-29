import streamlit as st
import uuid
import html
import json
from pathlib import Path

# -------- Store Name from File Name --------
SCRIPT_NAME = Path(__file__).stem
STORE_NAME = SCRIPT_NAME.replace("_", " ").title()

# Page အပြင်အဆင်
st.set_page_config(
    page_title=f"{STORE_NAME} - Menu",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------- Auth / Mode --------
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

ADMIN_KEY = "12345"

# -------- Data Storage --------
STORE_ID = SCRIPT_NAME
DATA_FILE = Path(f"store_data_{STORE_ID}.json")

def _load_data():
    try:
        if DATA_FILE.exists():
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            items = data.get("store_items", [])
            categories = data.get("categories", None)
            return items, categories
    except Exception:
        pass
    return None, None

def _save_data():
    try:
        payload = {
            "store_items": st.session_state.store_items,
            "categories": st.session_state.categories,
        }
        DATA_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as e:
        if st.session_state.get("is_admin"):
            st.error(f"Data save error: {e}")

# အချက်အလက်များ သိမ်းဆည်းရန်
loaded_items, loaded_cats = _load_data()

# Default categories
DEFAULT_CATEGORIES = ["Myanmar Breakfast", "Drinks", "Fresh Juice", "Shan"]

if 'categories' not in st.session_state:
    if loaded_cats is not None:
        st.session_state.categories = loaded_cats
    else:
        st.session_state.categories = DEFAULT_CATEGORIES.copy()

if 'store_items' not in st.session_state:
    if loaded_items is not None:
        st.session_state.store_items = loaded_items
    else:
        # Default items matching the image
        st.session_state.store_items = [
            # Myanmar Breakfast
            {"id": str(uuid.uuid4()), "name": "မုန့်ဟင်းခါး", "price": "2000", "category": "Myanmar Breakfast"},
            {"id": str(uuid.uuid4()), "name": "အုန်းနို့ခေါက်ဆွဲ", "price": "2000", "category": "Myanmar Breakfast"},
            {"id": str(uuid.uuid4()), "name": "ခေါက်ဆွဲသုပ်", "price": "1500", "category": "Myanmar Breakfast"},
            {"id": str(uuid.uuid4()), "name": "ကြာရံသုပ်", "price": "1500", "category": "Myanmar Breakfast"},
            {"id": str(uuid.uuid4()), "name": "အသုပ်မို့", "price": "1000", "category": "Myanmar Breakfast"},
            # Drinks
            {"id": str(uuid.uuid4()), "name": "Iced Tea", "price": "1000", "category": "Drinks"},
            {"id": str(uuid.uuid4()), "name": "Black Coffee", "price": "1500", "category": "Drinks"},
            {"id": str(uuid.uuid4()), "name": "Cappuccino", "price": "2500", "category": "Drinks"},
            {"id": str(uuid.uuid4()), "name": "Espresso", "price": "2000", "category": "Drinks"},
            {"id": str(uuid.uuid4()), "name": "Latte", "price": "2500", "category": "Drinks"},
            # Fresh Juice
            {"id": str(uuid.uuid4()), "name": "Sunkist", "price": "2000", "category": "Fresh Juice"},
            {"id": str(uuid.uuid4()), "name": "Passion", "price": "2500", "category": "Fresh Juice"},
            {"id": str(uuid.uuid4()), "name": "Avocado", "price": "3000", "category": "Fresh Juice"},
            {"id": str(uuid.uuid4()), "name": "Lime", "price": "1500", "category": "Fresh Juice"},
            {"id": str(uuid.uuid4()), "name": "Watermelon", "price": "2000", "category": "Fresh Juice"},
            # Shan
            {"id": str(uuid.uuid4()), "name": "ရှမ်းခေါက်ဆွဲ", "price": "2000", "category": "Shan"},
            {"id": str(uuid.uuid4()), "name": "တို့ဟူးငွေး", "price": "1500", "category": "Shan"},
            {"id": str(uuid.uuid4()), "name": "မိုးကုတ်ဦးရည်", "price": "1500", "category": "Shan"},
            {"id": str(uuid.uuid4()), "name": "ဝက်သားချဉ်", "price": "2500", "category": "Shan"},
            {"id": str(uuid.uuid4()), "name": "အီချက်ခေါက်ဆွဲ", "price": "2000", "category": "Shan"},
        ]

# Force reset: ပထမဆုံး run မှာ default data သုံးမယ်
if loaded_items is None or len(loaded_items) == 0:
    _save_data()

if 'editing_id' not in st.session_state:
    st.session_state.editing_id = None
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""

def validate_price(price_str):
    if not price_str or price_str.strip() == "":
        return False
    return True

# --- Sidebar / Header controls ---
if not st.session_state.is_admin:
    st.sidebar.header("⚙️ Admin Settings")
    key_input = st.sidebar.text_input("Enter Key", type="password")
    if st.sidebar.button("Login"):
        if (key_input or "").strip() == ADMIN_KEY:
            st.session_state.is_admin = True
            st.rerun()
        else:
            st.sidebar.error("❌ Key မှားနေပါတယ်။")
else:
    st.sidebar.header(f"🏪 {STORE_NAME}")
    st.sidebar.success("👨‍💼 Admin Mode")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.is_admin = False
        st.session_state.editing_id = None
        st.rerun()

if st.session_state.is_admin:
    st.sidebar.header("📦 ပစ္စည်းစီမံခန့်ခွဲမှု")
    
    # Search
    st.sidebar.subheader("🔍 ရှာဖွေရန်")
    st.session_state.search_query = st.sidebar.text_input("ပစ္စည်းအမည် ရှာဖွေပါ", value=st.session_state.search_query)
    
    # Category Management
    st.sidebar.divider()
    st.sidebar.subheader("📁 အမျိုးအစား စီမံခန့်ခွဲမှု")
    
    # Add new category
    new_cat = st.sidebar.text_input("အမျိုးအစား အသစ်ထည့်ရန်", placeholder="ဥပမာ: Desserts")
    if st.sidebar.button("➕ အမျိုးအစား ထည့်မည်", use_container_width=True):
        if new_cat and new_cat.strip():
            if new_cat.strip() not in st.session_state.categories:
                st.session_state.categories.append(new_cat.strip())
                _save_data()
                st.sidebar.success(f"✅ '{new_cat}' ထည့်ပြီးပါပြီ။")
                st.rerun()
            else:
                st.sidebar.warning("⚠️ ဒီအမျိုးအစား ရှိပြီးသားပါ။")
        else:
            st.sidebar.error("⚠️ အမျိုးအစား အမည် ထည့်ပါ။")
    
    # Show existing categories with delete option
    st.sidebar.caption("လက်ရှိ အမျိုးအစားများ:")
    for cat in st.session_state.categories:
        col_cat, col_del = st.sidebar.columns([3, 1])
        with col_cat:
            st.write(f"• {cat}")
        with col_del:
            if st.button("🗑️", key=f"del_cat_{cat}", help=f"Delete {cat}"):
                items_in_cat = [i for i in st.session_state.store_items if i.get('category') == cat]
                if items_in_cat:
                    st.sidebar.error(f"⚠️ '{cat}' တွင် ပစ္စည်း {len(items_in_cat)} ခုရှိနေပါသည်။")
                else:
                    st.session_state.categories.remove(cat)
                    _save_data()
                    st.rerun()
    
    # Add New Item Form
    st.sidebar.divider()
    st.sidebar.subheader("➕ ပစ္စည်းအသစ်ထည့်ရန်")
    with st.sidebar.form("add_form", clear_on_submit=True):
        name = st.text_input("ပစ္စည်းအမည် *", placeholder="ဥပမာ: Cappuccino")
        price = st.text_input("ဈေးနှုန်း *", placeholder="ဥပမာ: 2500")
        category = st.selectbox("အမျိုးအစား *", st.session_state.categories)
        submit = st.form_submit_button("✅ စာရင်းသွင်းမည်", use_container_width=True)
        if submit:
            if not name or not name.strip():
                st.sidebar.error("⚠️ ပစ္စည်းအမည် ထည့်သွင်းရန် လိုအပ်ပါသည်။")
            elif not validate_price(price):
                st.sidebar.error("⚠️ ဈေးနှုန်း ထည့်သွင်းရန် လိုအပ်ပါသည်။")
            else:
                st.session_state.store_items.append({
                    "id": str(uuid.uuid4()),
                    "name": name.strip(),
                    "price": price.strip(),
                    "category": category
                })
                _save_data()
                st.sidebar.success(f"✅ {name} ထည့်သွင်းပြီးပါပြီ။")
                st.rerun()
    
    st.sidebar.divider()
    st.sidebar.metric("📊 စုစုပေါင်း ပစ္စည်းများ", len(st.session_state.store_items))
    
    # Reset to defaults
    st.sidebar.divider()
    if st.sidebar.button("🔄 Reset to Defaults", use_container_width=True, type="secondary"):
        st.session_state.categories = DEFAULT_CATEGORIES.copy()
        st.session_state.store_items = [
            # Myanmar Breakfast
            {"id": str(uuid.uuid4()), "name": "မုန့်ဟင်းခါး", "price": "2000", "category": "Myanmar Breakfast"},
            {"id": str(uuid.uuid4()), "name": "အုန်းနို့ခေါက်ဆွဲ", "price": "2000", "category": "Myanmar Breakfast"},
            {"id": str(uuid.uuid4()), "name": "ခေါက်ဆွဲသုပ်", "price": "1500", "category": "Myanmar Breakfast"},
            {"id": str(uuid.uuid4()), "name": "ကြာရံသုပ်", "price": "1500", "category": "Myanmar Breakfast"},
            {"id": str(uuid.uuid4()), "name": "အသုပ်မို့", "price": "1000", "category": "Myanmar Breakfast"},
            # Drinks
            {"id": str(uuid.uuid4()), "name": "Iced Tea", "price": "1000", "category": "Drinks"},
            {"id": str(uuid.uuid4()), "name": "Black Coffee", "price": "1500", "category": "Drinks"},
            {"id": str(uuid.uuid4()), "name": "Cappuccino", "price": "2500", "category": "Drinks"},
            {"id": str(uuid.uuid4()), "name": "Espresso", "price": "2000", "category": "Drinks"},
            {"id": str(uuid.uuid4()), "name": "Latte", "price": "2500", "category": "Drinks"},
            # Fresh Juice
            {"id": str(uuid.uuid4()), "name": "Sunkist", "price": "2000", "category": "Fresh Juice"},
            {"id": str(uuid.uuid4()), "name": "Passion", "price": "2500", "category": "Fresh Juice"},
            {"id": str(uuid.uuid4()), "name": "Avocado", "price": "3000", "category": "Fresh Juice"},
            {"id": str(uuid.uuid4()), "name": "Lime", "price": "1500", "category": "Fresh Juice"},
            {"id": str(uuid.uuid4()), "name": "Watermelon", "price": "2000", "category": "Fresh Juice"},
            # Shan
            {"id": str(uuid.uuid4()), "name": "ရှမ်းခေါက်ဆွဲ", "price": "2000", "category": "Shan"},
            {"id": str(uuid.uuid4()), "name": "တို့ဟူးငွေး", "price": "1500", "category": "Shan"},
            {"id": str(uuid.uuid4()), "name": "မိုးကုတ်ဦးရည်", "price": "1500", "category": "Shan"},
            {"id": str(uuid.uuid4()), "name": "ဝက်သားချဉ်", "price": "2500", "category": "Shan"},
            {"id": str(uuid.uuid4()), "name": "အီချက်ခေါက်ဆွဲ", "price": "2000", "category": "Shan"},
        ]
        _save_data()
        st.sidebar.success("✅ Reset ပြီးပါပြီ။")
        st.rerun()

# --- Main Interface ---
fresh_items, fresh_cats = _load_data()
if fresh_items is not None:
    st.session_state.store_items = fresh_items
if fresh_cats is not None:
    st.session_state.categories = fresh_cats

st.title(f"🏪 {STORE_NAME}")
st.write("**Menu List**")

# Filter items
filtered_items = st.session_state.store_items
if st.session_state.search_query:
    filtered_items = [
        item for item in st.session_state.store_items
        if st.session_state.search_query.lower() in item['name'].lower()
    ]

# Group by category
category_items = {cat: [] for cat in st.session_state.categories}
for item in filtered_items:
    cat = item.get('category', '')
    if cat in category_items:
        category_items[cat].append(item)

if not st.session_state.store_items:
    st.info("ℹ️ ပစ္စည်းစာရင်း မရှိသေးပါ။")
elif not filtered_items:
    st.warning(f"⚠️ '{st.session_state.search_query}' မတွေ့ရှိပါ။")
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
    
    cats_list = [c for c in st.session_state.categories if category_items.get(c)]
    mid = (len(cats_list) + 1) // 2
    left_cats = cats_list[:mid]
    right_cats = cats_list[mid:]
    
    def render_category(cat, items):
        st.markdown(f'<div class="cat-header">{html.escape(cat)}</div>', unsafe_allow_html=True)
        for item in items:
            item_id = item['id']
            
            if st.session_state.editing_id == item_id and st.session_state.is_admin:
                with st.container(border=True):
                    with st.form(f"edit_{item_id}", clear_on_submit=False):
                        new_name = st.text_input("အမည်", value=item['name'])
                        new_price = st.text_input("ဈေးနှုန်း", value=item['price'])
                        cat_idx = st.session_state.categories.index(item.get('category', st.session_state.categories[0])) if item.get('category') in st.session_state.categories else 0
                        new_cat = st.selectbox("အမျိုးအစား", st.session_state.categories, index=cat_idx)
                        col1, col2 = st.columns(2)
                        with col1:
                            save = st.form_submit_button("💾 သိမ်း", use_container_width=True)
                        with col2:
                            cancel = st.form_submit_button("❌ ပယ်", use_container_width=True)
                        if save and new_name.strip() and validate_price(new_price):
                            for i, s in enumerate(st.session_state.store_items):
                                if s['id'] == item_id:
                                    st.session_state.store_items[i] = {"id": item_id, "name": new_name.strip(), "price": new_price.strip(), "category": new_cat}
                                    break
                            _save_data()
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
                    f'<span class="menu-price">{html.escape(item["price"])}</span>'
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
                            st.session_state.delete_confirm_id = item_id
                            st.rerun()
    
    with col_left:
        for cat in left_cats:
            render_category(cat, category_items[cat])
    
    with col_right:
        for cat in right_cats:
            render_category(cat, category_items[cat])

# Delete confirmation
if 'delete_confirm_id' in st.session_state:
    item_to_del = next((i for i in st.session_state.store_items if i['id'] == st.session_state.delete_confirm_id), None)
    if item_to_del:
        st.warning(f"⚠️ '{item_to_del['name']}' ကို ဖျက်မည်လား?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ ဖျက်မည်", type="primary", use_container_width=True):
                st.session_state.store_items = [i for i in st.session_state.store_items if i['id'] != st.session_state.delete_confirm_id]
                _save_data()
                del st.session_state.delete_confirm_id
                st.rerun()
        with c2:
            if st.button("❌ မဖျက်ပါ", use_container_width=True):
                del st.session_state.delete_confirm_id
                st.rerun()

st.divider()
st.caption("💻 Developed with Cursor AI & Streamlit")

import streamlit as st
import streamlit_antd_components as sac
from dashboard.home import home
from dashboard.portfolio import portfolio
from helpers.data import load_portfolios
from helpers.login_form import login_form

st.set_page_config(page_title="DeepStocks", layout="centered")

@st.cache_data
def get_auth_status():
    if 'auth_status' not in st.session_state:
        st.session_state['auth_status'] = {"authenticated": False, "username": None}
    return st.session_state['auth_status']

def set_auth_status(authenticated, username):
    st.session_state['auth_status'] = {"authenticated": authenticated, "username": username}
    st.cache_data.clear()  # Clear the cache to update the status

# Initialize session state with cached authentication status
auth_status = get_auth_status()
if "authenticated" not in st.session_state:
    st.session_state.authenticated = auth_status["authenticated"]
    st.session_state.username = auth_status["username"]

# Custom CSS for the login page
st.markdown("""
    <style>
    .login-box {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
        margin: auto;        
        border-radius: 50px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        
    }
    .login-left {
        text-align: center;
        background-color: transparent;
        color: white;
        border-radius: 30px;
        padding: 50px;
        width: 100%;
        
    }
    .login-title {
        font-size: 2.5em;    
        font-weight: bold;
        color: #ff4b4b;
    }
    .login-logo {
        width: 170px;
        margin-bottom: 0px;
        border-radius: 2px;
    }
    .login-button {
        background-color: #ff4b4b;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        cursor: pointer;
    }
    </style>
""", unsafe_allow_html=True)

# Check if the image path is correct
import os
if not os.path.isfile('assets/icon.png'):
    st.error("Logo image not found. Please ensure 'assets/icon.png' exists.")

# Display login form if user is not authenticated
if not st.session_state["authenticated"]:
    st.markdown("""
        <div class="login-box">
            <div class="login-left">
                <img src="https://i.ibb.co/RSbPFh1/candlestick-svgrepo-com.png" class="login-logo" alt="DeepStocks Logo">
                <h1 class="login-title">Welcome to DeepStocks</h1>
            </div>
    """, unsafe_allow_html=True)

    client = login_form(
        title="Sign In",
        user_tablename="users",
        username_col="username",
        password_col="password",
        create_title="Create an account 🚀",
        login_title="Login to your account key 🔑",
        allow_guest=False,
        allow_create=True,
        guest_title="Guest login 🥷",
        create_username_label="Create a username",
        create_username_placeholder="JohnDoe123",
        create_password_label="Create a password",
        create_password_help="Password cannot be recovered if lost",
        create_submit_label="Continue",
        create_success_message="Account created and logged-in 🎉",
        login_username_label="Username",
        login_password_label="Password",
        login_success_message="Login succeeded 🎉",
        login_error_message="Wrong username/password ❌",
        guest_submit_label="Guest login"
    )
    
    if st.session_state["authenticated"]:
        set_auth_status(st.session_state["authenticated"], st.session_state["username"])
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

else:
    username = st.session_state.get("username", "Guest")
    portfolios = load_portfolios(username)

    with st.sidebar:
        st.title("Navigation")
        st.write(f"Welcome, {username}!")
        portfolio_items = [sac.MenuItem(name, icon='briefcase-fill') for name in portfolios.keys()]
        menu_items = [
            sac.MenuItem('Home', icon='house-fill'),
            sac.MenuItem('Portfolios', icon='box-fill', children=portfolio_items)
        ]
        selected_item = sac.menu(menu_items, open_all=True)

        st.markdown("---")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.username = None
            set_auth_status(False, None)
            st.rerun()

    if selected_item == 'Home':
        home(username)
    elif selected_item in portfolios:
        portfolio(username, selected_item)

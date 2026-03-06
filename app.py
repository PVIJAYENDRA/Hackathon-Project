"""VisionSense - AI Retail Analytics Platform for Tile Showroom."""

import streamlit as st

from backend.database import init_db
from backend.seed import run_seed
from backend.auth import create_access_token, decode_token, hash_password, verify_password
from backend.models import User
from backend.database import SessionLocal


def init_session() -> None:
    if "token" not in st.session_state:
        st.session_state.token = None
    if "user" not in st.session_state:
        st.session_state.user = None


def login_user(email: str, password: str) -> bool:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            return False
        token = create_access_token({"sub": user.email, "user_id": user.user_id})
        st.session_state.token = token
        st.session_state.user = {"email": user.email, "name": user.name, "role": user.role}
        return True
    finally:
        db.close()


def signup_user(name: str, email: str, password: str) -> tuple[bool, str]:
    """Register a new user. Returns (success, message)."""
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == email).first():
            return False, "Email already registered."
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role="manager",
        )
        db.add(user)
        db.commit()
        return True, "Account created successfully. You can now log in."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()


def is_authenticated() -> bool:
    token = st.session_state.get("token")
    if not token:
        return False
    payload = decode_token(token)
    return payload is not None


def render_login() -> None:
    st.set_page_config(page_title="VisionSense - Login", layout="centered", initial_sidebar_state="collapsed")
    st.title("VisionSense")
    st.subheader("AI Retail Analytics for Tile Showroom")
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="admin@visionsense.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submitted = st.form_submit_button("Login")
        with col2:
            forgot = st.form_submit_button("Forgot Password")
        if forgot:
            st.info("Contact your administrator to reset your password.")
        if submitted:
            if login_user(email, password):
                st.success("Login successful. Redirecting...")
                st.rerun()
            else:
                st.error("Invalid email or password.")
    st.divider()
    if st.button("Don't have an account? **Sign up**"):
        st.session_state.auth_page = "signup"
        st.rerun()


def render_signup() -> None:
    st.set_page_config(page_title="VisionSense - Sign Up", layout="centered", initial_sidebar_state="collapsed")
    st.title("VisionSense")
    st.subheader("Create your account")
    with st.form("signup_form"):
        name = st.text_input("Full Name", placeholder="John Doe")
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        confirm = st.text_input("Confirm Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Sign Up")
        if submitted:
            if not name or not email or not password:
                st.error("Please fill in all fields.")
            elif password != confirm:
                st.error("Passwords do not match.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                ok, msg = signup_user(name, email, password)
                if ok:
                    st.success(msg)
                    st.session_state.auth_page = "login"
                    st.rerun()
                else:
                    st.error(msg)
    st.divider()
    if st.button("Already have an account? **Log in**"):
        st.session_state.auth_page = "login"
        st.rerun()


def render_main() -> None:
    st.set_page_config(
        page_title="VisionSense - Analytics",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    user = st.session_state.get("user", {})
    st.sidebar.title("VisionSense")
    st.sidebar.caption(f"Logged in as {user.get('name', 'User')}")
    st.sidebar.divider()

    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Live Camera", "Heatmap", "Visitor Analytics", "Sentiment Analysis", "Reports"],
        label_visibility="collapsed",
    )
    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.session_state.user = None
        st.rerun()

    if page == "Dashboard":
        from pages.dashboard import render
        render()
    elif page == "Live Camera":
        from pages.live_camera import render
        render()
    elif page == "Heatmap":
        from pages.heatmap import render
        render()
    elif page == "Visitor Analytics":
        from pages.visitor_analytics import render
        render()
    elif page == "Sentiment Analysis":
        from pages.sentiment_analysis import render
        render()
    elif page == "Reports":
        from pages.reports import render
        render()


def main() -> None:
    init_db()
    run_seed()
    init_session()
    if "auth_page" not in st.session_state:
        st.session_state.auth_page = "login"
    if not is_authenticated():
        if st.session_state.auth_page == "signup":
            render_signup()
        else:
            render_login()
    else:
        render_main()


if __name__ == "__main__":
    main()

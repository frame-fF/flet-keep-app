import flet as ft

from api import ApiError, login as api_login, logout as api_logout, register as api_register, split_errors
from auth_state import clear_session, get_token, is_logged_in, set_session

NAV_ROUTES = ["/", "/archive", "/trash"]
BAR_COLOR = ft.Colors.SURFACE_CONTAINER


def app_bar(title: str, is_dark: bool, toggle_theme, on_profile_click) -> ft.AppBar:
    return ft.AppBar(
        title=ft.Text(title),
        bgcolor=BAR_COLOR,
        actions=[
            ft.IconButton(
                icon=ft.Icons.DARK_MODE if is_dark else ft.Icons.LIGHT_MODE,
                on_click=lambda e: toggle_theme(),
            ),
            ft.IconButton(
                icon=ft.Icons.ACCOUNT_CIRCLE,
                on_click=on_profile_click,
            ),
        ],
    )


def profile_drawer(on_logout) -> ft.NavigationDrawer:
    return ft.NavigationDrawer(
        controls=[
            ft.Container(height=12),
            ft.ListTile(leading=ft.Icon(ft.Icons.ACCOUNT_CIRCLE), title=ft.Text("Profile")),
            ft.ListTile(leading=ft.Icon(ft.Icons.SETTINGS_OUTLINED), title=ft.Text("Settings")),
            ft.ListTile(leading=ft.Icon(ft.Icons.LOGOUT), title=ft.Text("Logout"), on_click=on_logout),
        ]
    )


def _is_currently_dark(page: ft.Page) -> bool:
    if page.theme_mode == ft.ThemeMode.DARK:
        return True
    if page.theme_mode == ft.ThemeMode.LIGHT:
        return False
    return page.platform_brightness == ft.Brightness.DARK


def use_theme_toggle():
    """Local dark-mode state, seeded from what's actually on screen right now."""
    page = ft.context.page
    is_dark, set_is_dark = ft.use_state(lambda: _is_currently_dark(page))

    def toggle_theme():
        new_value = not is_dark
        set_is_dark(new_value)
        page.theme_mode = ft.ThemeMode.DARK if new_value else ft.ThemeMode.LIGHT
        page.update()

    return is_dark, toggle_theme


def nav_bar(selected_index: int) -> ft.NavigationBar:
    page = ft.context.page
    return ft.NavigationBar(
        selected_index=selected_index,
        bgcolor=BAR_COLOR,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED, label="Home"),
            ft.NavigationBarDestination(icon=ft.Icons.ARCHIVE_OUTLINED, label="Archive"),
            ft.NavigationBarDestination(icon=ft.Icons.DELETE_OUTLINE, label="Trash"),
        ],
        on_change=lambda e: page.navigate(NAV_ROUTES[e.control.selected_index]),
    )


def page_view(title: str, content: ft.Control, **view_kwargs) -> ft.View:
    page = ft.context.page
    route = ft.use_route_location()

    if not is_logged_in():
        page.navigate("/login")
        return ft.View(route=route, controls=[ft.ProgressRing()])

    is_dark, toggle_theme = use_theme_toggle()
    index = NAV_ROUTES.index(route)

    async def open_profile_menu(e):
        await view.show_end_drawer()

    async def handle_logout(e):
        token = get_token()
        try:
            await api_logout(token)
        except ApiError:
            pass
        clear_session()
        page.navigate("/login")

    view = ft.View(
        route=route,
        appbar=app_bar(title, is_dark, toggle_theme, open_profile_menu),
        navigation_bar=nav_bar(index),
        end_drawer=profile_drawer(handle_logout),
        controls=[content],
        **view_kwargs,
    )
    return view


@ft.component
def Home():
    appbar_title = "Home"
    content = ft.Text("This is the Home page")
    fab = ft.FloatingActionButton(icon=ft.Icons.ADD, on_click=lambda e: None)

    return page_view(appbar_title, content, floating_action_button=fab)


@ft.component
def Archive():
    appbar_title = "Archive"
    content = ft.Text("This is the Archive page")

    return page_view(appbar_title, content)


@ft.component
def Trash():
    appbar_title = "Trash"
    content = ft.Text("This is the Trash page")

    return page_view(appbar_title, content)


@ft.component
def LoginForm():
    page = ft.context.page
    error_text, set_error_text = ft.use_state("")
    field_errors, set_field_errors = ft.use_state({})
    loading, set_loading = ft.use_state(False)

    username, set_username = ft.use_state("")
    password, set_password = ft.use_state("")

    async def handle_login(e):
        set_loading(True)
        set_error_text("")
        set_field_errors({})
        try:
            data = await api_login(username, password)
            set_session(data["token"], data["user"])
            page.navigate("/")
        except ApiError as ex:
            general, fields = split_errors(ex.errors) if ex.errors else (str(ex), {})
            set_error_text(general)
            set_field_errors(fields)
            set_loading(False)

    return ft.Column(
        [
            ft.Text("Login", size=28, weight=ft.FontWeight.BOLD),
            ft.TextField(
                label="Username or Email",
                value=username,
                on_change=lambda e: set_username(e.control.value),
                error=field_errors.get("username"),
            ),
            ft.TextField(
                label="Password",
                password=True,
                can_reveal_password=True,
                value=password,
                on_change=lambda e: set_password(e.control.value),
                error=field_errors.get("password"),
            ),
            ft.Container(height=24 if error_text else 0, content=ft.Text(error_text, color=ft.Colors.ERROR)),
            ft.FilledButton(
                content=ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.Colors.ON_PRIMARY)
                if loading
                else ft.Text("Login"),
                on_click=handle_login,
                disabled=loading,
            ),
            ft.TextButton(
                "Don't have an account? Register",
                on_click=lambda e: page.navigate("/register"),
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        width=350,
    )


@ft.component
def Login():
    return ft.View(
        route="/login",
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[LoginForm()],
    )


@ft.component
def RegisterForm():
    page = ft.context.page
    error_text, set_error_text = ft.use_state("")
    field_errors, set_field_errors = ft.use_state({})
    loading, set_loading = ft.use_state(False)

    username, set_username = ft.use_state("")
    email, set_email = ft.use_state("")
    password, set_password = ft.use_state("")
    password2, set_password2 = ft.use_state("")

    async def handle_register(e):
        set_loading(True)
        set_error_text("")
        set_field_errors({})
        try:
            await api_register(username, email, password, password2)
            page.navigate("/login")
        except ApiError as ex:
            general, fields = split_errors(ex.errors) if ex.errors else (str(ex), {})
            set_error_text(general)
            set_field_errors(fields)
            set_loading(False)

    return ft.Column(
        [
            ft.Text("Register", size=28, weight=ft.FontWeight.BOLD),
            ft.TextField(
                label="Username",
                value=username,
                on_change=lambda e: set_username(e.control.value),
                error=field_errors.get("username"),
            ),
            ft.TextField(
                label="Email",
                value=email,
                on_change=lambda e: set_email(e.control.value),
                error=field_errors.get("email"),
            ),
            ft.TextField(
                label="Password",
                password=True,
                can_reveal_password=True,
                value=password,
                on_change=lambda e: set_password(e.control.value),
                error=field_errors.get("password"),
            ),
            ft.TextField(
                label="Confirm Password",
                password=True,
                can_reveal_password=True,
                value=password2,
                on_change=lambda e: set_password2(e.control.value),
                error=field_errors.get("password2"),
            ),
            ft.Container(height=24 if error_text else 0, content=ft.Text(error_text, color=ft.Colors.ERROR)),
            ft.FilledButton(
                content=ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.Colors.ON_PRIMARY)
                if loading
                else ft.Text("Register"),
                on_click=handle_register,
                disabled=loading,
            ),
            ft.TextButton(
                "Already have an account? Login",
                on_click=lambda e: page.navigate("/login"),
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        width=350,
    )


@ft.component
def Register():
    return ft.View(
        route="/register",
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[RegisterForm()],
    )


@ft.component
def App():
    return ft.Router(
        [
            ft.Route(path="/", component=Home),
            ft.Route(path="/archive", component=Archive),
            ft.Route(path="/trash", component=Trash),
            ft.Route(path="/login", component=Login),
            ft.Route(path="/register", component=Register),
        ],
        manage_views=True,
    )


def main(page: ft.Page):
    page.window.width = 440
    page.window.height = 800

    page.theme = ft.Theme(
        page_transitions=ft.PageTransitionsTheme(
            android=ft.PageTransitionTheme.NONE,
            ios=ft.PageTransitionTheme.NONE,
            linux=ft.PageTransitionTheme.NONE,
            macos=ft.PageTransitionTheme.NONE,
            windows=ft.PageTransitionTheme.NONE,
        )
    )
    page.render_views(App)


if __name__ == "__main__":
    ft.run(main)

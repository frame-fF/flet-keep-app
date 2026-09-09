import flet as ft

NAV_ROUTES = ["/", "/archive", "/trash"]
BAR_COLOR = ft.Colors.SURFACE_CONTAINER


def app_bar(title: str, is_dark: bool, toggle_theme) -> ft.AppBar:
    page = ft.context.page
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
                on_click=lambda e: page.navigate("/profile"),
            ),
        ],
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
    route = ft.use_route_location()
    is_dark, toggle_theme = use_theme_toggle()
    index = NAV_ROUTES.index(route)
    return ft.View(
        route=route,
        appbar=app_bar(title, is_dark, toggle_theme),
        navigation_bar=nav_bar(index),
        controls=[content],
        **view_kwargs,
    )


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
def App():
    return ft.Router(
        [
            ft.Route(path="/", component=Home),
            ft.Route(path="/archive", component=Archive),
            ft.Route(path="/trash", component=Trash),
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

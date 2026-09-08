import flet as ft

NAV_ROUTES = ["/", "/archive", "/trash"]


def app_bar(title: str) -> ft.AppBar:
    page = ft.context.page
    return ft.AppBar(
        title=ft.Text(title),
        actions=[
            ft.IconButton(
                icon=ft.Icons.ACCOUNT_CIRCLE,
                on_click=lambda e: page.navigate("/profile"),
            ),
        ],
    )


def nav_bar(selected_index: int) -> ft.NavigationBar:
    page = ft.context.page
    return ft.NavigationBar(
        selected_index=selected_index,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED, label="Home"),
            ft.NavigationBarDestination(icon=ft.Icons.ARCHIVE_OUTLINED, label="Archive"),
            ft.NavigationBarDestination(icon=ft.Icons.DELETE_OUTLINE, label="Trash"),
        ],
        on_change=lambda e: page.navigate(NAV_ROUTES[e.control.selected_index]),
    )


@ft.component
def Home():
    return ft.View(
        route="/",
        appbar=app_bar("Home"),
        navigation_bar=nav_bar(0),
        controls=[ft.Text("This is the Home page")],
    )


@ft.component
def Archive():
    return ft.View(
        route="/archive",
        appbar=app_bar("Archive"),
        navigation_bar=nav_bar(1),
        controls=[ft.Text("This is the Archive page")],
    )


@ft.component
def Trash():
    return ft.View(
        route="/trash",
        appbar=app_bar("Trash"),
        navigation_bar=nav_bar(2),
        controls=[ft.Text("This is the Trash page")],
    )


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

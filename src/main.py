import flet as ft

NAV_ROUTES = ["/", "/archive", "/trash"]


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
        appbar=ft.AppBar(title=ft.Text("Home")),
        navigation_bar=nav_bar(0),
        controls=[ft.Text("This is the Home page")],
    )


@ft.component
def Archive():
    return ft.View(
        route="/archive",
        appbar=ft.AppBar(title=ft.Text("Archive")),
        navigation_bar=nav_bar(1),
        controls=[ft.Text("This is the Archive page")],
    )


@ft.component
def Trash():
    return ft.View(
        route="/trash",
        appbar=ft.AppBar(title=ft.Text("Trash")),
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

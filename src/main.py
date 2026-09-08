import flet as ft


def main(page: ft.Page):
    page.appbar = ft.AppBar(
        title=ft.Text("Keep"),
        actions=[ft.IconButton(icon=ft.Icons.SEARCH)],
    )

    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.LIGHTBULB_OUTLINE, label="Notes"),
            ft.NavigationBarDestination(icon=ft.Icons.ARCHIVE_OUTLINED, label="Archive"),
        ],
        on_change=lambda e: print("selected tab:", e.control.selected_index),
    )


if __name__ == "__main__":
    ft.run(main)

import uuid

import flet as ft
from flet_color_pickers import BlockPicker

from api import (
    ApiError,
    create_note as api_create_note,
    list_labels as api_list_labels,
    list_notes as api_list_notes,
    login as api_login,
    logout as api_logout,
    register as api_register,
    split_errors,
    update_note as api_update_note,
)
from auth_state import clear_session, get_refresh_token, get_token, is_logged_in, set_session
from models import ChecklistItem, Note

NAV_ROUTES = ["/", "/archive", "/trash"]
BAR_COLOR = ft.Colors.SURFACE_CONTAINER
NOTE_COLOR_SWATCHES = {
    "default": "#ffffff",
    "red": "#f28b82",
    "orange": "#fbbc04",
    "yellow": "#fff475",
    "green": "#ccff90",
    "teal": "#a7ffeb",
    "blue": "#aecbfa",
    "purple": "#d7aefb",
    "pink": "#fdcfe8",
    "brown": "#e6c9a8",
    "gray": "#e8eaed",
}
def _normalize_hex(value: str) -> str:
    value = value.strip().lower()
    if not value.startswith("#"):
        value = f"#{value}"
    if len(value) == 9:  # "#aarrggbb" (BlockPicker includes an alpha channel) -> "#rrggbb"
        value = "#" + value[3:]
    return value


SWATCH_TO_COLOR_NAME = {
    _normalize_hex(hex_value): name for name, hex_value in NOTE_COLOR_SWATCHES.items()
}


def color_name_for_hex(hex_value: str) -> str:
    return SWATCH_TO_COLOR_NAME.get(_normalize_hex(hex_value), "default")


def dialog_bgcolor_for(color_name: str) -> str | None:
    """"default" adapts to the current theme; other colors keep their fixed pastel."""
    return None if color_name == "default" else NOTE_COLOR_SWATCHES[color_name]


def _is_currently_dark(page: ft.Page) -> bool:
    if page.theme_mode == ft.ThemeMode.DARK:
        return True
    if page.theme_mode == ft.ThemeMode.LIGHT:
        return False
    return page.platform_brightness == ft.Brightness.DARK


@ft.component
def ThemeToggleButton():
    """Owns its own dark-mode state, so toggling it never re-renders the parent shell."""
    page = ft.context.page
    is_dark, set_is_dark = ft.use_state(lambda: _is_currently_dark(page))

    def toggle_theme(e):
        new_value = not is_dark
        set_is_dark(new_value)
        page.theme_mode = ft.ThemeMode.DARK if new_value else ft.ThemeMode.LIGHT
        page.update()

    return ft.IconButton(
        icon=ft.Icons.DARK_MODE if is_dark else ft.Icons.LIGHT_MODE,
        on_click=toggle_theme,
    )


def app_bar(title: str, on_profile_click) -> ft.AppBar:
    return ft.AppBar(
        title=ft.Text(title),
        bgcolor=BAR_COLOR,
        actions=[
            ThemeToggleButton(),
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

    index = NAV_ROUTES.index(route)

    async def open_profile_menu(e):
        await view.show_end_drawer()

    async def handle_logout(e):
        token = get_token()
        refresh = get_refresh_token()
        try:
            await api_logout(token, refresh)
        except ApiError:
            pass
        clear_session()
        page.navigate("/login")

    view = ft.View(
        route=route,
        appbar=app_bar(title, open_profile_menu),
        navigation_bar=nav_bar(index),
        end_drawer=profile_drawer(handle_logout),
        controls=[content],
        **view_kwargs,
    )
    return view


@ft.component
def NoteEditorFab(on_saved=None, open_ref=None):
    """FAB that opens a Keep-style note editor dialog for a new or existing note."""
    page = ft.context.page
    show, set_show = ft.use_state(False)
    editing_id, set_editing_id = ft.use_state(None)
    title, set_title = ft.use_state("")
    items, set_items = ft.use_state([])
    color, set_color = ft.use_state("default")
    pinned, set_pinned = ft.use_state(False)
    saving, set_saving = ft.use_state(False)
    error_text, set_error_text = ft.use_state("")
    picking_color, set_picking_color = ft.use_state(False)
    labels, set_labels = ft.use_state([])
    available_labels, set_available_labels = ft.use_state([])
    picking_labels, set_picking_labels = ft.use_state(False)
    new_label_text, set_new_label_text = ft.use_state("")

    async def load_labels():
        try:
            data = await api_list_labels(get_token())
            set_available_labels(data)
        except ApiError:
            pass

    ft.use_effect(lambda: page.run_task(load_labels), [])

    def reset_and_close():
        set_show(False)
        set_editing_id(None)
        set_title("")
        set_items([])
        set_color("default")
        set_pinned(False)
        set_error_text("")
        set_saving(False)
        set_labels([])
        set_new_label_text("")

    def open_for_edit(note: Note):
        set_editing_id(note.id)
        set_title(note.title)
        set_items(
            [
                {"id": item.id, "text": item.text, "checked": item.is_checked}
                for item in sorted(note.checklist_items, key=lambda i: i.order)
            ]
        )
        set_color(note.color)
        set_pinned(note.is_pinned)
        set_labels(list(note.labels))
        set_error_text("")
        set_show(True)

    if open_ref is not None:
        open_ref.current = open_for_edit

    def toggle_label(name: str):
        if name in labels:
            set_labels([n for n in labels if n != name])
        else:
            set_labels(labels + [name])

    def remove_label(name: str):
        set_labels([n for n in labels if n != name])

    def add_new_label(e):
        name = new_label_text.strip()
        if name and name not in labels:
            set_labels(labels + [name])
        set_new_label_text("")

    def add_item(e):
        set_items(items + [{"id": uuid.uuid4().hex, "text": "", "checked": False}])

    def update_item_text(index: int, value: str):
        new_items = [dict(item) for item in items]
        new_items[index]["text"] = value
        set_items(new_items)

    def toggle_item_checked(index: int):
        new_items = [dict(item) for item in items]
        new_items[index]["checked"] = not new_items[index]["checked"]
        set_items(new_items)

    def remove_item(index: int):
        set_items(items[:index] + items[index + 1 :])

    def handle_reorder(e: ft.OnReorderEvent):
        if e.old_index is None or e.new_index is None:
            return
        new_items = list(items)
        moved = new_items.pop(e.old_index)
        new_items.insert(e.new_index, moved)
        set_items(new_items)

    def handle_color_pick(e):
        set_color(color_name_for_hex(e.data))
        set_picking_color(False)

    async def save_note(e):
        set_saving(True)
        set_error_text("")
        try:
            checklist_items = [
                ChecklistItem(
                    id=item["id"] if isinstance(item["id"], int) else None,
                    text=item["text"],
                    order=i + 1,
                    is_checked=item["checked"],
                )
                for i, item in enumerate(items)
                if item["text"].strip()
            ]
            if editing_id is None:
                await api_create_note(
                    get_token(),
                    title=title.strip() or "Untitled",
                    content="",
                    color=color,
                    is_pinned=pinned,
                    labels=labels,
                    checklist_items=checklist_items,
                )
            else:
                await api_update_note(
                    get_token(),
                    editing_id,
                    title=title.strip() or "Untitled",
                    content="",
                    color=color,
                    is_pinned=pinned,
                    labels=labels,
                    checklist_items=checklist_items,
                )
            reset_and_close()
            if on_saved:
                on_saved()
        except ApiError as ex:
            set_error_text(str(ex))
            set_saving(False)

    checklist_rows = [
        ft.Row(
            [
                ft.ReorderableDragHandle(
                    key=f"drag_handle_{item['id']}",
                    content=ft.Icon(ft.Icons.DRAG_INDICATOR, size=18),
                    mouse_cursor=ft.MouseCursor.GRAB,
                ),
                ft.Checkbox(
                    value=item["checked"],
                    on_change=lambda e, i=i: toggle_item_checked(i),
                ),
                ft.TextField(
                    value=item["text"],
                    hint_text="รายการ",
                    border=ft.InputBorder.NONE,
                    expand=True,
                    autofocus=True,
                    on_change=lambda e, i=i: update_item_text(i, e.control.value),
                ),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_size=16,
                    on_click=lambda e, i=i: remove_item(i),
                ),
            ],
            key=item["id"],
        )
        for i, item in enumerate(items)
    ]

    checklist_view = ft.ReorderableListView(
        controls=checklist_rows,
        show_default_drag_handles=False,
        on_reorder=handle_reorder,
        height=56 * len(items),
    )

    editor = ft.Container(
        width=350,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.TextField(
                            value=title,
                            hint_text="ชื่อเรื่อง",
                            border=ft.InputBorder.NONE,
                            text_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD),
                            expand=True,
                            on_change=lambda e: set_title(e.control.value),
                        ),
                        ft.IconButton(icon=ft.Icons.CLOSE, on_click=lambda e: reset_and_close()),
                    ]
                ),
                checklist_view,
                ft.TextButton("+  รายการ", on_click=add_item),
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Text(name, size=12),
                                    ft.IconButton(
                                        icon=ft.Icons.CLOSE,
                                        icon_size=12,
                                        on_click=lambda e, n=name: remove_label(n),
                                    ),
                                ],
                                tight=True,
                                spacing=2,
                            ),
                            padding=ft.Padding.symmetric(horizontal=8, vertical=0),
                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                            border_radius=16,
                        )
                        for name in labels
                    ]
                    + [
                        ft.IconButton(
                            icon=ft.Icons.NEW_LABEL,
                            icon_size=18,
                            on_click=lambda e: set_picking_labels(True),
                        )
                    ],
                    wrap=True,
                ),
                ft.Container(height=20 if error_text else 0, content=ft.Text(error_text, color=ft.Colors.ERROR)),
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.PALETTE_OUTLINED,
                            on_click=lambda e: set_picking_color(True),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.PUSH_PIN if pinned else ft.Icons.PUSH_PIN_OUTLINED,
                            on_click=lambda e: set_pinned(not pinned),
                        ),
                        ft.Container(expand=True),
                        ft.TextButton(
                            content=ft.ProgressRing(width=16, height=16, stroke_width=2)
                            if saving
                            else ft.Text("บันทึก"),
                            on_click=save_note,
                            disabled=saving,
                        ),
                    ]
                ),
            ],
            tight=True,
        ),
    )

    ft.use_dialog(
        ft.AlertDialog(
            bgcolor=dialog_bgcolor_for(color),
            content=editor,
            on_dismiss=lambda: reset_and_close(),
        )
        if show
        else None
    )

    ft.use_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Text("เลือกสี"),
            content=BlockPicker(
                color=NOTE_COLOR_SWATCHES[color],
                available_colors=list(NOTE_COLOR_SWATCHES.values()),
                on_color_change=handle_color_pick,
            ),
            actions=[ft.TextButton("ปิด", on_click=lambda e: set_picking_color(False))],
        )
        if picking_color
        else None
    )

    ft.use_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Text("เลือก label"),
            content=ft.Column(
                [
                    ft.Checkbox(
                        label=lbl.name,
                        value=lbl.name in labels,
                        on_change=lambda e, n=lbl.name: toggle_label(n),
                    )
                    for lbl in available_labels
                ]
                + [
                    ft.Row(
                        [
                            ft.TextField(
                                value=new_label_text,
                                hint_text="label ใหม่",
                                expand=True,
                                on_change=lambda e: set_new_label_text(e.control.value),
                                on_submit=add_new_label,
                            ),
                            ft.IconButton(icon=ft.Icons.ADD, on_click=add_new_label),
                        ]
                    ),
                ],
                tight=True,
                width=300,
            ),
            actions=[ft.TextButton("ปิด", on_click=lambda e: set_picking_labels(False))],
        )
        if picking_labels
        else None
    )

    def open_for_new(e):
        set_editing_id(None)
        set_title("")
        set_items([])
        set_color("default")
        set_pinned(False)
        set_error_text("")
        set_labels([])
        set_new_label_text("")
        set_show(True)

    return ft.FloatingActionButton(icon=ft.Icons.ADD, on_click=open_for_new)


def note_card(note: Note, on_click=None) -> ft.Control:
    bgcolor = dialog_bgcolor_for(note.color)

    body: list[ft.Control] = [
        ft.Row(
            [
                ft.Text(note.title or "Untitled", weight=ft.FontWeight.BOLD, expand=True),
                ft.Icon(ft.Icons.PUSH_PIN, size=16) if note.is_pinned else ft.Container(),
            ]
        ),
    ]
    if note.content:
        body.append(ft.Text(note.content))

    for item in sorted(note.checklist_items, key=lambda i: i.order):
        body.append(
            ft.Row(
                [
                    ft.Checkbox(value=item.is_checked, disabled=True),
                    ft.Text(
                        item.text,
                        color=ft.Colors.ON_SURFACE_VARIANT if item.is_checked else None,
                    ),
                ]
            )
        )

    if note.labels:
        body.append(
            ft.Row(
                [
                    ft.Container(
                        content=ft.Text(name, size=11),
                        padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                        border_radius=12,
                    )
                    for name in note.labels
                ],
                wrap=True,
            )
        )

    return ft.Card(
        bgcolor=bgcolor,
        content=ft.Container(
            padding=12,
            content=ft.Column(body, tight=True),
            on_click=on_click,
        ),
    )


@ft.component
def NotesList(reload_ref=None, open_editor_ref=None):
    page = ft.context.page
    notes, set_notes = ft.use_state([])
    loading, set_loading = ft.use_state(True)
    error_text, set_error_text = ft.use_state("")

    async def load_notes():
        set_loading(True)
        set_error_text("")
        try:
            data = await api_list_notes(get_token())
            set_notes(data)
        except ApiError as ex:
            set_error_text(str(ex))
        finally:
            set_loading(False)

    if reload_ref is not None:
        reload_ref.current = lambda: page.run_task(load_notes)

    ft.use_effect(lambda: page.run_task(load_notes), [])

    if loading:
        return ft.Row([ft.ProgressRing()], alignment=ft.MainAxisAlignment.CENTER)

    if error_text:
        return ft.Text(error_text, color=ft.Colors.ERROR)

    if not notes:
        return ft.Text("ยังไม่มีโน้ต", color=ft.Colors.ON_SURFACE_VARIANT)

    def edit_note(note):
        if open_editor_ref is not None and open_editor_ref.current is not None:
            open_editor_ref.current(note)

    return ft.ListView(
        controls=[note_card(note, on_click=lambda e, n=note: edit_note(n)) for note in notes],
        spacing=8,
        expand=True,
    )


@ft.component
def Home():
    appbar_title = "Home"
    reload_notes_ref = ft.use_ref(None)
    open_editor_ref = ft.use_ref(None)
    content = NotesList(reload_ref=reload_notes_ref, open_editor_ref=open_editor_ref)
    fab = NoteEditorFab(
        on_saved=lambda: reload_notes_ref.current and reload_notes_ref.current(),
        open_ref=open_editor_ref,
    )

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
            set_session(data.token, data.refresh, data.user)
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


TEXT_STYLE_NAMES = [
    "body_large", "body_medium", "body_small",
    "display_large", "display_medium", "display_small",
    "headline_large", "headline_medium", "headline_small",
    "label_large", "label_medium", "label_small",
    "title_large", "title_medium", "title_small",
]


def build_text_theme() -> ft.TextTheme:
    """Poppins first, falling back to Prompt for glyphs it doesn't have (e.g. Thai)."""
    style = ft.TextStyle(font_family="Poppins", font_family_fallback=["Prompt"])
    return ft.TextTheme(**{name: style for name in TEXT_STYLE_NAMES})


def main(page: ft.Page):
    page.window.width = 440
    page.window.height = 800

    page.fonts = {
        "Poppins": "font/Poppins-Regular.ttf",
        "Prompt": "font/Prompt-Regular.ttf",
    }

    page.theme = ft.Theme(
        font_family="Poppins",
        text_theme=build_text_theme(),
        page_transitions=ft.PageTransitionsTheme(
            android=ft.PageTransitionTheme.NONE,
            ios=ft.PageTransitionTheme.NONE,
            linux=ft.PageTransitionTheme.NONE,
            macos=ft.PageTransitionTheme.NONE,
            windows=ft.PageTransitionTheme.NONE,
        ),
    )
    page.render_views(App)


if __name__ == "__main__":
    ft.run(main)
